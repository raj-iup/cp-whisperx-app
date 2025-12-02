#!/usr/bin/env python3
"""
Subtitle Segment Merger - Phase 3: Readability Improvements

Merges short subtitle segments for optimal readability with:
- Intelligent merging logic
- Natural line breaking
- Reading speed optimization (17-20 CPS)
"""


class SubtitleSegmentMerger:
    """
    Merge short subtitle segments for optimal readability (Phase 3).

    Reading speed guidelines:
    - Comfortable: 17-20 characters/second
    - Fast: 21-25 characters/second
    - Too fast: >25 characters/second

    Line breaking guidelines:
    - Max 42 characters per line
    - Max 2 lines per subtitle (84 chars total)
    - Break at natural phrase boundaries
    """

    def __init__(self, config=None, logger=None):
        """Initialize segment merger with configuration."""
        self.logger = logger

        # Load parameters from config or use defaults
        if config:
            self.max_gap = getattr(config, 'segment_merge_max_gap', 1.5)
            self.max_chars = getattr(config, 'segment_merge_max_chars', 84)
            self.min_duration = getattr(config, 'subtitle_min_duration', 1.0)
            self.max_duration = getattr(config, 'segment_merge_max_duration', 7.0)
            self.min_chars_per_second = getattr(config, 'segment_merge_min_cps', 17.0)
            self.max_chars_per_second = getattr(config, 'segment_merge_max_cps', 20.0)
            self.max_chars_per_line = getattr(config, 'subtitle_max_line_length', 42)
            self.max_lines = getattr(config, 'subtitle_max_lines', 2)
        else:
            self.max_gap = 1.5
            self.max_chars = 84
            self.min_duration = 1.0
            self.max_duration = 7.0
            self.min_chars_per_second = 17.0
            self.max_chars_per_second = 20.0
            self.max_chars_per_line = 42
            self.max_lines = 2

        self.fast_chars_per_second = self.max_chars_per_second * 1.25
        self.stats = {
            'original_count': 0,
            'merged_count': 0,
            'too_fast_count': 0,
            'split_count': 0,
            'adjusted_count': 0
        }

    def should_merge(self, seg1, seg2):
        """Determine if two consecutive segments should be merged."""
        if seg1.get('is_lyrics') or seg2.get('is_lyrics'):
            return False
        if seg1.get('speaker') != seg2.get('speaker'):
            return False
        gap = seg2['start'] - seg1['end']
        if gap > self.max_gap:
            return False
        text1 = seg1.get('text', '').strip()
        text2 = seg2.get('text', '').strip()
        combined_length = len(text1) + len(text2) + 1
        if combined_length > self.max_chars:
            return False
        combined_duration = seg2['end'] - seg1['start']
        if combined_duration > self.max_duration:
            return False
        chars_per_second = combined_length / combined_duration if combined_duration > 0 else 0
        if chars_per_second > self.fast_chars_per_second:
            return False
        return True

    def break_lines(self, text, max_chars=None):
        """Break text into multiple lines at natural boundaries."""
        if max_chars is None:
            max_chars = self.max_chars_per_line
        if len(text) <= max_chars:
            return text
        if len(text) <= max_chars * 2:
            mid = len(text) // 2
            for offset in range(0, max_chars):
                if mid - offset > 0 and text[mid - offset] in ' ,-.:;!?':
                    line1 = text[:mid - offset].strip()
                    line2 = text[mid - offset:].strip()
                    if len(line1) <= max_chars and len(line2) <= max_chars:
                        return f"{line1}\n{line2}"
                if mid + offset < len(text) and text[mid + offset] in ' ,-.:;!?':
                    line1 = text[:mid + offset].strip()
                    line2 = text[mid + offset:].strip()
                    if len(line1) <= max_chars and len(line2) <= max_chars:
                        return f"{line1}\n{line2}"
        line1 = text[:max_chars].strip()
        line2 = text[max_chars:max_chars * 2].strip()
        return f"{line1}\n{line2}" if line2 else line1

    def adjust_timing(self, segment):
        """Adjust segment timing for optimal reading speed."""
        text = segment.get('text', '').strip()
        if not text:
            return segment
        duration = segment['end'] - segment['start']
        text_length = len(text)
        chars_per_second = text_length / duration if duration > 0 else 0
        if chars_per_second > self.max_chars_per_second:
            ideal_duration = text_length / self.max_chars_per_second
            new_duration = min(ideal_duration, self.max_duration)
            segment['end'] = segment['start'] + new_duration
            self.stats['adjusted_count'] += 1
        elif duration < self.min_duration:
            segment['end'] = segment['start'] + self.min_duration
            self.stats['adjusted_count'] += 1
        return segment

    def merge_segments(self, segments):
        """Main merging pipeline: merge short segments for optimal readability."""
        if not segments:
            return segments
        self.stats['original_count'] = len(segments)
        merged = []
        current_merged = None
        for segment in segments:
            if not segment.get('text', '').strip():
                continue
            if current_merged is None:
                current_merged = segment.copy()
                continue
            if self.should_merge(current_merged, segment):
                current_text = current_merged.get('text', '').strip()
                new_text = segment.get('text', '').strip()
                current_merged['text'] = f"{current_text} {new_text}"
                current_merged['end'] = segment['end']
                self.stats['merged_count'] += 1
            else:
                text = current_merged.get('text', '').strip()
                if len(text) > self.max_chars_per_line:
                    current_merged['text'] = self.break_lines(text)
                    self.stats['split_count'] += 1
                current_merged = self.adjust_timing(current_merged)
                merged.append(current_merged)
                current_merged = segment.copy()
        if current_merged is not None:
            text = current_merged.get('text', '').strip()
            if len(text) > self.max_chars_per_line:
                current_merged['text'] = self.break_lines(text)
                self.stats['split_count'] += 1
            current_merged = self.adjust_timing(current_merged)
            merged.append(current_merged)
        final_count = len(merged)
        reduction = self.stats['original_count'] - final_count
        reduction_pct = (reduction / self.stats['original_count'] * 100) if self.stats['original_count'] > 0 else 0
        if self.logger:
            self.logger.info(f"📊 Segment merging statistics:")
            self.logger.info(f"   Original segments: {self.stats['original_count']}")
            self.logger.info(f"   Final segments: {final_count}")
            self.logger.info(f"   Reduction: {reduction} segments ({reduction_pct:.1f}%)")
            self.logger.info(f"   Merged pairs: {self.stats['merged_count']}")
            self.logger.info(f"   Split for line breaking: {self.stats['split_count']}")
            self.logger.info(f"   Timing adjusted: {self.stats['adjusted_count']}")
        return merged
