# Logging Architecture Diagram

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PIPELINE ORCHESTRATOR                       │
│                   (scripts/run-pipeline.py)                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ├─ Writes to ─→ logs/99_pipeline_*.log
                             │                (Main orchestration log)
                             │
              ┌──────────────┴──────────────┐
              │     Stage Execution         │
              │  (Each stage gets StageIO)  │
              └──────────────┬──────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    ┌─────────┐         ┌─────────┐       ┌─────────┐
    │ Stage 1 │         │ Stage 2 │       │ Stage N │
    │ (demux) │         │  (asr)  │       │  (mux)  │
    └────┬────┘         └────┬────┘       └────┬────┘
         │                   │                  │
         ├─ stage.log        ├─ stage.log      ├─ stage.log
         │  (Detailed log)   │  (Detailed log) │  (Detailed log)
         │                   │                  │
         ├─ manifest.json    ├─ manifest.json  ├─ manifest.json
         │  (I/O tracking)   │  (I/O tracking) │  (I/O tracking)
         │                   │                  │
         └─ Output files     └─ Output files   └─ Output files
```

## Directory Structure Detail

```
out/<job-id>/
│
├── logs/                                    ← Main logs directory
│   └── 99_pipeline_20251127_140915.log     ← Main orchestration log
│                                               • Stage transitions
│                                               • Overall progress
│                                               • High-level errors
│
├── 01_demux/                                ← Stage 1 directory
│   ├── stage.log                            ← Detailed stage log
│   │                                           • All DEBUG messages
│   │                                           • Tool output (ffmpeg)
│   │                                           • Processing details
│   │
│   ├── manifest.json                        ← I/O tracking manifest
│   │   {                                       • Inputs used
│   │     "inputs": [...],                     • Outputs created
│   │     "outputs": [...],                    • Config used
│   │     "intermediate_files": [...],         • Errors/warnings
│   │     "config": {...},                     • Timing/resources
│   │     "errors": [...],
│   │     "warnings": [...]
│   │   }
│   │
│   ├── audio.wav                            ← Primary output
│   └── metadata.json                        ← Stage metadata
│
├── 02_tmdb/                                 ← Stage 2 directory
│   ├── stage.log
│   ├── manifest.json
│   ├── enrichment.json
│   └── metadata.json
│
├── 03_source_separation/                    ← Stage 3 directory
│   ├── stage.log
│   ├── manifest.json
│   ├── vocals.wav                           ← Output (tracked)
│   ├── accompaniment.wav                    ← Intermediate (tracked)
│   └── metadata.json
│
├── 04_pyannote_vad/                         ← Stage 4 directory
│   ├── stage.log
│   ├── manifest.json
│   ├── speech_segments.json
│   └── metadata.json
│
├── 05_asr/                                  ← Stage 5 directory
│   ├── stage.log
│   ├── manifest.json
│   ├── segments.json
│   └── metadata.json
│
└── ... (more stages)
```

## Logging Flow

```
┌──────────────────────────────────────────────────────────────┐
│                    Stage Execution                           │
└──────────────────────────────────────────────────────────────┘
                             │
                             │ 1. Initialize
                             ▼
                    ┌────────────────┐
                    │    StageIO     │
                    │  initialized   │
                    └───────┬────────┘
                            │
                            ├─ Creates: stage.log
                            ├─ Creates: manifest.json
                            └─ Creates: stage directory
                             │
                             │ 2. Get Logger
                             ▼
                    ┌────────────────┐
                    │  Dual Logger   │
                    │   configured   │
                    └───────┬────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
    ┌──────────────────┐      ┌──────────────────┐
    │   Stage Logger   │      │ Pipeline Logger  │
    │ (to stage.log)   │      │ (to pipeline.log)│
    └──────────────────┘      └──────────────────┘
              │                           │
    ┌─────────┴────────┐        ┌────────┴─────────┐
    │ ALL log levels   │        │ INFO and above   │
    │ • DEBUG          │        │ • INFO           │
    │ • INFO           │        │ • WARNING        │
    │ • WARNING        │        │ • ERROR          │
    │ • ERROR          │        │ • CRITICAL       │
    └──────────────────┘        └──────────────────┘
                             │
                             │ 3. Track I/O
                             ▼
                    ┌────────────────┐
                    │  track_input() │
                    │ track_output() │
                    └───────┬────────┘
                            │
                            ├─ Adds to manifest.inputs[]
                            ├─ Adds to manifest.outputs[]
                            └─ Records metadata
                             │
                             │ 4. Process Data
                             ▼
                    ┌────────────────┐
                    │   Processing   │
                    │   (your code)  │
                    └───────┬────────┘
                            │
                            ├─ logger.debug() → stage.log only
                            ├─ logger.info()  → both logs
                            ├─ logger.error() → both logs
                             │
                             │ 5. Finalize
                             ▼
                    ┌────────────────┐
                    │  finalize()    │
                    └───────┬────────┘
                            │
                            ├─ Sets status (success/failed/skipped)
                            ├─ Records duration
                            ├─ Adds custom metadata
                            └─ Saves manifest.json
