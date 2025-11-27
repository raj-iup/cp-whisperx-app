#!/usr/bin/env python3
"""
vad_chunker.py
- Handles long audio by chunking (prevents 413 on remote services)
- Local VAD via pyannote.audio (CUDA optional)
- Optional remote VAD per chunk (expects JSON: {"segments":[{"start":..,"end":..},...]})
- Merges tiny inter-segment gaps
- Exports JSON (and optional SRT)

Usage:
  python vad_chunker.py input.wav --out-json speech.json
  python vad_chunker.py input.wav --device cuda --win 45 --pad 0.25 --merge-gap 0.2 --out-json speech.json --out-srt speech.srt
  python vad_chunker.py input.wav --remote-url https://example.com/vad --out-json speech.json

Notes:
  - Requires: soundfile, numpy, pyannote.audio. Optional: librosa (resampling), requests (remote).
  - For MP4 inputs, demux first:
      ffmpeg -i movie.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 audio.wav
"""
import argparse
import json
import os
import sys
import tempfile
import warnings
from pathlib import Path
from typing import List, Tuple

import numpy as np

# Suppress torchaudio deprecation warnings
warnings.filterwarnings('ignore', message='.*torchaudio._backend.list_audio_backends.*')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='pyannote')
warnings.filterwarnings('ignore', message='.*torchaudio._backend/utils.py.*')
warnings.filterwarnings('ignore', message='.*torchcodec.*')
warnings.filterwarnings('ignore', category=UserWarning, module='torchaudio')
warnings.filterwarnings('ignore', category=UserWarning, module='torchaudio._backend')

try:
    import soundfile as sf
except Exception as e:
    print("Please install soundfile: pip install soundfile", file=sys.stderr)
    raise e

# Add parent directory to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from shared.config import load_config
    HAS_CONFIG = True
except Exception:
    HAS_CONFIG = False

try:
    from mps_utils import cleanup_mps_memory, log_mps_memory
    HAS_MPS_UTILS = True
except Exception:
    HAS_MPS_UTILS = False
    # Fallback no-op functions
    def cleanup_mps_memory(logger=None):
        pass
    def log_mps_memory(logger, prefix=""):
        pass

def _get_mps_memory() -> float:
    """Get MPS memory in GB"""
    try:
        from mps_utils import get_mps_memory_allocated
        return get_mps_memory_allocated()
    except:
        return 0.0

def load_audio_mono(path: str, target_sr: int = 16000):
    data, sr = sf.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    if sr != target_sr:
        try:
            import librosa
            data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
        except Exception:
            print(f"[warn] librosa not available; input sr={sr}. Consider ffmpeg resample to {target_sr} Hz.", file=sys.stderr)
    return data.astype("float32"), sr

def chunk_spans(duration: float, win: float, pad: float):
    spans = []
    t = 0.0
    while t < duration:
        s = max(0.0, t - pad)
        e = min(duration, t + win + pad)
        spans.append((s, e))
        t += win
    return spans

def write_wav_slice(audio: np.ndarray, sr: int, s: float, e: float):
    si, ei = int(s*sr), int(e*sr)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, audio[si:ei], sr)
    return path

def merge_segments(segments, merge_gap: float):
    if not segments:
        return []
    segments = sorted(segments, key=lambda x: (x[0], x[1]))
    merged = [segments[0]]
    for s, e in segments[1:]:
        ls, le = merged[-1]
        if s - le < merge_gap:
            merged[-1] = (ls, max(le, e))
        else:
            merged.append((s, e))
    return merged

