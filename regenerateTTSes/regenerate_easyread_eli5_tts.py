#!/usr/bin/env python3
"""
TTS Regeneration Script for EasyRead, ELI5, and Image Content

This script asynchronously regenerates TTS audio for existing easyread, eli5, and image text content 
using OpenAI's TTS API. It reads the simplified text from JSON files and generates audio files.

Usage:
    python regenerate_easyread_eli5_tts.py --start-page 0 --end-page 5 --language en --type easyread
    python regenerate_easyread_eli5_tts.py --start-page 10 --end-page 15 --language es --type eli5
    python regenerate_easyread_eli5_tts.py --start-page 0 --end-page 5 --language both --type img
    python regenerate_easyread_eli5_tts.py --start-page 0 --end-page 5 --language both --type all
"""

import asyncio
import json
import os
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from datetime import datetime
import concurrent.futures

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('easyread_eli5_tts_regeneration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EasyReadELI5ImageTTSRegenerator:
    def __init__(self, openai_api_key: str):
        """Initialize the TTS regenerator with OpenAI API key."""
        self.api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.texts_dir = Path("content/i18n")
        
        # Rate limiting
        self.max_concurrent_requests = 5  # More conservative for TTS
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Thread pool for blocking operations
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.executor.shutdown(wait=True)
    
    def load_texts(self, language: str) -> Dict[str, str]:
        """Load texts from JSON file for the specified language."""
        texts_file = self.texts_dir / language / "texts.json"
        
        if not texts_file.exists():
            logger.error(f"Texts file not found: {texts_file}")
            return {}
            
        try:
            with open(texts_file, 'r', encoding='utf-8') as f:
                texts = json.load(f)
            logger.info(f"Loaded {len(texts)} texts for language: {language}")
            return texts
        except Exception as e:
            logger.error(f"Error loading texts for {language}: {e}")
            return {}
    
    def filter_texts_by_page_range_and_type(
        self, texts: Dict[str, str], start_page: int, end_page: int, text_type: str
    ) -> Dict[str, str]:
        """Filter texts to only include easyread/eli5/img texts within the specified page range."""
        filtered_texts = {}
        
        for key, text in texts.items():
            # Check if this is an easyread, eli5, or img key
            if text_type == 'easyread' and key.startswith('easyread-text-'):
                try:
                    # Extract page number from easyread-text-{page}-{section} format
                    parts = key.split('-')
                    if len(parts) >= 3:
                        page_num = int(parts[2])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
            elif text_type == 'eli5' and key.startswith('sectioneli5-'):
                try:
                    # Extract page number from sectioneli5-{page}-{section} format
                    parts = key.split('-')
                    if len(parts) >= 3:  # Fixed: should be >= 3, not >= 2
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
            elif text_type == 'img' and key.startswith('img-'):
                try:
                    # Extract page number from img-{page}-{section} format
                    parts = key.split('-')
                    if len(parts) >= 2:
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Filtered to {len(filtered_texts)} {text_type} texts for pages "
                   f"{start_page}-{end_page} in language")
        return filtered_texts
    
    def get_voice_and_instructions(self, language: str, text_type: str) -> Tuple[str, str]:
        """Get appropriate voice and instructions based on language and text type."""
        if language == 'es':
            voice = "nova"  # Female voice for Spanish
            if text_type == 'easyread':
                instructions = (
                    "Lee este texto de manera clara y pausada, apropiado para personas "
                    "con dificultades de lectura. Usa un tono amigable y accesible. "
                    "Pronuncia con acento salvadoreño cuando sea apropiado."
                )
            elif text_type == 'eli5':
                instructions = (
                    "Lee este texto como si fueras un maestro paciente explicando "
                    "conceptos a un niño de 5 años. Usa un tono cálido y educativo. "
                    "Pronuncia con acento salvadoreño cuando sea apropiado."
                )
            else:  # img
                instructions = (
                    "Describe esta imagen de manera clara y detallada, como si fueras "
                    "un maestro describiendo una ilustración a niños. Usa un tono "
                    "descriptivo y educativo. Pronuncia con acento salvadoreño cuando sea apropiado."
                )
        else:  # English
            voice = "alloy"  # Clear voice for English
            if text_type == 'easyread':
                instructions = (
                    "Read this text clearly and at a steady pace, appropriate for people "
                    "with reading difficulties. Use a friendly and accessible tone."
                )
            elif text_type == 'eli5':
                instructions = (
                    "Read this text as if you were a patient teacher explaining "
                    "concepts to a 5-year-old child. Use a warm and educational tone."
                )
            else:  # img
                instructions = (
                    "Describe this image clearly and in detail, as if you were a teacher "
                    "describing an illustration to children. Use a descriptive and educational tone."
                )
        
        return voice, instructions
    
    def get_audio_dir(self, language: str) -> Path:
        """Get the audio directory for the specified language."""
        audio_dir = self.texts_dir / language / "audio"
        # Ensure audio directory exists
        audio_dir.mkdir(parents=True, exist_ok=True)
        return audio_dir
    
    def get_audio_filename(self, text_key: str, language: str) -> str:
        """Generate audio filename based on text key and language."""
        return f"{text_key}_{language}.mp3"
    
    async def generate_audio(
        self, text: str, text_key: str, language: str, text_type: str
    ) -> Tuple[str, bool]:
        """Generate TTS audio using OpenAI API."""
        if not text.strip():
            logger.warning(f"Empty text for {text_key}, skipping")
            return text_key, False
            
        async with self.semaphore:  # Rate limiting
            try:
                logger.info(f"Generating TTS for: {text_key}")
                
                voice, instructions = self.get_voice_and_instructions(language, text_type)
                audio_filename = self.get_audio_filename(text_key, language)
                audio_dir = self.get_audio_dir(language)
                audio_path = audio_dir / audio_filename
                
                # Run TTS generation in executor to avoid blocking
                loop = asyncio.get_event_loop()
                
                def generate_tts():
                    with self.client.audio.speech.with_streaming_response.create(
                        model="gpt-4o-mini-tts",
                        voice=voice,
                        input=text,
                        instructions=instructions,
                        response_format="mp3"
                    ) as response:
                        response.stream_to_file(audio_path)
                        return True
                
                success = await loop.run_in_executor(self.executor, generate_tts)
                
                if success:
                    logger.info(f"Successfully generated TTS: {audio_filename}")
                    return text_key, True
                else:
                    logger.error(f"Failed to generate TTS for: {text_key}")
                    return text_key, False
                        
            except Exception as e:
                logger.error(f"Error generating TTS for {text_key}: {e}")
                return text_key, False
    
    async def regenerate_tts_for_language_and_type(
        self, language: str, start_page: int, end_page: int, text_type: str
    ) -> Tuple[int, int]:
        """Regenerate TTS for a specific language, page range, and type."""
        logger.info(f"Starting TTS regeneration for {language}, pages {start_page}-{end_page}, type: {text_type}")
        
        # Load texts
        texts = self.load_texts(language)
        if not texts:
            return 0, 0
            
        # Filter by page range and type
        filtered_texts = self.filter_texts_by_page_range_and_type(
            texts, start_page, end_page, text_type
        )
        if not filtered_texts:
            logger.warning(f"No {text_type} texts found for pages {start_page}-{end_page} in {language}")
            return 0, 0
        
        # Generate TTS for all texts
        tasks = []
        
        for text_key, text_content in filtered_texts.items():
            task = self.generate_audio(text_content, text_key, language, text_type)
            tasks.append(task)
        
        # Execute all tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successes = 0
        failures = 0
        
        for result in results:
            if isinstance(result, Exception):
                failures += 1
                logger.error(f"Task failed with exception: {result}")
            else:
                key, success = result
                if success:
                    successes += 1
                else:
                    failures += 1
        
        logger.info(f"Completed {language} {text_type} TTS: {successes} successful, {failures} failed")
        return successes, failures
    
    async def regenerate(
        self, start_page: int, end_page: int, languages: List[str], text_types: List[str]
    ) -> Dict[str, Dict[str, Tuple[int, int]]]:
        """Regenerate TTS for specified languages, page range, and types."""
        logger.info(f"Starting TTS regeneration for pages {start_page}-{end_page}, "
                   f"languages: {languages}, types: {text_types}")
        start_time = datetime.now()
        
        results = {}
        
        for language in languages:
            results[language] = {}
            
            for text_type in text_types:
                try:
                    success_count, failure_count = await self.regenerate_tts_for_language_and_type(
                        language, start_page, end_page, text_type
                    )
                    
                    results[language][text_type] = (success_count, failure_count)
                    
                except Exception as e:
                    logger.error(f"Error processing {language} {text_type}: {e}")
                    results[language][text_type] = (0, 1)
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"TTS regeneration completed in {duration}")
        
        return results


