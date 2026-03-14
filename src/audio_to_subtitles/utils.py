"""Text normalization and pinyin conversion utilities."""

import re
import unicodedata

from pypinyin import lazy_pinyin, Style


# Chinese and CJK punctuation to strip for alignment
_PUNCTUATION_RE = re.compile(
    r"[，。！？、；：\u201C\u201D\u2018\u2019【】《》（）—…·\s"
    r"\u3000-\u303F"  # CJK symbols and punctuation
    r"\uFF00-\uFFEF"  # fullwidth forms
    r"\u0000-\u002F"  # ASCII punctuation/control
    r"\u003A-\u0040"  # more ASCII punctuation
    r"\u005B-\u0060"  # brackets etc.
    r"\u007B-\u007F"  # braces etc.
    r"]+"
)

_CJK_RANGES = [
    (0x4E00, 0x9FFF),    # CJK Unified Ideographs
    (0x3400, 0x4DBF),    # CJK Extension A
    (0x20000, 0x2A6DF),  # CJK Extension B
    (0xF900, 0xFAFF),    # CJK Compatibility Ideographs
]


def is_cjk(char: str) -> bool:
    """Check if a character is a CJK ideograph."""
    cp = ord(char)
    return any(start <= cp <= end for start, end in _CJK_RANGES)


def normalize_text(text: str) -> str:
    """Remove punctuation and whitespace, normalize unicode."""
    text = unicodedata.normalize("NFKC", text)
    return _PUNCTUATION_RE.sub("", text)


def text_to_pinyin(text: str) -> list[str]:
    """Convert text to a list of tone-stripped pinyin syllables.

    Each CJK character produces one pinyin entry.
    Non-CJK characters (e.g. English letters, digits) are kept as-is,
    one entry per character, lowercased.

    Returns a list with one entry per character in the input.
    """
    result: list[str] = []
    for char in text:
        if is_cjk(char):
            # lazy_pinyin returns one syllable per character
            py = lazy_pinyin(char, style=Style.NORMAL)
            result.append(py[0])
        else:
            result.append(char.lower())
    return result


def split_at_punctuation(text: str) -> list[str]:
    """Split text into chunks at Chinese punctuation boundaries.

    Keeps punctuation attached to the preceding chunk.
    Useful for breaking subtitles at natural sentence boundaries.
    """
    chunks: list[str] = []
    current: list[str] = []

    for char in text:
        current.append(char)
        # Split after sentence-ending punctuation
        if char in "，。！？；、…":
            chunks.append("".join(current))
            current = []

    if current:
        chunks.append("".join(current))

    return chunks
