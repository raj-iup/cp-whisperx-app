# Subtitling Pipeline Architecture (Offline Batch, Apple Silicon / MPS)

## 1. Overview

This document describes an offline batch subtitling pipeline that:

- Ingests video/audio files (e.g., MP4, MKV).
- Extracts and preprocesses audio.
- Uses **Silero VAD** for fast speech segmentation.
- Uses **Whisper** for ASR.
- Uses **pyannote VAD** (and optionally **pyannote diarization**) to refine speech regions and add speaker labels.
- Produces **SRT/WebVTT** subtitle files, and optionally muxes or burns them into video files.

Target runtime environment:

- macOS on Apple Silicon (e.g., M1 Pro).
- GPU acceleration via **Apple Metal / PyTorch MPS**.
- Offline batch processing (no real-time constraints).

---

## 2. Goals & Non-Goals

### 2.1 Goals

- **Accurate subtitles** with:
  - Good alignment of subtitle in/out times to speech.
  - Robustness to noise, music, and overlapping speakers.
- **Efficient batch processing**:
  - Avoid decoding silence.
  - Leverage MPS for Whisper and pyannote where possible.
- **Speaker-aware subtitles** (optional):
  - Label who is speaking if diarization is enabled.
- **Composable architecture**:
  - Clear layers that can be independently improved (better VAD, ASR, MT, etc.).

### 2.2 Non-Goals

- Real-time or low-latency subtitling.
- UI / frontend design (only backend workflow).
- Full translation workflow (can be added later on top of this pipeline).

---

## 3. High-Level Data Flow

```text
[Input Media: MP4/MKV/MOV]
          |
          v
   (1) Media Ingestion & Job Queue
          |
          v
   (2) Audio Extraction (FFmpeg -> 16k mono WAV)
          |
          v
   (3) Audio Pre-processing (optional normalize/denoise)
          |
          v
   (4) Silero VAD (fast segmentation)
          |
          v
   (5) Whisper ASR per segment
          |
          v
   Provisional subtitles (rough timings)
          |
          +---------------------------+
          |                           |
          v                           |
   (6) pyannote VAD (full file)       |
   (7) pyannote Diarization (optional)|
          |                           |
          v                           |
   Refined speech regions + speakers  |
          |                           |
          +---------------------------+
          |
          v
   (8) Subtitle Assembly & Formatting
          |
          v
   (9) Export: SRT/WebVTT (+ FFmpeg mux/burn-in)