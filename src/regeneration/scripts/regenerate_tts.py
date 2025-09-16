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
from src.regeneration.classes.adt_tts_regenerator import ADTTSRegenerator

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
    """Main function to parse arguments and run TTS regeneration."""
    parser = argparse.ArgumentParser(description="Regenerate TTS audio files using OpenAI API")
    parser.add_argument("--start-page", type=int, required=True, 
                       help="Starting page number (inclusive)")
    parser.add_argument("--end-page", type=int, required=True,
                       help="Ending page number (inclusive)")
    parser.add_argument("--language", type=str,
                       help="Language to regenerate (en,es)")
    parser.add_argument("--input-json", type=str,
                       help="Path to input JSON file containing text content (overrides HTML parsing)")

    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OpenAI API key must be provided via --api-key or OPENAI_API_KEY environment variable")
        return 1

    # Validate page range
    if args.start_page > args.end_page:
        logger.error("Start page must be less than or equal to end page")
        return 1

    # Determine languages to process
    if args.language == 'both':
        languages = ['en', 'es']
    else:
        languages = [args.language]

    # Run regeneration using the new class
    try:
        regenerator = ADTTSRegenerator(api_key, logger=logger)
        results = await regenerator.regenerate(args.start_page, args.end_page, languages)

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