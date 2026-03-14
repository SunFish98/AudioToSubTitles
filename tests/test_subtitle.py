"""Tests for SRT generation."""

from audio_to_subtitles.align import AlignedSegment
from audio_to_subtitles.subtitle import _format_timestamp, to_srt


def test_format_timestamp_zero():
    assert _format_timestamp(0.0) == "00:00:00,000"


def test_format_timestamp_simple():
    assert _format_timestamp(1.5) == "00:00:01,500"


def test_format_timestamp_minutes():
    assert _format_timestamp(65.25) == "00:01:05,250"


def test_format_timestamp_hours():
    assert _format_timestamp(3661.1) == "01:01:01,100"


def test_format_timestamp_negative():
    # Negative should clamp to 0
    assert _format_timestamp(-5.0) == "00:00:00,000"


def test_to_srt_basic():
    segments = [
        AlignedSegment(start=0.0, end=2.0, text="你好世界"),
        AlignedSegment(start=2.5, end=4.0, text="这是测试"),
    ]
    srt = to_srt(segments)
    lines = srt.strip().split("\n")

    # First subtitle block
    assert lines[0] == "1"
    assert "00:00:00,000 --> 00:00:02,000" in lines[1]
    assert lines[2] == "你好世界"

    # Second subtitle block
    assert lines[4] == "2"
    assert "00:00:02,500 --> 00:00:04,000" in lines[5]
    assert lines[6] == "这是测试"


def test_to_srt_empty():
    assert to_srt([]) == ""
