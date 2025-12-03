"""
Job management for pipeline orchestration.

Handles:
- Job ID generation (YYYYMMDD-SEQ format)
- Job-based directory structure (Year/Month/Day/UserID/JobID)
- Job-specific environment file management
- Job manifest tracking
"""
# Standard library
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json


class JobManager:
    """Manages job IDs, directories, and environment files."""
    
    def __init__(self, config_dir: Path = None, output_root: Path = None, log_root: Path = None):
        """Initialize job manager."""
        self.config_dir = config_dir or Path("config")
        self.output_root = output_root or Path("out")
        self.log_root = log_root or Path("logs")
        self.job_id = None
        self.user_id = None
        self.job_env_file = None
        self.job_output_dir = None
        self.job_log_dir = None
    
    def generate_job_id(self) -> str:
        """
        Generate a unique job ID based on current date and sequence.
        Format: YYYYMMDD-NNN (e.g., 20251030-001)
        
        Returns:
            Generated job ID
        """
        now = datetime.now()
        date_prefix = now.strftime("%Y%m%d")
        
        # Find next sequence number for today
        sequence = 1
        year_dir = self.output_root / str(now.year)
        if year_dir.exists():
            month_dir = year_dir / f"{now.month:02d}"
            if month_dir.exists():
                day_dir = month_dir / f"{now.day:02d}"
                if day_dir.exists():
                    # Find all existing job IDs for today
                    existing_jobs = set()
                    for user_dir in day_dir.iterdir():
                        if user_dir.is_dir():
                            for job_dir in user_dir.iterdir():
                                if job_dir.is_dir() and job_dir.name.startswith(date_prefix):
                                    existing_jobs.add(job_dir.name)
                    
                    # Find highest sequence
                    for job_id in existing_jobs:
                        try:
                            seq = int(job_id.split('-')[1])
                            if seq >= sequence:
                                sequence = seq + 1
                        except (IndexError, ValueError):
                            pass
        
        return f"{date_prefix}-{sequence:03d}"
    
    def create_job(self, user_id: int = 1, base_env_file: Path = None) -> Dict[str, Any]:
        """
        Create a new job with ID, directories, and environment file.
        
        Args:
            user_id: User ID (default: 1)
            base_env_file: Base environment file to copy (default: config/.env)
        
        Returns:
            Dict with job information
        """
        # Generate job ID
        self.job_id = self.generate_job_id()
        self.user_id = user_id
        
        # Parse job ID for directory structure
        now = datetime.now()
        year = now.year
        month = now.month
        day = now.day
        
        # Create directory structure: Year/Month/Day/UserID/JobID
        base_path_parts = [str(year), f"{month:02d}", f"{day:02d}", str(user_id), self.job_id]
        
        # Create output directory
        self.job_output_dir = self.output_root
        for part in base_path_parts:
            self.job_output_dir = self.job_output_dir / part
        self.job_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create log directory
        self.job_log_dir = self.log_root
        for part in base_path_parts:
            self.job_log_dir = self.job_log_dir / part
        self.job_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create job-specific environment file
        if base_env_file is None:
            base_env_file = self.config_dir / ".env"
        
        if not base_env_file.exists():
            raise FileNotFoundError(f"Base environment file not found: {base_env_file}")
        
        # Copy base env to job-specific env
        self.job_env_file = self.config_dir / f".env.job_{self.job_id}"
        shutil.copy2(base_env_file, self.job_env_file)
        
        # Update job env file with job-specific settings
        self._update_job_env_file()
        
        # Copy job env to output directory for records
        job_env_backup = self.job_output_dir / "job.env"
        shutil.copy2(self.job_env_file, job_env_backup)
        
        # Create job info file
        job_info = {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "output_dir": str(self.job_output_dir),
            "log_dir": str(self.job_log_dir),
            "env_file": str(self.job_env_file),
            "env_backup": str(job_env_backup)
        }
        
        job_info_file = self.job_output_dir / "job_info.json"
        with open(job_info_file, 'w') as f:
            json.dump(job_info, f, indent=2)
        
        return job_info
    
    def _update_job_env_file(self):
        """Update job environment file with job-specific values."""
        # Read current env file
        with open(self.job_env_file, 'r') as f:
            lines = f.readlines()
        
        # Convert paths to container paths (all containers mount to /app)
        container_output_dir = f"/app/{self.job_output_dir}"
        container_log_dir = f"/app/{self.job_log_dir}"
        
        # Update or add job-specific variables
        updated_lines = []
        found_vars = {
            'JOB_ID': False,
            'USER_ID': False,
            'OUTPUT_ROOT': False,
            'LOG_ROOT': False
        }
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('JOB_ID='):
                updated_lines.append(f"JOB_ID={self.job_id}\n")
                found_vars['JOB_ID'] = True
            elif stripped.startswith('USER_ID='):
                updated_lines.append(f"USER_ID={self.user_id}\n")
                found_vars['USER_ID'] = True
            elif stripped.startswith('OUTPUT_ROOT='):
                updated_lines.append(f"OUTPUT_ROOT={container_output_dir}\n")
                found_vars['OUTPUT_ROOT'] = True
            elif stripped.startswith('LOG_ROOT='):
                updated_lines.append(f"LOG_ROOT={container_log_dir}\n")
                found_vars['LOG_ROOT'] = True
            else:
                updated_lines.append(line)
        
        # Add missing variables
        if not found_vars['JOB_ID']:
            updated_lines.append(f"\n# Job Configuration\nJOB_ID={self.job_id}\n")
        if not found_vars['USER_ID']:
            updated_lines.append(f"USER_ID={self.user_id}\n")
        if not found_vars['OUTPUT_ROOT']:
            updated_lines.append(f"OUTPUT_ROOT={container_output_dir}\n")
        if not found_vars['LOG_ROOT']:
            updated_lines.append(f"LOG_ROOT={container_log_dir}\n")
        
        # Write updated file
        with open(self.job_env_file, 'w') as f:
            f.writelines(updated_lines)
    
    def cleanup_job_env(self):
        """Clean up job-specific environment file after completion."""
        if self.job_env_file and self.job_env_file.exists():
            # Keep backup in output directory, remove from config
            self.job_env_file.unlink()
    
    def get_job_env_path(self) -> Path:
        """Get path to job-specific environment file."""
        return self.job_env_file
    
    def get_job_output_dir(self) -> Path:
        """Get job output directory."""
        return self.job_output_dir
    
    def get_job_log_dir(self) -> Path:
        """Get job log directory."""
        return self.job_log_dir
