# Native Pipeline Debug Quick Reference

**Fast debugging guide for native MPS pipeline**

---

## 🎯 Recommended: Stage 7 ASR Debug

```powershell
# Windows
.\native\run_asr_debug.ps1 <MOVIE_NAME> [-Model base] [-Language en]

# macOS/Linux
./native/run_asr_debug.sh <MOVIE_NAME> [--model base] [--language en]
```

### Examples
```powershell
# Windows
.\native\run_asr_debug.ps1 My_Movie_2024
.\native\run_asr_debug.ps1 My_Movie_2024 -Model small -Language hi

# macOS/Linux
./native/run_asr_debug.sh My_Movie_2024
./native/run_asr_debug.sh My_Movie_2024 --model small --language hi
```

---

## 🔧 Manual Debug Mode (Any Stage)

### Step 1: Set Environment Variable
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"

# macOS/Linux
export LOG_LEVEL=DEBUG
```

### Step 2: Activate Stage Venv
```powershell
# Windows
.\native\venvs\<STAGE>\Scripts\Activate.ps1

# macOS/Linux
source native/venvs/<STAGE>/bin/activate
```

### Step 3: Run Script
```powershell
# Windows/macOS/Linux
python native/scripts/<SCRIPT>.py `
    --input "in/video.mp4" `
    --movie-dir "out/Movie_Name"
```

---

## ⚡ Quick Stage Commands

### Stage 4 - Silero VAD
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"
.\native\venvs\silero-vad\Scripts\Activate.ps1
python native\scripts\04_silero_vad.py --input "in\video.mp4" --movie-dir "out\Movie"

# macOS/Linux
export LOG_LEVEL=DEBUG && source native/venvs/silero-vad/bin/activate
python native/scripts/04_silero_vad.py --input "in/video.mp4" --movie-dir "out/Movie"
```

### Stage 5 - PyAnnote VAD
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"
.\native\venvs\pyannote-vad\Scripts\Activate.ps1
python native\scripts\05_pyannote_vad.py --input "in\video.mp4" --movie-dir "out\Movie"

# macOS/Linux
export LOG_LEVEL=DEBUG && source native/venvs/pyannote-vad/bin/activate
python native/scripts/05_pyannote_vad.py --input "in/video.mp4" --movie-dir "out/Movie"
```

### Stage 6 - Diarization
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"
.\native\venvs\diarization\Scripts\Activate.ps1
python native\scripts\06_diarization.py --input "in\video.mp4" --movie-dir "out\Movie"

# macOS/Linux
export LOG_LEVEL=DEBUG && source native/venvs/diarization/bin/activate
python native/scripts/06_diarization.py --input "in/video.mp4" --movie-dir "out/Movie"
```

### Stage 7 - ASR
```powershell
# Windows
.\native\run_asr_debug.ps1 Movie -Model base

# macOS/Linux
./native/run_asr_debug.sh Movie --model base
```

### Stage 8 - Post-NER
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"
.\native\venvs\post-ner\Scripts\Activate.ps1
python native\scripts\08_post_ner.py --input "in\video.mp4" --movie-dir "out\Movie"

# macOS/Linux
export LOG_LEVEL=DEBUG && source native/venvs/post-ner/bin/activate
python native/scripts/08_post_ner.py --input "in/video.mp4" --movie-dir "out/Movie"
```

### Stage 9 - Subtitle Gen
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"
.\native\venvs\subtitle-gen\Scripts\Activate.ps1
python native\scripts\09_subtitle_gen.py --input "in\video.mp4" --movie-dir "out\Movie"

# macOS/Linux
export LOG_LEVEL=DEBUG && source native/venvs/subtitle-gen/bin/activate
python native/scripts/09_subtitle_gen.py --input "in/video.mp4" --movie-dir "out/Movie"
```

### Stage 10 - Mux
```powershell
# Windows
$env:LOG_LEVEL="DEBUG"
.\native\venvs\mux\Scripts\Activate.ps1
python native\scripts\10_mux.py --input "in\video.mp4" --movie-dir "out\Movie"

# macOS/Linux
export LOG_LEVEL=DEBUG && source native/venvs/mux/bin/activate
python native/scripts/10_mux.py --input "in/video.mp4" --movie-dir "out/Movie"
```

---

## 📁 Log Locations

### All Logs
```
logs/
```

### Stage Log
```
logs/<stage>_<movie>_<timestamp>.log
```

### Session Log
```
logs/session_<movie>_<timestamp>.log
```

---

## 👀 Viewing Logs

### View Latest Log (Windows)
```powershell
Get-ChildItem logs\asr_*.log | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Get-Content
```

### View Latest Log (macOS/Linux)
```bash
ls -t logs/asr_*.log | head -1 | xargs cat
```

### Follow in Real-Time (Windows)
```powershell
Get-Content logs\asr_*.log -Wait -Tail 50
```

### Follow in Real-Time (macOS/Linux)
```bash
tail -f logs/asr_*.log
```

### Find Errors (Windows)
```powershell
Select-String -Path logs\asr_*.log -Pattern "ERROR"
```

### Find Errors (macOS/Linux)
```bash
grep ERROR logs/asr_*.log
```

### View Last 50 Lines (Windows)
```powershell
Get-Content logs\asr_*.log -Tail 50
```

### View Last 50 Lines (macOS/Linux)
```bash
tail -50 logs/asr_*.log
```

---

## 🎛️ ASR Model Options

| Model | Speed | Quality | VRAM | Use Case |
|-------|-------|---------|------|----------|
| `tiny` | ⚡⚡⚡⚡⚡ | ⭐ | 1GB | Quick tests |
| `base` | ⚡⚡⚡⚡ | ⭐⭐ | 1GB | **Default** |
| `small` | ⚡⚡⚡ | ⭐⭐⭐ | 2GB | Better quality |
| `medium` | ⚡⚡ | ⭐⭐⭐⭐ | 5GB | High quality |
| `large-v2` | ⚡ | ⭐⭐⭐⭐⭐ | 10GB | Best quality |
| `large-v3` | ⚡ | ⭐⭐⭐⭐⭐ | 10GB | Latest |

---

## ⚠️ Common Issues

### ✗ Movie dir not found
```powershell
# Windows
Test-Path out\<MOVIE_NAME>
New-Item -ItemType Directory -Path out\<MOVIE_NAME> -Force

# macOS/Linux
ls -la out/
mkdir -p out/<MOVIE_NAME>
```

### ✗ Venv not found
```powershell
# Windows
.\native\setup_venvs.ps1

# macOS/Linux
./native/setup_venvs.sh
```

### ✗ Audio file missing
- Run Stage 1 (demux) first
```powershell
# Windows
Test-Path out\<MOVIE>\audio\

# macOS/Linux
ls -la out/<MOVIE>/audio/
```

### ✗ Speaker segments missing
- Run Stage 6 (diarization) first
```powershell
# Windows
Test-Path out\<MOVIE>\diarization\

# macOS/Linux
ls -la out/<MOVIE>/diarization/
```

---

## ✅ Debugging Checklist

- [ ] Venv activated
- [ ] LOG_LEVEL set to DEBUG
- [ ] Input file exists
- [ ] Movie directory exists
- [ ] Previous stage outputs present
- [ ] logs/ directory exists
- [ ] Sufficient disk space
- [ ] Check logs for detailed errors

---

## 📚 More Information

See [Debug Mode Guide](../docs/guides/developer/debug-mode.md) for comprehensive information.
