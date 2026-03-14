"""Whisper transcription wrapper."""

from dataclasses import dataclass

import whisper


@dataclass
class Segment:
    """A transcription segment with timing and text."""

    start: float  # seconds
    end: float    # seconds
    text: str


def transcribe(
    audio_path: str,
    model_name: str = "small",
    language: str = "zh",
) -> list[Segment]:
    """Transcribe an audio file using Whisper.

    Args:
        audio_path: Path to the audio file.
        model_name: Whisper model size (tiny, base, small, medium, large).
        language: Language code for transcription.

    Returns:
        List of transcription segments with timestamps.
    """
    model = whisper.load_model(model_name)
    result = model.transcribe(
        audio_path,
        language=language,
        verbose=False,
    )

    segments: list[Segment] = []
    for seg in result["segments"]:
        text = seg["text"].strip()
        if text:
            segments.append(Segment(
                start=seg["start"],
                end=seg["end"],
                text=text,
            ))

    return segments
