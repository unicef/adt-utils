#!/usr/bin/env python3
"""
JSON Translation Script

Translates JSON files containing key-value pairs to multiple target languages using OpenAI.
Creates translated files in language-specific directories.

Usage:
    python translate_json.py input.json --input-language es --output-languages en,pt,ur
    python translate_json.py texts.json --input-language en --output-languages es,fr --api-key sk-xxx
"""

import json
import argparse
import os
import time
from pathlib import Path
from openai import OpenAI
from typing import Dict, List
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class JSONTranslator:
    def __init__(self, input_language: str, api_key: str = None):
        """Initialize OpenAI client with input language configuration."""
        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()
        self.input_language = input_language

        # Language configuration
        self.lang_config = {
            "sq": "Albanian",
            "am": "Amharic",
            "ar": "Arabic",
            "hy": "Armenian",
            "bn": "Bengali",
            "bs": "Bosnian",
            "bg": "Bulgarian",
            "my": "Burmese",
            "ca": "Catalan",
            "zh": "Chinese",
            "hr": "Croatian",
            "cs": "Czech",
            "cus": "Cushitic",
            "da": "Danish",
            "dz": "Dzongkha",
            "nl": "Dutch",
            "en": "English",
            "et": "Estonian",
            "fi": "Finnish",
            "fr": "French",
            "ka": "Georgian",
            "de": "German",
            "el": "Greek",
            "gu": "Gujarati",
            "ht": "Haitian",
            "he": "Hebrew",
            "hi": "Hindi",
            "hmn": "Hmong",
            "hu": "Hungarian",
            "is": "Icelandic",
            "id": "Indonesian",
            "it": "Italian",
            "ja": "Japanese",
            "kn": "Kannada",
            "kk": "Kazakh",
            "ko": "Korean",
            "lv": "Latvian",
            "lt": "Lithuanian",
            "mk": "Macedonian",
            "ml": "Malayalam",
            "ms": "Malay",
            "mi": "Te Reo Maori",
            "mr": "Marathi",
            "mn": "Mongolian",
            "ne": "Nepali",
            "no": "Norwegian",
            "pa": "Punjabi",
            "pl": "Polish",
            "pt": "Portuguese",
            "ro": "Romanian",
            "ru": "Russian",
            "sr": "Serbian",
            "sk": "Slovak",
            "sl": "Slovenian",
            "so": "Somali",
            "es": "Spanish",
            "sw": "Swahili",
            "sv": "Swedish",
            "ta": "Tamil",
            "te": "Telugu",
            "th": "Thai",
            "tl": "Tagalog",
            "tr": "Turkish",
            "uk": "Ukrainian",
            "ur": "Urdu",
            "vi": "Vietnamese",
        }

    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from code."""
        return self.lang_config.get(lang_code, lang_code.upper())

    def translate_text(
        self, text: str, target_language: str, text_key: str = ""
    ) -> str:
        """Translate a single text string to target language."""

        input_lang_name = self.get_language_name(self.input_language)
        target_lang_name = self.get_language_name(target_language)

        prompt = f"""You are translating content from {input_lang_name} to {target_lang_name}.

Please translate this {input_lang_name} text to {target_lang_name}, maintaining:
- Natural {target_lang_name} phrasing
- Appropriate tone and context
- Accuracy of meaning

Text to translate (Key: {text_key}):
'{text}'

Provide only the {target_lang_name} translation, no explanations or additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator translating from {input_lang_name} to {target_lang_name}.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )

            translation = response.choices[0].message.content.strip()

            # Remove quotes if the model added them
            if translation.startswith('"') and translation.endswith('"'):
                translation = translation[1:-1]
            if translation.startswith("'") and translation.endswith("'"):
                translation = translation[1:-1]

            return translation

        except Exception as e:
            print(f"Error translating key '{text_key}': {e}")
            return f"[TRANSLATION ERROR: {text}]"

    def translate_json_data(
        self, data: Dict[str, str], target_language: str
    ) -> Dict[str, str]:
        """Translate all values in a JSON dictionary to target language in one API call."""
        input_lang_name = self.get_language_name(self.input_language)
        target_lang_name = self.get_language_name(target_language)

        print(
            f"🚀 Translating {len(data)} items from {input_lang_name} to {target_lang_name} in batch..."
        )

        # Create JSON string for the prompt
        json_string = json.dumps(data, ensure_ascii=False, indent=2)

        prompt = f"""You are translating a JSON file from {input_lang_name} to {target_lang_name}.

Translate ALL the values in this JSON object from {input_lang_name} to {target_lang_name}, maintaining:
- Natural {target_lang_name} phrasing
- Appropriate tone and context
- Accuracy of meaning
- The exact same JSON structure and keys

Input JSON:
{json_string}

Return ONLY the translated JSON with the same structure and keys, but with all values translated to {target_lang_name}. Do not include any explanations or additional text."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator. You translate JSON files from {input_lang_name} to {target_lang_name}, preserving the structure but translating all values.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=4000,
                temperature=0.3,
            )

            translation_text = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if translation_text.startswith("```json"):
                translation_text = translation_text[7:]
            if translation_text.startswith("```"):
                translation_text = translation_text[3:]
            if translation_text.endswith("```"):
                translation_text = translation_text[:-3]

            # Parse the translated JSON
            translated_data = json.loads(translation_text.strip())

            print(f"✅ Successfully translated {len(translated_data)} items")
            return translated_data

        except json.JSONDecodeError as e:
            print(f"❌ Error parsing translated JSON: {e}")
            print("📝 Raw response (first 500 chars):")
            print(
                translation_text[:500] + "..."
                if len(translation_text) > 500
                else translation_text
            )
            print("\n🔄 Falling back to individual translation...")
            return self.translate_json_data_individually(data, target_language)

        except Exception as e:
            print(f"❌ Error in batch translation: {e}")
            print("🔄 Falling back to individual translation...")
            return self.translate_json_data_individually(data, target_language)

    def translate_json_data_individually(
        self, data: Dict[str, str], target_language: str
    ) -> Dict[str, str]:
        """Translate all values in a JSON dictionary to target language."""
        translated_data = {}
        total_items = len(data)

        input_lang_name = self.get_language_name(self.input_language)
        target_lang_name = self.get_language_name(target_language)

        print(
            f"🚀 Translating {total_items} items from {input_lang_name} to {target_lang_name}..."
        )

        for i, (key, value) in enumerate(data.items(), 1):
            print(f"[{i}/{total_items}] Translating key: {key}")
            print(f"   {input_lang_name}: {value}")

            if isinstance(value, str) and value.strip():
                translated_value = self.translate_text(value, target_language, key)
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            else:
                translated_value = value  # Keep non-string values as is

            translated_data[key] = translated_value
            print(f"   {target_lang_name}: {translated_value}")
            print()

        return translated_data


def load_json_file(file_path: Path) -> Dict:
    """Load JSON file and return the data."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File {file_path} not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {file_path}: {e}")
        return None


