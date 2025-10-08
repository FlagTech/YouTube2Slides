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
        self.sentence_endings = {'.', '!', '?', '。', '！', '？', '。'}
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

        # Language-specific sentence markers (for languages without punctuation in auto-generated subtitles)
        self.language_markers = {
            'ja': {  # Japanese
                'endings': ['です', 'ます', 'でした', 'ました', 'だった', 'である', 'でしょう', 'ません', 'ない'],
                'particles': ['か', 'ね', 'よ', 'な', 'わ', 'ぞ', 'ぜ', 'さ', 'の']
            },
            'ko': {  # Korean
                'endings': ['니다', '습니다', '었습니다', '였습니다', '는데요', '어요', '아요'],
                'particles': ['요', '네요', '까요', '세요', '죠', '군요']
            },
            'zh': {  # Chinese (including zh-TW, zh-CN)
                'endings': ['了', '過', '著'],
                'particles': ['吧', '呢', '啊', '嗎', '嘛', '的', '喔', '哦', '耶']
            },
            'th': {  # Thai
                'endings': ['แล้ว', 'อยู่', 'ไป', 'มา'],
                'particles': ['ครับ', 'ค่ะ', 'นะ', 'จ้ะ', 'จ๊ะ', 'ล่ะ']
            }
        }

        # General merge configuration (for languages without punctuation)
        self.merge_config = {
            'min_chars': 40,         # Minimum characters per segment
            'target_chars': 80,      # Target characters per segment
            'max_chars': 150,        # Maximum characters per segment
            'max_time_gap': 1.5,     # Maximum time gap between segments (seconds)
            'min_segments': 2,       # Minimum segments to merge
        }

        # Normalize punctuation handling for CJK (e.g., Japanese/Chinese)
        # This overrides any mis-encoded defaults and ensures proper sentence detection.
        self._setup_unicode_punct()

    def _setup_unicode_punct(self):
        """Ensure punctuation sets and regex support CJK sentence breaks.

        YouTube auto captions in Japanese/Chinese commonly use full-width punctuation.
        This method defines a Unicode-aware sentence pattern so that '。', '！', '？'
        and ellipsis are treated as valid sentence boundaries without requiring
        a following space/capital letter.
        """
        # Sentence-ending punctuation marks (Latin + CJK)
        self.sentence_endings = {'.', '!', '?', '。', '！', '？'}
        # Comma and pause marks (not sentence endings)
        self.pause_marks = {',', ';', ':', '、', '，', '；', '：'}
        # Ellipsis should be treated as sentence ending
        self.ellipsis_marks = {'…', '...', '……'}
        # Regex to find any sentence-ending punctuation (no dependency on spaces/case)
        self.sentence_pattern = re.compile(r"[\.\!\?。！？]|(?:\.\.\.)|…")

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

    def detect_language_ending(self, text: str, language: str = None) -> bool:
        """
        Check if text ends with language-specific sentence markers

        Args:
            text: Text to check
            language: Language code (ja, ko, zh, th, etc.)

        Returns:
            True if text ends with a sentence marker
        """
        if not text or not language:
            return False

        # Extract base language code (e.g., 'zh-TW' -> 'zh')
        lang_base = language.split('-')[0].lower()

        if lang_base not in self.language_markers:
            return False

        markers = self.language_markers[lang_base]
        text_stripped = text.strip()

        # Check if text ends with any ending marker
        for ending in markers.get('endings', []):
            if text_stripped.endswith(ending):
                return True

        # Check if text ends with any particle
        for particle in markers.get('particles', []):
            if text_stripped.endswith(particle):
                return True

        return False

    def should_merge_with_next(self, text: str, language: str = None) -> bool:
        """
        Determine if this subtitle segment should be merged with the next one
        Strategy: Merge until we have a complete sentence

        Args:
            text: Subtitle text
            language: Language code (optional)

        Returns:
            True if should merge with next segment
        """
        # First check for punctuation-based sentence
        if self.contains_complete_sentence(text):
            return False

        # If no punctuation, check language-specific markers
        if language and self.detect_language_ending(text, language):
            return False

        # Default: merge
        return True

    def _has_ending_punctuation(self, text: str) -> bool:
        """Check if text ends with any punctuation"""
        text = text.strip()
        if not text:
            return False

        last_char = text[-1]
        return last_char in (self.sentence_endings | self.pause_marks)

    def _parse_timestamp(self, timestamp: str) -> float:
        """
        Convert SRT timestamp to seconds

        Args:
            timestamp: Timestamp string (e.g., '00:01:23,456')

        Returns:
            Time in seconds
        """
        try:
            # Format: HH:MM:SS,mmm
            time_part, ms_part = timestamp.split(',')
            h, m, s = map(int, time_part.split(':'))
            ms = int(ms_part)
            return h * 3600 + m * 60 + s + ms / 1000.0
        except:
            return 0.0

    def _calculate_time_gap(self, seg1: dict, seg2: dict) -> float:
        """
        Calculate time gap between two segments

        Args:
            seg1: First segment
            seg2: Second segment

        Returns:
            Time gap in seconds
        """
        end_time1 = self._parse_timestamp(seg1['end_time'])
        start_time2 = self._parse_timestamp(seg2['start_time'])
        return start_time2 - end_time1

    def optimize_srt_file(self, input_path: str, output_path: str = None, language: str = None) -> str:
        """
        Optimize SRT file by merging segments into complete sentences

        Args:
            input_path: Path to input SRT file
            output_path: Path to output SRT file (if None, creates .optimized version)
            language: Language code (e.g., 'ja', 'ko', 'zh', 'en')

        Returns:
            Path to optimized SRT file
        """
        if output_path is None:
            # Create optimized version with .optimized suffix
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"{input_file.stem}.optimized{input_file.suffix}")

        # Parse SRT file
        segments = self._parse_srt(input_path)

        # Detect if subtitles have punctuation
        has_punctuation = self._detect_punctuation(segments)

        # Choose merging strategy
        if has_punctuation:
            # Use punctuation-based merging
            merged_segments = self._merge_segments(segments, language)
        else:
            # Use smart merging for auto-generated subtitles
            merged_segments = self._smart_merge(segments, language)

        # Write optimized SRT
        self._write_srt(merged_segments, output_path)

        return output_path

    def _detect_punctuation(self, segments: List[dict]) -> bool:
        """
        Detect if segments contain punctuation marks

        Args:
            segments: List of subtitle segments

        Returns:
            True if punctuation found in at least 30% of segments
        """
        if not segments:
            return False

        punct_count = 0
        for seg in segments[:min(20, len(segments))]:  # Check first 20 segments
            text = seg['text']
            if any(p in text for p in self.sentence_endings | self.pause_marks):
                punct_count += 1

        return punct_count / min(20, len(segments)) > 0.3

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

    def _smart_merge(self, segments: List[dict], language: str = None) -> List[dict]:
        """
        Smart merging for subtitles without punctuation
        Uses time gaps, text length, and language-specific markers

        Args:
            segments: List of subtitle segments
            language: Language code

        Returns:
            List of merged segments
        """
        if not segments:
            return []

        merged = []
        i = 0

        while i < len(segments):
            current = {
                'start_time': segments[i]['start_time'],
                'end_time': segments[i]['end_time'],
                'text': segments[i]['text']
            }

            # Keep merging while conditions are met
            while i < len(segments) - 1:
                next_seg = segments[i + 1]
                current_len = len(current['text'])

                # Calculate time gap
                time_gap = self._calculate_time_gap(
                    {'end_time': current['end_time']},
                    {'start_time': next_seg['start_time']}
                )

                # Decision criteria
                should_merge = False

                # 1. If current text is too short, keep merging
                if current_len < self.merge_config['min_chars']:
                    should_merge = True

                # 2. If time gap is small and not too long yet
                elif (time_gap < self.merge_config['max_time_gap'] and
                      current_len < self.merge_config['target_chars']):
                    should_merge = True

                # 3. Check language-specific ending
                elif language:
                    if not self.detect_language_ending(current['text'], language):
                        # No language ending detected, continue merging
                        if current_len < self.merge_config['max_chars']:
                            should_merge = True

                # Stop merging if reached max length
                if current_len >= self.merge_config['max_chars']:
                    should_merge = False

                if not should_merge:
                    break

                # Merge next segment
                i += 1
                if current['text'] and not current['text'].endswith(' '):
                    current['text'] += ' '
                current['text'] += next_seg['text']
                current['end_time'] = next_seg['end_time']

            merged.append(current)
            i += 1

        return merged

    def _merge_segments(self, segments: List[dict], language: str = None) -> List[dict]:
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
