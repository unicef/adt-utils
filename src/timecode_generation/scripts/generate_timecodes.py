#!/usr/bin/env python3
"""Generate ADT timecode JSON files from audio files using Whisper."""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.core import TimecodeGenerationConfig
from src.timecode_generation.classes import AudioTimecodeGenerator
from src.utils import add_standard_args, parse_page_range


load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("timecode_generation.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate timecode JSON files from ADT language audio files"
    )
    parser = add_standard_args(parser)
    parser.add_argument(
        "--language",
        type=str,
        required=True,
        help="Language code to process (for example: es, en)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY env variable)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="whisper-1",
        help="OpenAI transcription model (default: whisper-1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview generated output files without writing them",
    )
    parser.add_argument(
        "--non-strict-data-ids",
        action="store_true",
        help="Allow generation when element count does not exactly match texts.json data-id count",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        return 1

    try:
        start_page, end_page = parse_page_range(args.start_page, args.end_page)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        print(
            "Error: OpenAI API key must be provided via --api-key or OPENAI_API_KEY",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = TimecodeGenerationConfig(
        start_page=start_page,
        end_page=end_page,
        target_dir=target_dir,
        language=args.language,
        api_key=api_key,
        model=args.model,
        dry_run=args.dry_run,
        strict_data_ids=not args.non_strict_data_ids,
    )

    generator = AudioTimecodeGenerator(
        openai_api_key=api_key,
        logger=logger,
        model=args.model,
    )
    result = generator.process_page_range(config)

    print("\n" + "=" * 50)
    print("TIMECODE GENERATION SUMMARY")
    print("=" * 50)
    print(f"Language: {args.language}")
    print(f"Audio files matched: {result.metadata.get('matched_audio_files', 0)}")
    print(f"Data-ids loaded from texts.json: {result.metadata.get('texts_data_ids_loaded', 0)}")
    print(f"Strict data-id mode: {result.metadata.get('strict_data_ids', True)}")
    print(f"Generated files: {result.metadata.get('generated_files', 0)}")
    print(f"Failed files: {result.metadata.get('failed_files', 0)}")
    print(f"Timecode output: {result.metadata.get('timecode_dir', 'N/A')}")

    if result.processed_pages:
        print(
            "Processed pages: "
            f"{min(result.processed_pages)}-{max(result.processed_pages)} "
            f"({len(result.processed_pages)} pages)"
        )

    if args.dry_run:
        print("Dry run mode enabled. No files were written.")

    if result.errors:
        print("\nErrors:")
        for error in result.errors[:15]:
            print(f"- {error}")
        if len(result.errors) > 15:
            print(f"... and {len(result.errors) - 15} more")

    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())