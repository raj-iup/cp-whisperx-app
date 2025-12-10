#!/usr/bin/env python3
"""
Train ML Model for Adaptive Quality Prediction

This script trains the XGBoost model using historical job data.
It should be run periodically (e.g., after every 10-20 jobs) to
continuously improve predictions.

Usage:
    # Train on all available data
    python3 tools/train-ml-model.py
    
    # Train with minimum samples threshold
    python3 tools/train-ml-model.py --min-samples 50
    
    # Dry run (show what would be trained)
    python3 tools/train-ml-model.py --dry-run

Architecture Decision: AD-015 (ML-Based Adaptive Optimization)
"""

# Standard library
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.logger import get_logger
from shared.ml_optimizer import AdaptiveQualityPredictor, AudioFingerprint
from tools.extract_ml_training_data import TrainingDataExtractor

logger = get_logger(__name__)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Train ML model for adaptive quality prediction"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=100,
        help="Minimum training samples required (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be trained without actually training"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Train even if below minimum samples threshold"
    )
    
    args = parser.parse_args()
    
    logger.info("🎓 ML Model Training Script")
    logger.info("=" * 60)
    
    # Extract training data from historical jobs
    logger.info("📊 Step 1: Extracting training data from historical jobs...")
    extractor = TrainingDataExtractor(PROJECT_ROOT / "out")
    training_data = extractor.extract_all()
    
    num_samples = len(training_data)
    logger.info(f"✅ Extracted {num_samples} training samples")
    
    if num_samples == 0:
        logger.warning("⚠️  No training data found!")
        logger.info("💡 Run some jobs first to generate training data:")
        logger.info("   ./prepare-job.sh --media in/sample.mp4 --workflow transcribe")
        logger.info("   ./run-pipeline.sh job-XXXXXXXX-user-NNNN")
        return 1
    
    # Check minimum threshold
    if num_samples < args.min_samples and not args.force:
        logger.warning(f"⚠️  Insufficient training data: {num_samples} < {args.min_samples}")
        logger.info("💡 Options:")
        logger.info(f"   1. Run more jobs ({args.min_samples - num_samples} more needed)")
        logger.info("   2. Lower threshold: --min-samples 50")
        logger.info("   3. Force training: --force")
        return 1
    
    # Show statistics
    logger.info("")
    logger.info("📈 Training Data Statistics:")
    logger.info("-" * 60)
    
    # Duration distribution
    durations = [s["audio_fingerprint"]["duration"] for s in training_data]
    logger.info(f"  Duration:  {min(durations):.1f}s - {max(durations):.1f}s (avg: {sum(durations)/len(durations):.1f}s)")
    
    # Model distribution
    models_used = {}
    for s in training_data:
        model = s["config_used"].get("whisper_model", "unknown")
        models_used[model] = models_used.get(model, 0) + 1
    
    logger.info("  Models used:")
    for model, count in sorted(models_used.items(), key=lambda x: -x[1]):
        logger.info(f"    - {model}: {count} samples ({count/num_samples*100:.1f}%)")
    
    # Language distribution
    languages = {}
    for s in training_data:
        lang = s["audio_fingerprint"].get("language", "unknown")
        languages[lang] = languages.get(lang, 0) + 1
    
    logger.info("  Languages:")
    for lang, count in sorted(languages.items(), key=lambda x: -x[1]):
        logger.info(f"    - {lang}: {count} samples ({count/num_samples*100:.1f}%)")
    
    logger.info("-" * 60)
    
    # Dry run?
    if args.dry_run:
        logger.info("")
        logger.info("🏃 DRY RUN: Would train model on this data")
        logger.info("   Remove --dry-run to actually train")
        return 0
    
    # Train model
    logger.info("")
    logger.info("🎓 Step 2: Training XGBoost model...")
    
    predictor = AdaptiveQualityPredictor(min_training_samples=args.min_samples)
    success = predictor.train_model(training_data)
    
    if not success:
        logger.error("❌ Model training failed!")
        return 1
    
    # Test predictions
    logger.info("")
    logger.info("🧪 Step 3: Testing predictions on sample data...")
    
    test_cases = [
        ("Clean short audio", AudioFingerprint(
            duration=120.0, sample_rate=16000, channels=1,
            snr_estimate=30.0, language="en", speaker_count=1,
            complexity_score=0.3, file_size=10.0
        )),
        ("Noisy long audio", AudioFingerprint(
            duration=1800.0, sample_rate=16000, channels=1,
            snr_estimate=12.0, language="hi", speaker_count=3,
            complexity_score=0.8, file_size=150.0
        )),
        ("Medium quality", AudioFingerprint(
            duration=600.0, sample_rate=16000, channels=1,
            snr_estimate=20.0, language="en", speaker_count=2,
            complexity_score=0.5, file_size=50.0
        )),
    ]
    
    for name, audio_fp in test_cases:
        config = predictor.predict_optimal_config(audio_fp)
        logger.info(f"  {name}:")
        logger.info(f"    → Model: {config.whisper_model}")
        logger.info(f"    → Batch: {config.batch_size}")
        logger.info(f"    → Confidence: {config.confidence:.0%}")
        logger.info(f"    → Reason: {config.reasoning}")
    
    # Success
    logger.info("")
    logger.info("✅ ML model training complete!")
    logger.info(f"📁 Model saved to: {predictor.model_path}")
    logger.info("")
    logger.info("💡 Next steps:")
    logger.info("   1. Model will be used automatically in future jobs")
    logger.info("   2. Re-train periodically as more jobs complete")
    logger.info("   3. Monitor predictions vs. actual performance")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
