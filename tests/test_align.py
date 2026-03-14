"""Tests for pinyin-based text alignment."""

from audio_to_subtitles.align import AlignedSegment, align
from audio_to_subtitles.transcribe import Segment


def test_align_exact_match():
    """When Whisper text matches original exactly, timing should transfer."""
    segments = [
        Segment(start=0.0, end=2.0, text="你好世界"),
        Segment(start=2.0, end=4.0, text="这是测试"),
    ]
    original = "你好世界，这是测试。"
    result = align(segments, original)
    assert len(result) > 0
    # First segment should start near 0
    assert result[0].start < 0.5
    # Last segment should end near 4.0
    assert result[-1].end > 2.0


def test_align_with_homophones():
    """Whisper uses wrong characters (homophones) but alignment still works."""
    # Whisper hears "jintian tianqi hen hao" but writes wrong chars
    segments = [
        Segment(start=0.0, end=3.0, text="金田天气很好"),
    ]
    # Original has the correct characters
    original = "今天天气很好"
    result = align(segments, original)
    assert len(result) > 0
    assert result[0].text == "今天天气很好"
    assert result[0].start < 0.5


def test_align_empty_input():
    """Empty inputs should return empty results."""
    assert align([], "some text") == []
    assert align([Segment(0, 1, "test")], "") == []
    assert align([], "") == []


def test_align_respects_max_chars():
    """Long text should be split respecting max_chars_per_line."""
    segments = [
        Segment(start=0.0, end=10.0, text="今天天气真的非常非常好我们一起去公园散步吧"),
    ]
    original = "今天天气真的非常非常好，我们一起去公园散步吧。"
    result = align(segments, original, max_chars_per_line=15)
    assert len(result) >= 2
    for seg in result:
        assert len(seg.text) <= 15


def test_align_multiple_segments():
    """Multiple Whisper segments should align to corresponding original text."""
    segments = [
        Segment(start=0.0, end=2.0, text="大家好"),
        Segment(start=2.5, end=5.0, text="欢迎来到我的频道"),
        Segment(start=5.5, end=8.0, text="今天我们聊一聊"),
    ]
    original = "大家好，欢迎来到我的频道，今天我们聊一聊。"
    result = align(segments, original)
    assert len(result) >= 3
    # Timing should be roughly sequential
    for i in range(1, len(result)):
        assert result[i].start >= result[i - 1].start


def test_align_timing_monotonic():
    """Aligned segments should have monotonically increasing start times."""
    segments = [
        Segment(start=0.0, end=3.0, text="第一句话"),
        Segment(start=3.0, end=6.0, text="第二句话"),
        Segment(start=6.0, end=9.0, text="第三句话"),
    ]
    original = "第一句话，第二句话，第三句话。"
    result = align(segments, original)
    for i in range(1, len(result)):
        assert result[i].start >= result[i - 1].start
