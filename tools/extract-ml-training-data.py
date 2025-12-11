#!/usr/bin/env python3
"""
Extract ML Training Data from Historical Jobs

This script extracts training data from past job manifests to train
the adaptive quality predictor ML model.

Features:
- Scans all job directories in out/
- Extracts audio fingerprints from stage manifests
- Extracts processing results (duration, WER)
- Generates training dataset
- Trains ML model

Usage:
    # Extract and train
    python3 tools/extract-ml-training-data.py
    
    # Extract only (no training)
    python3 tools/extract-ml-training-data.py --extract-only
    
    # Train on existing data
    python3 tools/extract-ml-training-data.py --train-only
"""

# Standard library
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Local
from shared.logger import get_logger
from shared.ml_optimizer import AdaptiveQualityPredictor, AudioFingerprint

logger = get_logger(__name__)


class TrainingDataExtractor:
    """
    Extract training data from historical job manifests.
    
    This class scans job directories and extracts:
    - Audio characteristics (from Stage 01 demux)
    - Processing parameters (from job config)
    - Processing results (from Stage 06 ASR, Stage 07 alignment)
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize training data extractor.
        
        Args:
            output_dir: Root output directory containing job folders
        """
        self.output_dir = output_dir
        self.training_samples = []
    
    def scan_jobs(self) -> List[Path]:
        """
        Scan output directory for job folders.
        
        Returns:
            List of job directory paths
        """
        logger.info(f"📂 Scanning for jobs in {self.output_dir}")
        
        job_dirs = []
        
        # out/{year}/{month}/{day}/{user}/job-{date}-{user}-{id}/
        if self.output_dir.exists():
            for year_dir in self.output_dir.iterdir():
                if not year_dir.is_dir() or not year_dir.name.isdigit():
                    continue
                
                for month_dir in year_dir.iterdir():
                    if not month_dir.is_dir() or not month_dir.name.isdigit():
                        continue
                    
                    for day_dir in month_dir.iterdir():
                        if not day_dir.is_dir() or not day_dir.name.isdigit():
                            continue
                        
                        for user_dir in day_dir.iterdir():
                            if not user_dir.is_dir():
                                continue
                            
                            for job_dir in user_dir.iterdir():
                                if job_dir.is_dir() and job_dir.name.startswith("job-"):
                                    job_dirs.append(job_dir)
        
        logger.info(f"✅ Found {len(job_dirs)} job directories")
        return job_dirs
    
    def extract_audio_fingerprint(self, job_dir: Path) -> Optional[AudioFingerprint]:
        """
        Extract audio fingerprint from job manifests.
        
        Args:
            job_dir: Job directory path
        
        Returns:
            AudioFingerprint or None if extraction failed
        """
        try:
            # Read demux manifest for audio info
            demux_manifest = job_dir / "01_demux" / "stage_manifest.json"
            if not demux_manifest.exists():
                return None
            
            with open(demux_manifest) as f:
                demux_data = json.load(f)
            
            # Get audio duration from outputs
            audio_duration = 0.0
            for output in demux_data.get("outputs", []):
                if "audio" in output.get("key", "").lower():
                    # Duration might be in metadata
                    audio_duration = output.get("metadata", {}).get("duration", 0.0)
            
            if audio_duration == 0.0:
                # Fallback: estimate from file size (rough approximation)
                for output in demux_data.get("outputs", []):
                    if "audio" in output.get("key", "").lower():
                        file_size = output.get("size_bytes", 0) / (1024 * 1024)  # MB
                        # Rough estimate: 16kHz mono WAV ≈ 2 MB/min
                        audio_duration = (file_size / 2.0) * 60.0
            
            # Read VAD manifest for speaker count
            speaker_count = 0
            vad_manifest = job_dir / "05_pyannote_vad" / "stage_manifest.json"
            if vad_manifest.exists():
                with open(vad_manifest) as f:
                    vad_data = json.load(f)
                
                # Try to find speaker count in outputs
                for output in vad_data.get("outputs", []):
                    if "segments" in output.get("key", ""):
                        # Load segments file
                        segments_file = job_dir / "05_pyannote_vad" / output["filename"]
                        if segments_file.exists():
                            with open(segments_file) as f:
                                segments = json.load(f)
                                speakers = set()
                                for seg in segments.get("segments", []):
                                    if "speaker" in seg:
                                        speakers.add(seg["speaker"])
                                speaker_count = len(speakers)
            
            # Read job config for language
            language = "auto"
            job_json = job_dir / "job.json"
            if job_json.exists():
                with open(job_json) as f:
                    job_data = json.load(f)
                    language = job_data.get("source_language", "auto")
            
            # Estimate SNR and complexity (simplified)
            snr_estimate = 20.0  # Default
            complexity_score = 0.5  # Default
            
            # Create fingerprint
            fingerprint = AudioFingerprint(
                duration=audio_duration,
                sample_rate=16000,
                channels=1,
                snr_estimate=snr_estimate,
                language=language,
                speaker_count=speaker_count,
                complexity_score=complexity_score,
                file_size=0.0  # Not critical for training
            )
            
            return fingerprint
        
        except Exception as e:
            logger.debug(f"Failed to extract fingerprint from {job_dir.name}: {e}")
            return None
    
    def extract_config_used(self, job_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Extract configuration used for job.
        
        Args:
            job_dir: Job directory path
        
        Returns:
            Configuration dict or None if extraction failed
        """
        try:
            # Read ASR manifest
            asr_manifest = job_dir / "06_whisperx_asr" / "stage_manifest.json"
            if not asr_manifest.exists():
                return None
            
            with open(asr_manifest) as f:
                asr_data = json.load(f)
            
            # Extract model configuration from metadata
            config = {
                "whisper_model": "large-v3",  # Default
                "batch_size": 8,
                "beam_size": 5,
            }
            
            # Try to find model in metadata
            metadata = asr_data.get("metadata", {})
            if "model" in metadata:
                config["whisper_model"] = metadata["model"]
            if "batch_size" in metadata:
                config["batch_size"] = metadata["batch_size"]
            if "beam_size" in metadata:
                config["beam_size"] = metadata["beam_size"]
            
            return config
        
        except Exception as e:
            logger.debug(f"Failed to extract config from {job_dir.name}: {e}")
            return None
    
    def extract_actual_result(self, job_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Extract actual processing results.
        
        Args:
            job_dir: Job directory path
        
        Returns:
            Result dict or None if extraction failed
        """
        try:
            result = {}
            
            # Read ASR manifest for processing time
            asr_manifest = job_dir / "06_whisperx_asr" / "stage_manifest.json"
            if asr_manifest.exists():
                with open(asr_manifest) as f:
                    asr_data = json.load(f)
                
                # Calculate duration from timestamps
                if "start_time" in asr_data and "end_time" in asr_data:
                    try:
                        start = datetime.fromisoformat(asr_data["start_time"].replace('Z', '+00:00'))
                        end = datetime.fromisoformat(asr_data["end_time"].replace('Z', '+00:00'))
                        result["processing_duration"] = (end - start).total_seconds()
                    except:
                        pass
            
            # Estimate WER (simplified - would need ground truth for real WER)
            # For now, assume successful jobs have reasonable WER
            result["estimated_wer"] = 0.05  # Assume 5% WER for completed jobs
            
            # Quality score (from manifest status)
            result["success"] = True  # If we got here, job succeeded
            
            return result
        
        except Exception as e:
            logger.debug(f"Failed to extract result from {job_dir.name}: {e}")
            return None
    
    def extract_from_job(self, job_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Extract complete training sample from job.
        
        Args:
            job_dir: Job directory path
        
        Returns:
            Training sample dict or None if extraction failed
        """
        logger.debug(f"📊 Extracting from {job_dir.name}")
        
        # Extract all components
        audio_fp = self.extract_audio_fingerprint(job_dir)
        config_used = self.extract_config_used(job_dir)
        actual_result = self.extract_actual_result(job_dir)
        
        # Validate we have all components
        if audio_fp is None or config_used is None or actual_result is None:
            return None
        
        # Check for valid data
        if audio_fp.duration <= 0:
            return None
        
        sample = {
            "job_dir": str(job_dir),
            "audio_fingerprint": {
                "duration": audio_fp.duration,
                "sample_rate": audio_fp.sample_rate,
                "channels": audio_fp.channels,
                "snr_estimate": audio_fp.snr_estimate,
                "language": audio_fp.language,
                "speaker_count": audio_fp.speaker_count,
                "complexity_score": audio_fp.complexity_score,
                "file_size": audio_fp.file_size,
            },
            "config_used": config_used,
            "actual_result": actual_result,
        }
        
        return sample
    
    def extract_all(self) -> List[Dict[str, Any]]:
        """
        Extract training data from all jobs.
        
        Returns:
            List of training samples
        """
        logger.info("🔍 Extracting training data from historical jobs...")
        
        job_dirs = self.scan_jobs()
        
        self.training_samples = []
        for job_dir in job_dirs:
            sample = self.extract_from_job(job_dir)
            if sample:
                self.training_samples.append(sample)
        
        logger.info(f"✅ Extracted {len(self.training_samples)} valid training samples")
        return self.training_samples
    
    def save_training_data(self, output_file: Path) -> None:
        """
        Save training data to file.
        
        Args:
            output_file: Path to output JSON file
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.training_samples, f, indent=2)
        
        logger.info(f"💾 Saved training data to {output_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract ML training data from historical jobs"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("out"),
        help="Output directory containing jobs (default: out/)"
    )
    parser.add_argument(
        "--training-data",
        type=Path,
        default=Path.home() / ".cp-whisperx" / "models" / "training_data" / "historical_data.json",
        help="Path to save training data"
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Extract data only, don't train model"
    )
    parser.add_argument(
        "--train-only",
        action="store_true",
        help="Train model on existing data, don't extract"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=100,
        help="Minimum samples required for training (default: 100)"
    )
    
    args = parser.parse_args()
    
    # Initialize predictor
    predictor = AdaptiveQualityPredictor(min_training_samples=args.min_samples)
    
    # Extract training data
    if not args.train_only:
        extractor = TrainingDataExtractor(args.output_dir)
        training_samples = extractor.extract_all()
        
        # Save training data
        extractor.save_training_data(args.training_data)
        
        logger.info(f"📊 Training Data Summary:")
        logger.info(f"   Total samples: {len(training_samples)}")
        
        if len(training_samples) > 0:
            # Statistics
            durations = [s["audio_fingerprint"]["duration"] for s in training_samples]
            languages = [s["audio_fingerprint"]["language"] for s in training_samples]
            models = [s["config_used"]["whisper_model"] for s in training_samples]
            
            logger.info(f"   Audio duration: {min(durations):.0f}s - {max(durations):.0f}s")
            logger.info(f"   Languages: {set(languages)}")
            logger.info(f"   Models used: {set(models)}")
    else:
        # Load existing training data
        if not args.training_data.exists():
            logger.error(f"❌ Training data not found: {args.training_data}")
            return 1
        
        with open(args.training_data) as f:
            training_samples = json.load(f)
        
        logger.info(f"📂 Loaded {len(training_samples)} samples from {args.training_data}")
    
    # Train model
    if not args.extract_only:
        if len(training_samples) < args.min_samples:
            logger.warning(
                f"⚠️  Insufficient training data: {len(training_samples)} < {args.min_samples}"
            )
            logger.info("💡 Use --min-samples to lower threshold or collect more data")
            return 1
        
        logger.info("🎓 Training ML model...")
        success = predictor.train_model(training_samples)
        
        if success:
            logger.info("✅ Model training complete!")
            logger.info(f"📁 Model saved to: {predictor.model_path}")
            return 0
        else:
            logger.error("❌ Model training failed")
            return 1
    
    logger.info("✅ Training data extraction complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
