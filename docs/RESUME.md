# Resume Guide

**Continue failed jobs from checkpoints**

## How Resume Works

Pipeline uses manifest.json to track stage completion. When a job fails, you can resume from the last successful checkpoint.

## Usage

```bash
# Resume from last checkpoint
./resume-pipeline.sh 20251108-0001

# Check what will be resumed
./scripts/pipeline-status.sh 20251108-0001
```

Return to [Documentation Index](INDEX.md)
