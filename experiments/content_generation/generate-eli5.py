#!/usr/bin/env python3
"""
ELI5 Generator for HTML Pages

This script:
1. Scans HTML files and extracts all text content via data-id attributes
2. Pulls text from i18n JSON files 
3. Uses GPT to generate "Explain Like I'm 5" simplified explanations
4. Updates the i18n JSON files with new ELI5 content
5. Overwrites existing ELI5 content if it exists

Usage:
    python generate-eli5.py
    python generate-eli5.py --force  # Regenerate all ELI5 content

Requirements:
    pip install openai beautifulsoup4
"""

import os
import glob
import json
import argparse
import re
from typing import List, Optional, Dict

try:
    from bs4 import BeautifulSoup
    from openai import OpenAI
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install openai beautifulsoup4")
    exit(1)


class ELI5Generator:
    def __init__(self, api_key: Optional[str] = None, force_regenerate: bool = False):
        """Initialize the ELI5 generator with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment "
                "variable or pass it directly."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.processed_files = []
        self.updated_sections = []
        self.i18n_data = {}
        self.force_regenerate = force_regenerate
        self.load_i18n_files()
        
    def load_i18n_files(self) -> None:
        """Load existing i18n JSON files."""
        for lang in ['es', 'en']:
            file_path = f"content/i18n/{lang}/texts.json"
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.i18n_data[lang] = json.load(f)
                    print(f"Loaded {lang} translations: "
                          f"{len(self.i18n_data[lang])} entries")
                except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                    self.i18n_data[lang] = {}
            else:
                print(f"i18n file not found: {file_path}")
                self.i18n_data[lang] = {}
    
    def save_i18n_files(self) -> None:
        """Save updated i18n JSON files."""
        for lang in ['es', 'en']:
            if lang in self.i18n_data:
                file_path = f"content/i18n/{lang}/texts.json"
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(self.i18n_data[lang], f, 
                                ensure_ascii=False, indent=2)
                    print(f"Updated {file_path}")
                except Exception as e:
                    print(f"Error saving {file_path}: {e}")
    
    def extract_section_id(self, file_path: str) -> str:
        """Extract section ID from filename (e.g., '26_0_adt.html' -> '26-0')."""
        filename = os.path.basename(file_path)
        # Remove .html extension and _adt suffix
        base_name = filename.replace('.html', '').replace('_adt', '')
        # Convert underscores to dashes for section ID
        section_id = base_name.replace('_', '-')
        return section_id
    
    def find_html_files(self, directory: str = ".") -> List[str]:
        """Find all relevant HTML files in the directory."""
        html_files = []
        for pattern in ["*_adt.html", "index.html"]:
            files = glob.glob(
                os.path.join(directory, pattern), 
                recursive=False
            )
            html_files.extend(files)
        
        # Filter out files in 'old', 'skip', 'assets' directories
        html_files = [
            f for f in html_files 
            if not any(excluded in f for excluded in 
                      ['/old/', '\\old\\', '/skip/', '\\skip\\', 
                       '/assets/', '\\assets\\'])
        ]
        return sorted(html_files)
    
    def extract_text_content(self, file_path: str, lang: str = 'es') -> str:
        """Extract all text content from HTML file using data-id attributes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all elements with data-id attributes that start with 'text-'
            text_elements = soup.find_all(attrs={'data-id': True})
            
            collected_texts = []
            for element in text_elements:
                data_id = element.get('data-id', '')
                if data_id.startswith('text-'):
                    # Get text from i18n data
                    if (lang in self.i18n_data and 
                        data_id in self.i18n_data[lang]):
                        text_content = self.i18n_data[lang][data_id].strip()
                        if text_content:
                            collected_texts.append(text_content)
            
            return ' '.join(collected_texts)
            
        except Exception as e:
            print(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def generate_eli5_explanation(
        self, 
        text_content: str, 
        section_id: str,
        lang: str = "es"
    ) -> Optional[str]:
        """Generate ELI5 explanation using GPT."""
        if not text_content.strip():
            print(f"No text content found for section {section_id}")
            return None
            
        try:
            language_instructions = {
                'es': {
                    'lang_name': 'Spanish',
                    'context_note': 'Este manual es sobre autocuidado en español.',
                    'eli5_intro': 'Imagina que tienes',
                    'example': 'Por ejemplo, si hablas de ejercicio, puedes decir: "Como cuando juegas en el parque y corres mucho, eso ayuda a tu cuerpo a estar fuerte."'
                },
                'en': {
                    'lang_name': 'English',
                    'context_note': 'This manual is about self-care in English.',
                    'eli5_intro': 'Imagine you have',
                    'example': 'For example, if talking about exercise, you could say: "Like when you play at the park and run around a lot, that helps your body stay strong."'
                }
            }
            
            lang_info = language_instructions.get(lang, language_instructions['es'])
            
            prompt = f"""
Please create a short "Explain Like I'm 5" (ELI5) version of the following text about self-care. 

Context: This is from a self-care manual. {lang_info['context_note']}

Original text: {text_content}

Guidelines for ELI5 explanation in {lang_info['lang_name']}:
- Write as if explaining to a 5-year-old child
- Keep it to ONE paragraph maximum (3-5 sentences)
- Use simple words and concepts they can understand
- Include fun emojis throughout (😊 🌟 💪 🎈 🧸 etc.)
- Use analogies with things kids know (toys, games, animals, superheroes, etc.)
- Make it engaging and friendly but CONCISE
- Keep the core message but simplify the language
- Use examples that relate to a child's world
- Start creatively like "{lang_info['eli5_intro']}..." or similar child-friendly opening
- {lang_info['example']}
- Aim for 50-80 words total - short enough to keep a child's attention

Provide only the ELI5 explanation, nothing else.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300,
                temperature=0.7  # Slightly higher for more creative explanations
            )
            
            explanation = response.choices[0].message.content.strip()
            
            # Clean up the explanation
            explanation = explanation.strip('"\'')
            
            print(f"Generated ELI5 for section {section_id} ({lang}): "
                  f"{explanation[:100]}...")
            return explanation
            
        except Exception as e:
            print(f"Error generating ELI5 for section {section_id}: {e}")
            return None
    
    def process_html_file(self, file_path: str) -> bool:
        """Process a single HTML file to generate ELI5 content."""
        print(f"\nProcessing: {file_path}")
        
        # Extract section ID from filename
        section_id = self.extract_section_id(file_path)
        
        # Special handling for index.html
        if 'index.html' in file_path:
            section_id = '0-0'
        
        updated = False
        
        # Process for both languages
        for lang in ['es', 'en']:
            eli5_key = f"sectioneli5-{section_id}"
            
            # Check if ELI5 already exists
            has_eli5 = (lang in self.i18n_data and 
                       eli5_key in self.i18n_data[lang])
            
            if has_eli5 and not self.force_regenerate:
                print(f"  ELI5 already exists for {section_id} ({lang}): "
                      f"{self.i18n_data[lang][eli5_key][:60]}...")
                continue
            
            if has_eli5 and self.force_regenerate:
                print(f"  Forcing regeneration of ELI5 for {section_id} ({lang})")
            else:
                print(f"  Generating new ELI5 for {section_id} ({lang})")
            
            # Extract text content from the page
            text_content = self.extract_text_content(file_path, lang)
            
            if not text_content:
                print(f"  No text content found in {file_path} for {lang}")
                continue
            
            # Generate ELI5 explanation
            eli5_explanation = self.generate_eli5_explanation(
                text_content, section_id, lang
            )
            
            if eli5_explanation:
                # Add to i18n data
                if lang not in self.i18n_data:
                    self.i18n_data[lang] = {}
                
                # Store old explanation for comparison if forcing regeneration
                old_explanation = None
                if self.force_regenerate and eli5_key in self.i18n_data[lang]:
                    old_explanation = self.i18n_data[lang][eli5_key]
                
                self.i18n_data[lang][eli5_key] = eli5_explanation
                
                updated = True
                self.updated_sections.append({
                    'file': file_path,
                    'section_id': section_id,
                    'eli5_key': eli5_key,
                    'lang': lang,
                    'explanation': eli5_explanation,
                    'old_explanation': old_explanation,
                    'force_regenerated': self.force_regenerate and old_explanation is not None
                })
                
                if old_explanation:
                    print(f"  ✓ Updated {lang} ELI5: {eli5_explanation[:60]}...")
                else:
                    print(f"  ✓ Added {lang} ELI5: {eli5_explanation[:60]}...")
            else:
                print(f"  ✗ Failed to generate {lang} ELI5")
        
        if updated and file_path not in self.processed_files:
            self.processed_files.append(file_path)
        
        return updated
    
    def process_all_files(self, directory: str = ".") -> None:
        """Process all HTML files in the directory."""
        html_files = self.find_html_files(directory)
        
        if not html_files:
            print("No HTML files found.")
            return
        
        print(f"Found {len(html_files)} HTML files to process:")
        for file in html_files:
            print(f"  - {file}")
        
        print("\nStarting ELI5 generation...")
        
        any_updated = False
        for file_path in html_files:
            if self.process_html_file(file_path):
                any_updated = True
        
        # Save updated i18n files
        if any_updated:
            self.save_i18n_files()
        
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print a summary of the processing."""
        print(f"\n{'='*60}")
        print("ELI5 GENERATION SUMMARY")
        print(f"{'='*60}")
        print(f"HTML files processed: {len(self.processed_files)}")
        print(f"ELI5 explanations generated: {len(self.updated_sections)}")
        
        if self.force_regenerate:
            regenerated_count = sum(1 for section in self.updated_sections 
                                   if section.get('force_regenerated', False))
            print(f"Forced regenerations: {regenerated_count}")
        
        if self.updated_sections:
            print("\nGenerated ELI5 explanations:")
            for section in self.updated_sections:
                print(f"  📁 {section['file']}")
                print(f"     🔑 {section['eli5_key']} ({section['lang']})")
                
                if section.get('force_regenerated', False):
                    print(f"     🔄 OLD: {section['old_explanation'][:60]}...")
                    print(f"     ✨ NEW: {section['explanation'][:60]}...")
                else:
                    print(f"     📝 {section['explanation'][:80]}...")
                print()
        
        if self.processed_files:
            print("Files with ELI5 content generated:")
            for file in self.processed_files:
                print(f"  - {file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate ELI5 explanations for HTML page content"
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force regeneration of existing ELI5 explanations'
    )
    
    args = parser.parse_args()
    
    print("ELI5 Generator for Self-Care Manual")
    print("="*50)
    
    if args.force:
        print("🔄 Force regeneration mode enabled - "
              "will regenerate ALL ELI5 explanations")
        print()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OpenAI API key not found!")
        print("Please set your OpenAI API key as an environment variable:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        generator = ELI5Generator(force_regenerate=args.force)
        generator.process_all_files()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
