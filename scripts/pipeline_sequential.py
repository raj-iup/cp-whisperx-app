#!/usr/bin/env python3
"""
CP-WhisperX-App Sequential Pipeline Orchestrator
Rebuilt from scratch following arch/workflow-arch.txt

Features:
- Sequential execution with dependency management
- Standardized structured logging
- Stage control: run all stages or specific stages
- Resume capability with manifest tracking
- Real-time progress reporting
"""
import sys
import subprocess
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent / 'shared'))

from shared.logger import setup_logger
from shared.config import load_config
from shared.utils import parse_filename


@dataclass
class StageDefinition:
    """Definition of a pipeline stage."""
    name: str
    service: str
    description: str
    timeout: int
    critical: bool
    output_validation: Optional[callable] = None


@dataclass
class StageResult:
    """Result of a stage execution."""
    stage: str
    success: bool
    duration: float
    start_time: str
    end_time: str
    status: str
    error: Optional[str] = None
    output_verified: bool = False


class PipelineManifest:
    """Manages pipeline execution state and results."""
    
    def __init__(self, manifest_path: Path):
        self.path = manifest_path
        self.data = self._load_or_init()
    
    def _load_or_init(self) -> dict:
        """Load existing manifest or create new one."""
        if self.path.exists():
            with open(self.path, 'r') as f:
                return json.load(f)
        
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "input": {},
            "output_dir": "",
            "pipeline": {
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "completed_at": None,
                "total_duration": 0,
                "stages": {},
                "completed_stages": [],
                "failed_stages": [],
                "skipped_stages": []
            }
        }
    
    def set_input(self, input_file: str, title: str, year: Optional[int]):
        """Set input metadata."""
        self.data["input"] = {
            "file": input_file,
            "title": title,
            "year": year,
            "size_bytes": Path(input_file).stat().st_size if Path(input_file).exists() else 0
        }
        self.save()
    
    def set_output_dir(self, output_dir: str):
        """Set output directory."""
        self.data["output_dir"] = output_dir
        self.save()
    
    def is_stage_completed(self, stage_name: str) -> bool:
        """Check if stage was previously completed."""
        return stage_name in self.data["pipeline"]["completed_stages"]
    
    def record_stage_result(self, result: StageResult):
        """Record stage execution result."""
        self.data["pipeline"]["stages"][result.stage] = {
            "success": result.success,
            "duration": result.duration,
            "start_time": result.start_time,
            "end_time": result.end_time,
            "status": result.status,
            "error": result.error,
            "output_verified": result.output_verified
        }
        
        if result.success:
            if result.stage not in self.data["pipeline"]["completed_stages"]:
                self.data["pipeline"]["completed_stages"].append(result.stage)
            if result.stage in self.data["pipeline"]["failed_stages"]:
                self.data["pipeline"]["failed_stages"].remove(result.stage)
        else:
            if result.stage not in self.data["pipeline"]["failed_stages"]:
                self.data["pipeline"]["failed_stages"].append(result.stage)
        
        self.save()
    
    def finalize(self, status: str, total_duration: float):
        """Finalize pipeline execution."""
        self.data["pipeline"]["status"] = status
        self.data["pipeline"]["completed_at"] = datetime.now().isoformat()
        self.data["pipeline"]["total_duration"] = total_duration
        self.save()
    
    def save(self):
        """Save manifest to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w') as f:
            json.dump(self.data, f, indent=2)


class SequentialPipeline:
    """
    Sequential pipeline orchestrator for cp-whisperx-app.
    
    Pipeline stages (as per arch/workflow-arch.txt):
    1. demux - Extract 16kHz mono audio from video
    2. tmdb - Fetch movie metadata
    3. pre_ner - Extract entities before ASR
    4. silero_vad - Coarse speech segmentation
    5. pyannote_vad - Refined contextual boundaries
    6. diarization - Speaker labeling
    7. asr - WhisperX ASR + forced alignment
    8. post_ner - Entity correction & enrichment
    9. subtitle_gen - Generate SRT subtitles
    10. mux - Embed subtitles into video
    """
    
    # Stage definitions following workflow-arch.txt
    STAGES = [
        StageDefinition(
            name="demux",
            service="demux",
            description="FFmpeg demux: extract 16kHz mono audio",
            timeout=600,
            critical=True
        ),
        StageDefinition(
            name="tmdb",
            service="tmdb",
            description="TMDB metadata fetch",
            timeout=120,
            critical=False
        ),
        StageDefinition(
            name="pre_ner",
            service="pre-ner",
            description="Pre-ASR NER: extract named entities",
            timeout=300,
            critical=False
        ),
        StageDefinition(
            name="silero_vad",
            service="silero-vad",
            description="Silero VAD: coarse speech segmentation",
            timeout=1800,
            critical=True
        ),
        StageDefinition(
            name="pyannote_vad",
            service="pyannote-vad",
            description="PyAnnote VAD: refined contextual boundaries",
            timeout=3600,
            critical=True
        ),
        StageDefinition(
            name="diarization",
            service="diarization",
            description="PyAnnote diarization: mandatory speaker labeling",
            timeout=1800,
            critical=True
        ),
        StageDefinition(
            name="asr",
            service="asr",
            description="WhisperX ASR + forced alignment",
            timeout=3600,
            critical=True
        ),
        StageDefinition(
            name="post_ner",
            service="post-ner",
            description="Post-ASR NER: entity correction & enrichment",
            timeout=600,
            critical=False
        ),
        StageDefinition(
            name="subtitle_gen",
            service="subtitle-gen",
            description="Subtitle generation (.srt)",
            timeout=300,
            critical=True
        ),
        StageDefinition(
            name="mux",
            service="mux",
            description="FFmpeg mux: embed English soft-subtitles",
            timeout=600,
            critical=True
        )
    ]
    
    def __init__(self, config_file: Optional[str] = None, stages: Optional[List[str]] = None):
        """
        Initialize pipeline orchestrator.
        
        Args:
            config_file: Optional config file path
            stages: Optional list of specific stages to run (None = all stages)
        """
        self.config = load_config(config_file)
        self.logger = setup_logger(
            "pipeline_sequential",
            log_level=self.config.log_level,
            log_format="text",
            log_to_console=True,
            log_to_file=True,
            log_dir=self.config.log_root
        )
        
        # Filter stages if specific stages requested
        if stages:
            self.stages = [s for s in self.STAGES if s.name in stages]
            if len(self.stages) != len(stages):
                found = {s.name for s in self.stages}
                missing = set(stages) - found
                self.logger.warning(f"Unknown stages will be skipped: {missing}")
        else:
            self.stages = self.STAGES
        
        self.manifest: Optional[PipelineManifest] = None
        self.movie_dir: Optional[Path] = None
        self.input_path: Optional[Path] = None
        self.file_info: Optional[dict] = None
        self.start_time = time.time()
    
    def _print_header(self):
        """Print pipeline header."""
        self.logger.info("=" * 80)
        self.logger.info("  CP-WHISPERX-APP SEQUENTIAL PIPELINE")
        self.logger.info("  Built from arch/workflow-arch.txt")
        self.logger.info("=" * 80)
    
    def _print_stage_header(self, idx: int, total: int, stage: StageDefinition):
        """Print stage execution header."""
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info(f"  STAGE {idx}/{total}: {stage.name.upper()}")
        self.logger.info(f"  {stage.description}")
        self.logger.info(f"  Service: {stage.service} | Timeout: {stage.timeout}s | Critical: {stage.critical}")
        self.logger.info("=" * 80)
    
    def _print_summary(self, success: bool, duration: float):
        """Print pipeline execution summary."""
        self.logger.info("")
        self.logger.info("=" * 80)
        if success:
            self.logger.info("  ✓ PIPELINE COMPLETED SUCCESSFULLY")
        else:
            self.logger.info("  ✗ PIPELINE FAILED")
        self.logger.info("=" * 80)
        self.logger.info(f"  Total duration: {duration:.1f}s ({duration/60:.1f} minutes)")
        self.logger.info(f"  Output directory: {self.movie_dir}")
        self.logger.info(f"  Manifest: {self.manifest.path}")
        
        # Stage summary
        completed = len(self.manifest.data["pipeline"]["completed_stages"])
        failed = len(self.manifest.data["pipeline"]["failed_stages"])
        total = len(self.stages)
        
        self.logger.info("")
        self.logger.info(f"  Stages: {completed}/{total} completed, {failed} failed")
        
        if failed > 0:
            failed_stages = self.manifest.data["pipeline"]["failed_stages"]
            self.logger.info(f"  Failed stages: {', '.join(failed_stages)}")
        
        self.logger.info("=" * 80)
    
    def _validate_stage_output(self, stage_name: str) -> bool:
        """
        Validate that stage produced expected output.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            True if validation passed, False otherwise
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
                return validations[stage_name]()
            except Exception as e:
                self.logger.debug(f"Validation error for {stage_name}: {e}")
                return False
        
        return True
    
    def _get_stage_args(self, stage_name: str) -> List[str]:
        """
        Get command-line arguments for a stage.
        
        Args:
            stage_name: Name of the stage
            
        Returns:
            List of arguments to pass to the Docker container
        """
        if stage_name == "demux":
            return [str(self.input_path)]
        elif stage_name == "tmdb":
            args = [self.file_info['title']]
            if self.file_info.get('year'):
                args.append(str(self.file_info['year']))
            return args
        elif stage_name == "mux":
            output_file = self.movie_dir / "final_output.mp4"
            subtitle_file = self.movie_dir / "subtitles" / "subtitles.srt"
            return [str(self.input_path), str(subtitle_file), str(output_file)]
        else:
            return [str(self.movie_dir)]
    
    def _run_docker_stage(self, stage: StageDefinition) -> StageResult:
        """
        Execute a pipeline stage in Docker container.
        
        Args:
            stage: Stage definition
            
        Returns:
            StageResult with execution details
        """
        start_time = time.time()
        start_time_str = datetime.now().isoformat()
        
        # Build docker compose command
        cmd = [
            "docker", "compose", "-f", "docker-compose.yml",
            "run", "--rm", stage.service
        ]
        
        # Add stage-specific arguments
        args = self._get_stage_args(stage.name)
        cmd.extend(args)
        
        self.logger.info(f"Executing: {' '.join(cmd)}")
        self.logger.info(f"Timeout: {stage.timeout}s")
        
        try:
            # Run container
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=stage.timeout,
                check=True
            )
            
            # Log output
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    self.logger.info(f"  {line}")
            
            duration = time.time() - start_time
            end_time_str = datetime.now().isoformat()
            
            # Validate output
            output_verified = self._validate_stage_output(stage.name)
            
            if output_verified:
                self.logger.info(f"✓ Stage completed successfully in {duration:.1f}s")
                self.logger.info(f"✓ Output verified")
                status = "success"
            else:
                self.logger.warning(f"✓ Stage completed in {duration:.1f}s but output verification failed")
                status = "success_unverified"
            
            return StageResult(
                stage=stage.name,
                success=True,
                duration=duration,
                start_time=start_time_str,
                end_time=end_time_str,
                status=status,
                error=None,
                output_verified=output_verified
            )
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            end_time_str = datetime.now().isoformat()
            error = f"Stage timed out after {stage.timeout}s"
            self.logger.error(f"✗ {error}")
            
            return StageResult(
                stage=stage.name,
                success=False,
                duration=duration,
                start_time=start_time_str,
                end_time=end_time_str,
                status="timeout",
                error=error,
                output_verified=False
            )
            
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            end_time_str = datetime.now().isoformat()
            error = f"Stage failed with exit code {e.returncode}"
            
            self.logger.error(f"✗ {error}")
            if e.stdout:
                self.logger.error("STDOUT:")
                for line in e.stdout.strip().split('\n'):
                    self.logger.error(f"  {line}")
            if e.stderr:
                self.logger.error("STDERR:")
                for line in e.stderr.strip().split('\n'):
                    self.logger.error(f"  {line}")
            
            return StageResult(
                stage=stage.name,
                success=False,
                duration=duration,
                start_time=start_time_str,
                end_time=end_time_str,
                status="failed",
                error=error,
                output_verified=False
            )
            
        except Exception as e:
            duration = time.time() - start_time
            end_time_str = datetime.now().isoformat()
            error = f"Unexpected error: {str(e)}"
            self.logger.error(f"✗ {error}")
            
            return StageResult(
                stage=stage.name,
                success=False,
                duration=duration,
                start_time=start_time_str,
                end_time=end_time_str,
                status="error",
                error=error,
                output_verified=False
            )
    
    def run(self, input_file: str, resume: bool = True) -> bool:
        """
        Execute the pipeline.
        
        Args:
            input_file: Path to input video file
            resume: Whether to resume from previous run
            
        Returns:
            True if pipeline completed successfully, False otherwise
        """
        self._print_header()
        
        # Validate input
        self.input_path = Path(input_file)
        if not self.input_path.exists():
            self.logger.error(f"Input file not found: {input_file}")
            return False
        
        self.logger.info(f"Input file: {self.input_path}")
        self.logger.info(f"File size: {self.input_path.stat().st_size / (1024*1024):.2f} MB")
        
        # Parse filename
        self.file_info = parse_filename(self.input_path.name)
        title = self.file_info['title']
        year = self.file_info.get('year')
        
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
        
        self.logger.info(f"Output directory: {self.movie_dir}")
        
        # Initialize manifest
        manifest_file = self.movie_dir / "manifest.json"
        self.manifest = PipelineManifest(manifest_file)
        self.manifest.set_input(str(self.input_path), title, year)
        self.manifest.set_output_dir(str(self.movie_dir))
        
        # Check for resume
        if resume and manifest_file.exists():
            completed = self.manifest.data["pipeline"].get("completed_stages", [])
            if completed:
                self.logger.info("")
                self.logger.info("📋 RESUMING FROM PREVIOUS RUN")
                self.logger.info(f"   Previously completed: {', '.join(completed)}")
                self.logger.info("")
        
        # Execute stages
        total_stages = len(self.stages)
        failed_critical = False
        
        for idx, stage in enumerate(self.stages, 1):
            self._print_stage_header(idx, total_stages, stage)
            
            # Check if should skip
            if resume and self.manifest.is_stage_completed(stage.name):
                self.logger.info(f"⏭️  Skipping - already completed successfully")
                self.logger.info(f"Progress: {idx}/{total_stages} stages")
                continue
            
            # Execute stage
            result = self._run_docker_stage(stage)
            
            # Record result
            self.manifest.record_stage_result(result)
            
            # Check for failure
            if not result.success:
                if stage.critical:
                    self.logger.error(f"✗ Critical stage failed - stopping pipeline")
                    failed_critical = True
                    break
                else:
                    self.logger.warning(f"⚠️  Optional stage failed - continuing")
                    if stage.name not in self.manifest.data["pipeline"]["skipped_stages"]:
                        self.manifest.data["pipeline"]["skipped_stages"].append(stage.name)
                        self.manifest.save()
            
            self.logger.info(f"Progress: {idx}/{total_stages} stages")
        
        # Finalize
        total_duration = time.time() - self.start_time
        success = not failed_critical and idx == total_stages
        
        self.manifest.finalize(
            status="completed" if success else "failed",
            total_duration=total_duration
        )
        
        self._print_summary(success, total_duration)
        
        return success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="CP-WhisperX-App Sequential Pipeline Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python pipeline_sequential.py -i in/movie.mp4
  
  # Run specific stages only
  python pipeline_sequential.py -i in/movie.mp4 --stages demux tmdb asr
  
  # Run without resume (start fresh)
  python pipeline_sequential.py -i in/movie.mp4 --no-resume
  
  # Use custom config
  python pipeline_sequential.py -i in/movie.mp4 --config config/custom.env
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        required=False,
        help="Input video file path"
    )
    
    parser.add_argument(
        "--stages",
        nargs="+",
        help="Specific stages to run (default: all stages)",
        choices=["demux", "tmdb", "pre_ner", "silero_vad", "pyannote_vad", 
                 "diarization", "asr", "post_ner", "subtitle_gen", "mux"]
    )
    
    parser.add_argument(
        "--config",
        help="Path to config file (default: config/.env)"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start from scratch (ignore previous progress)"
    )
    
    parser.add_argument(
        "--list-stages",
        action="store_true",
        help="List all available stages and exit"
    )
    
    args = parser.parse_args()
    
    # List stages if requested
    if args.list_stages:
        print("\nAvailable stages (in execution order):")
        print("=" * 80)
        for idx, stage in enumerate(SequentialPipeline.STAGES, 1):
            critical_str = "CRITICAL" if stage.critical else "optional"
            print(f"{idx:2}. {stage.name:15} - {stage.description}")
            print(f"    Service: {stage.service:15} Timeout: {stage.timeout:4}s  [{critical_str}]")
        print("=" * 80)
        return 0
    
    # Validate input required for pipeline run
    if not args.input:
        parser.error("the following arguments are required: -i/--input")
    
    # Create and run pipeline
    pipeline = SequentialPipeline(
        config_file=args.config,
        stages=args.stages
    )
    
    success = pipeline.run(
        input_file=args.input,
        resume=not args.no_resume
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