def run_vad_local(chunk_path: str, device: str = "cpu"):
    try:
        from pyannote.audio import Pipeline
        import torch
    except Exception as e:
        print("Please install pyannote.audio: pip install pyannote.audio", file=sys.stderr)
        raise e
    
    if not hasattr(run_vad_local, "_pipe"):
        print(f"[info] Loading PyAnnote VAD pipeline on device={device} ...", file=sys.stderr)
        
        # Get HuggingFace token from environment or config
        hf_token = os.environ.get('HF_TOKEN')
        
        # Fallback: try loading from config if HF_TOKEN not in environment
        if not hf_token and HAS_CONFIG:
            try:
                config_path = os.environ.get('CONFIG_PATH')
                if config_path:
                    config = load_config(config_path)
                    hf_token = getattr(config, 'hf_token', None)
                else:
                    # Try default config path
                    config = load_config('config/.env.pipeline')
                    hf_token = getattr(config, 'hf_token', None)
            except Exception:
                pass
        
        try:
            if hf_token:
                run_vad_local._pipe = Pipeline.from_pretrained(
                    "pyannote/voice-activity-detection",
                    token=hf_token
                )
            else:
                print("[warn] No HF_TOKEN found - trying without authentication", file=sys.stderr)
                run_vad_local._pipe = Pipeline.from_pretrained("pyannote/voice-activity-detection")
            
            if run_vad_local._pipe is None:
                raise RuntimeError("Failed to load PyAnnote pipeline - returned None")
        except Exception as e:
            error_msg = str(e).lower()
            print(f"[error] Failed to load PyAnnote VAD pipeline: {e}", file=sys.stderr)
            
            # Check for specific error conditions
            if "401" in error_msg or "expired" in error_msg or "unauthorized" in error_msg:
                print(f"[error] HuggingFace token is invalid or expired", file=sys.stderr)
                print(f"[error] Please update your HF_TOKEN:", file=sys.stderr)
                print(f"[error]   1. Get a new token from: https://huggingface.co/settings/tokens", file=sys.stderr)
                print(f"[error]   2. Accept model terms at: https://huggingface.co/pyannote/voice-activity-detection", file=sys.stderr)
                print(f"[error]   3. Set HF_TOKEN environment variable or update config/.env.pipeline", file=sys.stderr)
            elif "repository not found" in error_msg or "404" in error_msg:
                print(f"[error] Make sure you have accepted the model terms at:", file=sys.stderr)
                print(f"[error] https://huggingface.co/pyannote/voice-activity-detection", file=sys.stderr)
            else:
                print(f"[error] Unable to load model - check network and authentication", file=sys.stderr)
            
            raise RuntimeError(f"PyAnnote VAD initialization failed - see errors above") from e
        
        try:
            # Convert device string to torch.device object and move pipeline
            if device.lower() == "mps":
                # For MPS, use string directly as torch.device may not work correctly
                import torch
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    run_vad_local._pipe.to(torch.device("mps"))
                    print(f"[info] Pipeline moved to device: mps", file=sys.stderr)
                    # Log memory after model load
                    if HAS_MPS_UTILS:
                        print(f"[info] MPS memory after load: {_get_mps_memory():.2f} GB", file=sys.stderr)
                else:
                    print(f"[warn] MPS not available, using CPU", file=sys.stderr)
                    run_vad_local._pipe.to(torch.device("cpu"))
            else:
                torch_device = torch.device(device)
                run_vad_local._pipe.to(torch_device)
                print(f"[info] Pipeline moved to device: {device}", file=sys.stderr)
        except Exception as e:
            print(f"[warn] Failed to move pipeline to {device}: {e}", file=sys.stderr)
            print(f"[warn] Will attempt to run on CPU", file=sys.stderr)
            run_vad_local._pipe.to(torch.device("cpu"))
    
    # Log memory before VAD processing
    if device.lower() == "mps" and HAS_MPS_UTILS:
        print(f"[info] MPS memory before VAD: {_get_mps_memory():.2f} GB", file=sys.stderr)
    
    try:
        if run_vad_local._pipe is None:
            raise RuntimeError("Pipeline is None - this should not happen")
        tl = run_vad_local._pipe(chunk_path)
        result = [(float(seg.start), float(seg.end)) for seg in tl.itersegments()]
        
        # Cleanup MPS memory after processing
        if device.lower() == "mps" and HAS_MPS_UTILS:
            cleanup_mps_memory()
            print(f"[info] MPS memory after VAD: {_get_mps_memory():.2f} GB", file=sys.stderr)
        
        return result
    except Exception as e:
        print(f"[error] VAD processing failed: {e}", file=sys.stderr)
        raise

