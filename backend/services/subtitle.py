"""
Subtitle processing and parsing service
"""
import re
from typing import List, Dict, Tuple
from pathlib import Path
from dataclasses import dataclass
from datetime import timedelta


@dataclass
class SubtitleSegment:
    """Represents a single subtitle segment"""
    index: int
    start_time: float  # in seconds
    end_time: float    # in seconds
    text: str

    def __repr__(self):
        return f"SubtitleSegment({self.index}, {self.start_time:.2f}-{self.end_time:.2f}, '{self.text[:30]}...')"


class SubtitleProcessor:
    """Process and parse subtitle files"""

    def __init__(self):
        self.segments: List[SubtitleSegment] = []

    def parse_srt(self, file_path: str) -> List[SubtitleSegment]:
        """
        Parse SRT subtitle file
        Args:
            file_path: Path to SRT file
        Returns:
            List of SubtitleSegment objects
        """
        segments = []

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by double newlines to get individual subtitle blocks
        blocks = re.split(r'\n\n+', content.strip())

        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue

            try:
                # Parse index
                index = int(lines[0].strip())

                # Parse timestamps
                time_line = lines[1].strip()
                start_str, end_str = time_line.split(' --> ')
                start_time = self._parse_timestamp(start_str)
                end_time = self._parse_timestamp(end_str)

                # Parse text (may span multiple lines)
                text = '\n'.join(lines[2:]).strip()

                segments.append(SubtitleSegment(
                    index=index,
                    start_time=start_time,
                    end_time=end_time,
                    text=text
                ))
            except (ValueError, IndexError) as e:
                print(f"Warning: Failed to parse subtitle block: {block[:50]}... Error: {e}")
                continue

        self.segments = segments
        return segments

    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Convert SRT timestamp to seconds
        Format: HH:MM:SS,mmm or HH:MM:SS.mmm
        """
        timestamp = timestamp.replace(',', '.')
        parts = timestamp.split(':')

        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])

        return hours * 3600 + minutes * 60 + seconds

    def get_keyframe_timestamps(self, offset: float = 0.0, position: str = 'middle') -> List[float]:
        """
        Extract keyframe timestamps based on subtitle changes
        Args:
            offset: Time offset in seconds (can be negative)
            position: 'start', 'middle', or 'end' of subtitle segment
        Returns:
            List of timestamps in seconds
        """
        if not self.segments:
            return []

        keyframes = []
        for segment in self.segments:
            if position == 'start':
                ts = segment.start_time
            elif position == 'end':
                ts = segment.end_time
            else:  # middle (default)
                ts = (segment.start_time + segment.end_time) / 2.0

            # Apply offset and ensure non-negative
            ts = max(0.0, ts + offset)
            keyframes.append(ts)

        return keyframes

    def get_subtitle_at_time(self, timestamp: float) -> str:
        """
        Get subtitle text at a specific timestamp
        When timestamp equals start_time of a segment, return that segment (not the previous one)
        """
        for segment in self.segments:
            # Use < for end_time to avoid matching both segments when timestamp == start_time/end_time boundary
            if segment.start_time <= timestamp < segment.end_time:
                return segment.text
            # Special case: if this is the last segment and timestamp equals end_time
            if segment == self.segments[-1] and timestamp == segment.end_time:
                return segment.text
        return ""

    def merge_segments(self, max_duration: float = 5.0) -> List[SubtitleSegment]:
        """
        Merge consecutive subtitle segments for better readability
        Args:
            max_duration: Maximum duration for merged segments
        Returns:
            List of merged SubtitleSegment objects
        """
        if not self.segments:
            return []

        merged = []
        current_segment = self.segments[0]
        current_text = [current_segment.text]

        for segment in self.segments[1:]:
            duration = segment.end_time - current_segment.start_time

            # Merge if within max_duration
            if duration <= max_duration:
                current_text.append(segment.text)
            else:
                # Save current merged segment
                merged.append(SubtitleSegment(
                    index=len(merged) + 1,
                    start_time=current_segment.start_time,
                    end_time=self.segments[self.segments.index(segment) - 1].end_time,
                    text=' '.join(current_text)
                ))

                # Start new segment
                current_segment = segment
                current_text = [segment.text]

        # Add last segment
        if current_text:
            merged.append(SubtitleSegment(
                index=len(merged) + 1,
                start_time=current_segment.start_time,
                end_time=self.segments[-1].end_time,
                text=' '.join(current_text)
            ))

        return merged

    def export_to_srt(self, segments: List[SubtitleSegment], output_path: str):
        """
        Export subtitle segments to SRT file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"{segment.index}\n")
                f.write(f"{self._format_timestamp(segment.start_time)} --> {self._format_timestamp(segment.end_time)}\n")
                f.write(f"{segment.text}\n\n")

    def _format_timestamp(self, seconds: float) -> str:
        """
        Convert seconds to SRT timestamp format
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def get_statistics(self) -> Dict:
        """
        Get subtitle statistics
        """
        if not self.segments:
            return {}

        total_duration = self.segments[-1].end_time - self.segments[0].start_time
        total_chars = sum(len(s.text) for s in self.segments)

        return {
            'total_segments': len(self.segments),
            'total_duration': total_duration,
            'total_characters': total_chars,
            'avg_segment_duration': total_duration / len(self.segments),
            'avg_chars_per_segment': total_chars / len(self.segments),
            'first_timestamp': self.segments[0].start_time,
            'last_timestamp': self.segments[-1].end_time
        }
