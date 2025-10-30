#!/usr/bin/env python3
"""
CP-WhisperX-App Pipeline Orchestrator (Enhanced)
Runs the complete dockerized pipeline with manifest tracking and resume capability
"""
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, 'shared')
sys.path.insert(0, 'scripts')

from config import load_config
from logger import PipelineLogger
from utils import parse_filename, save_json
from manifest import ManifestBuilder


# Stage configuration following arch/workflow-arch.txt:
# (stage_name, next_stage, service_name, timeout_seconds, critical)
# Sequential pipeline: demux → tmdb → pre-ner → silero-vad → pyannote-vad → 
#                      diarization → asr → post-ner → subtitle-gen → mux
STAGE_DEFINITIONS = [
    ("demux", "tmdb", "demux", 600, True),                    # FFmpeg demux: extract 16kHz mono audio
    ("tmdb", "pre_ner", "tmdb", 120, True),                   # TMDB metadata fetch
    ("pre_ner", "silero_vad", "pre-ner", 300, True),          # Pre-ASR NER extraction
    ("silero_vad", "pyannote_vad", "silero-vad", 1800, True), # Silero VAD: coarse speech segmentation
    ("pyannote_vad", "diarization", "pyannote-vad", 3600, True), # PyAnnote VAD: refined boundaries
    ("diarization", "asr", "diarization", 1800, True),        # PyAnnote diarization: speaker labeling
    ("asr", "post_ner", "asr", 3600, True),                   # WhisperX ASR + forced alignment
    ("post_ner", "subtitle_gen", "post-ner", 600, True),      # Post-ASR NER: entity correction
    ("subtitle_gen", "mux", "subtitle-gen", 300, True),       # Subtitle generation (.srt)
    ("mux", None, "mux", 600, True),                          # FFmpeg mux: embed subtitles
]


