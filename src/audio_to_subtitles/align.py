"""Align Whisper segments with original text using pinyin-based matching."""

from __future__ import annotations

import difflib
from dataclasses import dataclass

from .transcribe import Segment
from .utils import normalize_text, split_at_punctuation, text_to_pinyin


@dataclass
class AlignedSegment:
    """A subtitle segment with correct text and Whisper timing."""

    start: float
    end: float
    text: str


def _build_char_to_segment_map(
    segments: list[Segment],
) -> tuple[str, list[int]]:
    """Concatenate segment texts and track which segment each char belongs to.

    Returns:
        normalized_text: All segment texts concatenated and normalized.
        char_segment_ids: For each char in normalized_text, the index of its
            source segment.
    """
    normalized_text = ""
    char_segment_ids: list[int] = []

    for i, seg in enumerate(segments):
        seg_normalized = normalize_text(seg.text)
        normalized_text += seg_normalized
        char_segment_ids.extend([i] * len(seg_normalized))

    return normalized_text, char_segment_ids


def _interpolate_time(
    seg: Segment,
    char_index: int,
    total_chars: int,
) -> float:
    """Estimate a timestamp within a segment by linear interpolation.

    Assumes characters are spoken at a roughly uniform rate within a segment.
    """
    if total_chars <= 1:
        return seg.start
    fraction = char_index / total_chars
    return seg.start + fraction * (seg.end - seg.start)


def align(
    segments: list[Segment],
    original_text: str,
    max_chars_per_line: int = 20,
) -> list[AlignedSegment]:
    """Align Whisper segments with original text using pinyin matching.

    Algorithm:
    1. Normalize and concatenate all Whisper segment texts.
    2. Convert both concatenated Whisper text and original text to pinyin.
    3. Use SequenceMatcher to align the two pinyin sequences.
    4. For each character in the original text, find the corresponding
       Whisper segment and interpolate a timestamp.
    5. Split the original text into subtitle chunks at punctuation boundaries,
       assigning each chunk the time range of its constituent characters.

    Args:
        segments: Whisper transcription segments.
        original_text: The correct original text.
        max_chars_per_line: Maximum characters per subtitle line.

    Returns:
        List of aligned subtitle segments with correct text and timing.
    """
    if not segments or not original_text.strip():
        return []

    # Step 1: Build concatenated whisper text with segment tracking
    whisper_normalized, char_segment_ids = _build_char_to_segment_map(segments)
    original_normalized = normalize_text(original_text)

    if not whisper_normalized or not original_normalized:
        return []

    # Track how many normalized chars each segment contributed
    seg_char_counts: dict[int, int] = {}
    for sid in char_segment_ids:
        seg_char_counts[sid] = seg_char_counts.get(sid, 0) + 1

    # Step 2: Convert to pinyin
    whisper_pinyin = text_to_pinyin(whisper_normalized)
    original_pinyin = text_to_pinyin(original_normalized)

    # Step 3: Align pinyin sequences
    matcher = difflib.SequenceMatcher(
        None, whisper_pinyin, original_pinyin, autojunk=False
    )
    matching_blocks = matcher.get_matching_blocks()

    # Step 4: Map each original char to a timestamp
    # For each char in original_normalized, find which whisper char it matched
    # and compute a timestamp.
    total_duration = segments[-1].end - segments[0].start
    orig_char_times: list[float] = [0.0] * len(original_normalized)
    matched_orig: set[int] = set()

    for block in matching_blocks:
        whisper_pos, orig_pos, size = block.a, block.b, block.size
        for k in range(size):
            w_idx = whisper_pos + k
            o_idx = orig_pos + k
            seg_id = char_segment_ids[w_idx]
            seg = segments[seg_id]

            # Find which char within this segment this is
            chars_before = sum(
                1 for j in range(w_idx)
                if char_segment_ids[j] == seg_id
            )
            total_in_seg = seg_char_counts[seg_id]

            orig_char_times[o_idx] = _interpolate_time(
                seg, chars_before, total_in_seg
            )
            matched_orig.add(o_idx)

    # Fill in unmatched characters by interpolating from neighbors
    _fill_unmatched(orig_char_times, matched_orig, segments)

    # Step 5: Split into subtitle chunks
    return _build_subtitle_segments(
        original_text, original_normalized, orig_char_times, max_chars_per_line
    )


def _fill_unmatched(
    char_times: list[float],
    matched: set[int],
    segments: list[Segment],
) -> None:
    """Fill timestamps for unmatched characters by interpolating neighbors."""
    n = len(char_times)
    if not matched:
        # No matches at all — spread evenly across audio duration
        if segments:
            total = segments[-1].end - segments[0].start
            for i in range(n):
                char_times[i] = segments[0].start + (i / max(n - 1, 1)) * total
        return

    for i in range(n):
        if i in matched:
            continue

        # Find nearest matched neighbors
        left_time = None
        right_time = None
        for j in range(i - 1, -1, -1):
            if j in matched:
                left_time = char_times[j]
                break
        for j in range(i + 1, n):
            if j in matched:
                right_time = char_times[j]
                break

        if left_time is not None and right_time is not None:
            char_times[i] = (left_time + right_time) / 2
        elif left_time is not None:
            char_times[i] = left_time
        elif right_time is not None:
            char_times[i] = right_time


def _build_subtitle_segments(
    original_text: str,
    original_normalized: str,
    orig_char_times: list[float],
    max_chars_per_line: int,
) -> list[AlignedSegment]:
    """Build subtitle segments by splitting at punctuation boundaries."""
    # Split original text at punctuation
    chunks = split_at_punctuation(original_text)

    # Map each chunk back to normalized char positions to get timing
    result: list[AlignedSegment] = []
    norm_offset = 0

    for chunk in chunks:
        chunk_normalized = normalize_text(chunk)
        chunk_len = len(chunk_normalized)

        if chunk_len == 0:
            continue

        start_time = orig_char_times[norm_offset]
        end_idx = min(norm_offset + chunk_len - 1, len(orig_char_times) - 1)
        end_time = orig_char_times[end_idx]

        # Ensure end > start
        if end_time <= start_time:
            end_time = start_time + 0.5

        display_text = chunk.strip()
        if not display_text:
            norm_offset += chunk_len
            continue

        # Further split if chunk exceeds max_chars_per_line
        if len(display_text) > max_chars_per_line:
            sub_segments = _split_long_chunk(
                display_text,
                start_time,
                end_time,
                max_chars_per_line,
            )
            result.extend(sub_segments)
        else:
            result.append(AlignedSegment(
                start=start_time,
                end=end_time,
                text=display_text,
            ))

        norm_offset += chunk_len

    return result


def _split_long_chunk(
    text: str,
    start: float,
    end: float,
    max_chars: int,
) -> list[AlignedSegment]:
    """Split a long text chunk into smaller segments with interpolated times."""
    segments: list[AlignedSegment] = []
    total_len = len(text)
    duration = end - start
    pos = 0

    while pos < total_len:
        chunk_end = min(pos + max_chars, total_len)
        chunk_text = text[pos:chunk_end]

        t_start = start + (pos / total_len) * duration
        t_end = start + (chunk_end / total_len) * duration

        segments.append(AlignedSegment(
            start=t_start,
            end=t_end,
            text=chunk_text,
        ))
        pos = chunk_end

    return segments
