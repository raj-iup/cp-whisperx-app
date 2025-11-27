#!/usr/bin/env python3
"""
Log Aggregation and Analysis Tool for CP-WhisperX-App

Aggregates logs from multiple jobs and generates analysis reports.

Usage:
    python tools/analyze-logs.py [OPTIONS]
    
Features:
    - Aggregate logs from all jobs
    - Find common errors
    - Generate timing reports
    - Export to JSON/CSV
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Tuple
import re

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import setup_logger

logger = setup_logger("log_analyzer", log_level="INFO", log_format="text")


class LogAnalyzer:
    """Analyze logs from CP-WhisperX-App"""
    
    def __init__(self, logs_dir: Path, job_logs_dir: Path):
        self.logs_dir = logs_dir
        self.job_logs_dir = job_logs_dir
        self.errors = []
        self.warnings = []
        self.job_stats = defaultdict(dict)
        
    def analyze_script_logs(self, days: int = 7) -> Dict:
        """Analyze main script logs (bootstrap, prepare-job, etc.)"""
        logger.info(f"Analyzing script logs from last {days} days...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = list(self.logs_dir.glob("*.log"))
        
        stats = {
            "total_files": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "scripts": defaultdict(int),
            "error_messages": [],
            "warning_messages": []
        }
        
        for log_file in log_files:
            # Check file age
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                continue
                
            stats["total_files"] += 1
            
            # Extract script name from filename
            # Format: YYYYMMDD-HHMMSS-scriptname.log
            parts = log_file.stem.split("-", 3)
            if len(parts) >= 4:
                script_name = parts[3]
                stats["scripts"][script_name] += 1
            
            # Parse log content
            try:
                with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                    for line in f:
                        if "[ERROR]" in line or "[CRITICAL]" in line:
                            stats["total_errors"] += 1
                            stats["error_messages"].append({
                                "file": log_file.name,
                                "message": line.strip()
                            })
                        elif "[WARN]" in line:
                            stats["total_warnings"] += 1
                            stats["warning_messages"].append({
                                "file": log_file.name,
                                "message": line.strip()
                            })
            except Exception as e:
                logger.warning(f"Could not parse {log_file.name}: {e}")
        
        return stats
    
    def analyze_job_logs(self, limit: int = 10) -> List[Dict]:
        """Analyze pipeline job logs"""
        logger.info(f"Analyzing last {limit} job logs...")
        
        # Find all job directories
        job_dirs = []
        for path in self.job_logs_dir.rglob("job.json"):
            job_dir = path.parent
            job_dirs.append((job_dir, path.stat().st_mtime))
        
        # Sort by modification time (newest first)
        job_dirs.sort(key=lambda x: x[1], reverse=True)
        job_dirs = job_dirs[:limit]
        
        job_stats = []
        
        for job_dir, _ in job_dirs:
            try:
                # Read job metadata
                job_json = job_dir / "job.json"
                with open(job_json) as f:
                    job_data = json.load(f)
                
                job_id = job_data.get("job_id", "unknown")
                workflow = job_data.get("workflow", "unknown")
                
                # Analyze logs in job directory
                logs_dir = job_dir / "logs"
                if not logs_dir.exists():
                    continue
                
                stage_logs = list(logs_dir.glob("*.log"))
                
                errors = 0
                warnings = 0
                stages_completed = []
                
                for log_file in stage_logs:
                    # Extract stage name from filename
                    # Format: NN_stagename_timestamp.log
                    match = re.match(r'(\d+)_([^_]+)_', log_file.name)
                    if match:
                        stage_num, stage_name = match.groups()
                        stages_completed.append(stage_name)
                    
                    # Count errors/warnings
                    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        errors += content.count("[ERROR]") + content.count("[CRITICAL]")
                        warnings += content.count("[WARN]")
                
                job_stats.append({
                    "job_id": job_id,
                    "workflow": workflow,
                    "job_dir": str(job_dir),
                    "stages_completed": len(stages_completed),
                    "stages": stages_completed,
                    "errors": errors,
                    "warnings": warnings,
                    "log_files": len(stage_logs)
                })
                
            except Exception as e:
                logger.warning(f"Could not analyze job {job_dir.name}: {e}")
        
        return job_stats
    
    def generate_report(self, script_stats: Dict, job_stats: List[Dict]) -> str:
        """Generate text report"""
        report = []
        report.append("=" * 70)
        report.append("CP-WHISPERX-APP LOG ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Script logs summary
        report.append("SCRIPT LOGS SUMMARY")
        report.append("-" * 70)
        report.append(f"Total log files analyzed: {script_stats['total_files']}")
        report.append(f"Total errors: {script_stats['total_errors']}")
        report.append(f"Total warnings: {script_stats['total_warnings']}")
        report.append("")
        
        if script_stats['scripts']:
            report.append("Scripts run:")
            for script, count in sorted(script_stats['scripts'].items()):
                report.append(f"  • {script}: {count} times")
        report.append("")
        
        # Recent errors
        if script_stats['error_messages']:
            report.append("RECENT ERRORS (Last 10):")
            report.append("-" * 70)
            for error in script_stats['error_messages'][-10:]:
                report.append(f"[{error['file']}]")
                report.append(f"  {error['message']}")
                report.append("")
        
        # Job logs summary
        report.append("JOB LOGS SUMMARY")
        report.append("-" * 70)
        report.append(f"Jobs analyzed: {len(job_stats)}")
        report.append("")
        
        if job_stats:
            total_errors = sum(j['errors'] for j in job_stats)
            total_warnings = sum(j['warnings'] for j in job_stats)
            report.append(f"Total errors across all jobs: {total_errors}")
            report.append(f"Total warnings across all jobs: {total_warnings}")
            report.append("")
            
            report.append("Recent jobs:")
            for job in job_stats[:10]:
                status = "✓" if job['errors'] == 0 else f"✗ ({job['errors']} errors)"
                report.append(f"  {status} {job['job_id']} - {job['workflow']}")
                report.append(f"      Stages: {', '.join(job['stages'][:5])}")
                if len(job['stages']) > 5:
                    report.append(f"              ... and {len(job['stages']) - 5} more")
        
        report.append("")
        report.append("=" * 70)
        
        return "\n".join(report)
    
    def export_json(self, script_stats: Dict, job_stats: List[Dict], output_file: Path):
        """Export analysis to JSON"""
        data = {
            "generated_at": datetime.now().isoformat(),
            "script_logs": script_stats,
            "job_logs": job_stats
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Exported JSON report to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze logs from CP-WhisperX-App",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Analyze script logs from last N days (default: 7)"
    )
    
    parser.add_argument(
        "--jobs",
        type=int,
        default=10,
        help="Analyze last N jobs (default: 10)"
    )
    
    parser.add_argument(
        "--json",
        type=str,
        help="Export analysis to JSON file"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Save report to text file"
    )
    
    args = parser.parse_args()
    
    # Setup paths
    logs_dir = PROJECT_ROOT / "logs"
    job_logs_dir = PROJECT_ROOT / "out"
    
    if not logs_dir.exists():
        logger.error(f"Logs directory not found: {logs_dir}")
        return 1
    
    # Run analysis
    analyzer = LogAnalyzer(logs_dir, job_logs_dir)
    
    script_stats = analyzer.analyze_script_logs(days=args.days)
    job_stats = analyzer.analyze_job_logs(limit=args.jobs)
    
    # Generate report
    report = analyzer.generate_report(script_stats, job_stats)
    
    # Output report
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w') as f:
            f.write(report)
        logger.info(f"Report saved to: {output_path}")
    else:
        print(report)
    
    # Export JSON if requested
    if args.json:
        json_path = Path(args.json)
        analyzer.export_json(script_stats, job_stats, json_path)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
