# Phase 3: Advanced ASR Optimization Implementation Plan

**Date**: November 26, 2024  
**Duration**: 1-2 weeks  
**Expected Improvement**: Additional 10% accuracy (90-93% → 93-96%)

---

## Overview

Phase 3 focuses on Tier 3 improvements from the ASR analysis:
1. Multi-pass refinement - Re-process low-confidence segments
2. Speaker diarization integration - Context-aware bias terms
3. Lyrics detection optimization - Separate handling for songs
4. Quality metrics system - Measure and track improvements

---

## Task Breakdown

### Task 1: Multi-Pass Refinement System

**Objective**: Re-process segments with low confidence scores to improve accuracy

#### Current Behavior
- Single-pass transcription
- Low-confidence segments accepted as-is
- No iterative refinement

#### Proposed Multi-Pass Strategy

**Pass 1: Initial Transcription** (Existing)
- Standard WhisperX with Phase 2 parameters
- Collect confidence scores for all segments
- Flag segments with confidence < 0.6

**Pass 2: Targeted Re-transcription**
- Re-process flagged segments with adjusted parameters
- Increase beam size to 15 (from 10)
- Use stricter temperature = 0.0 (already set)
- Apply enhanced bias for character names

**Pass 3: Context-Aware Refinement**
- Use surrounding high-confidence segments for context
- Apply glossary matching with fuzzy thresholds
- Compare multiple candidates and select best

**Pass 4: Validation & Selection**
- Compare Pass 1 vs Pass 2-3 results
- Select higher confidence version
- Merge back into final transcript

#### Implementation

**New Script**: `scripts/06_asr/multi_pass_refiner.py`

```python
class MultiPassRefiner:
    """Multi-pass refinement for low-confidence segments."""
    
    def __init__(self, config):
        self.confidence_threshold = config.get('MULTIPASS_CONFIDENCE_THRESHOLD', 0.6)
        self.max_passes = config.get('MULTIPASS_MAX_ITERATIONS', 3)
        self.beam_size_increment = 5
        
    def identify_low_confidence_segments(self, segments):
        """Find segments that need refinement."""
        low_conf = []
        for seg in segments:
            conf = self._calculate_confidence(seg)
            if conf < self.confidence_threshold:
                low_conf.append((seg, conf))
        return low_conf
    
    def refine_segment(self, segment, audio, pass_num):
        """Re-transcribe single segment with enhanced parameters."""
        # Increase beam size for more thorough search
        beam_size = 10 + (pass_num * self.beam_size_increment)
        
        # Extract audio for this segment
        segment_audio = self._extract_segment_audio(audio, segment)
        
        # Get context from surrounding segments
        context = self._get_segment_context(segment)
        
        # Re-transcribe with enhanced parameters
        result = self._transcribe_with_params(
            segment_audio,
            beam_size=beam_size,
            temperature=0.0,
            context=context
        )
        
        return result
    
    def merge_refined_segments(self, original, refined):
        """Merge refined segments back into transcript."""
        merged = []
        refined_dict = {r['id']: r for r in refined}
        
        for seg in original:
            if seg['id'] in refined_dict:
                # Use refined version if confidence improved
                refined_seg = refined_dict[seg['id']]
                if refined_seg['confidence'] > seg['confidence']:
                    merged.append(refined_seg)
                    continue
            merged.append(seg)
        
        return merged
```

**Configuration Parameters** (add to `.env.pipeline`):
```bash
# Multi-Pass Refinement
MULTIPASS_ENABLED=false                    # Enable multi-pass refinement
MULTIPASS_CONFIDENCE_THRESHOLD=0.6         # Threshold for refinement
MULTIPASS_MAX_ITERATIONS=3                 # Maximum refinement passes
MULTIPASS_BEAM_SIZE_INCREMENT=5            # Beam size increase per pass
MULTIPASS_MIN_SEGMENT_DURATION=1.0         # Minimum segment length (seconds)
```

**Files to Modify**:
- `scripts/06_asr/transcribe.py` - Integrate multi-pass refiner
- `config/.env.pipeline` - Add multi-pass parameters
- `scripts/shared/config.py` - Add parameter definitions

**Testing**:
```bash
# Enable multi-pass in job config
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --multipass
```

**Expected Impact**:
- 3-5% accuracy improvement on difficult segments
- 30-40% more processing time (acceptable for quality)
- Confidence scores distribution shifts higher

---

### Task 2: Speaker Diarization Integration

**Objective**: Use speaker information for context-aware bias term application