class PipelineOrchestrator:
    """Orchestrates the complete pipeline execution with manifest tracking."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize orchestrator with configuration."""
        self.config = load_config(config_file)
        
        # Setup logging
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.logger = PipelineLogger("orchestrator", log_file)
        
        self.manifest = None
        self.start_time = datetime.now()
        self.movie_dir = None
        
    def should_skip_stage(self, stage_name: str) -> bool:
        """Check if stage should be skipped based on manifest."""
        if not self.manifest:
            return False
        completed = self.manifest.data["pipeline"].get("completed_stages", [])
        return stage_name in completed
    
    def verify_stage_output(self, stage_name: str) -> bool:
        """
        Verify that stage produced expected output files.
        
        Returns:
            True if verification passed, False otherwise
        """
        validations = {
            "demux": lambda: (self.movie_dir / "audio" / "audio.wav").exists(),
            "tmdb": lambda: (self.movie_dir / "metadata" / "tmdb_data.json").exists(),
            "pre_ner": lambda: (self.movie_dir / "entities" / "pre_ner.json").exists(),
            "silero_vad": lambda: (self.movie_dir / "vad" / "silero_segments.json").exists(),
            "pyannote_vad": lambda: (self.movie_dir / "vad" / "pyannote_segments.json").exists(),
            "diarization": lambda: (self.movie_dir / "diarization" / "speaker_segments.json").exists(),
            "asr": lambda: (self.movie_dir / "transcription" / "transcript.json").exists(),
            "post_ner": lambda: (self.movie_dir / "entities" / "post_ner.json").exists(),
            "subtitle_gen": lambda: (self.movie_dir / "subtitles" / "subtitles.srt").exists(),
            "mux": lambda: (self.movie_dir / "final_output.mp4").exists(),
        }
        
        if stage_name in validations:
            try:
                result = validations[stage_name]()
                if not result:
                    self.logger.warning(f"Validation failed for {stage_name}: expected output not found")
                return result
            except Exception as e:
                self.logger.warning(f"Validation error for {stage_name}: {e}")
                return False
        
        # No validation defined, assume OK
        return True
        
    def run_docker_step(self, service_name: str, args: List[str] = None, timeout: int = 3600) -> bool:
        """
        Run a single pipeline step in Docker container with timeout.
        
        Args:
            service_name: Docker Compose service name
            args: Additional arguments to pass to container
            timeout: Maximum execution time in seconds
        
        Returns:
            True if step succeeded, False otherwise
        """
        cmd = [
            "docker", "compose", "-f", "docker-compose.yml",
            "run", "--rm", service_name
        ]
        
        if args:
            cmd.extend(args)
        
        self.logger.debug(f"Command: {' '.join(cmd)}")
        self.logger.debug(f"Timeout: {timeout}s")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            
            if result.stdout:
                self.logger.debug(f"Output: {result.stdout}")
            
            return True
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Step timed out after {timeout}s")
            return False
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Step failed with exit code {e.returncode}")
            if e.stderr:
                self.logger.error(f"Error: {e.stderr}")
            return False
        
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return False
    
    def run_pipeline(self, input_file: str) -> bool:
        """
        Run the complete pipeline with manifest tracking and resume capability.
        
        Args:
            input_file: Path to input video file
        
        Returns:
            True if pipeline completed successfully, False otherwise
        """
        self.logger.info("="*60)
        self.logger.info("CP-WHISPERX-APP PIPELINE STARTED")
        self.logger.info("="*60)
        self.logger.info(f"Input: {input_file}")
        
        # Validate input
        input_path = Path(input_file)
        if not input_path.exists():
            self.logger.error(f"Input file not found: {input_file}")
            return False
        
        # Parse filename
        file_info = parse_filename(input_path.name)
        title = file_info['title']
        year = file_info.get('year')
        
        self.logger.info(f"Title: {title}")
        if year:
            self.logger.info(f"Year: {year}")
        
        # Setup output directory
        output_root = Path(self.config.output_root)
        output_root.mkdir(parents=True, exist_ok=True)
        
        if year:
            dir_name = f"{title.replace(' ', '_')}_{year}"
        else:
            dir_name = title.replace(' ', '_')
        
        self.movie_dir = output_root / dir_name
        self.movie_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize manifest
        manifest_file = self.movie_dir / "manifest.json"
        self.manifest = ManifestBuilder(manifest_file)
        self.manifest.set_input(str(input_path), title, year, None)
        self.manifest.set_output_dir(str(self.movie_dir))
        
        # Check for resume
        if manifest_file.exists():
            completed = self.manifest.data["pipeline"].get("completed_stages", [])
            skipped = self.manifest.data["pipeline"].get("skipped_stages", [])
            if completed or skipped:
                self.logger.info("")
                self.logger.info("📋 RESUMING FROM PREVIOUS RUN")
                self.logger.info(f"   Completed: {', '.join(completed) if completed else 'none'}")
                if skipped:
                    self.logger.info(f"   Skipped: {', '.join(skipped)}")
                self.logger.info("")
        
        # Execute stages
        total_stages = len(STAGE_DEFINITIONS)
        for idx, (stage_name, next_stage, service, timeout, critical) in enumerate(STAGE_DEFINITIONS, 1):
            self.logger.info("")
            self.logger.info("="*60)
            self.logger.info(f"STAGE {idx}/{total_stages}: {stage_name.upper()}")
            self.logger.info("="*60)
            
            # Check if should skip
            if self.should_skip_stage(stage_name):
                self.logger.info(f"⏭️  Skipping - already completed successfully")
                continue
            
            # Run stage with timing
            start_time = time.time()
            
            try:
                # Prepare arguments based on stage
                args = self._get_stage_args(stage_name, input_path, file_info)
                
                # Run the docker container
                self.logger.info(f"Running {service} container (timeout: {timeout}s)...")
                success = self.run_docker_step(service, args, timeout=timeout)
                
                duration = time.time() - start_time
                
                if not success:
                    raise Exception(f"Container execution failed")
                
                # Verify output
                if not self.verify_stage_output(stage_name):
                    self.logger.warning(f"Output verification failed, but continuing...")
                
                # Record success in manifest
                self.manifest.set_pipeline_step(
                    stage_name,
                    True,
                    completed=True,
                    next_stage=next_stage,
                    status="success",
                    duration=duration
                )
                
                self.logger.info(f"✓ Stage completed in {duration:.1f}s")
                self.logger.info(f"Progress: {idx}/{total_stages} stages complete")
                
            except Exception as e:
                duration = time.time() - start_time
                error_msg = str(e)
                
                self.logger.error(f"✗ Stage failed: {error_msg}")
                self.logger.error(f"Duration before failure: {duration:.1f}s")
                
                if critical:
                    # Critical failure - stop pipeline
                    self.manifest.set_pipeline_step(
                        stage_name,
                        False,
                        completed=True,
                        next_stage=None,
                        status="failed",
                        error=error_msg,
                        duration=duration
                    )
                    self.manifest.finalize(status="failed")
                    
                    self.logger.error("")
                    self.logger.error("="*60)
                    self.logger.error("PIPELINE FAILED - CRITICAL STAGE ERROR")
                    self.logger.error("="*60)
                    return False
                else:
                    # Optional failure - skip and continue
                    self.manifest.set_pipeline_step(
                        stage_name,
                        False,
                        completed=True,
                        next_stage=next_stage,
                        status="skipped",
                        notes=f"Failed: {error_msg}",
                        duration=duration
                    )
                    
                    self.logger.warning(f"⚠️  Optional stage failed - continuing to next stage")
        
        # Pipeline completed successfully
        total_duration = time.time() - self.start_time.timestamp()
        
        self.logger.info("")
        self.logger.info("="*60)
        self.logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
        self.logger.info("="*60)
        self.logger.info(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
        self.logger.info(f"Output directory: {self.movie_dir}")
        self.logger.info(f"Manifest: {manifest_file}")
        
        # Finalize manifest
        self.manifest.finalize(status="completed")
        
        return True
    
    def _get_stage_args(self, stage_name: str, input_path: Path, file_info: dict) -> List[str]:
        """
        Get command-line arguments for a specific stage.
        
        Args:
            stage_name: Name of the stage
            input_path: Input video file path
            file_info: Parsed filename information
        
        Returns:
            List of arguments to pass to the container
        """
        # Most stages just need the movie directory
        movie_dir_arg = str(self.movie_dir)
        
        if stage_name == "demux":
            return [str(input_path)]
        elif stage_name == "tmdb":
            args = [file_info['title']]
            if file_info.get('year'):
                args.append(str(file_info['year']))
            return args
        elif stage_name == "mux":
            output_file = self.movie_dir / "final_output.mp4"
            subtitle_file = self.movie_dir / "subtitles" / "subtitles.srt"
            return [str(input_path), str(subtitle_file), str(output_file)]
        else:
            # Most stages take the movie directory as the argument
            return [movie_dir_arg]


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <input_file>")
        print("   or: python pipeline.py <input_file> <config_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    config_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Verify preflight check
    preflight_results = Path("out/preflight_results.json")
    
    if not preflight_results.exists():
        print("\n⚠️  No preflight check found")
        print("🔍 Running preflight validation...")
        result = subprocess.run(["python", "preflight.py"], capture_output=False)
        if result.returncode != 0:
            print("\n❌ Preflight checks failed. Please fix issues before running pipeline.")
            sys.exit(1)
    else:
        try:
            with open(preflight_results) as f:
                results = json.load(f)
            
            # Check if recent and successful
            last_run = datetime.fromisoformat(results["timestamp"])
            age = datetime.now() - last_run
            
            if age > timedelta(hours=24):
                print(f"\n⚠️  Preflight check is {age.seconds//3600}h old (>24 hours)")
                print("🔍 Re-running preflight validation...")
                subprocess.run(["python", "preflight.py"])
            elif results.get("status") != "success":
                print("\n⚠️  Previous preflight check failed")
                print("🔍 Re-running preflight validation...")
                subprocess.run(["python", "preflight.py"])
            else:
                hours = age.seconds // 3600
                minutes = (age.seconds % 3600) // 60
                print(f"\n✅ Preflight check valid ({hours}h {minutes}m old)")
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"\n⚠️  Could not read preflight results: {e}")
            print("🔍 Running preflight validation...")
            subprocess.run(["python", "preflight.py"])
    
    print("\n✅ Preflight checks passed. Starting pipeline...\n")
    
    # Run pipeline
    orchestrator = PipelineOrchestrator(config_file)
    success = orchestrator.run_pipeline(input_file)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
