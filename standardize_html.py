#!/usr/bin/env python3
"""
HTML Standardization Script

This script standardizes HTML files by:
1. Setting the body tag to use standard Tailwind classes
2. Setting the main container div to use standard Tailwind classes
3. Removing all classes from section tags

Usage:
    python standardize_html.py <start_page> <end_page>
    
Example:
    python standardize_html.py 6 58
    This will process files from 6_0_adt.html to 58_0_adt.html
"""

import argparse
import os
import re
import glob
from pathlib import Path


class HTMLStandardizer:
    def __init__(self, output_dir="./output"):
        self.output_dir = Path(output_dir)
        self.body_template = ('class="bg-white lg:p-5 md:p-5 sm:p-0 mb-12 '
                              'font-sans text-lg"')
        self.container_template = ('class="container mx-auto max-w-5xl '
                                   'bg-white rounded-lg lg:px-24 md:px-12 '
                                   'sm:px-6 pt-12 pb-12" id="content"')
    
    def get_file_list(self, start_page, end_page):
        """Generate list of files to process based on start and end page
        numbers"""
        files = []
        
        # Get all HTML files in the pattern
        for page_num in range(start_page, end_page + 1):
            # Find all files that match the pattern {page_num}_*_adt.html
            pattern = f"{page_num}_*_adt.html"
            matching_files = glob.glob(str(self.output_dir / pattern))
            files.extend(matching_files)
        
        return sorted(files)
    
    def standardize_body_tag(self, content):
        """Replace body tag classes with standard template"""
        # Pattern to match body tag with any classes
        body_pattern = r'<body[^>]*class="[^"]*"[^>]*>'
        
        # Find the body tag
        match = re.search(body_pattern, content)
        if match:
            # Extract other attributes from the body tag (excluding class)
            body_tag = match.group(0)
            # Remove existing class attribute and add our template
            body_without_class = re.sub(r'\s*class="[^"]*"', '', body_tag)
            # Add our standard class
            new_body = body_without_class.replace(
                '<body', f'<body {self.body_template}')
            content = content.replace(body_tag, new_body)
        else:
            # If no class attribute exists, add it
            body_pattern_no_class = r'<body([^>]*)>'
            content = re.sub(body_pattern_no_class,
                             rf'<body {self.body_template}\1>', content)
        
        return content
    
    def standardize_container_div(self, content):
        """Replace main container div classes with standard template"""
        # Pattern to match div with container class
        container_pattern = r'<div[^>]*class="[^"]*container[^"]*"[^>]*>'
        
        match = re.search(container_pattern, content)
        if match:
            old_div = match.group(0)
            # Replace with our template
            new_div = f'<div {self.container_template}>'
            content = content.replace(old_div, new_div)
        
        return content
    
    def remove_section_classes(self, content):
        """Remove all class attributes from section tags"""
        # Pattern to match section tags with class attributes
        section_pattern = r'<section([^>]*)\s+class="[^"]*"([^>]*)>'
        
        def replace_section(match):
            before_class = match.group(1)
            after_class = match.group(2)
            # Reconstruct section tag without class attribute
            return f'<section{before_class}{after_class}>'
        
        content = re.sub(section_pattern, replace_section, content)
        
        return content
    
    def process_file(self, file_path):
        """Process a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply transformations
            content = self.standardize_body_tag(content)
            content = self.standardize_container_div(content)
            content = self.remove_section_classes(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Updated: {os.path.basename(file_path)}")
                return True
            else:
                print(f"- No changes needed: {os.path.basename(file_path)}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            return False
    
    def standardize_files(self, start_page, end_page):
        """Standardize all files in the specified range"""
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
        
        print(f"\nCompleted! Updated {updated_count} out of {len(files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Standardize HTML files with consistent Tailwind classes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standardize_html.py 6 58    # Process files from 6_0_adt.html to 58_0_adt.html
  python standardize_html.py 10 15   # Process files from 10_0_adt.html to 15_0_adt.html
        """
    )
    
    parser.add_argument('start_page', type=int, help='Starting page number (e.g., 6 for 6_0_adt.html)')
    parser.add_argument('end_page', type=int, help='Ending page number (e.g., 58 for 58_0_adt.html)')
    parser.add_argument('--output-dir', default='./output', help='Directory containing HTML files (default: ./output)')
    
    args = parser.parse_args()
    
    if args.start_page > args.end_page:
        print("Error: Start page must be less than or equal to end page")
        return 1
    
    standardizer = HTMLStandardizer(args.output_dir)
    standardizer.standardize_files(args.start_page, args.end_page)
    
    return 0


if __name__ == "__main__":
    exit(main())