#### Current Behavior
- Diarization runs separately (stage 7)
- Results not used in ASR stage
- No speaker-specific glossary application

#### Proposed Integration

**Pre-ASR Diarization**
- Move diarization before ASR (reorder stages)
- Identify speaker segments upfront
- Tag segments with speaker IDs

**Speaker-Aware Bias**
- Maintain speaker-specific glossary
- Character A's dialogue → boost character A's name in glossary
- Character B speaks → boost character B's related terms

**Context Window Enhancement**
- When character speaks, boost their name + related terms
- Use speaker change detection for context boundaries
- Apply different glossary weights per speaker

#### Implementation

**Modified Pipeline Order**:
```
Current: VAD → ASR → Alignment → Diarization
Proposed: VAD → Diarization → ASR → Alignment
```

**New Script**: `scripts/06_asr/speaker_aware_bias.py`

```python
class SpeakerAwareBias:
    """Apply speaker-specific bias terms during transcription."""
    
    def __init__(self, diarization_results, glossary, tmdb_cast):
        self.speakers = diarization_results
        self.glossary = glossary
        self.cast = tmdb_cast
        self.speaker_glossaries = self._build_speaker_glossaries()
    
    def _build_speaker_glossaries(self):
        """Create glossary subsets per speaker based on co-occurrence."""
        speaker_glossaries = {}
        
        for speaker_id in self.speakers.keys():
            # Start with full glossary
            speaker_terms = set(self.glossary.keys())
            
            # Later: Use ML to associate speakers with character names
            # For now: Use all terms with speaker-specific weights
            speaker_glossaries[speaker_id] = speaker_terms
        
        return speaker_glossaries
    
    def get_bias_terms_for_segment(self, segment_time, speaker_id):
        """Get weighted glossary terms for this segment."""
        # Base terms from speaker's glossary
        terms = self.speaker_glossaries.get(speaker_id, set())
        
        # Boost character names that co-occur with this speaker
        boosted_terms = self._boost_cooccurring_terms(speaker_id, terms)
        
        return boosted_terms
    
    def apply_speaker_context(self, segment, speaker_id):
        """Enhance segment with speaker context."""
        # Get speaker's typical terms
        bias_terms = self.get_bias_terms_for_segment(
            segment['start'], 
            speaker_id
        )
        
        # Apply to segment metadata
        segment['speaker_id'] = speaker_id
        segment['bias_terms'] = bias_terms
        
        return segment
```

**Configuration**:
```bash
# Speaker-Aware Bias
SPEAKER_AWARE_BIAS_ENABLED=false           # Enable speaker-aware bias
SPEAKER_BIAS_BOOST_FACTOR=1.5              # Boost weight for speaker terms
SPEAKER_CONTEXT_WINDOW=10.0                # Context window (seconds)
```

**Files to Modify**:
- `run-pipeline.sh` - Reorder stages (VAD → Diarization → ASR)
- `scripts/06_asr/transcribe.py` - Use speaker information
- `scripts/07_alignment/align.py` - Update for new order

**Expected Impact**:
- 5-8% improvement in character name accuracy
- Better context-aware transcription
- Reduced confusion between similar-sounding names

---

### Task 3: Lyrics Detection Optimization

**Objective**: Separate handling for song segments vs. dialogue

#### Current Behavior
- Lyrics detection runs after ASR (stage 8)
- Music segments transcribed same as dialogue
- High hallucination rate in songs

#### Proposed Optimization

**Pre-ASR Music Detection**
- Run lyrics detection before ASR
- Skip/light transcription for high-confidence music
- Full transcription only for dialogue

**Specialized Song Transcription**
- Different parameters for songs vs. dialogue
- Higher temperature for creative lyrics (0.2)
- Special handling for repetitive choruses

**Post-Processing**
- Tag song segments in output
- Optional: Remove song transcriptions from subtitles
- Provide separate song lyrics file

#### Implementation

**Modified Pipeline Order**:
```
Current: ASR → ... → Lyrics Detection
Proposed: VAD → Music Detection → ASR (conditional) → ...
```

**New Script**: `scripts/05b_music_detection/pre_asr_music.py`

