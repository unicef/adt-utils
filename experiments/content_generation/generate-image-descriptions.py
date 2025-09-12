#!/usr/bin/env python3
"""
Image Description Generator for HTML Files

This script:
1. Scans all HTML files for images
2. Checks if images have alt text descriptions via data-id and i18n files
3. Uses GPT to generate descriptions for images without alt text
4. Updates the i18n JSON files with new descriptions
5. Removes redundant aria-label attributes when alt text exists

Usage:
    python generate-image-descriptions.py

Requirements:
    pip install openai beautifulsoup4 requests pillow
"""

import os
import glob
import base64
import json
import argparse
from typing import List, Optional, Dict
import requests
from PIL import Image
from io import BytesIO

try:
    from bs4 import BeautifulSoup
    from openai import OpenAI
except ImportError:
    print("Required packages not installed. Please run:")
    print("pip install openai beautifulsoup4 requests pillow")
    exit(1)


class ImageDescriptionGenerator:
    def __init__(self, api_key: Optional[str] = None, force_regenerate: bool = False):
        """Initialize the generator with OpenAI API key."""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment "
                "variable or pass it directly."
            )
        
        self.client = OpenAI(api_key=self.api_key)
        self.processed_files = []
        self.updated_images = []
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
                    print(f"Loaded {lang} translations: {len(self.i18n_data[lang])} entries")
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
                        json.dump(self.i18n_data[lang], f, ensure_ascii=False, indent=2)
                    print(f"Updated {file_path}")
                except Exception as e:
                    print(f"Error saving {file_path}: {e}")
    
    def get_context_from_i18n(self, data_id: str, lang: str = 'es') -> str:
        """Get context text from i18n data based on data-id."""
        if lang not in self.i18n_data:
            return ""
        
        # Look for related text elements around the image
        context_parts = []
        
        # Extract the base pattern (e.g., "img-10-1" -> "10")
        if data_id.startswith('img-'):
            parts = data_id.split('-')
            if len(parts) >= 2:
                page_num = parts[1]
                
                # Look for text elements from the same page
                for key, value in self.i18n_data[lang].items():
                    if (key.startswith(f'text-{page_num}-') and 
                        isinstance(value, str) and 
                        len(value.strip()) > 0):
                        context_parts.append(value.strip())
                        if len(context_parts) >= 3:  # Limit context
                            break
        
        return " ".join(context_parts)
    
    def find_html_files(self, directory: str = ".") -> List[str]:
        """Find all HTML files in the directory."""
        html_files = []
        for pattern in ["*.html", "**/*.html"]:
            files = glob.glob(
                os.path.join(directory, pattern), 
                recursive=True
            )
            html_files.extend(files)
        
        # Filter out files in 'old' directory
        html_files = [
            f for f in html_files 
            if '/old/' not in f and '\\old\\' not in f
        ]
        return sorted(html_files)
    
    def encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Encode image to base64 for GPT Vision API."""
        try:
            # Handle both local paths and URLs
            if image_path.startswith(('http://', 'https://')):
                response = requests.get(image_path)
                Image.open(BytesIO(response.content))  # Validate image
                return base64.b64encode(response.content).decode('utf-8')
            else:
                # Convert relative path to absolute
                if not os.path.isabs(image_path):
                    image_path = os.path.join(
                        os.getcwd(), 
                        image_path.lstrip('./')
                    )
                
                if not os.path.exists(image_path):
                    print(f"Warning: Image file not found: {image_path}")
                    return None
                
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                    return base64.b64encode(image_data).decode('utf-8')
                    
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None
    
    def generate_image_description(
        self, 
        image_path: str, 
        context: str = "",
        lang: str = "es"
    ) -> Optional[str]:
        """Generate image description using GPT Vision."""
        try:
            base64_image = self.encode_image_to_base64(image_path)
            if not base64_image:
                return None
            
            # Determine image format
            image_format = "jpeg"
            if image_path.lower().endswith('.png'):
                image_format = "png"
            elif image_path.lower().endswith('.gif'):
                image_format = "gif"
            elif image_path.lower().endswith('.webp'):
                image_format = "webp"
            
            language_instructions = {
                'es': {
                    'lang_name': 'Spanish',
                    'context_note': 'Este manual es en español.',
                    'example_format': 'Ejemplo: "Ilustración de una mujer meditando en posición de loto"'
                },
                'en': {
                    'lang_name': 'English', 
                    'context_note': 'This manual is in English.',
                    'example_format': 'Example: "Illustration of a woman meditating in lotus position"'
                }
            }
            
            lang_info = language_instructions.get(lang, language_instructions['es'])
            
            prompt = f"""
Please provide a descriptive alt text for this image for accessibility purposes.

Context: This image appears in a self-care manual (Manual de Autocuidado).
{lang_info['context_note']}

Content context: {context if context else "No additional context available."}

Guidelines:
- Aim for under 125 characters, but go longer if absolutely necessary for clarity
- Be descriptive and focus on essential visual content
- Use {lang_info['lang_name']} language
- Start with "Imagen: " or "Ilustración: " as appropriate
- Don't be overly verbose but ensure key elements are described
- {lang_info['example_format']}

