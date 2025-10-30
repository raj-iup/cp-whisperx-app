🎬 MP4 Source (Film Scene)
   ↓
[FFmpeg Demux] — extract 16kHz mono audio
   ↓
[TMDB Metadata Fetch] — movie data: cast, places, plot, keywords
   ↓
[Pre-ASR NER] — extract named entities (names, locations, titles) → builds smarter ASR initial prompt
   ↓
[Silero VAD] — coarse speech segmentation
   ↓
[PyAnnote VAD] — refined contextual boundaries
   ↓
[PyAnnote Diarization] — mandatory speaker labeling
   ↓
[WhisperX ASR + Forced Alignment] — English translation + time-aligned transcription (uses NER-enriched prompt)
   ↓
[Post-ASR NER] — entity correction & enrichment (match TMDB names, fix spellings)
   ↓
[Subtitle Generation (.srt)] — speaker-prefixed, entity-corrected English subtitles
   ↓
[FFmpeg Mux] — embed English soft-subtitles into MP4 (mov_text)
   ↓
🎞️ Final Output: movie_with_en_subs.mp4