```python
class PreASRMusicDetector:
    """Detect music before ASR to optimize transcription."""
    
    def __init__(self, config):
        self.confidence_threshold = config.get('MUSIC_CONFIDENCE_THRESHOLD', 0.7)
        self.min_music_duration = config.get('MIN_MUSIC_DURATION', 10.0)
        
    def classify_segments(self, audio_path, vad_segments):
        """Classify segments as dialogue or music."""
        classifications = []
        
        for segment in vad_segments:
            # Extract segment audio
            seg_audio = self._extract_audio(audio_path, segment)
            
            # Analyze for music characteristics
            music_score = self._detect_music(seg_audio)
            
            classification = {
                'start': segment['start'],
                'end': segment['end'],
                'type': 'music' if music_score > self.confidence_threshold else 'dialogue',
                'music_confidence': music_score
            }
            classifications.append(classification)
        
        return classifications
    
    def _detect_music(self, audio):
        """Detect music characteristics in audio."""
        # Features indicating music:
        # - Regular rhythm/beat
        # - Harmonic structure
        # - Repetitive patterns
        # - Frequency distribution
        
        rhythm_score = self._analyze_rhythm(audio)
        harmony_score = self._analyze_harmony(audio)
        repetition_score = self._analyze_repetition(audio)
        
        # Weighted combination
        music_score = (
            0.4 * rhythm_score +
            0.3 * harmony_score +
            0.3 * repetition_score
        )
        
        return music_score
```

**Conditional ASR**:
```python
def transcribe_with_music_awareness(segments, classifications):
    """Transcribe with different parameters for music vs. dialogue."""
    
    results = []
    
    for segment, classification in zip(segments, classifications):
        if classification['type'] == 'music':
            # Light transcription or skip
            if classification['music_confidence'] > 0.9:
                # Very confident it's music, skip
                result = {
                    'text': '[MUSIC]',
                    'type': 'music',
                    'confidence': classification['music_confidence']
                }
            else:
                # Might be singing, light transcription
                result = transcribe_light(segment)
        else:
            # Full dialogue transcription
            result = transcribe_full(segment)
        
        results.append(result)
    
    return results
```

**Configuration**:
```bash
# Music Detection & Handling
MUSIC_DETECTION_ENABLED=true              # Pre-ASR music detection
MUSIC_CONFIDENCE_THRESHOLD=0.7            # Classification threshold
MIN_MUSIC_DURATION=10.0                   # Minimum music segment (seconds)
SKIP_HIGH_CONFIDENCE_MUSIC=true           # Skip transcription if >0.9 confidence
MUSIC_TRANSCRIPTION_TEMPERATURE=0.2       # Temperature for singing
MUSIC_TAG_IN_SUBTITLES=true               # Add [MUSIC] tags
```

**Files to Create**:
- `scripts/05b_music_detection/pre_asr_music.py` - Music detector
- `scripts/06_asr/conditional_transcribe.py` - Conditional ASR

**Files to Modify**:
- `run-pipeline.sh` - Add music detection stage
- `scripts/06_asr/transcribe.py` - Conditional transcription

**Expected Impact**:
- 60-80% reduction in music-related hallucinations
- 20-30% faster processing (skipping music)
- Cleaner dialogue-only subtitles

---

### Task 4: Quality Metrics System

**Objective**: Measure and track transcription/translation quality

#### Metrics to Track

**Transcription Quality**:
- Word Error Rate (WER)
- Character Error Rate (CER)
- Confidence score distribution
- Hallucination detection rate
- Segment-level quality scores

**Translation Quality**:
- BLEU score
- METEOR score
- Character name preservation rate
- Glossary term hit rate
- Untranslated text detection

**Performance Metrics**:
- Processing time per stage
- Real-time factor (RTF)
- Memory usage
- GPU utilization
- Cache hit rates

#### Implementation

**New Script**: `scripts/metrics/quality_analyzer.py`

```python
class QualityAnalyzer:
    """Analyze transcription and translation quality."""
    
    def analyze_transcription(self, segments, reference=None):
        """Calculate transcription quality metrics."""
        metrics = {
            'total_segments': len(segments),
            'total_duration': self._calculate_duration(segments),
            'confidence_distribution': self._analyze_confidence(segments),
            'hallucination_rate': self._detect_hallucinations(segments),
            'low_confidence_segments': self._count_low_confidence(segments),
        }
        
        if reference:
            # Calculate WER if reference available
            metrics['wer'] = self._calculate_wer(segments, reference)
            metrics['cer'] = self._calculate_cer(segments, reference)
        
        return metrics
    
    def analyze_translation(self, source, translated, glossary=None):
        """Calculate translation quality metrics."""
        metrics = {
            'total_segments': len(translated),
            'bleu_score': self._calculate_bleu(source, translated),
            'untranslated_text_count': self._count_untranslated(translated),
        }
        
        if glossary:
            metrics['glossary_hit_rate'] = self._calculate_glossary_hits(
                translated, glossary
            )
            metrics['character_name_accuracy'] = self._check_character_names(
                translated, glossary
            )
        
        return metrics
    
    def generate_report(self, job_dir, metrics):
        """Generate quality metrics report."""
        report = {
            'job_id': self._extract_job_id(job_dir),
            'timestamp': datetime.now().isoformat(),
            'transcription_metrics': metrics.get('transcription', {}),
            'translation_metrics': metrics.get('translation', {}),
            'performance_metrics': metrics.get('performance', {}),
        }
        
        # Save to JSON
        report_path = job_dir / 'quality_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate human-readable summary
        self._generate_summary_text(report, job_dir / 'quality_summary.txt')
        
        return report
```

