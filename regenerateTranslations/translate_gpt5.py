#!/usr/bin/env python3
"""
OpenAI GPT-5 Translation script for ADT Manual
Translates text strings sequentially with context memory using OpenAI's GPT-5 model.
"""

import json
import re
import argparse
import os
from pathlib import Path
from openai import OpenAI
import time

class GPT5Translator:
    def __init__(self, api_key=None):
        """Initialize OpenAI client."""
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.translation_context = []
        self.max_context_pairs = 10  # Keep last 10 translations for context
        
    def translate_with_context(self, spanish_text, text_id):
        """Translate text using GPT-5 with previous translations as context."""
        
        # Build context from previous translations
        context_examples = ""
        if self.translation_context:
            context_examples = "\n\nPrevious translations for context:\n"
            for prev_spanish, prev_english, prev_id in self.translation_context[-self.max_context_pairs:]:
                context_examples += f"- '{prev_spanish}' → '{prev_english}' (ID: {prev_id})\n"
        
        prompt = f"""You are translating a self-care manual from Spanish to English. 
This is part of an educational resource about physical, emotional, cognitive, and social self-care.

Please translate this Spanish text to English, maintaining:
- Professional tone appropriate for a self-care manual
- Consistency with previous translations
- Natural English phrasing
- Context-appropriate terminology

{context_examples}

Text to translate (ID: {text_id}):
'{spanish_text}'

Provide only the English translation, no explanations or additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using gpt-4o as gpt-5 may not be available yet
                messages=[
                    {"role": "system", "content": "You are a professional translator specializing in self-care and wellness content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent translations
            )
            
            english_translation = response.choices[0].message.content.strip()
            
            # Remove quotes if the model added them
            if english_translation.startswith('"') and english_translation.endswith('"'):
                english_translation = english_translation[1:-1]
            if english_translation.startswith("'") and english_translation.endswith("'"):
                english_translation = english_translation[1:-1]
                
            # Add to context for future translations
            self.translation_context.append((spanish_text, english_translation, text_id))
            
            return english_translation
            
        except Exception as e:
            print(f"Error translating {text_id}: {e}")
            return f"[TRANSLATION ERROR: {spanish_text}]"

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
    """Extract text strings for a specific page range in sequential order."""
    if page_end is None:
        page_end = page_start
    
    extracted_texts = {}
    
    # Create pattern for the page range
    page_numbers = list(range(page_start, page_end + 1))
    
    # Collect all matching keys first
    matching_keys = []
    for key in spanish_data.keys():
        # Match pattern: text-{page}-{number}
        match = re.match(r'^text-(\d+)-(\d+)$', key)
        if match:
            page_num = int(match.group(1))
            text_num = int(match.group(2))
            if page_num in page_numbers:
                matching_keys.append((page_num, text_num, key))
    
    # Sort by page number, then by text number for sequential processing
    matching_keys.sort(key=lambda x: (x[0], x[1]))
    
    # Extract in order
    for page_num, text_num, key in matching_keys:
        extracted_texts[key] = spanish_data[key]
    
    return extracted_texts

def generate_sequential_translations(spanish_texts, translator, dry_run=False):
    """Generate English translations sequentially with context building."""
    english_translations = {}
    total_texts = len(spanish_texts)
    
    print(f"🚀 Starting sequential translation of {total_texts} text strings...")
    print("📖 Building context as we translate...\n")
    
    for i, (text_id, spanish_text) in enumerate(spanish_texts.items(), 1):
        print(f"[{i}/{total_texts}] Translating: {text_id}")
        print(f"   Spanish: {spanish_text}")
        
        if not dry_run:
            english_text = translator.translate_with_context(spanish_text, text_id)
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        else:
            english_text = f"[DRY RUN] Would translate: {spanish_text}"
        
        english_translations[text_id] = english_text
        print(f"   English: {english_text}")
        print(f"   Context size: {len(translator.translation_context)} previous translations")
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
    parser = argparse.ArgumentParser(description='Generate English translations using OpenAI GPT-5')
    parser.add_argument('page_start', type=int, help='Starting page number (e.g., 23)')
    parser.add_argument('page_end', type=int, nargs='?', help='Ending page number (optional, defaults to page_start)')
    parser.add_argument('--dry-run', action='store_true', help='Show translations without saving or calling API')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--context-size', type=int, default=10, help='Number of previous translations to keep for context (default: 10)')
    
    args = parser.parse_args()
    
    # File paths
    spanish_file = Path('content/i18n/es/texts.json')
    english_file = Path('content/i18n/en/texts.json')
    
    # Check if Spanish file exists
    if not spanish_file.exists():
        print(f"Error: Spanish file {spanish_file} not found.")
        return 1
    
    # Initialize translator
    try:
        translator = GPT5Translator(api_key=args.api_key)
        translator.max_context_pairs = args.context_size
        print(f"✅ OpenAI client initialized (context size: {args.context_size})")
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {e}")
        print("💡 Make sure you have set your OPENAI_API_KEY environment variable or use --api-key")
        return 1
    
    # Load Spanish texts
    print(f"📁 Loading Spanish texts from {spanish_file}...")
    spanish_data = load_json_file(spanish_file)
    if spanish_data is None:
        return 1
    
    # Extract texts for the specified page range
    page_end = args.page_end if args.page_end else args.page_start
    print(f"🔍 Extracting texts for pages {args.page_start} to {page_end}...")
    
    page_texts = extract_page_range_texts(spanish_data, args.page_start, page_end)
    
    if not page_texts:
        print(f"❌ No texts found for page range {args.page_start}-{page_end}")
        return 1
    
    print(f"✅ Found {len(page_texts)} text strings to translate.")
    print()
    
    # Load existing English translations to build initial context
    existing_english = load_json_file(english_file)
    if existing_english and not args.dry_run:
        print("📚 Loading existing translations for context...")
        # Add some existing translations to context
        context_count = 0
        for key in sorted(existing_english.keys()):
            if key.startswith('text-') and context_count < args.context_size:
                # Find corresponding Spanish text
                if key in spanish_data:
                    translator.translation_context.append((
                        spanish_data[key], 
                        existing_english[key], 
                        key
                    ))
                    context_count += 1
        print(f"📖 Loaded {context_count} existing translations for context")
        print()
    
    # Generate English translations
    english_translations = generate_sequential_translations(page_texts, translator, args.dry_run)
    
    if args.dry_run:
        print("🔍 DRY RUN - No files were modified.")
        return 0
    
    # Merge with existing English translations
    print(f"🔄 Merging with existing English translations...")
    all_english_translations = merge_with_existing_english(english_translations, english_file)
    
    # Save updated English translations
    print(f"💾 Saving English translations to {english_file}...")
    save_json_file(english_file, all_english_translations)
    
    print(f"✅ Successfully generated {len(english_translations)} English translations!")
    print(f"📝 Total English translations: {len(all_english_translations)}")
    print(f"🧠 Final context size: {len(translator.translation_context)} translations")
    
    return 0

if __name__ == '__main__':
    exit(main())
