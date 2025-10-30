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
from typing import List, Tuple

import numpy as np

try:
    import soundfile as sf
except Exception as e:
    print("Please install soundfile: pip install soundfile", file=sys.stderr)
    raise e

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
    except Exception as e:
        print("Please install pyannote.audio: pip install pyannote.audio", file=sys.stderr)
        raise e
    if not hasattr(run_vad_local, "_pipe"):
        print(f"[info] Loading PyAnnote VAD pipeline on device={device} ...", file=sys.stderr)
        run_vad_local._pipe = Pipeline.from_pretrained("pyannote/voice-activity-detection")
        try:
            run_vad_local._pipe.to(device)
        except Exception:
            pass
    tl = run_vad_local._pipe(chunk_path)
    return [(float(seg.start), float(seg.end)) for seg in tl.itersegments()]

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
    with open(path, "w", encoding="utf-8") as f:
        json.dump([{"start": round(s,3), "end": round(e,3)} for s,e in segments], f, ensure_ascii=False, indent=2)

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
    ap.add_argument("--device", default="cpu", choices=["cpu","cuda"], help="Device for local VAD.")
    ap.add_argument("--remote-url", default=None, help="If set, call this VAD endpoint per chunk (multipart upload).")
    ap.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout for remote mode (sec).")
    ap.add_argument("--target-sr", type=int, default=16000, help="Resample target Hz (if librosa available).")
    ap.add_argument("--out-json", default="speech_segments.json", help="Output JSON file.")
    ap.add_argument("--out-srt", default=None, help="Optional SRT path.")
    args = ap.parse_args()

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

if __name__ == "__main__":
    main()
