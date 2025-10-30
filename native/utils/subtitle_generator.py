"""
SRT Subtitle Generation wrapper for native MPS pipeline.
Generates properly formatted SRT subtitles from corrected transcripts.
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import timedelta


class SubtitleGenerator:
    """
    Generate SRT subtitles from transcript with timing and speaker information.
    
    SRT Format:
    1
    00:00:00,000 --> 00:00:05,000
    Speaker: Text content
    
    2
    00:00:05,000 --> 00:00:10,000
    Speaker: More text
    """
    
    def __init__(self, logger=None):
        """
        Initialize subtitle generator.
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
        
    def format_timestamp(self, seconds: float) -> str:
        """
        Format seconds to SRT timestamp format (HH:MM:SS,mmm).
        
        Args:
            seconds: Time in seconds (float)
            
        Returns:
            Formatted timestamp string
            
        Example:
            >>> format_timestamp(65.5)
            '00:01:05,500'
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millis = int((td.total_seconds() % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def clean_text(self, text: str) -> str:
        """
        Clean and format subtitle text.
        
        Args:
            text: Raw text from transcript
            
        Returns:
            Cleaned text suitable for subtitles
        """
        if not text:
            return ""
        
        # Strip whitespace
        text = text.strip()
        
        # Remove multiple spaces
        import re
        text = re.sub(r'\s+', ' ', text)
        
        # Remove problematic characters for SRT
        text = text.replace('\n', ' ')
        text = text.replace('\r', ' ')
        
        return text
    
    def split_long_text(
        self,
        text: str,
        max_chars_per_line: int = 42,
        max_lines: int = 2
    ) -> List[str]:
        """
        Split long text into multiple lines for readability.
        
        Args:
            text: Input text
            max_chars_per_line: Maximum characters per line
            max_lines: Maximum number of lines
            
        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            word_length = len(word)
            # +1 for space
            if current_length + word_length + len(current_line) > max_chars_per_line:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                    current_length = word_length
                    
                    if len(lines) >= max_lines:
                        break
                else:
                    # Single word too long, add it anyway
                    lines.append(word)
                    if len(lines) >= max_lines:
                        break
            else:
                current_line.append(word)
                current_length += word_length
        
        # Add remaining words
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return lines
    
    def merge_short_segments(
        self,
        segments: List[Dict],
        min_duration: float = 1.0,
        max_duration: float = 7.0,
        max_chars: int = 84  # 2 lines * 42 chars
    ) -> List[Dict]:
        """
        Merge very short segments into longer, more readable subtitles.
        
        Args:
            segments: List of transcript segments
            min_duration: Minimum duration for a subtitle (seconds)
            max_duration: Maximum duration for a subtitle (seconds)
            max_chars: Maximum characters per subtitle
            
        Returns:
            List of merged segments
        """
        if not segments:
            return []
        
        merged = []
        current = None
        
        for segment in segments:
            duration = segment.get('end', 0) - segment.get('start', 0)
            text = segment.get('text', '').strip()
            
            if not text:
                continue
            
            if current is None:
                # Start new subtitle
                current = segment.copy()
            else:
                # Check if we should merge
                combined_duration = segment['end'] - current['start']
                combined_text = current['text'] + ' ' + text
                combined_chars = len(combined_text)
                
                same_speaker = (segment.get('speaker') == current.get('speaker'))
                
                should_merge = (
                    same_speaker and
                    combined_duration <= max_duration and
                    combined_chars <= max_chars
                )
                
                if should_merge:
                    # Merge with current
                    current['end'] = segment['end']
                    current['text'] = combined_text
                else:
                    # Save current and start new
                    merged.append(current)
                    current = segment.copy()
        
        # Add last subtitle
        if current:
            merged.append(current)
        
        return merged
    
    def split_long_segments(
        self,
        segments: List[Dict],
        max_duration: float = 7.0,
        max_chars: int = 84
    ) -> List[Dict]:
        """
        Split very long segments into smaller subtitles.
        
        Args:
            segments: List of transcript segments
            max_duration: Maximum duration for a subtitle (seconds)
            max_chars: Maximum characters per subtitle
            
        Returns:
            List of segments with long ones split
        """
        result = []
        
        for segment in segments:
            duration = segment.get('end', 0) - segment.get('start', 0)
            text = segment.get('text', '').strip()
            
            if not text:
                continue
            
            # If segment is within limits, keep as is
            if duration <= max_duration and len(text) <= max_chars:
                result.append(segment)
                continue
            
            # Split long segment
            words = text.split()
            if not words:
                result.append(segment)
                continue
            
            # Estimate time per word
            time_per_word = duration / len(words)
            
            current_words = []
            current_chars = 0
            current_start = segment['start']
            
            for i, word in enumerate(words):
                word_len = len(word)
                
                # Check if adding this word exceeds limits
                if current_chars + word_len + len(current_words) > max_chars:
                    # Save current subtitle
                    if current_words:
                        current_end = current_start + (len(current_words) * time_per_word)
                        result.append({
                            'start': current_start,
                            'end': min(current_end, segment['end']),
                            'text': ' '.join(current_words),
                            'speaker': segment.get('speaker', 'UNKNOWN')
                        })
                        current_start = current_end
                        current_words = []
                        current_chars = 0
                
                current_words.append(word)
                current_chars += word_len
            
            # Add remaining words
            if current_words:
                result.append({
                    'start': current_start,
                    'end': segment['end'],
                    'text': ' '.join(current_words),
                    'speaker': segment.get('speaker', 'UNKNOWN')
                })
        
        return result
    
    def generate_srt(
        self,
        segments: List[Dict],
        include_speaker: bool = True,
        max_chars_per_line: int = 42,
        max_lines: int = 2
    ) -> str:
        """
        Generate SRT formatted subtitle string from segments.
        
        Args:
            segments: List of transcript segments
            include_speaker: Whether to include speaker labels
            max_chars_per_line: Maximum characters per line
            max_lines: Maximum lines per subtitle
            
        Returns:
            SRT formatted string
        """
        if self.logger:
            self.logger.info(f"Generating SRT from {len(segments)} segments")
        
        srt_lines = []
        subtitle_number = 1
        
        for segment in segments:
            start_time = segment.get('start', 0)
            end_time = segment.get('end', 0)
            text = self.clean_text(segment.get('text', ''))
            speaker = segment.get('speaker', 'UNKNOWN')
            
            if not text:
                continue
            
            # Format timestamps
            start_ts = self.format_timestamp(start_time)
            end_ts = self.format_timestamp(end_time)
            
            # Add speaker label if requested
            if include_speaker and speaker and speaker != 'UNKNOWN':
                text = f"{speaker}: {text}"
            
            # Split into lines if too long
            lines = self.split_long_text(text, max_chars_per_line, max_lines)
            subtitle_text = '\n'.join(lines)
            
            # Format SRT entry
            srt_entry = f"{subtitle_number}\n{start_ts} --> {end_ts}\n{subtitle_text}\n"
            srt_lines.append(srt_entry)
            
            subtitle_number += 1
        
        return '\n'.join(srt_lines)
    
    def process_transcript(
        self,
        transcript: Dict,
        config: Dict = None
    ) -> Tuple[str, Dict]:
        """
        Process transcript and generate SRT subtitles.
        
        Args:
            transcript: Transcript dictionary with segments
            config: Optional configuration dict
            
        Returns:
            Tuple of (srt_content, statistics)
        """
        # Default configuration
        default_config = {
            'include_speaker': True,
            'merge_short': True,
            'split_long': True,
            'min_duration': 1.0,
            'max_duration': 7.0,
            'max_chars': 84,
            'max_chars_per_line': 42,
            'max_lines': 2
        }
        
        if config:
            default_config.update(config)
        
        if self.logger:
            self.logger.info("Processing transcript for subtitle generation")
            self.logger.debug(f"Configuration: {default_config}")
        
        segments = transcript.get('segments', [])
        
        if not segments:
            if self.logger:
                self.logger.warning("No segments found in transcript")
            return "", {
                'total_segments': 0,
                'total_subtitles': 0,
                'total_duration': 0.0
            }
        
        if self.logger:
            self.logger.info(f"Processing {len(segments)} transcript segments")
        
        # Process segments
        processed = segments.copy()
        
        # Merge short segments
        if default_config['merge_short']:
            if self.logger:
                self.logger.debug("Merging short segments...")
            processed = self.merge_short_segments(
                processed,
                min_duration=default_config['min_duration'],
                max_duration=default_config['max_duration'],
                max_chars=default_config['max_chars']
            )
            if self.logger:
                self.logger.info(f"After merging: {len(processed)} segments")
        
        # Split long segments
        if default_config['split_long']:
            if self.logger:
                self.logger.debug("Splitting long segments...")
            processed = self.split_long_segments(
                processed,
                max_duration=default_config['max_duration'],
                max_chars=default_config['max_chars']
            )
            if self.logger:
                self.logger.info(f"After splitting: {len(processed)} segments")
        
        # Generate SRT
        srt_content = self.generate_srt(
            processed,
            include_speaker=default_config['include_speaker'],
            max_chars_per_line=default_config['max_chars_per_line'],
            max_lines=default_config['max_lines']
        )
        
        # Calculate statistics
        total_duration = 0.0
        if processed:
            first_start = processed[0].get('start', 0)
            last_end = processed[-1].get('end', 0)
            total_duration = last_end - first_start
        
        stats = {
            'original_segments': len(segments),
            'processed_segments': len(processed),
            'total_subtitles': len(processed),
            'total_duration': round(total_duration, 2),
            'avg_subtitle_duration': round(
                total_duration / len(processed) if processed else 0.0, 2
            ),
            'speakers': len(set(s.get('speaker', 'UNKNOWN') for s in processed))
        }
        
        if self.logger:
            self.logger.info(f"Generated {stats['total_subtitles']} subtitle entries")
            self.logger.info(f"Total duration: {stats['total_duration']:.2f}s")
            self.logger.info(f"Average subtitle duration: {stats['avg_subtitle_duration']:.2f}s")
            self.logger.info(f"Unique speakers: {stats['speakers']}")
        
        return srt_content, stats