def run_vad_remote(chunk_path: str, url: str, timeout: float = 60.0):
    try:
        import requests
    except Exception as e:
        print("Remote mode requires 'requests': pip install requests", file=sys.stderr)
        raise e
    with open(chunk_path, "rb") as f:
        files = {"file": (os.path.basename(chunk_path), f, "audio/wav")}
        r = requests.post(url, files=files, timeout=timeout)
    if r.status_code == 413:
        raise RuntimeError("HTTP 413 Payload Too Large: reduce --win/--pad to lower chunk size.")
    r.raise_for_status()
    js = r.json()
    return [(float(s["start"]), float(s["end"])) for s in js.get("segments", [])]

def export_json(segments, path: str):
    """Export segments in format expected by pipeline"""
    import time
    output = {
        "segments": [{"start": round(s, 3), "end": round(e, 3)} for s, e in segments],
        "metadata": {
            "model": "pyannote/segmentation",
            "num_segments": len(segments),
            "total_duration": round(segments[-1][1], 3) if segments else 0.0,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

def export_srt(segments, path: str):
    def fmt(t):
        h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60.0
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    with open(path, "w", encoding="utf-8") as f:
        for i, (s, e) in enumerate(segments, 1):
            f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n[speech]\n\n")

def main():
    ap = argparse.ArgumentParser(description="Chunked VAD runner (handles 413 by design).")
    ap.add_argument("input", help="Path to audio file (WAV 16k mono recommended).")
    ap.add_argument("--win", type=float, default=45.0, help="Chunk duration (sec).")
    ap.add_argument("--pad", type=float, default=0.25, help="Chunk padding (sec).")
    ap.add_argument("--merge-gap", type=float, default=0.2, help="Merge gaps shorter than this (sec).")
    ap.add_argument("--device", default="cpu", choices=["cpu","cuda","mps"], help="Device for local VAD.")
    ap.add_argument("--remote-url", default=None, help="If set, call this VAD endpoint per chunk (multipart upload).")
    ap.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout for remote mode (sec).")
    ap.add_argument("--target-sr", type=int, default=16000, help="Resample target Hz (if librosa available).")
    ap.add_argument("--out-json", default="speech_segments.json", help="Output JSON file.")
    ap.add_argument("--out-srt", default=None, help="Optional SRT path.")
    args = ap.parse_args()

    try:
        audio, sr = load_audio_mono(args.input, target_sr=args.target_sr)
        duration = len(audio) / sr
        print(f"[info] Loaded {args.input}: {duration:.2f}s @ {sr} Hz (mono)", file=sys.stderr)

        spans = chunk_spans(duration, args.win, args.pad)
        print(f"[info] Chunks: {len(spans)} (win={args.win}s, pad={args.pad}s)", file=sys.stderr)

        all_segments = []
        for idx, (s, e) in enumerate(spans, 1):
            tmp = write_wav_slice(audio, sr, s, e)
            try:
                if args.remote_url:
                    segs = run_vad_remote(tmp, args.remote_url, timeout=args.timeout)
                else:
                    segs = run_vad_local(tmp, device=args.device)
                rebased = [(s + a, s + b) for a, b in segs]
                all_segments.extend(rebased)
                print(f"[ok] {idx}/{len(spans)}: {len(segs)} seg(s)", file=sys.stderr)
            except Exception as ex:
                print(f"[warn] chunk {idx} failed: {ex}", file=sys.stderr)
            finally:
                try: os.remove(tmp)
                except Exception: pass

        merged = merge_segments(all_segments, args.merge_gap)
        print(f"[info] Merged: {len(all_segments)} → {len(merged)}", file=sys.stderr)

        export_json(merged, args.out_json)
        print(f"[save] JSON: {args.out_json}", file=sys.stderr)

        if args.out_srt:
            export_srt(merged, args.out_srt)
            print(f"[save] SRT: {args.out_srt}", file=sys.stderr)
        
        return 0
    except Exception as e:
        print(f"[error] Failed to process: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
