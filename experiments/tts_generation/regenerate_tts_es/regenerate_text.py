#!/usr/bin/env python3
"""
Text Regeneration Script for EasyRead and ELI5 Content

This script asynchronously regenerates easyread and eli5 text content using OpenAI's API.
It supports both English and Spanish languages, creating simplified versions of existing text.
You can specify page ranges to regenerate specific sections of content.

Usage:
    python regenerate_text.py --start-page 0 --end-page 5 --language en --type easyread
    python regenerate_text.py --start-page 10 --end-page 15 --language es --type eli5
    python regenerate_text.py --start-page 0 --end-page 5 --language both --type both
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('text_regeneration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TextRegenerator:
    def __init__(self, openai_api_key: str):
        """Initialize the text regenerator with OpenAI API key."""
        self.api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.output_dir = Path("content/i18n")
        
        # Rate limiting
        self.max_concurrent_requests = 10
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
    
    def filter_texts_by_page_range_and_type(
        self, texts: Dict[str, str], start_page: int, end_page: int, text_type: str
    ) -> Dict[str, str]:
        """Filter texts to only include those within the specified page range and type."""
        filtered_texts = {}
        
        for key, text in texts.items():
            # Only process text keys (not easyread/eli5 keys)
            if key.startswith('text-'):
                try:
                    parts = key.split('-')
                    if len(parts) >= 2:
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            # Create the target key based on type
                            if text_type == 'easyread':
                                target_key = f"easyread-{key}"
                            elif text_type == 'eli5':
                                target_key = f"sectioneli5-{key.replace('text-', '')}"
                            else:
                                continue
                            
                            filtered_texts[target_key] = text
                except (ValueError, IndexError):
                    continue
        
        logger.info(f"Filtered to {len(filtered_texts)} texts for pages "
                   f"{start_page}-{end_page}, type: {text_type}")
        return filtered_texts
    
    def get_system_prompt(self, text_type: str, language: str) -> str:
        """Get appropriate system prompt based on text type and language."""
        if language == 'es':
            if text_type == 'easyread':
                return (
                    "Eres un asistente que simplifica textos en español. "
                    "Debes crear versiones CONCISAS y fáciles de leer, usando lenguaje sencillo "
                    "y añadiendo algunos emojis relevantes. El texto simplificado debe ser más "
                    "corto que el original. Usa el español de El Salvador cuando sea apropiado."
                )
            else:  # eli5
                return (
                    "Eres un experto en explicar conceptos complejos de manera simple "
                    "para niños de 5 años en español. Usa analogías simples, ejemplos "
                    "familiares y un lenguaje muy básico. Explica como si fueras un "
                    "maestro paciente hablando con un niño pequeño. "
                    "Usa el español de El Salvador cuando sea apropiado."
                )
        else:  # English
            if text_type == 'easyread':
                return (
                    "You are an expert in creating easy-read content in English. "
                    "Your job is to simplify complex texts to make them accessible "
                    "for people with reading or comprehension difficulties. "
                    "Use simple words, short sentences, and clear concepts. "
                    "Keep the original meaning but make it easier to understand."
                )
            else:  # eli5
                return (
                    "You are an expert at explaining complex concepts in simple terms "
                    "for 5-year-old children in English. Use simple analogies, familiar "
                    "examples, and very basic language. Explain as if you were a patient "
                    "teacher talking to a young child."
                )
    
    def get_user_prompt(self, text: str, text_type: str, language: str) -> str:
        """Get user prompt for the specific text and type."""
        if language == 'es':
            if text_type == 'easyread':
                return f"""
Convertir el siguiente texto a formato de lectura fácil siguiendo estas instrucciones:

INSTRUCCIONES PARA CREAR TEXTOS DE LECTURA FÁCIL:
1. Usar frases cortas y sencillas con estructura: sujeto + verbo + complementos.
2. Simplificar el vocabulario usando palabras comunes y cotidianas.
3. Explicar SOLO términos técnicos esenciales, de forma muy breve.
4. Usar listas con viñetas para ideas múltiples.
5. Reducir la longitud total - el texto simplificado debe ser más corto que el original.
6. Añadir emojis relevantes con moderación (máximo 1 por párrafo o punto de lista).
7. Eliminar información secundaria o redundante.
8. Mantener el mismo orden de las ideas del texto original.
9. No añadir información o explicaciones que no estén en el texto original.
10. No repetir conceptos que ya se han explicado.

IMPORTANTE: El texto simplificado debe ser MÁS CORTO que el original.

FORMATO DE RESPUESTA:
Devolver solo el texto simplificado con emojis apropiados. No incluir preguntas, explicaciones ni indicar que es lectura fácil.

EJEMPLO:

INPUT:
La deforestación excesiva, la caza indiscriminada de algunas especies, la pesca intensiva (merluza, por ejemplo), la perforación de terrenos para la explotación minera (petróleo, carbón y otros minerales) son algunos ejemplos de actividades que pueden provocar daños en el planeta.

OUTPUT:
🌎 Algunas actividades humanas dañan el planeta:

- Cortar demasiados árboles (deforestación)
- Cazar animales sin control 
- Pescar en exceso, como la merluza
- Hacer agujeros para sacar minerales como petróleo y carbón

Estas acciones dañan la naturaleza y hacen que algunos seres vivos desaparezcan.

TEXTO A CONVERTIR:
{text}