```

## Manifest Data Flow

```
                    Input Stage              Current Stage
                   (e.g., demux)              (e.g., asr)
                         │                         │
                         │                         │
    ┌────────────────────┴─────┐     ┌───────────┴────────────┐
    │  01_demux/manifest.json  │     │  05_asr/manifest.json  │
    │  {                       │     │  {                     │
    │    "outputs": [          │     │    "inputs": [         │
    │      {                   │     │      {                 │
    │        "type": "audio",  │────────────"type": "audio", │
    │        "path": "...",    │     │        "path": "...",  │
    │        "size_bytes": ... │     │        "size_bytes":..│
    │      }                   │     │      }                 │
    │    ]                     │     │    ],                  │
    │  }                       │     │    "outputs": [        │
    └──────────────────────────┘     │      {                 │
                                      │        "type": "...", │
                                      │        "path": "..."  │
                                      │      }                 │
                                      │    ]                   │
                                      │  }                     │
                                      └────────────────────────┘
                                               │
                                               │ Output becomes
                                               │ input to next stage
                                               ▼
                                      ┌────────────────────────┐
                                      │ Next Stage             │
                                      │ (e.g., alignment)      │
                                      └────────────────────────┘
```

## Log Level Routing

```
┌──────────────────────────────────────────────────────────────┐
│                    Log Message Emitted                       │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ├─ logger.debug("Details...")
                       ├─ logger.info("Progress...")
                       ├─ logger.warning("Issue...")
                       └─ logger.error("Failed...")
                       │
        ┌──────────────┴───────────────┐
        │     Which logger called?     │
        └──────────────┬───────────────┘
                       │
         ┌─────────────┴──────────────┐
         │                            │
         ▼                            ▼
    Stage Logger              Pipeline Logger
    (stage.log)               (99_pipeline_*.log)
         │                            │
         ├─ DEBUG  ✓                  ├─ DEBUG  ✗
         ├─ INFO   ✓                  ├─ INFO   ✓
         ├─ WARN   ✓                  ├─ WARN   ✓
         ├─ ERROR  ✓                  └─ ERROR  ✓
         └─ CRITICAL ✓
         
    ┌─────────────┴──────────────┐
    │ Stage log gets EVERYTHING  │
    │ Pipeline log gets INFO+    │
    └────────────────────────────┘
```

## Manifest Structure

```
manifest.json
├── stage: "asr"
├── stage_number: 5
├── timestamp: "2025-11-27T14:09:16.123456"
├── status: "success" | "failed" | "skipped"
├── duration_seconds: 45.2
├── completed_at: "2025-11-27T14:10:01.345678"
│
├── inputs: [
│     {
│       type: "audio",           ← File type
│       path: "path/to/file",    ← File location
│       size_bytes: 47493120,    ← File size
│       format: "wav",           ← Custom metadata
│       sample_rate: 16000       ← Custom metadata
│     }
│   ]
│
├── outputs: [
│     {
│       type: "transcript",
│       path: "path/to/segments.json",
│       size_bytes: 12345,
│       format: "json",
│       segments: 150            ← Custom metadata
│     }
│   ]
│
├── intermediate_files: [
│     {
│       type: "intermediate",
│       path: "path/to/cache.bin",
│       retained: true,          ← Kept after stage?
│       reason: "Model cache",   ← Why created?
│       size_bytes: 1048576
│     }
│   ]
│
├── config: {
│     model: "whisper-large-v3",
│     device: "mps",
│     batch_size: 16,
│     language: "hi"
│   }
│
├── resources: {
│     cpu_percent: 85.5,
│     memory_mb: 2048,
│     gpu_used: true
│   }
│
├── errors: [
│     {
│       timestamp: "...",
│       message: "Error description",
│       exception_type: "ValueError",
│       exception_detail: "..."
│     }
│   ]
│
└── warnings: [
      {
        timestamp: "...",
        message: "Warning description"
      }
    ]
