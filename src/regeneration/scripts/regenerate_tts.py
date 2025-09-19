#!/usr/bin/env python3
"""
TTS Audio Regeneration Script

This script asynchronously regenerates TTS audio files for text keys using OpenAI's API.
It supports both English and Spanish languages, with Spanish using El Salvador accent features.
You can specify page ranges to regenerate specific sections of content.

Usage:
    python regenerate_tts.py target_dir --start-page 0 --end-page 5 --language en
    python regenerate_tts.py target_dir --start-page 10 --end-page 15 --language es
    python regenerate_tts.py target_dir --input-json changes.json --language es,en
"""

import asyncio
import os
import argparse
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
import tempfile
import json

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.regeneration.classes.adt_tts_regenerator import ADTTTSRegenerator


load_dotenv(dotenv_path=Path(__file__).parent.parent.parent.parent / ".env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tts_regeneration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="Regenerate TTS audio files using OpenAI API")
    parser.add_argument("target_dir", type=str, help="Target directory containing content/i18n")
    parser.add_argument("--start-page", type=int, help="Starting page number (inclusive)")
    parser.add_argument("--end-page", type=int, help="Ending page number (inclusive)")
    parser.add_argument("--language", type=str, required=True, help="Comma-separated list of languages to regenerate (e.g. 'en', 'es', or 'en,es')")
    parser.add_argument("--input-json", type=str, help="Path to input JSON file containing text content (overrides HTML parsing)")
    parser.add_argument("--api-key", type=str, help="OpenAI API key (or set OPENAI_API_KEY env variable)")
    parser.add_argument("--data-ids", type=str, help="Comma-separated list of data IDs to regenerate (e.g. 'text-01-01,text-01-02')")
    parser.add_argument("--config", type=str, default="configs/tts_config.yaml", help="Path to TTS config file (YAML/JSON)")
    parser.add_argument("--instruction", type=str, help="Custom instruction to override config/default")

    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)

    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key must be provided via --api-key or OPENAI_API_KEY environment variable")
        return 1

    languages = [lang.strip() for lang in args.language.split(',') if lang.strip()]
    if not languages:
        logger.error("No valid languages specified. Use --language en,es or similar.")
        return 1

    start_page = args.start_page if args.start_page is not None else 0
    end_page = args.end_page if args.end_page is not None else 0
    input_json = args.input_json
    data_ids = [i.strip() for i in args.data_ids.split(',')] if args.data_ids else None

    custom_instruction = None
    if args.instruction:
        try:
            custom_instruction = json.loads(args.instruction)
        except Exception:
            custom_instruction = args.instruction  # fallback to single string

    try:
        regenerator = ADTTTSRegenerator(
            api_key,
            output_dir=target_dir / "content/i18n",
            logger=logger,
            config_path=args.config,
            custom_instruction=custom_instruction,
        )
        results = await regenerator.regenerate(
            start_page=start_page,
            end_page=end_page,
            languages=languages,
            input_json=input_json,
            data_ids=data_ids,
        )

        # Print summary
        print("\n" + "="*50)
        print("TTS REGENERATION SUMMARY")
        print("="*50)

        total_success = 0
        total_failure = 0

        for language, (success, failure) in results.items():
            print(f"{language.upper()}: {success} successful, {failure} failed")
            total_success += success
            total_failure += failure

        print(f"\nTOTAL: {total_success} successful, {total_failure} failed")

        if total_failure > 0:
            print("\nCheck tts_regeneration.log for detailed error information")
            return 1

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(asyncio.run(main()))