Provide only the alt text description, nothing else.
"""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4 with vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};"
                                           f"base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=200,  # Increased for longer descriptions if needed
                temperature=0.3
            )
            
            description = response.choices[0].message.content.strip()
            
            # Clean up the description
            description = description.strip('"\'')
            
            print(f"Generated description for "
                  f"{os.path.basename(image_path)} ({lang}): {description}")
            return description
            
        except Exception as e:
            print(f"Error generating description for {image_path}: {e}")
            return None
    
    def process_html_file(self, file_path: str) -> bool:
        """Process a single HTML file."""
        print(f"\nProcessing: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            images = soup.find_all('img')
            
            if not images:
                print(f"  No images found in {file_path}")
                return False
            
            updated = False
            
            for img in images:
                src = img.get('src', '')
                data_id = img.get('data-id', '')
                aria_label = img.get('aria-label', '').strip()
                
                print(f"  Found image: {src} (data-id: {data_id})")
                
                # Check if image has description in i18n files
                has_description = False
                if data_id:
                    for lang in ['es', 'en']:
                        if (lang in self.i18n_data and 
                            data_id in self.i18n_data[lang]):
                            has_description = True
                            if not self.force_regenerate:
                                print(f"    ✓ Description exists in {lang}: "
                                      f"{self.i18n_data[lang][data_id][:60]}...")
                            else:
                                print(f"    ⚠️  Forcing regeneration of existing {lang} description: "
                                      f"{self.i18n_data[lang][data_id][:60]}...")
                            break
                
                # Generate description if missing or if force_regenerate is True
                if (not has_description or self.force_regenerate) and data_id:
                    if not has_description:
                        print("    Missing description, generating...")
                    else:
                        print("    Forcing regeneration of description...")
                    
                    # Get context from i18n data
                    for lang in ['es', 'en']:
                        context = self.get_context_from_i18n(data_id, lang)
                        
                        description = self.generate_image_description(
                            src, context, lang
                        )
                        
                        if description:
                            # Add to i18n data
                            if lang not in self.i18n_data:
                                self.i18n_data[lang] = {}
                            
                            # Store old description for comparison if forcing regeneration
                            old_description = None
                            if self.force_regenerate and data_id in self.i18n_data[lang]:
                                old_description = self.i18n_data[lang][data_id]
                            
                            self.i18n_data[lang][data_id] = description
                            
                            updated = True
                            self.updated_images.append({
                                'file': file_path,
                                'src': src,
                                'data_id': data_id,
                                'lang': lang,
                                'description': description,
                                'old_description': old_description,
                                'force_regenerated': self.force_regenerate and old_description is not None
                            })
                            
                            if old_description:
                                print(f"    ✓ Updated {lang} description: {description}")
                            else:
                                print(f"    ✓ Added {lang} description: {description}")
                        else:
                            print(f"    ✗ Failed to generate {lang} description")
                
                # Remove redundant accessibility attributes if description exists in i18n
                if has_description:
                    removed_attrs = []
                    
                    # Remove aria-label if it exists and is redundant
                    if aria_label:
                        if (aria_label.lower().startswith('imagen') or
                            aria_label.lower().startswith('image') or
                            aria_label.lower().startswith('ilustraci')):
                            
                            del img['aria-label']
                            removed_attrs.append(f"aria-label: {aria_label}")
                            updated = True
                    
                    # Remove data-aria-id since we have proper i18n descriptions
                    data_aria_id = img.get('data-aria-id', '').strip()
                    if data_aria_id:
                        del img['data-aria-id']
                        removed_attrs.append(f"data-aria-id: {data_aria_id}")
                        updated = True
                    
                    if removed_attrs:
                        print(f"    Removed redundant attributes: {', '.join(removed_attrs)}")
            
            # Save the updated HTML file (mainly for aria-label removal)
            if updated:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"  ✓ Updated HTML file: {file_path}")
                if file_path not in self.processed_files:
                    self.processed_files.append(file_path)
                
            return updated
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return False
    
    def process_all_files(self, directory: str = ".") -> None:
        """Process all HTML files in the directory."""
        html_files = self.find_html_files(directory)
        
        if not html_files:
            print("No HTML files found.")
            return
        
        print(f"Found {len(html_files)} HTML files to process:")
        for file in html_files:
            print(f"  - {file}")
        
        print("\nStarting processing...")
        
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
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"HTML files processed: {len(self.processed_files)}")
        print(f"Image descriptions generated: {len(self.updated_images)}")
        
        if self.force_regenerate:
            regenerated_count = sum(1 for img in self.updated_images if img.get('force_regenerated', False))
            print(f"Forced regenerations: {regenerated_count}")
        
        if self.updated_images:
            print("\nGenerated descriptions:")
            for img in self.updated_images:
                print(f"  📁 {img['file']}")
                print(f"     🖼️  {img['src']}")
                print(f"     🔑 {img['data_id']} ({img['lang']})")
                
                if img.get('force_regenerated', False):
                    print(f"     🔄 OLD: {img['old_description']}")
                    print(f"     ✨ NEW: {img['description']}")
                else:
                    print(f"     📝 {img['description']}")
                print()
        
        if self.processed_files:
            print("Modified files:")
            for file in self.processed_files:
                print(f"  - {file}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate alt text descriptions for images in HTML files using AI"
    )
    parser.add_argument(
        '--force', 
        action='store_true',
        help='Force regeneration of existing image descriptions'
    )
    
    args = parser.parse_args()
    
    print("Image Description Generator for HTML Files")
    print("="*50)
    
    if args.force:
        print("🔄 Force regeneration mode enabled - will regenerate ALL image descriptions")
        print()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️  OpenAI API key not found!")
        print("Please set your OpenAI API key as an environment variable:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        generator = ImageDescriptionGenerator(force_regenerate=args.force)
        generator.process_all_files()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
