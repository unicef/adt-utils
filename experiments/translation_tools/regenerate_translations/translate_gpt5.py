#!/usr/bin/env python3
"""
OpenAI GPT Translation script for ADT Manual
Translates text strings sequentially with context memory using OpenAI's GPT models.
Supports multiple source and target languages with configurable paths.
"""

import json
import re
import argparse
import os
from pathlib import Path
from openai import OpenAI
import time

class GPTTranslator:
    def __init__(self, source_lang="es", target_lang="en", api_key=None):
        """Initialize OpenAI client with language configuration."""
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translation_context = []
        self.max_context_pairs = 10  # Keep last 10 translations for context
        
        # Language configuration
        self.lang_config = {
            'es': {
                'name': 'Spanish',
                'context_description': 'self-care manual from Spanish'
            },
            'en': {
                'name': 'English', 
                'context_description': 'self-care manual to English'
            },
            'fr': {
                'name': 'French',
                'context_description': 'self-care manual to French'
            },
            'pt': {
                'name': 'Portuguese',
                'context_description': 'self-care manual to Portuguese'
            }
        }
        
    def get_language_name(self, lang_code):
        """Get full language name from code."""
        return self.lang_config.get(lang_code, {}).get('name', lang_code.upper())
        
    def translate_with_context(self, source_text, text_id):
        """Translate text using GPT with previous translations as context."""
        
        source_lang_name = self.get_language_name(self.source_lang)
        target_lang_name = self.get_language_name(self.target_lang)
        
        # Build context from previous translations
        context_examples = ""
        if self.translation_context:
            context_examples = f"\n\nPrevious translations for context:\n"
            for prev_source, prev_target, prev_id in self.translation_context[-self.max_context_pairs:]:
                context_examples += f"- '{prev_source}' → '{prev_target}' (ID: {prev_id})\n"
        
        prompt = f"""You are translating a self-care manual from {source_lang_name} to {target_lang_name}. 
This is part of an educational resource about physical, emotional, cognitive, and social self-care.

Please translate this {source_lang_name} text to {target_lang_name}, maintaining:
- Professional tone appropriate for a self-care manual
- Consistency with previous translations
- Natural {target_lang_name} phrasing
- Context-appropriate terminology

{context_examples}

Text to translate (ID: {text_id}):
'{source_text}'

Provide only the {target_lang_name} translation, no explanations or additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using gpt-4o as it's currently the most capable model
                messages=[
                    {"role": "system", "content": f"You are a professional translator specializing in self-care and wellness content, translating from {source_lang_name} to {target_lang_name}."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3  # Lower temperature for more consistent translations
            )
            
            target_translation = response.choices[0].message.content.strip()
            
            # Remove quotes if the model added them
            if target_translation.startswith('"') and target_translation.endswith('"'):
                target_translation = target_translation[1:-1]
            if target_translation.startswith("'") and target_translation.endswith("'"):
                target_translation = target_translation[1:-1]
                
            # Add to context for future translations
            self.translation_context.append((source_text, target_translation, text_id))
            
            return target_translation
            
        except Exception as e:
            print(f"Error translating {text_id}: {e}")
            return f"[TRANSLATION ERROR: {source_text}]"

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

def extract_page_range_texts(source_data, page_start, page_end=None):
    """Extract text strings for a specific page range in sequential order."""
    if page_end is None:
        page_end = page_start
    
    extracted_texts = {}
    
    # Create pattern for the page range
    page_numbers = list(range(page_start, page_end + 1))
    
    # Collect all matching keys first
    matching_keys = []
    for key in source_data.keys():
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
        extracted_texts[key] = source_data[key]
    
    return extracted_texts

def generate_sequential_translations(source_texts, translator, dry_run=False):
    """Generate target language translations sequentially with context building."""
    target_translations = {}
    total_texts = len(source_texts)
    
    source_lang_name = translator.get_language_name(translator.source_lang)
    target_lang_name = translator.get_language_name(translator.target_lang)
    
    print(f"🚀 Starting sequential translation of {total_texts} text strings...")
    print(f"📖 Translating from {source_lang_name} to {target_lang_name}...")
    print("📖 Building context as we translate...\n")
    
    for i, (text_id, source_text) in enumerate(source_texts.items(), 1):
        print(f"[{i}/{total_texts}] Translating: {text_id}")
        print(f"   {source_lang_name}: {source_text}")
        
        if not dry_run:
            target_text = translator.translate_with_context(source_text, text_id)
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        else:
            target_text = f"[DRY RUN] Would translate: {source_text}"
        
        target_translations[text_id] = target_text
        print(f"   {target_lang_name}: {target_text}")
        print(f"   Context size: {len(translator.translation_context)} previous translations")
        print()
    
    return target_translations

def merge_with_existing_translations(new_translations, target_file_path):
    """Merge new translations with existing target language translations."""
    existing_translations = load_json_file(target_file_path)
    if existing_translations is None:
        existing_translations = {}
    
    # Update existing translations with new ones
    existing_translations.update(new_translations)
    
    return existing_translations

def main():
    parser = argparse.ArgumentParser(description='Generate translations using OpenAI GPT models')
    parser.add_argument('target_dir', help='Target directory containing content/i18n/ structure')
    parser.add_argument('page_start', type=int, help='Starting page number (e.g., 23)')
    parser.add_argument('page_end', type=int, nargs='?', help='Ending page number (optional, defaults to page_start)')
    parser.add_argument('--source-lang', type=str, default='es', help='Source language code (default: es)')
    parser.add_argument('--target-lang', type=str, default='en', help='Target language code (default: en)')
    parser.add_argument('--dry-run', action='store_true', help='Show translations without saving or calling API')
    parser.add_argument('--api-key', type=str, help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    parser.add_argument('--context-size', type=int, default=10, help='Number of previous translations to keep for context (default: 10)')
    
    args = parser.parse_args()
    
    # Setup paths
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"❌ Error: Target directory '{target_dir}' does not exist.")
        return 1
    
    # File paths
    source_file = target_dir / 'content' / 'i18n' / args.source_lang / 'texts.json'
    target_file = target_dir / 'content' / 'i18n' / args.target_lang / 'texts.json'
    
    # Check if source file exists
    if not source_file.exists():
        print(f"❌ Error: Source file {source_file} not found.")
        return 1
    
    # Initialize translator
    try:
        translator = GPTTranslator(
            source_lang=args.source_lang,
            target_lang=args.target_lang,
            api_key=args.api_key
        )
        translator.max_context_pairs = args.context_size
        
        source_lang_name = translator.get_language_name(args.source_lang)
        target_lang_name = translator.get_language_name(args.target_lang)
        
        print(f"✅ OpenAI client initialized")
        print(f"📝 Translation: {source_lang_name} → {target_lang_name}")
        print(f"🧠 Context size: {args.context_size}")
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {e}")
        print("💡 Make sure you have set your OPENAI_API_KEY environment variable or use --api-key")
        return 1
    
    # Load source texts
    print(f"📁 Loading {translator.get_language_name(args.source_lang)} texts from {source_file}...")
    source_data = load_json_file(source_file)
    if source_data is None:
        return 1
    
    # Extract texts for the specified page range
    page_end = args.page_end if args.page_end else args.page_start
    print(f"🔍 Extracting texts for pages {args.page_start} to {page_end}...")
    
    page_texts = extract_page_range_texts(source_data, args.page_start, page_end)
    
    if not page_texts:
        print(f"❌ No texts found for page range {args.page_start}-{page_end}")
        return 1
    
    print(f"✅ Found {len(page_texts)} text strings to translate.")
    print()
    
    # Load existing target translations to build initial context
    existing_target = load_json_file(target_file)
    if existing_target and not args.dry_run:
        print(f"📚 Loading existing {translator.get_language_name(args.target_lang)} translations for context...")
        # Add some existing translations to context
        context_count = 0
        for key in sorted(existing_target.keys()):
            if key.startswith('text-') and context_count < args.context_size:
                # Find corresponding source text
                if key in source_data:
                    translator.translation_context.append((
                        source_data[key], 
                        existing_target[key], 
                        key
                    ))
                    context_count += 1
        print(f"📖 Loaded {context_count} existing translations for context")
        print()
    
    # Generate target translations
    target_translations = generate_sequential_translations(page_texts, translator, args.dry_run)
    
    if args.dry_run:
        print("🔍 DRY RUN - No files were modified.")
        return 0
    
    # Merge with existing target translations
    print(f"🔄 Merging with existing {translator.get_language_name(args.target_lang)} translations...")
    all_target_translations = merge_with_existing_translations(target_translations, target_file)
    
    # Save updated target translations
    print(f"💾 Saving {translator.get_language_name(args.target_lang)} translations to {target_file}...")
    save_json_file(target_file, all_target_translations)
    
    print(f"✅ Successfully generated {len(target_translations)} {translator.get_language_name(args.target_lang)} translations!")
    print(f"📝 Total {translator.get_language_name(args.target_lang)} translations: {len(all_target_translations)}")
    print(f"🧠 Final context size: {len(translator.translation_context)} translations")
    
    return 0

if __name__ == '__main__':
    exit(main())
