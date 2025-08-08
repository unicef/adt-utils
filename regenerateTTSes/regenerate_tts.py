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
from typing import Dict, List, Tuple, Optional
import aiohttp
import aiofiles
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
        self.base_url = "https://api.openai.com/v1/audio/speech"
        self.output_dir = Path("output/content/i18n")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiting
        self.max_concurrent_requests = 5
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
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
            else:
                # Include non-text keys if they match the pattern (img-, sectioneli5-, etc.)
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
    
    def get_voice_and_prompt(self, language: str) -> Tuple[str, str]:
        """Get appropriate voice and prompt based on language."""
        if language == 'es':
            voice = "nova"  # Female voice that works well with Spanish
            prompt_prefix = ("Habla con el acento y entonación característica de El Salvador. "
                           "Usa las particularidades del español salvadoreño, incluyendo la "
                           "pronunciación suave y las características fonéticas típicas de la región. ")
        else:  # English
            voice = "alloy"  # Clear, neutral English voice
            prompt_prefix = "Speak clearly with a neutral, professional tone. "
            
        return voice, prompt_prefix
    
    async def generate_audio(self, text: str, output_path: Path, language: str) -> bool:
        """Generate audio using OpenAI TTS API."""
        if not text.strip():
            logger.warning(f"Empty text for {output_path}, skipping")
            return False
            
        voice, prompt_prefix = self.get_voice_and_prompt(language)
        
        # For Spanish, add accent instruction to the text
        if language == 'es':
            enhanced_text = f"{prompt_prefix}{text}"
        else:
            enhanced_text = text
            
        async with self.semaphore:  # Rate limiting
            try:
                payload = {
                    "model": "tts-1",  # Using tts-1 as it's more cost-effective than tts-1-hd
                    "input": enhanced_text,
                    "voice": voice,
                    "response_format": "mp3"
                }
                
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                logger.info(f"Generating audio for: {output_path.name}")
                
                async with self.session.post(self.base_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        # Ensure output directory exists
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Write audio file
                        async with aiofiles.open(output_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        logger.info(f"Successfully generated: {output_path.name}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"API error for {output_path.name}: {response.status} - {error_text}")
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
        else:
            # For other keys, try to match existing patterns
            # Check if it starts with easyread- pattern
            return f"easyread-{text_key}_{language}.mp3"
    
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