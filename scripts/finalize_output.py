#!/usr/bin/env python3
"""
Final Output Organization Stage
Organizes final output by creating a title-based directory and moving files
"""

import sys
import os
import re
import shutil
from pathlib import Path
from datetime import datetime


def setup_logging():
    """Setup basic logging"""
    import logging
    
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [finalize] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def sanitize_title(title: str) -> str:
    """
    Sanitize title for use as directory/file name
    
    Args:
        title: Movie title
    
    Returns:
        Sanitized title safe for filesystem
    """
    # Remove or replace problematic characters
    sanitized = title.strip()
    
    # Replace spaces and special chars
    sanitized = re.sub(r'[<>:"/\\|?*]', '', sanitized)
    sanitized = re.sub(r'\s+', '_', sanitized)
    
    # Remove trailing dots and spaces
    sanitized = sanitized.rstrip('._')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized


def extract_title_from_log(log_file: Path, logger) -> str:
    """
    Extract title from orchestrator log (line 18)
    
    Args:
        log_file: Path to orchestrator log
        logger: Logger instance
    
    Returns:
        Movie title or None
    """
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            if len(lines) >= 18:
                line_18 = lines[17]  # 0-indexed, so line 18 is index 17
                
                # Parse: [timestamp] [orchestrator] [INFO] Title: Movie Name
                match = re.search(r'Title:\s*(.+)$', line_18.strip())
                if match:
                    title = match.group(1).strip()
                    logger.info(f"Extracted title from log: {title}")
                    return title
                else:
                    logger.warning(f"Line 18 doesn't contain 'Title:' pattern: {line_18}")
            else:
                logger.warning(f"Log file has fewer than 18 lines: {len(lines)}")
    
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
    
    return None


def find_orchestrator_log(job_dir: Path, logger) -> Path:
    """
    Find the orchestrator log file
    
    Args:
        job_dir: Job directory
        logger: Logger instance
    
    Returns:
        Path to orchestrator log or None
    """
    logs_dir = job_dir / "logs"
    
    if not logs_dir.exists():
        logger.error(f"Logs directory not found: {logs_dir}")
        return None
    
    # Find orchestrator log (starts with 00_orchestrator)
    orch_logs = list(logs_dir.glob("00_orchestrator_*.log"))
    
    if not orch_logs:
        logger.error("No orchestrator log found")
        return None
    
    if len(orch_logs) > 1:
        logger.warning(f"Multiple orchestrator logs found, using first: {orch_logs[0]}")
    
    return orch_logs[0]


def organize_final_output(job_dir: Path, logger):
    """
    Organize final output into title-based directory
    
    Args:
        job_dir: Job directory
        logger: Logger instance
    """
    logger.info("=" * 60)
    logger.info("FINAL OUTPUT ORGANIZATION")
    logger.info("=" * 60)
    
    # 1. Find orchestrator log
    logger.info("Step 1: Finding orchestrator log...")
    orch_log = find_orchestrator_log(job_dir, logger)
    
    if not orch_log:
        logger.error("Cannot proceed without orchestrator log")
        return False
    
    logger.info(f"Found log: {orch_log.name}")
    
    # 2. Extract title
    logger.info("Step 2: Extracting title from log...")
    title = extract_title_from_log(orch_log, logger)
    
    if not title:
        logger.error("Cannot proceed without title")
        return False
    
    # 3. Sanitize title
    sanitized_title = sanitize_title(title)
    logger.info(f"Sanitized title: {sanitized_title}")
    
    # 4. Check for final_output.mp4
    final_output = job_dir / "final_output.mp4"
    
    if not final_output.exists():
        logger.error(f"Final output not found: {final_output}")
        return False
    
    logger.info(f"Found final output: {final_output}")
    logger.info(f"File size: {final_output.stat().st_size / (1024*1024):.2f} MB")
    
    # 5. Create title directory
    title_dir = job_dir / sanitized_title
    
    if title_dir.exists():
        logger.warning(f"Title directory already exists: {title_dir}")
        
        # Check if file already there
        target_file = title_dir / f"{sanitized_title}.mp4"
        if target_file.exists():
            logger.info(f"Output already organized at: {target_file}")
            return True
    else:
        logger.info(f"Creating title directory: {title_dir}")
        title_dir.mkdir(parents=True, exist_ok=True)
    
    # 6. Move and rename final output
    target_file = title_dir / f"{sanitized_title}.mp4"
    
    logger.info(f"Moving final output...")
    logger.info(f"  From: {final_output}")
    logger.info(f"  To:   {target_file}")
    
    try:
        shutil.move(str(final_output), str(target_file))
        logger.info("✓ Final output moved successfully")
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        return False
    
    # 7. Copy subtitle files if they exist
    srt_files = list(job_dir.glob("*.srt"))
    
    if srt_files:
        logger.info(f"Found {len(srt_files)} subtitle files to copy...")
        
        for srt_file in srt_files:
            # Rename subtitle to match video
            if srt_file.name == "final_output.srt":
                target_srt = title_dir / f"{sanitized_title}.srt"
            else:
                target_srt = title_dir / srt_file.name
            
            try:
                shutil.copy2(str(srt_file), str(target_srt))
                logger.info(f"  ✓ Copied: {srt_file.name}")
            except Exception as e:
                logger.warning(f"  ✗ Failed to copy {srt_file.name}: {e}")
    
    # 8. Create a summary file
    summary_file = title_dir / "README.txt"
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Movie: {title}\n")
            f.write(f"Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Job ID: {job_dir.name}\n")
            f.write(f"\n")
            f.write(f"Files:\n")
            f.write(f"- {sanitized_title}.mp4 (final video with subtitles)\n")
            
            if srt_files:
                for srt_file in srt_files:
                    f.write(f"- {srt_file.name} (subtitle file)\n")
            
            f.write(f"\n")
            f.write(f"Pipeline output directory: {job_dir}\n")
        
        logger.info("✓ Created README.txt")
    except Exception as e:
        logger.warning(f"Could not create README: {e}")
    
    # 9. Final summary
    logger.info("")
    logger.info("=" * 60)
    logger.info("ORGANIZATION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Title: {title}")
    logger.info(f"Output directory: {title_dir}")
    logger.info(f"Video file: {target_file.name}")
    logger.info(f"")
    logger.info(f"Full path: {target_file}")
    logger.info("=" * 60)
    
    return True


def main():
    """Main entry point"""
    logger = setup_logging()
    
    # Get job directory from command line or environment
    if len(sys.argv) > 1:
        job_dir = Path(sys.argv[1])
    else:
        job_dir_str = os.environ.get('JOB_DIR')
        if not job_dir_str:
            logger.error("Usage: finalize_output.py <job_directory>")
            logger.error("   or set JOB_DIR environment variable")
            sys.exit(1)
        job_dir = Path(job_dir_str)
    
    if not job_dir.exists():
        logger.error(f"Job directory not found: {job_dir}")
        sys.exit(1)
    
    logger.info(f"Job directory: {job_dir}")
    
    # Organize output
    success = organize_final_output(job_dir, logger)
    
    if success:
        logger.info("Finalization completed successfully")
        sys.exit(0)
    else:
        logger.error("Finalization failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