**New Script**: `scripts/metrics/performance_tracker.py`

```python
class PerformanceTracker:
    """Track pipeline performance metrics."""
    
    def __init__(self):
        self.stage_timings = {}
        self.memory_usage = []
        self.gpu_usage = []
    
    def start_stage(self, stage_name):
        """Start timing a stage."""
        self.stage_timings[stage_name] = {
            'start': time.time(),
            'memory_start': self._get_memory_usage()
        }
    
    def end_stage(self, stage_name):
        """End timing a stage."""
        if stage_name in self.stage_timings:
            timing = self.stage_timings[stage_name]
            timing['end'] = time.time()
            timing['duration'] = timing['end'] - timing['start']
            timing['memory_end'] = self._get_memory_usage()
            timing['memory_delta'] = timing['memory_end'] - timing['memory_start']
    
    def calculate_rtf(self, audio_duration):
        """Calculate real-time factor."""
        total_time = sum(t['duration'] for t in self.stage_timings.values())
        rtf = audio_duration / total_time if total_time > 0 else 0
        return rtf
    
    def generate_performance_report(self, job_dir):
        """Generate performance report."""
        report = {
            'stage_timings': self.stage_timings,
            'total_time': sum(t['duration'] for t in self.stage_timings.values()),
            'rtf': self.calculate_rtf(self._get_audio_duration(job_dir)),
            'memory_peak': max(self.memory_usage) if self.memory_usage else 0,
        }
        
        return report
```

**Configuration**:
```bash
# Quality Metrics
QUALITY_METRICS_ENABLED=true              # Enable quality tracking
GENERATE_QUALITY_REPORT=true              # Generate report after pipeline
TRACK_PERFORMANCE_METRICS=true            # Track timing/memory
QUALITY_REPORT_FORMAT=json                # json | text | both
```

**Files to Create**:
- `scripts/metrics/quality_analyzer.py` - Quality metrics
- `scripts/metrics/performance_tracker.py` - Performance tracking
- `scripts/metrics/report_generator.py` - Report generation

**Files to Modify**:
- `run-pipeline.sh` - Integrate metrics collection
- All stage scripts - Add performance tracking hooks

**Output Files** (per job):
- `quality_report.json` - Detailed metrics
- `quality_summary.txt` - Human-readable summary
- `performance_report.json` - Timing and resource usage

**Expected Impact**:
- Objective quality measurement
- Identify problematic segments
- Track improvements over time
- Data-driven optimization

---

## Implementation Timeline

### Week 1
**Days 1-2**: Task 1 - Multi-pass refinement (12 hours)
- Implement multi-pass refiner
- Integrate with ASR stage
- Test and validate

**Days 3-4**: Task 2 - Speaker diarization integration (10 hours)
- Reorder pipeline stages
- Implement speaker-aware bias
- Test with multi-speaker scenes

**Day 5**: Testing and adjustment (6 hours)
- Test Tasks 1-2 together
- Measure improvements
- Fix issues

### Week 2
**Days 1-2**: Task 3 - Lyrics detection optimization (10 hours)
- Pre-ASR music detection
- Conditional transcription
- Test with music scenes

**Days 3-4**: Task 4 - Quality metrics system (10 hours)
- Implement metrics collection
- Build report generation
- Integrate with pipeline

**Day 5**: Final testing and documentation (8 hours)
- Full Phase 3 validation
- Performance benchmarking
- Documentation updates

---

## Success Criteria

### Task 1: Multi-Pass Refinement
- ✅ Low-confidence segments improved by 30%
- ✅ Overall accuracy +3-5%
- ✅ Processing time increase < 40%
- ✅ Configurable and optional

### Task 2: Speaker Diarization
- ✅ Character name accuracy +5-8%
- ✅ Context-aware bias working
- ✅ Speaker changes handled correctly
- ✅ No regression in single-speaker scenes