async def main():
    """Main function to parse arguments and run TTS regeneration."""
    parser = argparse.ArgumentParser(description="Regenerate TTS for easyread and eli5 text using OpenAI API")
    parser.add_argument("--start-page", type=int, required=True, 
                       help="Starting page number (inclusive)")
    parser.add_argument("--end-page", type=int, required=True,
                       help="Ending page number (inclusive)")
    parser.add_argument("--language", choices=['en', 'es', 'both'], default='both',
                       help="Language to regenerate (en, es, or both)")
    parser.add_argument("--type", choices=['easyread', 'eli5', 'img', 'all'], default='all',
                       help="Type of text to regenerate TTS for (easyread, eli5, img, or all)")
    parser.add_argument("--api-key", type=str,
                       help="OpenAI API key (can also be set via OPENAI_API_KEY env var)")
    
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
    
    # Determine text types to process
    if args.type == 'all':
        text_types = ['easyread', 'eli5', 'img']
    else:
        text_types = [args.type]
    
    # Run TTS regeneration
    try:
        async with EasyReadELI5ImageTTSRegenerator(api_key) as regenerator:
            results = await regenerator.regenerate(args.start_page, args.end_page, languages, text_types)
            
            # Print summary
            print("\n" + "="*60)
            print("TTS REGENERATION SUMMARY")
            print("="*60)
            
            total_success = 0
            total_failure = 0
            
            for language, type_results in results.items():
                print(f"\n{language.upper()}:")
                for text_type, (success, failure) in type_results.items():
                    print(f"  {text_type}: {success} successful, {failure} failed")
                    total_success += success
                    total_failure += failure
            
            print(f"\nTOTAL: {total_success} successful, {total_failure} failed")
            
            if total_failure > 0:
                print(f"\nCheck easyread_eli5_tts_regeneration.log for detailed error information")
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