```

## Example: ASR Stage Execution

```
Time  │ Action                        │ Logs To
──────┼───────────────────────────────┼─────────────────────────────
14:09 │ Pipeline: "▶️ Stage asr"      │ 99_pipeline_*.log
      │                               │
14:09 │ Stage: Initialize StageIO     │ (internal)
14:09 │ Stage: Create stage.log       │ 05_asr/stage.log created
14:09 │ Stage: Create manifest.json   │ 05_asr/manifest.json created
      │                               │
14:09 │ Stage: Get input from demux   │ 05_asr/stage.log (DEBUG)
14:09 │ Stage: Track input audio.wav  │ manifest.json → inputs[]
      │                               │
14:09 │ Stage: Load Whisper model     │ 05_asr/stage.log (DEBUG)
14:09 │ Stage: "Processing audio..."  │ 05_asr/stage.log (INFO)
      │                               │ 99_pipeline_*.log (INFO)
      │                               │
14:10 │ Stage: Transcribing batch 1   │ 05_asr/stage.log (DEBUG)
14:10 │ Stage: Transcribing batch 2   │ 05_asr/stage.log (DEBUG)
14:10 │ Stage: Transcribing batch 3   │ 05_asr/stage.log (DEBUG)
      │                               │
14:10 │ Stage: Save segments.json     │ 05_asr/stage.log (DEBUG)
14:10 │ Stage: Track output           │ manifest.json → outputs[]
      │                               │
14:10 │ Stage: Finalize success       │ manifest.json saved
14:10 │ Stage: "✓ Transcribed 150..."  │ 05_asr/stage.log (INFO)
      │                               │ 99_pipeline_*.log (INFO)
      │                               │
14:10 │ Pipeline: "✅ Stage asr: OK"   │ 99_pipeline_*.log
```

## Troubleshooting Flow

```
┌─────────────────────────────────────────┐
│  Problem: Pipeline failed               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Check main log first │
        │ logs/99_pipeline_*   │
        └──────────┬───────────┘
                   │
                   ├─ Find: "❌ Stage X: FAILED"
                   └─ Note: Stage name and time
                   │
                   ▼
        ┌──────────────────────┐
        │ Check stage log      │
        │ XX_stage/stage.log   │
        └──────────┬───────────┘
                   │
                   ├─ Read: Detailed error messages
                   ├─ Check: DEBUG output
                   └─ Find: Exact failure point
                   │
                   ▼
        ┌──────────────────────┐
        │ Check manifest       │
        │ XX_stage/manifest.json│
        └──────────┬───────────┘
                   │
                   ├─ Verify: inputs[] correct?
                   ├─ Check: outputs[] created?
                   ├─ Review: config{} settings
                   └─ Examine: errors[] array
                   │
                   ▼
        ┌──────────────────────┐
        │ Problem identified!  │
        │ Fix and retry        │
        └──────────────────────┘
```

## Key Benefits

1. **Clear Separation**
   - Main log: What happened (orchestration)
   - Stage log: How it happened (details)
   - Manifest: What was used/created (data lineage)

2. **Efficient Debugging**
   - Start with main log (quick overview)
   - Drill into stage log (detailed investigation)
   - Validate with manifest (verify data flow)

3. **Complete Audit Trail**
   - Every input tracked
   - Every output tracked
   - Every intermediate file documented
   - All configuration recorded

4. **Easy Analysis**
   - Main log: Pipeline-level patterns
   - Stage logs: Stage-level issues
   - Manifests: Data flow validation

5. **Reproducibility**
   - Manifests capture exact configuration
   - Can replay stages with same settings
   - Clear record of what was used
