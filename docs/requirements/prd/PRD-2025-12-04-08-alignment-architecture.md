# Product Requirement Document (PRD): Hybrid Alignment Architecture

**PRD ID:** PRD-2025-12-04-08-alignment-architecture  
**Related BRD:** [BRD-2025-12-04-08-alignment-architecture.md](../brd/BRD-2025-12-04-08-alignment-architecture.md)  
**Related AD:** AD-008 (ARCHITECTURE.md)  
**Status:** ✅ Implemented  
**Created:** 2025-12-04  
**Last Updated:** 2025-12-10

---

## I. Introduction

### Purpose
Eliminate segmentation faults during alignment by using subprocess isolation when MLX backend is active, while maintaining optimal performance through direct alignment for other backends.

### Problem
MLX backend causes segfaults during alignment phase (memory corruption), requiring process isolation to prevent crashes.

---

## II. User Personas

**Persona 1: Mac User Max (MLX User)**
- **Hardware:** MacBook Pro M2 with MLX
- **Pain Point:** Pipeline crashes during alignment with segfault
- **Current:** 0% success rate (always crashes)
- **Expected:** 100% success rate (reliable completion)

**Persona 2: Linux User Lucy (CPU/GPU User)**
- **Hardware:** Ubuntu workstation with NVIDIA GPU
- **Pain Point:** None (alignment works fine)
- **Expected:** Same performance as before (no slowdown)

---

## III. User Stories

**Story 1: Reliable MLX Alignment**
```
As a Mac user with MLX backend
I want alignment to complete without segfaults
So that my transcription jobs finish successfully

Acceptance Criteria:
- [x] No segfaults during alignment
- [x] 100% job completion rate
- [x] Word-level timestamps generated correctly
- [x] Subprocess isolation prevents memory corruption
- [x] 5-minute timeout for subprocess
- [x] Graceful fallback if subprocess fails
```

**Story 2: Preserved Performance (Non-MLX)**
```
As a Linux/Windows user
I want alignment performance to remain unchanged
So that I don't experience slowdowns from MLX fixes

Acceptance Criteria:
- [x] Non-MLX backends use direct alignment (no subprocess)
- [x] Same performance as before (no overhead)
- [x] No behavior changes for CPU/CUDA users
- [x] Hybrid architecture is transparent
```

**Story 3: Automatic Backend Routing**
```
As any user
I want the system to automatically choose the right alignment method
So that I get optimal results without configuration

Acceptance Criteria:
- [x] MLX backend → subprocess alignment (stability)
- [x] Other backends → direct alignment (performance)
- [x] Automatic detection (no user config)
- [x] Logs show which method was used
```

---

## IV. UX/UI Requirements

**MLX Backend (Subprocess Alignment):**
```bash
$ ./run-pipeline.sh -j job-001

🚀 ASR Backend: MLX-Whisper
   Transcription: 84 seconds ✅
   
🔄 Alignment Method: WhisperX subprocess (MLX backend detected)
   Reason: Prevents segmentation faults
   Timeout: 5 minutes
   
⏱️  Subprocess started...
   Duration: 39 seconds
   Words aligned: 1,847
   Segments: 200
   
✅ Alignment complete (subprocess isolated)
```

**Non-MLX Backend (Direct Alignment):**
```bash
$ ./run-pipeline.sh -j job-002

🚀 ASR Backend: CTranslate2 (CPU)
   Transcription: 180 seconds ✅
   
🔄 Alignment Method: Direct (in-process)
   Reason: Non-MLX backend (no segfault risk)
   
⏱️  Aligning segments...
   Duration: 35 seconds
   Words aligned: 1,847
   
✅ Alignment complete (direct method)
```

---

## V. Non-Functional Requirements

### Reliability

**MLX Backend:**
- **Segfault rate:** 0% (was 100% before fix)
- **Completion rate:** 100%
- **Subprocess timeout:** 5 minutes (configurable)
- **Fallback:** Return segments without word timestamps if subprocess fails

**Non-MLX Backends:**
- **No changes:** Same reliability as before
- **No overhead:** Direct alignment preserved

### Performance

**MLX Backend (Subprocess):**
- **Overhead:** 1-2 seconds for subprocess launch
- **Total alignment:** 39 seconds (acceptable)
- **Trade-off:** Slight overhead for 100% reliability ✅

**Non-MLX Backends (Direct):**
- **Performance:** Unchanged (no overhead)
- **Alignment:** 35-40 seconds (same as before)

---

## VI. Architecture

**Hybrid Design:**

```python
def align_segments(self, result, audio_file, language):
    """Hybrid alignment dispatcher."""
    if self.backend.name == "mlx-whisper":
        # Use subprocess isolation
        return self.align_with_whisperx_subprocess(
            result["segments"], 
            audio_file, 
            language
        )
    else:
        # Use direct alignment (optimal)
        return self.backend.align_segments(
            result["segments"], 
            audio_file, 
            language
        )
```

**Decision Logic:**
| Backend | Alignment Method | Reason |
|---------|------------------|--------|
| MLX-Whisper | Subprocess | Prevents segfaults |
| CTranslate2 | Direct | No segfault risk |
| WhisperX | Direct | No segfault risk |
| Faster-Whisper | Direct | No segfault risk |

---

## VII. Success Criteria

- [x] MLX backend: 0% segfault rate (was 100%)
- [x] MLX backend: 100% completion rate
- [x] Non-MLX backends: No performance degradation
- [x] Automatic routing: No user configuration needed
- [x] Subprocess timeout: Prevents hangs
- [x] Graceful fallback: Returns segments if alignment fails
- [x] Documentation: Hybrid architecture documented

---

## VIII. Risk Mitigation

**Risk 1: Subprocess Overhead**
- **Impact:** LOW (1-2 seconds)
- **Mitigation:** Only for MLX backend
- **Status:** ✅ Acceptable overhead for reliability

**Risk 2: Subprocess Failure**
- **Impact:** MEDIUM (no word timestamps)
- **Mitigation:** Fallback to segment timestamps
- **Status:** ✅ Graceful degradation implemented

**Risk 3: Timeout Issues**
- **Impact:** LOW (very long audio)
- **Mitigation:** 5-minute timeout (adjustable)
- **Status:** ✅ Configurable timeout

---

## IX. Testing

**Test Scenarios:**

1. **MLX + Subprocess:**
   - [x] Transcription completes successfully
   - [x] Subprocess alignment launches correctly
   - [x] No segfaults occur
   - [x] Word-level timestamps generated
   - [x] 200 segments, 1,847 words ✅

2. **Non-MLX + Direct:**
   - [x] Direct alignment used
   - [x] No subprocess overhead
   - [x] Performance unchanged
   - [x] Word-level timestamps generated

3. **Edge Cases:**
   - [x] Subprocess timeout (graceful fallback)
   - [x] Subprocess failure (return segments)
   - [x] Very long audio (>2 hours)

---

**Status:** ✅ IMPLEMENTED & VALIDATED  
**Reference:** ARCHITECTURE_ALIGNMENT_2025-12-04.md, AD-008  
**Success Rate:** 100% (up from 0% with MLX)  
**Template Version:** 1.0
