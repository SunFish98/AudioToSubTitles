"""SRT subtitle file generation."""

from __future__ import annotations

from .align import AlignedSegment


def _format_timestamp(seconds: float) -> str:
    """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0.0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds % 1) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def to_srt(segments: list[AlignedSegment]) -> str:
    """Convert aligned segments to SRT format string.

    Args:
        segments: List of aligned subtitle segments.

    Returns:
        SRT formatted string.
    """
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        start = _format_timestamp(seg.start)
        end = _format_timestamp(seg.end)
        lines.append(f"{i}")
        lines.append(f"{start} --> {end}")
        lines.append(seg.text)
        lines.append("")  # blank line separator

    return "\n".join(lines)


def write_srt(segments: list[AlignedSegment], output_path: str) -> None:
    """Write aligned segments to an SRT file.

    Args:
        segments: List of aligned subtitle segments.
        output_path: Path to write the SRT file.
    """
    srt_content = to_srt(segments)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)
