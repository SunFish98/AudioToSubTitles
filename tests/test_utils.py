"""Tests for text normalization and pinyin utilities."""

from audio_to_subtitles.utils import (
    is_cjk,
    normalize_text,
    split_at_punctuation,
    text_to_pinyin,
)


def test_is_cjk():
    assert is_cjk("你")
    assert is_cjk("好")
    assert not is_cjk("a")
    assert not is_cjk("1")
    assert not is_cjk("，")


def test_normalize_text_removes_chinese_punctuation():
    text = "你好，世界！这是一个测试。"
    result = normalize_text(text)
    assert result == "你好世界这是一个测试"


def test_normalize_text_removes_whitespace():
    text = "你好 世界\n测试"
    result = normalize_text(text)
    assert result == "你好世界测试"


def test_normalize_text_fullwidth():
    # Fullwidth letters should be converted to normal form
    text = "Ｈｅｌｌｏ"
    result = normalize_text(text)
    assert result == "Hello"


def test_text_to_pinyin_chinese():
    result = text_to_pinyin("你好")
    assert result == ["ni", "hao"]


def test_text_to_pinyin_mixed():
    result = text_to_pinyin("你好world")
    assert result[0] == "ni"
    assert result[1] == "hao"
    assert result[2:] == ["w", "o", "r", "l", "d"]


def test_text_to_pinyin_homophones():
    # 今天 and 金田 are homophones (jīntiān)
    py1 = text_to_pinyin("今天")
    py2 = text_to_pinyin("金田")
    # Tone-stripped, they should produce the same pinyin
    assert py1 == py2


def test_split_at_punctuation():
    text = "你好，世界。测试"
    result = split_at_punctuation(text)
    assert result == ["你好，", "世界。", "测试"]


def test_split_at_punctuation_no_punct():
    text = "你好世界"
    result = split_at_punctuation(text)
    assert result == ["你好世界"]
