# AudioToSubTitles - Implementation Plan

## Overview
A Python CLI tool that produces accurate Chinese subtitles by combining:
- **Whisper** (provides timestamps + rough Chinese transcription from audio)
- **Your original text** (provides correct Chinese characters)

## Core Algorithm

### The Problem
Whisper's Chinese transcription is often inaccurate (wrong characters, homophones, missing words), but its **timestamps are reliable**. Your written text is accurate but has **no timing info**. We align the two to get both.

### Alignment Strategy
1. **Run Whisper** on audio → list of segments, each with `(start_time, end_time, inaccurate_text)`
2. **Normalize** both Whisper text and original text (remove punctuation, whitespace)
3. **Align** Whisper segments to the original text using character-level sequence matching (`difflib.SequenceMatcher` or dynamic programming)
4. **Map** each Whisper segment's time range onto the corresponding span of correct text
5. **Output** SRT with correct text + Whisper's timing

### Why this works
Chinese is character-based. Even when Whisper picks wrong characters, many characters will still match (similar sounds → sometimes same character). The alignment algorithm finds the best mapping between Whisper's character sequence and your correct text, then transfers the timestamps.

## Project Structure

```
AudioToSubTitles/
├── pyproject.toml           # Project config, dependencies, CLI entry point
├── src/
│   └── audio_to_subtitles/
│       ├── __init__.py
│       ├── cli.py           # CLI interface (argparse)
│       ├── transcribe.py    # Whisper transcription wrapper
│       ├── align.py         # Text alignment algorithm
│       ├── subtitle.py      # SRT generation
│       └── utils.py         # Text normalization helpers
└── tests/
    ├── test_align.py        # Alignment algorithm tests
    └── test_subtitle.py     # SRT formatting tests
```

## Module Details

### 1. `cli.py` - Command Line Interface
```
audio2sub <audio_file> <text_file> -o output.srt [--model small] [--language zh]
```
- Arguments: audio file path, text file path
- Options: output path, Whisper model size, language, max characters per subtitle line

### 2. `transcribe.py` - Whisper Wrapper
- Load Whisper model (default: `small`, good balance for Chinese)
- Transcribe audio → return list of `Segment(start, end, text)`
- Handle model caching

### 3. `align.py` - Text Alignment (core logic)
- Strip punctuation from both texts for alignment
- Use `difflib.SequenceMatcher` to find matching blocks between Whisper's concatenated text and the original text
- For each Whisper segment, determine which portion of the original text it corresponds to
- Handle edge cases: Whisper segments that don't match anything, original text with no matching audio

**Algorithm detail:**
1. Concatenate all Whisper segment texts → `whisper_full`
2. Track character-to-segment mapping: each char in `whisper_full` knows which segment (and thus timestamp) it came from
3. Run SequenceMatcher(`whisper_full`, `original_text`) → matching blocks
4. For each region of `original_text`, find the Whisper segment(s) whose characters matched, and inherit their timestamps
5. Split original text into subtitle chunks at natural breakpoints (punctuation) within each time range

### 4. `subtitle.py` - SRT Output
- Format aligned segments as SRT (sequence number, timestamp, text)
- Handle subtitle line length limits
- SRT timestamp format: `HH:MM:SS,mmm`

### 5. `utils.py` - Helpers
- Chinese punctuation removal / normalization
- Text cleaning (full-width → half-width, etc.)

## Dependencies
- `openai-whisper` - Audio transcription
- `ffmpeg` - Audio processing (required by Whisper)
- No additional Chinese NLP libraries needed - character-level alignment with difflib is sufficient

## Edge Cases to Handle
- Original text is longer/shorter than audio (e.g., intro/outro text not spoken)
- Whisper hallucinates repeated text
- Long pauses in audio
- Mixed Chinese + English content
