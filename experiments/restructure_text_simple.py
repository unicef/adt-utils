#!/usr/bin/env python3
"""
HTML Text Restructuring Script - Simplified Version

This script restructures HTML content by:
1. Wrapping text content in <span> tags with data-id attributes
2. Moving data-id from <p> tags to <span> tags
3. Grouping spans into paragraphs based on content analysis

Usage:
    python restructure_text_simple.py <start_page> <end_page> [options]
"""

import argparse
import os
import glob
from pathlib import Path
from bs4 import BeautifulSoup


class SimpleTextRestructurer:
    def __init__(self, output_dir="./output"):
        self.output_dir = Path(output_dir)
    
    def get_file_list(self, start_page, end_page):
        """Generate list of files to process"""
        files = []
        for page_num in range(start_page, end_page + 1):
            pattern = f"{page_num}_*_adt.html"
            matching_files = glob.glob(str(self.output_dir / pattern))
            files.extend(matching_files)
        return sorted(files)
    
    def should_group_paragraphs(self, p1_text, p2_text):
        """Simple heuristic to determine if paragraphs should be grouped"""
        if not p1_text or not p2_text:
            return False
        
        # Count words
        p1_words = len(p1_text.split())
        p2_words = len(p2_text.split())
        
        # Don't group very short texts (likely titles or list items)
        if p1_words <= 3 or p2_words <= 3:
            return False
        
        # Group if both are substantial but not too long
        if (5 <= p1_words <= 30 and 5 <= p2_words <= 30):
            return True
        
        # Group if combined they make a reasonable paragraph (20-60 words)
        total_words = p1_words + p2_words
        if 20 <= total_words <= 60:
            return True
        
        return False
    
    def extract_paragraph_info(self, p_element):
        """Extract text and attributes from paragraph element"""
        if not p_element or p_element.name != 'p':
            return None
        
        # Get text content
        text = p_element.get_text(strip=True)
        if not text:
            return None
        
        # Get data-id
        data_id = p_element.get('data-id')
        if not data_id:
            return None
        
        # Get other attributes to preserve
        attrs = {}
        for attr in ['class', 'aria-label', 'data-aria-id', 'tabindex', 'role']:
            if p_element.get(attr):
                attrs[attr] = p_element[attr]
        
        return {
            'element': p_element,
            'text': text,
            'data_id': data_id,
            'attrs': attrs,
            'word_count': len(text.split())
        }
    
    def create_restructured_paragraph(self, soup, paragraphs_info):
        """Create a new paragraph with spans from list of paragraph info"""
        if not paragraphs_info:
            return None
        
        # Create new paragraph element
        new_p = soup.new_tag('p')
        
        # Use attributes from the first paragraph (except data-id)
        first_attrs = paragraphs_info[0]['attrs']
        for attr, value in first_attrs.items():
            new_p[attr] = value
        
        # Create spans for each text with their data-ids
        for i, p_info in enumerate(paragraphs_info):
            # Add space between spans (except first)
            if i > 0:
                new_p.append(' ')
            
            # Create span with text and data-id
            span = soup.new_tag('span')
            span['data-id'] = p_info['data_id']
            span.string = p_info['text']
            new_p.append(span)
        
        return new_p
    
    def restructure_content(self, soup):
        """Restructure the entire document content"""
        # Find all paragraph elements with data-id
        paragraphs = soup.find_all('p', {'data-id': True})
        
        if not paragraphs:
            return False
        
        print(f"    Found {len(paragraphs)} paragraphs to process")
        
        # Extract information from all paragraphs
        paragraphs_info = []
        for p in paragraphs:
            info = self.extract_paragraph_info(p)
            if info:
                paragraphs_info.append(info)
        
        if not paragraphs_info:
            return False
        
        # Group consecutive paragraphs that should be combined
        groups = []
        current_group = [paragraphs_info[0]]
        
        for i in range(1, len(paragraphs_info)):
            current = paragraphs_info[i]
            previous = paragraphs_info[i-1]
            
            if self.should_group_paragraphs(previous['text'], current['text']):
                current_group.append(current)
            else:
                groups.append(current_group)
                current_group = [current]
        
        # Add the last group
        groups.append(current_group)
        
        print(f"    Grouped into {len(groups)} paragraph groups")
        
        # Replace original paragraphs with restructured ones
        replacements = []
        for group in groups:
            new_p = self.create_restructured_paragraph(soup, group)
            if new_p:
                # Mark first element for replacement
                replacements.append((group[0]['element'], new_p, group))
        
        # Perform replacements
        for original_p, new_p, group in replacements:
            # Replace the first paragraph with the new one
            original_p.replace_with(new_p)
            
            # Remove the other paragraphs in this group
            for i in range(1, len(group)):
                group[i]['element'].extract()
        
        return len(replacements) > 0
    
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
                # Write the modified content back
                new_content = str(soup)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
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
        
        print(f"\nCompleted! Restructured {updated_count} out of "
              f"{len(files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Restructure HTML text content with spans and paragraphs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python restructure_text_simple.py 6 58     # Process all files 6-58
  python restructure_text_simple.py 28 28    # Process just file 28
        """
    )
    
    parser.add_argument('start_page', type=int,
                        help='Starting page number')
    parser.add_argument('end_page', type=int,
                        help='Ending page number')
    parser.add_argument('--output-dir', default='./output',
                        help='Directory containing HTML files')
    
    args = parser.parse_args()
    
    if args.start_page > args.end_page:
        print("Error: Start page must be less than or equal to end page")
        return 1
    
    try:
        restructurer = SimpleTextRestructurer(args.output_dir)
        restructurer.restructure_files(args.start_page, args.end_page)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
