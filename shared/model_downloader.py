#!/usr/bin/env python3
"""
Model Pre-Downloader for CP-WhisperX-App
Downloads and caches all required ML models during bootstrap
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# Suppress warnings during model downloads
warnings.filterwarnings('ignore')

class ModelDownloader:
    """Handles parallel downloading of ML models with progress tracking"""
    
    def __init__(self, cache_dir: Path, hf_token: Optional[str] = None, max_workers: int = 3):
        self.cache_dir = cache_dir
        self.hf_token = hf_token
        self.max_workers = max_workers
        self.results = {}
        
        # Set cache directories
        os.environ['TORCH_HOME'] = str(cache_dir / 'torch')
        os.environ['HF_HOME'] = str(cache_dir / 'huggingface')
        
    def download_whisper_model(self, model_name: str) -> Tuple[str, bool, str]:
        """Download a Whisper model via faster-whisper"""
        try:
            from faster_whisper import WhisperModel
            
            # Use int8 for efficiency during download
            model = WhisperModel(model_name, device='cpu', compute_type='int8')
            
            # Test that model loaded by checking the underlying model
            if model.model is None:
                raise ValueError("Model not loaded properly")
            
            return (model_name, True, f"Whisper {model_name} cached")
        except Exception as e:
            return (model_name, False, f"Failed: {str(e)[:80]}")
    
    def download_pyannote_model(self, model_name: str) -> Tuple[str, bool, str]:
        """Download PyAnnote model"""
        try:
            from pyannote.audio import Pipeline
            
            if not self.hf_token:
                return (model_name, False, "Skipped: No HF token")
            
            # Set token
            os.environ['HF_TOKEN'] = self.hf_token
            
            # Download pipeline
            pipeline = Pipeline.from_pretrained(
                model_name,
                use_auth_token=self.hf_token
            )
            
            model_short = model_name.split('/')[-1]
            return (model_name, True, f"PyAnnote {model_short} cached")
        except Exception as e:
            error_msg = str(e)
            if 'torchaudio' in error_msg.lower() or 'audiodata' in error_msg.lower():
                return (model_name, False, "Skipped: torchaudio issue")
            return (model_name, False, f"Failed: {str(e)[:80]}")
    
    def download_silero_vad(self) -> Tuple[str, bool, str]:
        """Download Silero VAD model via torch hub"""
        try:
            import torch
            
            # Force reload to ensure download
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            
            return ("silero-vad", True, "Silero VAD cached")
        except Exception as e:
            return ("silero-vad", False, f"Failed: {str(e)[:80]}")
    
    def download_spacy_model(self, model_name: str) -> Tuple[str, bool, str]:
        """Download spaCy model"""
        try:
            import spacy
            from spacy.cli import download
            
            # Check if already installed
            try:
                spacy.load(model_name)
                return (model_name, True, f"spaCy {model_name} cached")
            except OSError:
                pass
            
            # Download model
            download(model_name)
            
            # Verify installation
            spacy.load(model_name)
            
            return (model_name, True, f"spaCy {model_name} downloaded")
        except Exception as e:
            return (model_name, False, f"Failed: {str(e)[:80]}")
    
    def download_mlx_whisper(self) -> Tuple[str, bool, str]:
        """Test MLX-Whisper availability (models download on first use)"""
        try:
            import mlx_whisper
            
            # MLX models are downloaded on first use, just verify library works
            version = getattr(mlx_whisper, '__version__', 'installed')
            
            return ("mlx-whisper", True, f"MLX-Whisper {version} ready")
        except ImportError:
            return ("mlx-whisper", False, "Skipped: Not installed")
        except Exception as e:
            return ("mlx-whisper", False, f"Failed: {str(e)[:80]}")
    
    def download_all_models(self, whisper_models: List[str]) -> Dict[str, Tuple[bool, str]]:
        """Download all models in parallel"""
        tasks = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit Whisper model downloads
            for model_name in whisper_models:
                future = executor.submit(self.download_whisper_model, model_name)
                tasks.append(('whisper', future))
            
            # Submit Silero VAD download
            future = executor.submit(self.download_silero_vad)
            tasks.append(('silero', future))
            
            # Submit spaCy downloads
            for spacy_model in ['en_core_web_trf', 'en_core_web_sm']:
                future = executor.submit(self.download_spacy_model, spacy_model)
                tasks.append(('spacy', future))
            
            # Submit PyAnnote downloads (if token available)
            if self.hf_token:
                pyannote_models = [
                    'pyannote/speaker-diarization-3.1',
                    'pyannote/segmentation-3.0'
                ]
                for model_name in pyannote_models:
                    future = executor.submit(self.download_pyannote_model, model_name)
                    tasks.append(('pyannote', future))
            
            # Submit MLX test (Apple Silicon only)
            future = executor.submit(self.download_mlx_whisper)
            tasks.append(('mlx', future))
            
            # Collect results as they complete
            for category, future in tasks:
                try:
                    model_name, success, message = future.result(timeout=300)  # 5 min timeout per model
                    self.results[model_name] = (success, message, category)
                except Exception as e:
                    self.results[f"unknown-{category}"] = (False, f"Timeout: {str(e)[:80]}", category)
        
        return self.results


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_model_status(model_name: str, success: bool, message: str):
    """Print model download status"""
    status_icon = "✓" if success else "✗"
    
    # Format model name
    display_name = model_name.ljust(40)
    
    print(f"  {status_icon} {display_name} {message}")


def load_hardware_cache(project_root: Path) -> Dict:
    """Load hardware cache to determine recommended models"""
    cache_file = project_root / 'out' / 'hardware_cache.json'
    
    if cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {}


def main():
    parser = argparse.ArgumentParser(description='Pre-download ML models for CP-WhisperX-App')
    parser.add_argument('--hf-token', type=str, help='HuggingFace API token')
    parser.add_argument('--max-workers', type=int, default=3, help='Max parallel downloads')
    parser.add_argument('--whisper-models', type=str, nargs='+', 
                       help='Whisper models to download (default: auto-detect from hardware)')
    args = parser.parse_args()
    
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    cache_dir = project_root / '.cache'
    
    # Ensure cache directory exists
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print_section("ML MODEL PRE-DOWNLOAD")
    print("  Downloading and caching all required ML models...")
    print(f"  Cache directory: {cache_dir}")
    print(f"  Max parallel workers: {args.max_workers}")
    
    # Load HF token from secrets if not provided
    hf_token = args.hf_token
    if not hf_token:
        secrets_file = project_root / 'config' / 'secrets.json'
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r') as f:
                    secrets = json.load(f)
                    # Check multiple possible key names
                    hf_token = secrets.get('HF_TOKEN') or secrets.get('hf_token') or secrets.get('pyannote_token')
            except Exception:
                pass
    
    if hf_token:
        print("  ✓ HuggingFace token found - will download authenticated models")
    else:
        print("  ⚠ No HuggingFace token - PyAnnote models will be skipped")
    
    # Determine which Whisper models to download
    if args.whisper_models:
        whisper_models = args.whisper_models
    else:
        # Auto-detect from hardware cache
        hw_cache = load_hardware_cache(project_root)
        recommended_model = hw_cache.get('recommended_settings', {}).get('whisper_model', 'large-v3')
        
        # Download base + recommended model
        whisper_models = ['base', recommended_model]
        if recommended_model != 'large-v3':
            whisper_models.append('large-v3')  # Always include latest
        
        # Remove duplicates
        whisper_models = list(dict.fromkeys(whisper_models))
    
    print(f"  Whisper models to download: {', '.join(whisper_models)}")
    print()
    
    # Initialize downloader
    downloader = ModelDownloader(cache_dir, hf_token, args.max_workers)
    
    # Download all models
    print("  Starting parallel downloads...")
    print()
    results = downloader.download_all_models(whisper_models)
    
    # Print results by category
    print_section("DOWNLOAD RESULTS")
    
    categories = {
        'whisper': 'Whisper Models',
        'silero': 'VAD Models',
        'spacy': 'NER Models',
        'pyannote': 'Diarization Models',
        'mlx': 'Apple Silicon Acceleration'
    }
    
    stats = {'total': 0, 'success': 0, 'failed': 0, 'skipped': 0}
    
    for category, title in categories.items():
        category_results = [(name, success, msg) for name, (success, msg, cat) in results.items() if cat == category]
        
        if category_results:
            print(f"\n  {title}:")
            for model_name, success, message in category_results:
                print_model_status(model_name, success, message)
                stats['total'] += 1
                if success:
                    stats['success'] += 1
                elif 'Skipped' in message:
                    stats['skipped'] += 1
                else:
                    stats['failed'] += 1
    
    # Print summary
    print_section("SUMMARY")
    print(f"  Total models processed: {stats['total']}")
    print(f"  ✓ Successfully downloaded: {stats['success']}")
    if stats['skipped'] > 0:
        print(f"  ⊘ Skipped (optional): {stats['skipped']}")
    if stats['failed'] > 0:
        print(f"  ✗ Failed: {stats['failed']}")
    print()
    
    # Determine exit code
    # Only fail if critical models failed (not skipped)
    critical_failures = [name for name, (success, msg, cat) in results.items() 
                        if not success and 'Skipped' not in msg and cat in ['whisper', 'silero', 'spacy']]
    
    if critical_failures:
        print(f"  ⚠ Critical models failed: {', '.join(critical_failures)}")
        print(f"  These models will be downloaded on first use")
        print()
        sys.exit(0)  # Don't fail bootstrap, models can download on demand
    else:
        print(f"  ✓ All critical models ready!")
        if stats['skipped'] > 0:
            print(f"  ⚠ Some optional models skipped (will download on first use if needed)")
        print()
        sys.exit(0)


if __name__ == '__main__':
    main()
