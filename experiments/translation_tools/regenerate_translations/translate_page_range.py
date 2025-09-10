#!/usr/bin/env python3
"""
Translation script for ADT Manual
Extracts text strings from a page range in Spanish JSON and generates English translations.
"""

import json
import re
import argparse
import os
from pathlib import Path

def load_json_file(file_path):
    """Load JSON file and return the data."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return None

def save_json_file(file_path, data):
    """Save data to JSON file with proper formatting."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)

def extract_page_range_texts(spanish_data, page_start, page_end=None):
    """Extract text strings for a specific page range."""
    if page_end is None:
        page_end = page_start
    
    extracted_texts = {}
    pattern = re.compile(rf'^text-({page_start}|{"|".join(map(str, range(page_start, page_end + 1)))})-\d+$')
    
    for key, value in spanish_data.items():
        if pattern.match(key):
            extracted_texts[key] = value
    
    return extracted_texts

def simple_translate(spanish_text):
    """
    Simple translation mapping for common terms.
    This is a basic implementation - for production use, integrate with Google Translate API or similar.
    """
    translations = {
        # Common terms
        "Manual de Autocuidado": "Self-Care Manual",
        "Manual de autocuidado": "Self-care manual",
        "Manual de autocuido": "Self-care manual",
        "Autocuidado": "Self-care",
        "autocuidado": "self-care",
        "Autocuidado físico": "Physical self-care",
        "Autocuidado emocional": "Emotional self-care",
        "Autocuidado cognitivo": "Cognitive self-care",
        "Autocuidado social": "Social self-care",
        "Autocuidado espiritual": "Spiritual self-care",
        "Contenido": "Contents",
        "Introducción": "Introduction",
        "INTRODUCCIÓN": "INTRODUCTION",
        "¿Qué es el autocuidado?": "What is self-care?",
        "Principios del autocuidado": "Principles of self-care",
        "Importancia y beneficios del autocuidado": "Importance and benefits of self-care",
        "Tipos de autocuidado": "Types of self-care",
        "Ejercicios prácticos": "Practical exercises",
        "Bibliografía": "Bibliography",
        
        # Sleep and rest
        "Dormir y descansar lo suficiente:": "Get enough sleep and rest:",
        "Algunas recomendaciones para garantizar una rutina saludable del sueño son:": "Some recommendations to ensure a healthy sleep routine are:",
        "Cuidar el entorno:": "Take care of the environment:",
        "Ser constante:": "Be consistent:",
        "No consumas estimulantes después de media tarde:": "Don't consume stimulants after mid-afternoon:",
        
        # Emotions
        "Emociones": "Emotions",
        "¿Cómo se expresan las emociones?": "How are emotions expressed?",
        "Expresar Emociones": "Expressing Emotions",
        "Las Emociones": "The Emotions",
        
        # Hygiene
        "Cuidado de la higiene": "Hygiene care",
        "Cuidado de la higiene:": "Hygiene care:",
        
        # Physical care
        "Auto cuidado físico": "Physical self-care",
        "Auto Cuidado Físico": "Physical Self-Care",
        
        # General terms
        "es recomendable": "it is recommended",
        "Se recomienda": "It is recommended",
        "Para": "For",
        "por": "by",
        "de": "of",
        "la": "the",
        "el": "the",
        "una": "a",
        "un": "a",
        "y": "and",
        "o": "or",
        "en": "in",
        "con": "with",
        "para": "for",
        "que": "that",
        "como": "as",
        "son": "are",
        "es": "is",
        "del": "of the",
        "las": "the",
        "los": "the",
    }
    
    # Try exact match first
    if spanish_text in translations:
        return translations[spanish_text]
    
    # For longer texts, try to translate key terms
    translated = spanish_text
    for spanish, english in translations.items():
        if len(spanish) > 3:  # Only replace longer terms to avoid incorrect substitutions
            translated = translated.replace(spanish, english)
    
    return translated

def generate_english_translations(spanish_texts):
    """Generate English translations for Spanish text strings."""
    english_translations = {}
    
    for key, spanish_text in spanish_texts.items():
        english_text = simple_translate(spanish_text)
        english_translations[key] = english_text
        print(f"Translated: {key}")
        print(f"  ES: {spanish_text}")
        print(f"  EN: {english_text}")
        print()
    
    return english_translations

def merge_with_existing_english(new_translations, english_file_path):
    """Merge new translations with existing English translations."""
    existing_english = load_json_file(english_file_path)
    if existing_english is None:
        existing_english = {}
    
    # Update existing translations with new ones
    existing_english.update(new_translations)
    
    return existing_english

def main():
    parser = argparse.ArgumentParser(description='Generate English translations for a page range')
    parser.add_argument('page_start', type=int, help='Starting page number (e.g., 23)')
    parser.add_argument('page_end', type=int, nargs='?', help='Ending page number (optional, defaults to page_start)')
    parser.add_argument('--dry-run', action='store_true', help='Show translations without saving')
    
    args = parser.parse_args()
    
    # File paths
    spanish_file = Path('content/i18n/es/texts.json')
    english_file = Path('content/i18n/en/texts.json')
    
    # Check if Spanish file exists
    if not spanish_file.exists():
        print(f"Error: Spanish file {spanish_file} not found.")
        return 1
    
    # Load Spanish texts
    print(f"Loading Spanish texts from {spanish_file}...")
    spanish_data = load_json_file(spanish_file)
    if spanish_data is None:
        return 1
    
    # Extract texts for the specified page range
    page_end = args.page_end if args.page_end else args.page_start
    print(f"Extracting texts for pages {args.page_start} to {page_end}...")
    
    page_texts = extract_page_range_texts(spanish_data, args.page_start, page_end)
    
    if not page_texts:
        print(f"No texts found for page range {args.page_start}-{page_end}")
        return 1
    
    print(f"Found {len(page_texts)} text strings to translate.")
    print()
    
    # Generate English translations
    print("Generating English translations...")
    english_translations = generate_english_translations(page_texts)
    
    if args.dry_run:
        print("DRY RUN - No files were modified.")
        return 0
    
    # Merge with existing English translations
    print(f"Merging with existing English translations...")
    all_english_translations = merge_with_existing_english(english_translations, english_file)
    
    # Save updated English translations
    print(f"Saving English translations to {english_file}...")
    save_json_file(english_file, all_english_translations)
    
    print(f"✅ Successfully generated {len(english_translations)} English translations!")
    print(f"📝 Total English translations: {len(all_english_translations)}")
    
    return 0

if __name__ == '__main__':
    exit(main())
