# AudioToSubTitles

Generate accurate Chinese subtitles by combining Whisper's timestamps with your original text.

## The Problem

Whisper produces good timestamps but often gets Chinese characters wrong (homophones, wrong tones). If you already have the correct text, this tool aligns it with Whisper's timing to produce accurate subtitles.

## How It Works

1. Whisper transcribes audio → segments with timestamps + rough Chinese text
2. Both texts are converted to pinyin (pronunciation) using `pypinyin`
3. Pinyin sequences are aligned with `difflib.SequenceMatcher` — homophones match perfectly
4. Whisper's timestamps are mapped onto your correct original text
5. Text is split at punctuation boundaries and output as SRT

## Installation

Requires Python 3.9+ and [ffmpeg](https://ffmpeg.org/).

```bash
pip install -e .
```

## Usage

```bash
audio2sub audio.mp3 article.txt -o subtitles.srt
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-o, --output` | `output.srt` | Output SRT file path |
| `--model` | `small` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large`) |
| `--language` | `zh` | Language code for Whisper |
| `--max-chars` | `20` | Max characters per subtitle line |

### Example

```bash
# Use a larger model for better initial transcription
audio2sub recording.wav script.txt -o final.srt --model medium

# Shorter subtitle lines for mobile-friendly video
audio2sub podcast.mp3 notes.txt -o subs.srt --max-chars 12
```

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```
