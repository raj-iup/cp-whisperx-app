#!/usr/bin/env python3
"""
Docker Stage Runner with GPU Fallback

Runs Docker stages with automatic fallback from CUDA to CPU if:
- GPU is not available
- CUDA image doesn't exist
- GPU execution fails

Usage:
    python run_docker_stage.py silero-vad --movie-dir out/Movie_Name
    python run_docker_stage.py asr --movie-dir out/Movie_Name --try-gpu
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


class DockerStageRunner:
    """Run Docker stages with GPU fallback support"""
    
    def __init__(self, registry="rajiup", repo="cp-whisperx-app"):
        self.registry = os.getenv("DOCKERHUB_USER", registry)
        self.repo = repo
        
    def image_exists(self, stage, variant):
        """Check if Docker image exists locally"""
        image_name = f"{self.registry}/{self.repo}-{stage}:{variant}"
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", image_name],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def gpu_available(self):
        """Check if NVIDIA GPU is available"""
        try:
            result = subprocess.run(
                ["nvidia-smi"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def run_stage(self, stage, variant, args):
        """Run Docker stage with specified variant"""
        image_name = f"{self.registry}/{self.repo}-{stage}:{variant}"
        
        cmd = ["docker", "run", "--rm"]
        
        # Add GPU support if using CUDA variant
        if variant == "cuda":
            cmd.extend(["--gpus", "all"])
        
        # Add standard volume mounts
        cmd.extend([
            "-v", f"{os.getcwd()}/in:/app/in:ro",
            "-v", f"{os.getcwd()}/out:/app/out",
            "-v", f"{os.getcwd()}/config:/app/config:ro",
            "-v", f"{os.getcwd()}/shared:/app/shared:ro",
        ])
        
        # Add LLM volume for ML stages
        if stage in ["silero-vad", "pyannote-vad", "diarization", "asr", "pre-ner"]:
            cmd.extend(["-v", f"{os.getcwd()}/LLM:/app/LLM"])
        
        # Add scripts volume for stages that need it
        if stage in ["asr", "diarization", "pre-ner", "post-ner"]:
            cmd.extend(["-v", f"{os.getcwd()}/scripts:/app/scripts:ro"])
        
        # Environment variables
        cmd.extend([
            "-e", f"CONFIG_PATH={os.getenv('CONFIG_PATH', '/app/config/.env')}",
            "-e", "PYTHONPATH=/app",
        ])
        
        # Add memory limits for ASR
        if stage == "asr":
            cmd.extend(["--memory=16g", "--memory-swap=16g"])
        
        # Add image and arguments
        cmd.append(image_name)
        cmd.extend(args)
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True)
            return result.returncode
        except subprocess.CalledProcessError as e:
            return e.returncode
        except KeyboardInterrupt:
            print("\nInterrupted by user")
            return 130
    
    def run_with_fallback(self, stage, args, try_gpu=True):
        """
        Run stage with GPU fallback
        
        Strategy:
        1. If try_gpu=True and GPU available and CUDA image exists: Try CUDA
        2. If CUDA fails or unavailable: Fallback to CPU
        3. Always have CPU as final fallback
        """
        # Check if this is a GPU-capable stage
        gpu_stages = ["silero-vad", "pyannote-vad", "diarization", "asr", 
                      "second-pass-translation", "lyrics-detection"]
        
        if stage not in gpu_stages:
            # CPU-only stage
            print(f"[INFO] {stage} is CPU-only stage")
            return self.run_stage(stage, "cpu", args)
        
        # GPU-capable stage
        variants_to_try = []
        
        if try_gpu and self.gpu_available():
            if self.image_exists(stage, "cuda"):
                variants_to_try.append(("cuda", "GPU (CUDA)"))
            else:
                print(f"[WARNING] CUDA image not found for {stage}, will use CPU")
        else:
            if not try_gpu:
                print(f"[INFO] GPU execution disabled, using CPU")
            elif not self.gpu_available():
                print(f"[WARNING] GPU not available, using CPU")
        
        # Always add CPU as fallback
        if self.image_exists(stage, "cpu"):
            variants_to_try.append(("cpu", "CPU"))
        else:
            print(f"[ERROR] CPU fallback image not found for {stage}")
            return 1
        
        # Try each variant
        for i, (variant, desc) in enumerate(variants_to_try):
            is_last = (i == len(variants_to_try) - 1)
            
            print(f"\n{'='*60}")
            print(f"Attempting {stage} with {desc}")
            print(f"{'='*60}\n")
            
            exit_code = self.run_stage(stage, variant, args)
            
            if exit_code == 0:
                print(f"\n[SUCCESS] {stage} completed with {desc}")
                return 0
            else:
                print(f"\n[FAILED] {stage} failed with {desc} (exit code: {exit_code})")
                
                if not is_last:
                    print(f"[INFO] Falling back to next variant...")
                else:
                    print(f"[ERROR] All variants failed for {stage}")
                    return exit_code
        
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Run Docker stage with GPU fallback",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with GPU (will fallback to CPU if needed)
  python run_docker_stage.py asr --movie-dir out/Movie_Name --try-gpu
  
  # Force CPU execution
  python run_docker_stage.py asr --movie-dir out/Movie_Name --no-gpu
  
  # CPU-only stage
  python run_docker_stage.py demux --input in/movie.mp4

GPU-capable stages: silero-vad, pyannote-vad, diarization, asr
CPU-only stages: demux, tmdb, pre-ner, post-ner, subtitle-gen, mux
        """
    )
    
    parser.add_argument("stage", help="Stage name (e.g., asr, diarization)")
    parser.add_argument("--try-gpu", action="store_true", default=True,
                       help="Try GPU execution first (default: True)")
    parser.add_argument("--no-gpu", dest="try_gpu", action="store_false",
                       help="Force CPU execution")
    parser.add_argument("--registry", default=os.getenv("DOCKERHUB_USER", "rajiup"),
                       help="Docker registry (default: rajiup)")
    
    # Capture all remaining arguments to pass to Docker container
    args, docker_args = parser.parse_known_args()
    
    runner = DockerStageRunner(registry=args.registry)
    exit_code = runner.run_with_fallback(args.stage, docker_args, try_gpu=args.try_gpu)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
