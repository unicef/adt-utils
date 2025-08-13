#!/usr/bin/env python3
"""
TTS Audio Regeneration Script

This script asynchronously regenerates TTS audio files for text keys using OpenAI's API.
It supports both English and Spanish languages, with Spanish using El Salvador accent features.
You can specify page ranges to regenerate specific sections of content.

Usage:
    python regenerate_tts.py --start-page 0 --end-page 5 --language en
    python regenerate_tts.py --start-page 10 --end-page 15 --language es
    python regenerate_tts.py --start-page 0 --end-page 5 --language both
"""

import asyncio
import json
import os
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from openai import OpenAI
from datetime import datetime

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

class TTSRegenerator:
    def __init__(self, openai_api_key: str):
        """Initialize the TTS regenerator with OpenAI API key."""
        self.api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.output_dir = Path("content/i18n")
        
        # Rate limiting
        self.max_concurrent_requests = 5
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # No session to close with sync OpenAI client
        pass
    
    def load_texts(self, language: str) -> Dict[str, str]:
        """Load texts from JSON file for the specified language."""
        texts_file = self.output_dir / language / "texts.json"
        
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
    
    def filter_texts_by_page_range(self, texts: Dict[str, str], start_page: int, end_page: int) -> Dict[str, str]:
        """Filter texts to only include those within the specified page range."""
        filtered_texts = {}
        
        for key, text in texts.items():
            if key.startswith('text-'):
                # Extract page number from key like 'text-5-2'
                try:
                    parts = key.split('-')
                    if len(parts) >= 2:
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    # Skip keys that don't match expected format
                    continue
            elif key.startswith('easyread-text-'):
                # Handle easyread-text-{page}-{section} format
                try:
                    parts = key.split('-')
                    if len(parts) >= 3:
                        page_num = int(parts[2])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
            else:
                # Include other keys if they match the pattern (img-, sectioneli5-, etc.)
                try:
                    parts = key.split('-')
                    if len(parts) >= 2:
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Filtered to {len(filtered_texts)} texts for pages {start_page}-{end_page}")
        return filtered_texts
    
    def get_voice_and_instructions(self, language: str) -> Tuple[str, str]:
        """Get appropriate voice and instructions based on language."""
        if language == 'es':
            voice = "nova"  # Female voice for Spanish - better for teacher tone
            instructions = ("Lee este texto como si fueras un maestro paciente y cálido "
                          "enseñando a niños. Usa el acento y entonación característica "
                          "de El Salvador, incluyendo la pronunciación suave y las "
                          "características fonéticas típicas de la región salvadoreña. "
                          "Mantén un tono educativo, amigable y accesible apropiado "
                          "para contenido educativo dirigido a niños.")
        else:  # English
            voice = "alloy"  # Clear, neutral English voice
            instructions = ("Speak clearly with a warm, patient teacher tone "
                          "appropriate for educational content for children.")
            
        return voice, instructions
    
    async def generate_audio(self, text: str, output_path: Path, language: str) -> bool:
        """Generate audio using OpenAI TTS API with gpt-4o-mini-tts model."""
        if not text.strip():
            logger.warning(f"Empty text for {output_path}, skipping")
            return False
            
        voice, instructions = self.get_voice_and_instructions(language)
            
        async with self.semaphore:  # Rate limiting
            try:
                logger.info(f"Generating audio for: {output_path.name}")
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use sync client in async context - run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                
                def generate_sync():
                    with self.client.audio.speech.with_streaming_response.create(
                        model="gpt-4o-mini-tts",
                        voice=voice,
                        input=text,
                        instructions=instructions,
                        response_format="mp3"
                    ) as response:
                        response.stream_to_file(output_path)
                        return True
                
                # Run the sync operation in a thread to avoid blocking event loop
                success = await loop.run_in_executor(None, generate_sync)
                
                if success:
                    logger.info(f"Successfully generated: {output_path.name}")
                    return True
                else:
                    logger.error(f"Failed to generate: {output_path.name}")
                    return False
                        
            except Exception as e:
                logger.error(f"Error generating audio for {output_path.name}: {e}")
                return False
    
    def get_audio_filename(self, text_key: str, language: str) -> str:
        """Generate appropriate audio filename based on text key and language."""
        # Map different key prefixes to appropriate prefixes in audio filenames
        if text_key.startswith('text-'):
            # Standard text keys: text-5-2 -> text-5-2_en.mp3
            return f"{text_key}_{language}.mp3"
        elif text_key.startswith('img-'):
            # Image keys: img-5-1 -> img-5-1_en.mp3
            return f"{text_key}_{language}.mp3"
        elif text_key.startswith('sectioneli5-'):
            # Section keys: sectioneli5-5-1 -> sectioneli5-5-1_en.mp3
            return f"{text_key}_{language}.mp3"
        elif text_key.startswith('easyread-text-'):
            # Easyread keys: easyread-text-5-1 -> easyread-text-5-1_en.mp3
            return f"{text_key}_{language}.mp3"
        else:
            # For any other keys, use as-is with language suffix
            return f"{text_key}_{language}.mp3"
    
    async def regenerate_for_language(self, language: str, start_page: int, end_page: int) -> Tuple[int, int]:
        """Regenerate TTS files for a specific language and page range."""
        logger.info(f"Starting regeneration for {language}, pages {start_page}-{end_page}")
        
        # Load texts
        texts = self.load_texts(language)
        if not texts:
            return 0, 0
            
        # Filter by page range
        filtered_texts = self.filter_texts_by_page_range(texts, start_page, end_page)
        if not filtered_texts:
            logger.warning(f"No texts found for pages {start_page}-{end_page} in {language}")
            return 0, 0
        
        # Generate audio files
        audio_dir = self.output_dir / language / "audio"
        tasks = []
        
        for text_key, text_content in filtered_texts.items():
            audio_filename = self.get_audio_filename(text_key, language)
            output_path = audio_dir / audio_filename
            
            task = self.generate_audio(text_content, output_path, language)
            tasks.append(task)
        
        # Execute all tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        successes = sum(1 for result in results if result is True)
        failures = sum(1 for result in results if result is not True)
        
        logger.info(f"Completed {language}: {successes} successful, {failures} failed")
        return successes, failures
    
    async def regenerate(self, start_page: int, end_page: int, languages: List[str]) -> Dict[str, Tuple[int, int]]:
        """Regenerate TTS files for specified languages and page range."""
        logger.info(f"Starting TTS regeneration for pages {start_page}-{end_page}, languages: {languages}")
        start_time = datetime.now()
        
        results = {}
        
        for language in languages:
            try:
                success_count, failure_count = await self.regenerate_for_language(
                    language, start_page, end_page
                )
                results[language] = (success_count, failure_count)
            except Exception as e:
                logger.error(f"Error processing language {language}: {e}")
                results[language] = (0, 1)
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"TTS regeneration completed in {duration}")
        
        return results


async def main():
    """Main function to parse arguments and run TTS regeneration."""
    parser = argparse.ArgumentParser(description="Regenerate TTS audio files using OpenAI API")
    parser.add_argument("--start-page", type=int, required=True, 
                       help="Starting page number (inclusive)")
    parser.add_argument("--end-page", type=int, required=True,
                       help="Ending page number (inclusive)")
    parser.add_argument("--language", choices=['en', 'es', 'both'], default='both',
                       help="Language to regenerate (en, es, or both)")
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
    
    # Run regeneration
    try:
        async with TTSRegenerator(api_key) as regenerator:
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
                print(f"\nCheck tts_regeneration.log for detailed error information")
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