#!/usr/bin/env python3
"""
HTML Text Restructuring Script

This script restructures HTML content by:
1. Wrapping text content in <span> tags with data-id attributes
2. Moving data-id from <p> tags to <span> tags
3. Intelligently grouping related spans into paragraphs based on content analysis

Usage:
    python restructure_text.py <start_page> <end_page> [options]
    
Example:
    python restructure_text.py 6 58
    python restructure_text.py 10 15 --output-dir ./output
"""

import argparse
import json
import os
import re
import glob
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
import string


class TextRestructurer:
    def __init__(self, output_dir="./output", texts_json_path=None):
        self.output_dir = Path(output_dir)
        self.texts_json_path = (texts_json_path or
                                self.output_dir / "content/i18n/es/texts.json")
        self.texts_data = self.load_texts_data()
        
        # Download required NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            print("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt')
    
    def load_texts_data(self):
        """Load text data from JSON for analysis"""
        try:
            with open(self.texts_json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Could not load texts from {self.texts_json_path}")
            return {}
    
    def get_file_list(self, start_page, end_page):
        """Generate list of files to process"""
        files = []
        for page_num in range(start_page, end_page + 1):
            pattern = f"{page_num}_*_adt.html"
            matching_files = glob.glob(str(self.output_dir / pattern))
            files.extend(matching_files)
        return sorted(files)
    
    def analyze_text_content(self, text):
        """Analyze text to determine its characteristics"""
        if not text or not text.strip():
            return {'word_count': 0, 'sentence_count': 0, 'is_short': True}
        
        # Clean text
        clean_text = text.strip()
        
        # Count words and sentences
        words = word_tokenize(clean_text)
        word_count = len([w for w in words if w not in string.punctuation])
        
        try:
            sentences = sent_tokenize(clean_text)
            sentence_count = len(sentences)
        except Exception:
            # Fallback sentence counting
            sentence_count = len([s for s in clean_text.split('.')
                                 if s.strip()])
        
        # Determine if it's a short text (likely a title, list item, etc.)
        is_short = word_count <= 5 or sentence_count <= 1 and word_count <= 10
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'is_short': is_short,
            'text': clean_text
        }
    
    def should_group_texts(self, text1_info, text2_info):
        """Determine if two text elements should be grouped in same paragraph"""
        # Don't group if either is very short (likely title/list item)
        if text1_info['is_short'] or text2_info['is_short']:
            return False
        
        # Group if both are substantial sentences
        if (text1_info['sentence_count'] >= 1 and text2_info['sentence_count'] >= 1 and
            text1_info['word_count'] >= 10 and text2_info['word_count'] >= 10):
            return True
        
        # Group if combined they make a reasonable paragraph
        total_words = text1_info['word_count'] + text2_info['word_count']
        if total_words >= 15 and total_words <= 100:
            return True
        
        return False
    
    def extract_text_and_data_id(self, element):
        """Extract text content and data-id from an element"""
        if not element:
            return None, None
        
        # Get data-id
        data_id = element.get('data-id')
        
        # Get text content
        if element.string:
            text = element.string.strip()
        else:
            text = element.get_text(strip=True)
        
        return text, data_id
    
    def create_span_with_data_id(self, soup, text, data_id, additional_attrs=None):
        """Create a span element with text and data-id"""
        span = soup.new_tag('span')
        if data_id:
            span['data-id'] = data_id
        
        # Add any additional attributes
        if additional_attrs:
            for attr, value in additional_attrs.items():
                span[attr] = value
        
        span.string = text
        return span
    
    def process_paragraph_element(self, soup, p_element):
        """Process a single paragraph element"""
        if not p_element or p_element.name != 'p':
            return None
        
        # Extract text and data-id
        text, data_id = self.extract_text_and_data_id(p_element)
        
        if not text:
            return None
        
        # Preserve important attributes (except data-id which goes to span)
        preserved_attrs = {}
        for attr in ['class', 'aria-label', 'data-aria-id', 'tabindex', 'role']:
            if p_element.get(attr):
                preserved_attrs[attr] = p_element[attr]
        
        # Create new paragraph with span inside
        new_p = soup.new_tag('p')
        for attr, value in preserved_attrs.items():
            new_p[attr] = value
        
        # Create span with the text and data-id
        span = self.create_span_with_data_id(soup, text, data_id)
        new_p.append(span)
        
        return new_p, self.analyze_text_content(text)
    
    def group_consecutive_paragraphs(self, soup, paragraph_list):
        """Group consecutive paragraphs that should be combined"""
        if not paragraph_list:
            return []
        
        grouped = []
        current_group = [paragraph_list[0]]
        
        for i in range(1, len(paragraph_list)):
            current_p, current_info = paragraph_list[i]
            prev_p, prev_info = paragraph_list[i-1]
            
            # Check if current should be grouped with previous
            if self.should_group_texts(prev_info, current_info):
                current_group.append(paragraph_list[i])
            else:
                # Finalize current group and start new one
                grouped.append(current_group)
                current_group = [paragraph_list[i]]
        
        # Add final group
        grouped.append(current_group)
        
        return grouped
    
    def merge_paragraph_group(self, soup, group):
        """Merge a group of paragraphs into a single paragraph with multiple spans"""
        if len(group) == 1:
            return group[0][0]  # Return the single paragraph as-is
        
        # Create new paragraph with attributes from first element
        first_p, _ = group[0]
        merged_p = soup.new_tag('p')
        
        # Copy attributes from first paragraph (except data-id)
        for attr, value in first_p.attrs.items():
            if attr != 'data-id':
                merged_p[attr] = value
        
        # Add all spans from the group
        for p_element, _ in group:
            # Find the span inside this paragraph
            span = p_element.find('span')
            if span:
                # Add space between spans except for the first one
                if len(merged_p.contents) > 0:
                    merged_p.append(' ')
                merged_p.append(span.extract())
        
        return merged_p
    
    def restructure_content(self, soup):
        """Restructure the entire document content"""
        # Find all paragraph elements with data-id
        paragraphs = soup.find_all('p', {'data-id': True})
        
        if not paragraphs:
            return False
        
        print(f"    Found {len(paragraphs)} paragraphs to process")
        
        # Process each paragraph and collect analysis
        processed_paragraphs = []
        for p in paragraphs:
            result = self.process_paragraph_element(soup, p)
            if result:
                processed_paragraphs.append(result)
        
        if not processed_paragraphs:
            return False
        
        # Group paragraphs that should be combined
        grouped_paragraphs = self.group_consecutive_paragraphs(soup, processed_paragraphs)
        
        print(f"    Grouped into {len(grouped_paragraphs)} paragraph groups")
        
        # Replace original paragraphs with restructured ones
        original_paragraphs = [p for p, _ in processed_paragraphs]
        
        # Merge each group and replace in DOM
        for i, group in enumerate(grouped_paragraphs):
            merged_p = self.merge_paragraph_group(soup, group)
            
            # Replace the first original paragraph with the merged one
            first_original = group[0][0]
            original_parent = first_original.parent
            original_index = list(original_parent.children).index(first_original)
            
            # Insert the merged paragraph
            first_original.replace_with(merged_p)
            
            # Remove any remaining paragraphs from this group
            for j in range(1, len(group)):
                group[j][0].extract()
        
        return True
    
    def process_file(self, file_path):
        """Process a single HTML file"""
        try:
            print(f"Processing: {os.path.basename(file_path)}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Restructure content
            changed = self.restructure_content(soup)
            
            if changed:
                # Write the modified content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"  ✓ Restructured text content")
                return True
            else:
                print(f"  - No changes needed")
                return False
                
        except Exception as e:
            print(f"  ✗ Error processing {file_path}: {e}")
            return False
    
    def restructure_files(self, start_page, end_page):
        """Restructure all files in the specified range"""
        files = self.get_file_list(start_page, end_page)
        
        if not files:
            print(f"No files found in range {start_page} to {end_page}")
            return
        
        print(f"Found {len(files)} files to process:")
        for file_path in files:
            print(f"  - {os.path.basename(file_path)}")
        
        print("\nProcessing files...")
        
        updated_count = 0
        for file_path in files:
            if self.process_file(file_path):
                updated_count += 1
        
        print(f"\nCompleted! Restructured {updated_count} out of {len(files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Restructure HTML text content with spans and intelligent paragraphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python restructure_text.py 6 58    # Process files from 6_0_adt.html to 58_0_adt.html
  python restructure_text.py 10 15   # Process files from 10_0_adt.html to 15_0_adt.html
        """
    )
    
    parser.add_argument('start_page', type=int,
                        help='Starting page number (e.g., 6 for 6_0_adt.html)')
    parser.add_argument('end_page', type=int,
                        help='Ending page number (e.g., 58 for 58_0_adt.html)')
    parser.add_argument('--output-dir', default='./output',
                        help='Directory containing HTML files (default: ./output)')
    parser.add_argument('--texts-json',
                        help='Path to texts.json file (default: auto-detect)')
    
    args = parser.parse_args()
    
    if args.start_page > args.end_page:
        print("Error: Start page must be less than or equal to end page")
        return 1
    
    try:
        restructurer = TextRestructurer(args.output_dir, args.texts_json)
        restructurer.restructure_files(args.start_page, args.end_page)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