def save_json_file(file_path: Path, data: Dict):
    """Save data to JSON file with proper formatting."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)


def check_existing_translation(input_file: Path, target_lang: str) -> bool:
    """Check if translation already exists and has content."""
    output_dir = input_file.parent / target_lang
    output_file = output_dir / input_file.name

    if not output_file.exists():
        return False

    try:
        with open(output_file, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

        # Check if it's not empty and has meaningful content
        if not existing_data:
            return False

        # Check if it's not just an empty array or object with null values
        if isinstance(existing_data, list) and len(existing_data) == 0:
            return False

        if isinstance(existing_data, dict):
            # Check if all values are null or empty
            non_empty_values = [
                v for v in existing_data.values() if v and str(v).strip()
            ]
            if len(non_empty_values) == 0:
                return False

        print(f"✅ Translation already exists for {target_lang}: {output_file}")
        return True

    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️  Existing file {output_file} is corrupted: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Translate JSON files to multiple languages using OpenAI"
    )
    parser.add_argument("input_file", type=str, help="Input JSON file path")
    parser.add_argument(
        "--input-language",
        type=str,
        required=True,
        help="Input language code (e.g., es, en)",
    )
    parser.add_argument(
        "--output-languages",
        type=str,
        required=True,
        help="Comma-separated target language codes (e.g., en,pt,ur)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenAI API key (or set OPENAI_API_KEY environment variable)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be translated without calling API",
    )

    args = parser.parse_args()

    # Validate input file
    input_file = Path(args.input_file)
    if not input_file.exists():
        print(f"❌ Error: Input file '{input_file}' does not exist.")
        return 1

    # Parse output languages
    output_languages = [
        lang.strip() for lang in args.output_languages.split(",") if lang.strip()
    ]
    if not output_languages:
        print("❌ Error: No valid output languages specified.")
        return 1

    # Initialize translator
    try:
        translator = JSONTranslator(
            input_language=args.input_language, api_key=args.api_key
        )
        input_lang_name = translator.get_language_name(args.input_language)
        print(f"✅ OpenAI client initialized")
        print(f"📝 Input language: {input_lang_name}")
        print(
            f"🎯 Output languages: {', '.join([translator.get_language_name(lang) for lang in output_languages])}"
        )
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {e}")
        print(
            "💡 Make sure you have set your OPENAI_API_KEY environment variable or use --api-key"
        )
        return 1

    # Load input JSON
    print(f"📁 Loading input file: {input_file}")
    input_data = load_json_file(input_file)
    if input_data is None:
        return 1

    print(f"✅ Loaded {len(input_data)} items from input file")
    print()

    if args.dry_run:
        print("🔍 DRY RUN - Showing what would be translated:")
        for key, value in list(input_data.items())[:3]:  # Show first 3 items
            print(f"  {key}: {value}")
        if len(input_data) > 3:
            print(f"  ... and {len(input_data) - 3} more items")
        print()
        return 0

    # Process each target language
    for target_lang in output_languages:
        print(
            f"🌍 Processing language: {translator.get_language_name(target_lang)} ({target_lang})"
        )

        # Check if translation already exists
        if check_existing_translation(input_file, target_lang):
            print(f"⏭️  Skipping {target_lang} - translation already exists")
            continue

        # Create output directory and file path
        output_dir = input_file.parent / target_lang
        output_file = output_dir / input_file.name

        # Translate data
        translated_data = translator.translate_json_data(input_data, target_lang)

        # Save translated file
        print(f"💾 Saving translated file: {output_file}")
        save_json_file(output_file, translated_data)

        print(
            f"✅ Successfully created {translator.get_language_name(target_lang)} translation!"
        )
        print(f"📁 Saved to: {output_file}")
        print("-" * 50)
        print()

    print(
        f"🎉 Translation complete! Generated files for {len(output_languages)} languages."
    )
    return 0


if __name__ == "__main__":
    exit(main())
