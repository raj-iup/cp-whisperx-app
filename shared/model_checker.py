#!/usr/bin/env python3
"""
Model Status Checker for CP-WhisperX-App
Checks cached models and reports if newer versions are available
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class ModelChecker:
    """Checks status of cached models and availability of updates"""
    
    def __init__(self, cache_dir: Path, hf_token: Optional[str] = None):
        self.cache_dir = cache_dir
        self.hf_token = hf_token
        self.torch_cache = cache_dir / 'torch'
        self.hf_cache = cache_dir / 'huggingface'
        
        # Set cache directories
        os.environ['TORCH_HOME'] = str(self.torch_cache)
        os.environ['HF_HOME'] = str(self.hf_cache)
        
    def check_whisper_model(self, model_name: str) -> Tuple[str, bool, str, Optional[str]]:
        """Check if Whisper model is cached"""
        try:
            from faster_whisper import WhisperModel
            
            # Try to load model (if cached, this will be fast)
            model = WhisperModel(model_name, device='cpu', compute_type='int8', 
                               download_root=str(self.torch_cache / 'hub'))
            
            # Check cache directory for size info
            model_path = self.torch_cache / 'hub' / f'models--Systran--faster-whisper-{model_name}'
            if model_path.exists():
                size = self._get_dir_size(model_path)
                size_str = self._format_size(size)
                return (model_name, True, f"Cached ({size_str})", None)
            else:
                return (model_name, True, "Cached", None)
                
        except Exception as e:
            return (model_name, False, "Not cached", None)
    
    def check_pyannote_model(self, model_name: str) -> Tuple[str, bool, str, Optional[str]]:
        """Check if PyAnnote model is cached"""
        try:
            if not self.hf_token:
                return (model_name, False, "No HF token", None)
            
            # Check HuggingFace cache
            model_cache_path = self.hf_cache / 'hub' / f'models--{model_name.replace("/", "--")}'
            
            if model_cache_path.exists():
                size = self._get_dir_size(model_cache_path)
                size_str = self._format_size(size)
                return (model_name, True, f"Cached ({size_str})", None)
            else:
                return (model_name, False, "Not cached", "Available for download")
                
        except Exception as e:
            return (model_name, False, "Check failed", str(e)[:80])
    
    def check_silero_vad(self) -> Tuple[str, bool, str, Optional[str]]:
        """Check if Silero VAD is cached"""
        try:
            silero_path = self.torch_cache / 'hub' / 'snakers4_silero-vad_master'
            
            if silero_path.exists():
                size = self._get_dir_size(silero_path)
                size_str = self._format_size(size)
                return ("silero-vad", True, f"Cached ({size_str})", None)
            else:
                return ("silero-vad", False, "Not cached", "Available for download")
                
        except Exception as e:
            return ("silero-vad", False, "Check failed", str(e)[:80])
    
    def check_spacy_model(self, model_name: str) -> Tuple[str, bool, str, Optional[str]]:
        """Check if spaCy model is installed"""
        try:
            import spacy
            
            # Try to load model
            nlp = spacy.load(model_name)
            
            # Get model info
            meta = nlp.meta
            version = meta.get('version', 'unknown')
            
            return (model_name, True, f"Installed (v{version})", None)
            
        except OSError:
            return (model_name, False, "Not installed", "Available for download")
        except Exception as e:
            return (model_name, False, "Check failed", str(e)[:80])
    
    def check_mlx_whisper(self) -> Tuple[str, bool, str, Optional[str]]:
        """Check MLX-Whisper availability"""
        try:
            import mlx_whisper
            
            version = getattr(mlx_whisper, '__version__', 'unknown')
            return ("mlx-whisper", True, f"Installed (v{version})", None)
            
        except ImportError:
            return ("mlx-whisper", False, "Not installed", "Apple Silicon only")
        except Exception as e:
            return ("mlx-whisper", False, "Check failed", str(e)[:80])
    
    def check_all_models(self, whisper_models: List[str]) -> Dict[str, Tuple[bool, str, Optional[str]]]:
        """Check status of all models"""
        results = {}
        
        # Check Whisper models
        for model_name in whisper_models:
            name, cached, status, note = self.check_whisper_model(model_name)
            results[name] = (cached, status, note, 'whisper')
        
        # Check Silero VAD
        name, cached, status, note = self.check_silero_vad()
        results[name] = (cached, status, note, 'silero')
        
        # Check spaCy models
        for spacy_model in ['en_core_web_trf', 'en_core_web_sm']:
            name, cached, status, note = self.check_spacy_model(spacy_model)
            results[name] = (cached, status, note, 'spacy')
        
        # Check PyAnnote models (if token available)
        if self.hf_token:
            pyannote_models = [
                'pyannote/speaker-diarization-3.1',
                'pyannote/segmentation-3.0'
            ]
            for model_name in pyannote_models:
                name, cached, status, note = self.check_pyannote_model(model_name)
                results[name] = (cached, status, note, 'pyannote')
        
        # Check MLX
        name, cached, status, note = self.check_mlx_whisper()
        results[name] = (cached, status, note, 'mlx')
        
        return results
    
    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += entry.stat().st_size
        except Exception:
            pass
        return total
    
    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}TB"


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_model_status(model_name: str, cached: bool, status: str, note: Optional[str] = None):
    """Print model status"""
    status_icon = "✓" if cached else "✗"
    
    # Format model name
    display_name = model_name.ljust(40)
    
    full_status = status
    if note:
        full_status += f" - {note}"
    
    print(f"  {status_icon} {display_name} {full_status}")


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
    import argparse
    
    parser = argparse.ArgumentParser(description='Check ML model status for CP-WhisperX-App')
    parser.add_argument('--hf-token', type=str, help='HuggingFace API token')
    parser.add_argument('--whisper-models', type=str, nargs='+', 
                       help='Whisper models to check (default: auto-detect from hardware)')
    parser.add_argument('--check-updates', action='store_true',
                       help='Check for available updates (requires internet)')
    args = parser.parse_args()
    
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    cache_dir = project_root / '.cache'
    
    print_section("ML MODEL STATUS CHECK")
    print(f"  Cache directory: {cache_dir}")
    print(f"  Check time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Load HF token from secrets if not provided
    hf_token = args.hf_token
    if not hf_token:
        secrets_file = project_root / 'config' / 'secrets.json'
        if secrets_file.exists():
            try:
                with open(secrets_file, 'r') as f:
                    secrets = json.load(f)
                    hf_token = secrets.get('HF_TOKEN')
            except Exception:
                pass
    
    if hf_token:
        print("  ✓ HuggingFace token available")
    else:
        print("  ⚠ No HuggingFace token - PyAnnote models not checked")
    
    # Determine which Whisper models to check
    if args.whisper_models:
        whisper_models = args.whisper_models
    else:
        # Auto-detect from hardware cache
        hw_cache = load_hardware_cache(project_root)
        recommended_model = hw_cache.get('recommended_settings', {}).get('whisper_model', 'large-v3')
        
        # Check base + recommended model
        whisper_models = ['base', recommended_model, 'large-v3']
        
        # Remove duplicates
        whisper_models = list(dict.fromkeys(whisper_models))
    
    print(f"  Checking Whisper models: {', '.join(whisper_models)}")
    print()
    
    # Initialize checker
    checker = ModelChecker(cache_dir, hf_token)
    
    # Check all models
    results = checker.check_all_models(whisper_models)
    
    # Print results by category
    print_section("MODEL STATUS")
    
    categories = {
        'whisper': 'Whisper Models',
        'silero': 'VAD Models',
        'spacy': 'NER Models',
        'pyannote': 'Diarization Models',
        'mlx': 'Apple Silicon Acceleration'
    }
    
    stats = {'total': 0, 'cached': 0, 'missing': 0}
    missing_models = []
    
    for category, title in categories.items():
        category_results = [(name, cached, status, note) for name, (cached, status, note, cat) in results.items() if cat == category]
        
        if category_results:
            print(f"\n  {title}:")
            for model_name, cached, status, note in category_results:
                print_model_status(model_name, cached, status, note)
                stats['total'] += 1
                if cached:
                    stats['cached'] += 1
                else:
                    stats['missing'] += 1
                    if note and 'Available' in note:
                        missing_models.append(model_name)
    
    # Print cache size
    if cache_dir.exists():
        total_cache_size = checker._get_dir_size(cache_dir)
        cache_size_str = checker._format_size(total_cache_size)
        print(f"\n  Total cache size: {cache_size_str}")
    
    # Print summary
    print_section("SUMMARY")
    print(f"  Total models checked: {stats['total']}")
    print(f"  ✓ Cached/Installed: {stats['cached']}")
    print(f"  ✗ Missing: {stats['missing']}")
    
    if missing_models:
        print(f"\n  Missing models that can be downloaded:")
        for model in missing_models:
            print(f"    • {model}")
        print(f"\n  To download missing models, run:")
        print(f"    python shared/model_downloader.py")
    
    if args.check_updates:
        print(f"\n  ⓘ Update checking not yet implemented")
        print(f"  Models are downloaded from latest available versions")
    
    print()


if __name__ == '__main__':
    main()
