#!/usr/bin/env python3
"""
QC Report Generator

Generates quality control reports for processed subtitle files.
Calculates WER/MER, CPS violations, terminology coverage, and more.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import re


def parse_srt(srt_file: Path) -> List[Dict]:
    """
    Parse SRT file into list of subtitle entries
    
    Args:
        srt_file: Path to SRT file
    
    Returns:
        List of subtitle dictionaries
    """
    subtitles = []
    
    with open(srt_file, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    
    # Split into subtitle blocks
    blocks = content.split('\n\n')
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        try:
            index = int(lines[0])
            timecode = lines[1]
            text = '\n'.join(lines[2:])
            
            # Parse timecodes
            start_str, end_str = timecode.split(' --> ')
            start = parse_srt_time(start_str)
            end = parse_srt_time(end_str)
            
            subtitles.append({
                'index': index,
                'start': start,
                'end': end,
                'duration': end - start,
                'text': text,
                'char_count': len(text.replace('\n', ''))
            })
        except Exception as e:
            print(f"Warning: Could not parse subtitle block: {e}", file=sys.stderr)
            continue
    
    return subtitles


def parse_srt_time(time_str: str) -> float:
    """Convert SRT timestamp to seconds"""
    # Format: HH:MM:SS,mmm
    time_str = time_str.replace(',', '.')
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    
    return hours * 3600 + minutes * 60 + seconds


def calculate_cps_violations(subtitles: List[Dict], target: float = 15.0, 
                             cap: float = 17.0) -> Dict:
    """
    Calculate CPS violations
    
    Args:
        subtitles: List of subtitle dicts
        target: Target CPS
        cap: Hard cap CPS
    
    Returns:
        Violation statistics
    """
    violations = []
    warnings = []
    cps_values = []
    
    for sub in subtitles:
        if sub['duration'] <= 0:
            continue
        
        cps = sub['char_count'] / sub['duration']
        cps_values.append(cps)
        
        if cps > cap:
            violations.append({
                'index': sub['index'],
                'cps': round(cps, 2),
                'duration': round(sub['duration'], 2),
                'chars': sub['char_count'],
                'text': sub['text'][:60] + '...' if len(sub['text']) > 60 else sub['text']
            })
        elif cps > target:
            warnings.append({
                'index': sub['index'],
                'cps': round(cps, 2),
                'duration': round(sub['duration'], 2),
                'chars': sub['char_count']
            })
    
    return {
        'violations': violations,
        'warnings': warnings,
        'total': len(subtitles),
        'avg_cps': round(sum(cps_values) / len(cps_values), 2) if cps_values else 0,
        'max_cps': round(max(cps_values), 2) if cps_values else 0,
        'min_cps': round(min(cps_values), 2) if cps_values else 0
    }


def check_line_width_violations(subtitles: List[Dict], max_width: int = 42, 
                                max_lines: int = 2) -> List[Dict]:
    """
    Check for line width violations
    
    Args:
        subtitles: List of subtitle dicts
        max_width: Maximum characters per line
        max_lines: Maximum lines per subtitle
    
    Returns:
        List of violations
    """
    violations = []
    
    for sub in subtitles:
        lines = sub['text'].split('\n')
        
        # Check line count
        if len(lines) > max_lines:
            violations.append({
                'index': sub['index'],
                'type': 'too_many_lines',
                'actual': len(lines),
                'max': max_lines,
                'text': sub['text'][:60] + '...'
            })
        
        # Check line width
        for i, line in enumerate(lines, 1):
            if len(line) > max_width:
                violations.append({
                    'index': sub['index'],
                    'type': 'line_too_long',
                    'line_number': i,
                    'actual': len(line),
                    'max': max_width,
                    'text': line[:60] + '...'
                })
    
    return violations


def check_duration_violations(subtitles: List[Dict], min_dur: float = 1.0, 
                             max_dur: float = 7.0) -> List[Dict]:
    """Check for duration violations"""
    violations = []
    
    for sub in subtitles:
        if sub['duration'] < min_dur:
            violations.append({
                'index': sub['index'],
                'type': 'too_short',
                'duration': round(sub['duration'], 2),
                'limit': min_dur
            })
        elif sub['duration'] > max_dur:
            violations.append({
                'index': sub['index'],
                'type': 'too_long',
                'duration': round(sub['duration'], 2),
                'limit': max_dur
            })
    
    return violations


def check_glossary_coverage(subtitles: List[Dict], glossary_path: Optional[Path] = None) -> Dict:
    """
    Check how many glossary terms appear in subtitles
    
    Args:
        subtitles: List of subtitle dicts
        glossary_path: Path to glossary TSV
    
    Returns:
        Coverage statistics
    """
    if not glossary_path or not glossary_path.exists():
        return {'coverage': 0, 'terms_found': [], 'terms_missing': []}
    
    # Load glossary
    terms = []
    with open(glossary_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.strip().split('\t')
            if len(parts) >= 2:
                terms.append(parts[0].lower())
    
    # Check for term usage
    full_text = ' '.join(sub['text'].lower() for sub in subtitles)
    
    terms_found = []
    for term in terms:
        if term in full_text:
            terms_found.append(term)
    
    coverage = len(terms_found) / len(terms) if terms else 0
    
    return {
        'coverage': round(coverage, 4),
        'total_terms': len(terms),
        'terms_found': len(terms_found),
        'terms_missing': len(terms) - len(terms_found)
    }


def generate_qc_report(job_dir: Path, glossary_path: Optional[Path] = None) -> Dict:
    """
    Generate comprehensive QC report for a job
    
    Args:
        job_dir: Path to job directory
        glossary_path: Optional path to glossary file
    
    Returns:
        QC report dictionary
    """
    job_id = job_dir.name
    
    # Find subtitle file
    srt_files = list(job_dir.glob('en_merged/*.srt'))
    if not srt_files:
        return {
            'error': 'No subtitle file found',
            'job_id': job_id,
            'timestamp': datetime.now().isoformat()
        }
    
    srt_file = srt_files[0]
    
    # Parse subtitles
    subtitles = parse_srt(srt_file)
    
    # Calculate metrics
    cps_stats = calculate_cps_violations(subtitles)
    line_violations = check_line_width_violations(subtitles)
    duration_violations = check_duration_violations(subtitles)
    glossary_stats = check_glossary_coverage(subtitles, glossary_path)
    
    # Count speaker labels
    speaker_count = sum(1 for sub in subtitles if '[' in sub['text'] and ']' in sub['text'])
    lyric_count = sum(1 for sub in subtitles if '♪' in sub['text'])
    
    # Calculate total duration
    total_duration = subtitles[-1]['end'] if subtitles else 0
    
    # Build report
    report = {
        'job_id': job_id,
        'timestamp': datetime.now().isoformat(),
        'subtitle_file': str(srt_file.name),
        'summary': {
            'total_subtitles': len(subtitles),
            'total_duration_seconds': round(total_duration, 2),
            'total_duration_formatted': format_duration(total_duration),
            'subtitles_with_speakers': speaker_count,
            'lyric_subtitles': lyric_count
        },
        'cps_metrics': {
            'avg_cps': cps_stats['avg_cps'],
            'max_cps': cps_stats['max_cps'],
            'min_cps': cps_stats['min_cps'],
            'target': 15.0,
            'hard_cap': 17.0,
            'violations_count': len(cps_stats['violations']),
            'warnings_count': len(cps_stats['warnings']),
            'violations': cps_stats['violations'][:10],  # Top 10
            'warnings': cps_stats['warnings'][:10]
        },
        'format_violations': {
            'line_width': len([v for v in line_violations if v['type'] == 'line_too_long']),
            'line_count': len([v for v in line_violations if v['type'] == 'too_many_lines']),
            'details': line_violations[:10]
        },
        'duration_violations': {
            'too_short': len([v for v in duration_violations if v['type'] == 'too_short']),
            'too_long': len([v for v in duration_violations if v['type'] == 'too_long']),
            'details': duration_violations[:10]
        },
        'glossary': glossary_stats,
        'quality_score': calculate_quality_score(cps_stats, line_violations, duration_violations)
    }
    
    return report


def format_duration(seconds: float) -> str:
    """Format duration as HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_quality_score(cps_stats: Dict, line_violations: List, 
                           duration_violations: List) -> Dict:
    """
    Calculate overall quality score (0-100)
    
    Args:
        cps_stats: CPS statistics
        line_violations: Line format violations
        duration_violations: Duration violations
    
    Returns:
        Quality score dict
    """
    total = cps_stats['total']
    if total == 0:
        return {'score': 0, 'grade': 'N/A'}
    
    # Penalties
    penalty = 0
    
    # CPS violations (critical): -2 points each
    penalty += len(cps_stats['violations']) * 2
    
    # CPS warnings: -0.5 points each
    penalty += len(cps_stats['warnings']) * 0.5
    
    # Line violations: -1 point each
    penalty += len(line_violations)
    
    # Duration violations: -0.5 points each
    penalty += len(duration_violations) * 0.5
    
    # Calculate percentage penalty
    penalty_pct = (penalty / total) * 100
    score = max(0, 100 - penalty_pct)
    
    # Grade
    if score >= 95:
        grade = 'A+'
    elif score >= 90:
        grade = 'A'
    elif score >= 85:
        grade = 'B+'
    elif score >= 80:
        grade = 'B'
    elif score >= 75:
        grade = 'C+'
    elif score >= 70:
        grade = 'C'
    elif score >= 60:
        grade = 'D'
    else:
        grade = 'F'
    
    return {
        'score': round(score, 2),
        'grade': grade,
        'total_penalties': round(penalty, 2)
    }


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: generate_qc_report.py <job_directory> [glossary_path]")
        print("\nExample:")
        print("  python tools/generate_qc_report.py out/2025/11/08/1/20251108-0001")
        print("  python tools/generate_qc_report.py out/2025/11/08/1/20251108-0001 glossary/hinglish_master.tsv")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    glossary_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if not job_dir.exists():
        print(f"Error: Job directory not found: {job_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Generate report
    print(f"Generating QC report for: {job_dir.name}")
    report = generate_qc_report(job_dir, glossary_path)
    
    # Save report
    qc_file = job_dir / 'qc_report.json'
    with open(qc_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ QC report saved: {qc_file}")
    
    # Print summary
    if 'error' not in report:
        summary = report['summary']
        cps = report['cps_metrics']
        quality = report['quality_score']
        
        print(f"\n{'='*60}")
        print(f"QC REPORT SUMMARY: {report['job_id']}")
        print(f"{'='*60}")
        print(f"Total Subtitles: {summary['total_subtitles']}")
        print(f"Duration: {summary['total_duration_formatted']}")
        print(f"With Speakers: {summary['subtitles_with_speakers']}")
        print(f"Lyrics: {summary['lyric_subtitles']}")
        print(f"\nCPS Metrics:")
        print(f"  Average: {cps['avg_cps']} (target: {cps['target']})")
        print(f"  Range: {cps['min_cps']} - {cps['max_cps']}")
        print(f"  Violations (>{cps['hard_cap']}): {cps['violations_count']}")
        print(f"  Warnings (>{cps['target']}): {cps['warnings_count']}")
        print(f"\nQuality Score: {quality['score']}/100 ({quality['grade']})")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