### Task 3: Lyrics Detection
- ✅ Music segments detected with >85% accuracy
- ✅ Dialogue untouched, music skipped/tagged
- ✅ 60-80% reduction in music hallucinations
- ✅ Processing time reduced by 20-30%

### Task 4: Quality Metrics
- ✅ All key metrics collected
- ✅ Reports generated automatically
- ✅ Minimal performance overhead (<5%)
- ✅ Actionable insights provided

---

## Configuration Summary

### New Parameters (add to `.env.pipeline`)

```bash
# ============================================================================
# Phase 3: Advanced Features
# ============================================================================

# Multi-Pass Refinement
MULTIPASS_ENABLED=false
MULTIPASS_CONFIDENCE_THRESHOLD=0.6
MULTIPASS_MAX_ITERATIONS=3
MULTIPASS_BEAM_SIZE_INCREMENT=5
MULTIPASS_MIN_SEGMENT_DURATION=1.0

# Speaker-Aware Bias
SPEAKER_AWARE_BIAS_ENABLED=false
SPEAKER_BIAS_BOOST_FACTOR=1.5
SPEAKER_CONTEXT_WINDOW=10.0

# Music Detection & Handling
MUSIC_DETECTION_ENABLED=true
MUSIC_CONFIDENCE_THRESHOLD=0.7
MIN_MUSIC_DURATION=10.0
SKIP_HIGH_CONFIDENCE_MUSIC=true
MUSIC_TRANSCRIPTION_TEMPERATURE=0.2
MUSIC_TAG_IN_SUBTITLES=true

# Quality Metrics
QUALITY_METRICS_ENABLED=true
GENERATE_QUALITY_REPORT=true
TRACK_PERFORMANCE_METRICS=true
QUALITY_REPORT_FORMAT=json
```

---

## Testing Strategy

### Comprehensive Test Suite

**Test 1: Low-Confidence Segments**
```bash
# Test multi-pass refinement on noisy audio
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --start-time 00:30:00 --end-time 00:35:00 \
  --multipass
```

**Test 2: Multi-Speaker Scene**
```bash
# Test speaker-aware bias with character dialogue
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --start-time 00:15:00 --end-time 00:20:00 \
  --speaker-aware-bias
```

**Test 3: Music Scene**
```bash
# Test lyrics detection with song
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --start-time 00:00:00 --end-time 00:05:00 \
  --music-detection
```

**Test 4: Full Pipeline**
```bash
# Test all Phase 3 features together
./prepare-job.sh --media file.mp4 --workflow translate \
  --source-language hi --target-language en \
  --start-time 00:10:00 --end-time 00:30:00 \
  --multipass --speaker-aware-bias --music-detection
```

### Validation Metrics

Compare Phase 2 vs Phase 3 results:

| Metric | Phase 2 | Phase 3 Target |
|--------|---------|----------------|
| Accuracy | 90-93% | 93-96% |
| Character Names | 90-95% | 95%+ |
| Hallucination Rate | 5-10% | <3% |
| Music Handling | Poor | Excellent |
| Processing Time | 50-60s | 80-100s |

---

## Rollback Plan

If Phase 3 causes issues:

1. **Disable Phase 3 features**:
   ```bash
   # Edit config/.env.pipeline
   MULTIPASS_ENABLED=false
   SPEAKER_AWARE_BIAS_ENABLED=false
   MUSIC_DETECTION_ENABLED=false
   QUALITY_METRICS_ENABLED=false
   ```

2. **Revert stage ordering**:
   ```bash
   # Restore original pipeline order in run-pipeline.sh
   # VAD → ASR → Alignment → Diarization → Lyrics
   ```

3. **Use Phase 2 configuration**:
   ```bash
   cp config/.env.pipeline.phase2 config/.env.pipeline
   ```

---

## Expected Final Results

### After Full Phase 3 Implementation

**Transcription Quality**:
- Overall Accuracy: 93-96%
- Character Names: 95%+
- Hallucination Rate: <3%
- Confidence Scores: Higher distribution

**Translation Quality**:
- BLEU Score: >45
- Glossary Hit Rate: >70%
- No Untranslated Hindi Words
- Character Names Preserved

**Performance**:
- Processing Time: 80-100s for 5-min clip (1.6-2x realtime)
- Memory Usage: Stable <4GB
- GPU Utilization: Optimal

**User Experience**:
- High-quality subtitles
- Accurate character names
- Clean dialogue transcripts
- Music scenes handled gracefully

---

**Status**: Ready for implementation  
**Estimated Effort**: 56 hours over 2 weeks  
**Expected Outcome**: Production-grade 93-96% accuracy
