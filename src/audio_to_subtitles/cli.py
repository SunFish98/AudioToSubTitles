"""CLI entry point for audio2sub."""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="audio2sub",
        description=(
            "Generate accurate Chinese subtitles by aligning Whisper "
            "transcription with your original text."
        ),
    )
    parser.add_argument(
        "audio",
        help="Path to the audio file",
    )
    parser.add_argument(
        "text",
        help="Path to the original text file (correct Chinese text)",
    )
    parser.add_argument(
        "-o", "--output",
        default="output.srt",
        help="Output SRT file path (default: output.srt)",
    )
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: small)",
    )
    parser.add_argument(
        "--language",
        default="zh",
        help="Language code for Whisper (default: zh)",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=20,
        help="Maximum characters per subtitle line (default: 20)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # Lazy imports so --help is fast and doesn't require whisper installed
    from .align import align
    from .subtitle import write_srt
    from .transcribe import transcribe

    # Read original text
    with open(args.text, "r", encoding="utf-8") as f:
        original_text = f.read()

    # Transcribe audio with Whisper
    print(f"Transcribing {args.audio} with Whisper ({args.model})...")
    segments = transcribe(args.audio, model_name=args.model, language=args.language)
    print(f"Got {len(segments)} segments from Whisper.")

    # Align and generate subtitles
    print("Aligning with original text...")
    aligned = align(segments, original_text, max_chars_per_line=args.max_chars)
    print(f"Generated {len(aligned)} subtitle segments.")

    # Write output
    write_srt(aligned, args.output)
    print(f"Subtitles written to {args.output}")


if __name__ == "__main__":
    main()
