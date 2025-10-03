"""
Subtitle optimization service
Merges YouTube auto-generated subtitle segments into complete sentences
One sentence per subtitle segment
"""
import re
from typing import List
from pathlib import Path


class SubtitleOptimizer:
    """Optimize subtitle segmentation for better readability (one sentence per segment)"""

    def __init__(self):
        # Sentence-ending punctuation marks
        self.sentence_endings = {'.', '!', '?', '。', '！', '？'}
        # Comma and pause marks (not sentence endings)
        self.pause_marks = {',', ';', ':', '，', '；', '：'}
        # Ellipsis should not merge (treat as sentence ending)
        self.ellipsis_marks = {'…', '...'}

        # Regex pattern to split by sentence boundaries
        # Matches: . ! ? 。 ！ ？ ... …
        # Followed by space and capital letter OR end of string
        self.sentence_pattern = re.compile(
            r'([.!?。！？]|\.\.\.|\…)(\s+(?=[A-Z])|$)'
        )

    def contains_complete_sentence(self, text: str) -> bool:
        """
        Check if text contains at least one complete sentence
        A complete sentence ends with . ! ? 。 ！ ？ ... or …
        followed by a space + capital letter (indicating next sentence) or end of string

        Args:
            text: Text to check

        Returns:
            True if contains complete sentence
        """
        text = text.strip()
        if not text:
            return False

        # Use regex to find sentence boundaries
        match = self.sentence_pattern.search(text)
        return match is not None

    def should_merge_with_next(self, text: str) -> bool:
        """
        Determine if this subtitle segment should be merged with the next one
        Strategy: Merge until we have a complete sentence

        Args:
            text: Subtitle text

        Returns:
            True if should merge with next segment
        """
        # If text contains a complete sentence, stop merging
        return not self.contains_complete_sentence(text)

    def _has_ending_punctuation(self, text: str) -> bool:
        """Check if text ends with any punctuation"""
        text = text.strip()
        if not text:
            return False

        last_char = text[-1]
        return last_char in (self.sentence_endings | self.pause_marks)

    def optimize_srt_file(self, input_path: str, output_path: str = None) -> str:
        """
        Optimize SRT file by merging segments into complete sentences

        Args:
            input_path: Path to input SRT file
            output_path: Path to output SRT file (if None, overwrites input)

        Returns:
            Path to optimized SRT file
        """
        if output_path is None:
            # Create optimized version with .optimized suffix
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"{input_file.stem}.optimized{input_file.suffix}")

        # Parse SRT file
        segments = self._parse_srt(input_path)

        # Merge segments
        merged_segments = self._merge_segments(segments)

        # Write optimized SRT
        self._write_srt(merged_segments, output_path)

        return output_path

    def _parse_srt(self, srt_path: str) -> List[dict]:
        """Parse SRT file into segments"""
        segments = []

        with open(srt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            # Check if line is a number (segment index)
            if line.isdigit():
                index = int(line)

                # Next line should be timestamp
                if i + 1 < len(lines):
                    timestamp_line = lines[i + 1].strip()

                    # Parse timestamp
                    if '-->' in timestamp_line:
                        parts = timestamp_line.split('-->')
                        start_time = parts[0].strip()
                        end_time = parts[1].strip()

                        # Collect subtitle text (may span multiple lines)
                        text_lines = []
                        j = i + 2
                        while j < len(lines) and lines[j].strip() and not lines[j].strip().isdigit():
                            text_lines.append(lines[j].strip())
                            j += 1

                        text = ' '.join(text_lines)

                        segments.append({
                            'index': index,
                            'start_time': start_time,
                            'end_time': end_time,
                            'text': text
                        })

                        i = j
                        continue

            i += 1

        return segments

    def split_at_first_sentence(self, text: str) -> tuple:
        """
        Split text at the first sentence boundary

        Args:
            text: Text to split

        Returns:
            (first_sentence, remaining_text) tuple
        """
        match = self.sentence_pattern.search(text)
        if not match:
            return (text, '')

        # Split at the end of the sentence punctuation
        split_pos = match.end()
        first_sentence = text[:split_pos].strip()
        remaining = text[split_pos:].strip()

        return (first_sentence, remaining)

    def _merge_segments(self, segments: List[dict]) -> List[dict]:
        """
        Merge subtitle segments into complete sentences (one sentence per segment)

        Args:
            segments: List of subtitle segments

        Returns:
            List of merged segments (one sentence each)
        """
        if not segments:
            return []

        merged = []
        i = 0
        overflow_text = ""  # Text that belongs to next sentence

        while i < len(segments):
            # Start with overflow from previous iteration (if any)
            current_segment = {
                'start_time': segments[i]['start_time'],
                'end_time': segments[i]['end_time'],
                'text': overflow_text if overflow_text else segments[i]['text']
            }
            overflow_text = ""

            # If we started with overflow, don't consume this segment yet
            if current_segment['text'] != segments[i]['text']:
                # We used overflow, so add current segment
                if current_segment['text'] and not current_segment['text'].endswith(' '):
                    current_segment['text'] += ' '
                current_segment['text'] += segments[i]['text']
                current_segment['end_time'] = segments[i]['end_time']

            # Keep merging until we have at least one complete sentence
            while i < len(segments) - 1 and not self.contains_complete_sentence(current_segment['text']):
                i += 1
                next_segment = segments[i]

                # Add space if needed
                if current_segment['text'] and not current_segment['text'].endswith(' '):
                    current_segment['text'] += ' '

                # Merge the next segment
                current_segment['text'] += next_segment['text']
                current_segment['end_time'] = next_segment['end_time']

            # Now we have at least one complete sentence
            # Split off just the first sentence
            first_sentence, remaining = self.split_at_first_sentence(current_segment['text'])

            if first_sentence:
                sentence_segment = {
                    'start_time': current_segment['start_time'],
                    'end_time': current_segment['end_time'],
                    'text': first_sentence
                }
                merged.append(sentence_segment)

            # Save remaining text for next iteration
            overflow_text = remaining
            i += 1

        # Handle any remaining overflow text
        if overflow_text:
            # Find start time for this overflow (would be from last segment)
            if merged:
                last_segment = merged[-1]
                overflow_segment = {
                    'start_time': last_segment['end_time'],
                    'end_time': last_segment['end_time'],
                    'text': overflow_text
                }
                merged.append(overflow_segment)

        return merged

    def _write_srt(self, segments: List[dict], output_path: str):
        """Write segments to SRT file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                f.write(f"{i}\n")
                f.write(f"{segment['start_time']} --> {segment['end_time']}\n")
                f.write(f"{segment['text']}\n\n")

    def get_optimization_stats(self, input_path: str) -> dict:
        """Get statistics about subtitle optimization"""
        segments = self._parse_srt(input_path)
        merged = self._merge_segments(segments)

        return {
            'original_segments': len(segments),
            'optimized_segments': len(merged),
            'reduction_percentage': round((1 - len(merged) / len(segments)) * 100, 2) if segments else 0
        }