Provide me the text in easy-read format. Please think carefully before responding.
"""
            else:  # eli5
                return (
                    f"Explica el siguiente concepto como si fueras un maestro hablando "
                    f"con un niño de 5 años. Usa ejemplos simples y familiares:\n\n{text}\n\n"
                    f"Explicación para niños:"
                )
        else:  # English
            if text_type == 'easyread':
                return (
                    f"Convert the following text into an easy-read version. "
                    f"Keep the main meaning but make it simpler and clearer:\n\n{text}\n\n"
                    f"Easy-read version:"
                )
            else:  # eli5
                return (
                    f"Explain the following concept as if you were a teacher talking "
                    f"to a 5-year-old child. Use simple, familiar examples:\n\n{text}\n\n"
                    f"Explanation for children:"
                )
    
    async def generate_text(
        self, original_text: str, target_key: str, text_type: str, language: str
    ) -> Tuple[str, str]:
        """Generate simplified text using OpenAI API."""
        if not original_text.strip():
            logger.warning(f"Empty text for {target_key}, skipping")
            return target_key, ""
            
        async with self.semaphore:  # Rate limiting
            try:
                logger.info(f"Generating {text_type} text for: {target_key}")
                
                system_prompt = self.get_system_prompt(text_type, language)
                user_prompt = self.get_user_prompt(original_text, text_type, language)
                
                # Use sync client in async context - run in executor to avoid blocking
                loop = asyncio.get_event_loop()
                
                def generate_sync():
                    response = self.client.chat.completions.create(
                        model="gpt-4.1",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=1000,
                        temperature=0.5
                    )
                    return response.choices[0].message.content.strip()
                
                # Run the sync operation in a thread to avoid blocking event loop
                generated_text = await loop.run_in_executor(None, generate_sync)
                
                if generated_text:
                    logger.info(f"Successfully generated: {target_key}")
                    return target_key, generated_text
                else:
                    logger.error(f"Empty response for: {target_key}")
                    return target_key, ""
                        
            except Exception as e:
                logger.error(f"Error generating text for {target_key}: {e}")
                return target_key, ""
    
    async def regenerate_for_language_and_type(
        self, language: str, start_page: int, end_page: int, text_type: str
    ) -> Tuple[int, int, Dict[str, str]]:
        """Regenerate text for a specific language, page range, and type."""
        logger.info(f"Starting regeneration for {language}, pages {start_page}-{end_page}, type: {text_type}")
        
        # Load texts
        texts = self.load_texts(language)
        if not texts:
            return 0, 0, {}
            
        # Filter by page range and type
        filtered_texts = self.filter_texts_by_page_range_and_type(
            texts, start_page, end_page, text_type
        )
        if not filtered_texts:
            logger.warning(f"No texts found for pages {start_page}-{end_page} in {language}, type {text_type}")
            return 0, 0, {}
        
        # Generate simplified texts
        tasks = []
        
        for target_key, original_text in filtered_texts.items():
            task = self.generate_text(original_text, target_key, text_type, language)
            tasks.append(task)
        
        # Execute all tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        generated_texts = {}
        successes = 0
        failures = 0
        
        for result in results:
            if isinstance(result, Exception):
                failures += 1
                logger.error(f"Task failed with exception: {result}")
            else:
                key, text = result
                if text:
                    generated_texts[key] = text
                    successes += 1
                else:
                    failures += 1
        
        logger.info(f"Completed {language} {text_type}: {successes} successful, {failures} failed")
        return successes, failures, generated_texts
    
    def save_generated_texts(self, language: str, generated_texts: Dict[str, str]) -> bool:
        """Save generated texts back to the JSON file."""
        if not generated_texts:
            return True
            
        texts_file = self.output_dir / language / "texts.json"
        
        try:
            # Load existing texts
            existing_texts = {}
            if texts_file.exists():
                with open(texts_file, 'r', encoding='utf-8') as f:
                    existing_texts = json.load(f)
            
            # Update with generated texts
            existing_texts.update(generated_texts)
            
            # Save back to file
            with open(texts_file, 'w', encoding='utf-8') as f:
                json.dump(existing_texts, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(generated_texts)} generated texts to {texts_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving generated texts to {texts_file}: {e}")
            return False
    
    async def regenerate(
        self, start_page: int, end_page: int, languages: List[str], text_types: List[str]
    ) -> Dict[str, Dict[str, Tuple[int, int]]]:
        """Regenerate text for specified languages, page range, and types."""
        logger.info(f"Starting text regeneration for pages {start_page}-{end_page}, "
                   f"languages: {languages}, types: {text_types}")
        start_time = datetime.now()
        
        results = {}
        
        for language in languages:
            results[language] = {}
            
            for text_type in text_types:
                try:
                    success_count, failure_count, generated_texts = await self.regenerate_for_language_and_type(
                        language, start_page, end_page, text_type
                    )
                    
                    # Save generated texts
                    if generated_texts:
                        save_success = self.save_generated_texts(language, generated_texts)
                        if not save_success:
                            logger.error(f"Failed to save texts for {language} {text_type}")
                    
                    results[language][text_type] = (success_count, failure_count)
                    
                except Exception as e:
                    logger.error(f"Error processing {language} {text_type}: {e}")
                    results[language][text_type] = (0, 1)
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"Text regeneration completed in {duration}")
        
        return results


async def main():
    """Main function to parse arguments and run text regeneration."""
    parser = argparse.ArgumentParser(description="Regenerate easyread and eli5 text using OpenAI API")
    parser.add_argument("--start-page", type=int, required=True, 
                       help="Starting page number (inclusive)")
    parser.add_argument("--end-page", type=int, required=True,
                       help="Ending page number (inclusive)")
    parser.add_argument("--language", choices=['en', 'es', 'both'], default='both',
                       help="Language to regenerate (en, es, or both)")
    parser.add_argument("--type", choices=['easyread', 'eli5', 'both'], default='both',
                       help="Type of text to regenerate (easyread, eli5, or both)")
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
    if args.type == 'both':
        text_types = ['easyread', 'eli5']
    else:
        text_types = [args.type]
    
    # Run regeneration
    try:
        async with TextRegenerator(api_key) as regenerator:
            results = await regenerator.regenerate(args.start_page, args.end_page, languages, text_types)
            
            # Print summary
            print("\n" + "="*60)
            print("TEXT REGENERATION SUMMARY")
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
                print(f"\nCheck text_regeneration.log for detailed error information")
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
