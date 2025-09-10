#!/usr/bin/env python3
"""
HTML Heading Standardization Script

This script standardizes HTML heading tags (h1-h6) by:
1. Applying consistent Tailwind classes based on templates
2. Choosing appropriate colors based on existing color schemes
3. Preserving important attributes like data-id, aria-label, etc.

Usage:
    python standardize_headings.py <start_page> <end_page> [options]
    
Example:
    python standardize_headings.py 6 58
    python standardize_headings.py 10 15 --template custom_headings.json
"""

import argparse
import json
import os
import re
import glob
from pathlib import Path


class HeadingStandardizer:
    def __init__(self, output_dir="./output",
                 template_file="heading_templates.json"):
        self.output_dir = Path(output_dir)
        self.template_file = template_file
        self.load_templates()
    
    def load_templates(self):
        """Load heading templates from JSON file"""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.heading_templates = config.get('heading_templates', {})
            self.color_mapping = config.get('color_mapping', {})
            self.background_color_mapping = config.get(
                'background_color_mapping', {})
            self.background_templates = config.get('background_templates', {})
            self.preserve_attributes = config.get('preserve_attributes', [])
            
            print(f"✓ Loaded templates from {self.template_file}")
            
        except FileNotFoundError:
            print(f"✗ Template file {self.template_file} not found!")
            raise
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing template file: {e}")
            raise
    
    def get_file_list(self, start_page, end_page):
        """Generate list of files to process based on start and end page
        numbers"""
        files = []
        
        for page_num in range(start_page, end_page + 1):
            pattern = f"{page_num}_*_adt.html"
            matching_files = glob.glob(str(self.output_dir / pattern))
            files.extend(matching_files)
        
        return sorted(files)
    
    def extract_current_color(self, class_attr):
        """Extract current color from class attribute"""
        if not class_attr:
            return None
        
        # Look for text-{color}-{shade} patterns
        color_pattern = r'text-(\w+)-\d+'
        match = re.search(color_pattern, class_attr)
        
        if match:
            return match.group(1)
        
        # Look for simple text-{color} patterns
        simple_color_pattern = r'text-(\w+)(?=\s|$)'
        match = re.search(simple_color_pattern, class_attr)
        
        if match:
            color = match.group(1)
            # Exclude non-color words
            excluded_words = ['center', 'left', 'right', 'justify', 'start',
                              'end', 'xs', 'sm', 'md', 'lg', 'xl', 'base']
            if color not in excluded_words:
                return color
        
        return None
    
    def choose_best_color(self, current_color, available_colors):
        """Choose the best matching color from available options"""
        if not current_color:
            return available_colors[0]  # Default to first option
        
        # Direct mapping from config
        if current_color in self.color_mapping:
            mapped_color = self.color_mapping[current_color]
            if mapped_color in available_colors:
                return mapped_color
        
        # Fallback to first available color
        return available_colors[0]
    
    def extract_attributes(self, heading_tag):
        """Extract and preserve important attributes from heading tag"""
        preserved_attrs = {}
        
        for attr in self.preserve_attributes:
            # Pattern to find attribute="value"
            pattern = rf'{attr}="([^"]*)"'
            match = re.search(pattern, heading_tag)
            if match:
                preserved_attrs[attr] = match.group(1)
        
        return preserved_attrs
    
    def build_new_heading(self, tag_name, content, template, color,
                          preserved_attrs):
        """Build new heading tag with standardized classes"""
        # Start with basic heading
        attrs = [f'class="{template["classes"]} {color}"']
        
        # Add preserved attributes
        for attr, value in preserved_attrs.items():
            attrs.append(f'{attr}="{value}"')
        
        attrs_str = ' '.join(attrs)
        return f'<{tag_name} {attrs_str}>{content}</{tag_name}>'
    
    def standardize_headings(self, content):
        """Standardize all heading tags in the content"""
        # Pattern to match heading tags with their content
        heading_pattern = r'<(h[1-6])([^>]*)>(.*?)</\1>'
        
        def replace_heading(match):
            tag_name = match.group(1)
            tag_attrs = match.group(2)
            heading_content = match.group(3)
            
            # Get template for this heading level
            if tag_name not in self.heading_templates:
                return match.group(0)  # Return unchanged if no template
            
            template = self.heading_templates[tag_name]
            
            # Extract current color from existing classes
            class_match = re.search(r'class="([^"]*)"', tag_attrs)
            current_class = class_match.group(1) if class_match else ""
            current_color = self.extract_current_color(current_class)
            
            # Choose best matching color
            chosen_color = self.choose_best_color(current_color,
                                                  template['color_options'])
            
            # Extract and preserve important attributes
            full_tag = f'<{tag_name}{tag_attrs}>'
            preserved_attrs = self.extract_attributes(full_tag)
            
            # Build new heading
            new_heading = self.build_new_heading(
                tag_name, heading_content, template, chosen_color,
                preserved_attrs
            )
            
            return new_heading
        
        return re.sub(heading_pattern, replace_heading, content,
                      flags=re.DOTALL)
    
    def extract_background_color(self, class_attr):
        """Extract current background color from class attribute"""
        if not class_attr:
            return None
        
        # Look for bg-{color}-{shade} patterns
        bg_pattern = r'bg-(\w+)-\d+'
        match = re.search(bg_pattern, class_attr)
        
        if match:
            return match.group(1)
        
        # Look for simple bg-{color} patterns
        simple_bg_pattern = r'bg-(\w+)(?=\s|$)'
        match = re.search(simple_bg_pattern, class_attr)
        
        if match:
            color = match.group(1)
            # Exclude non-color words
            excluded_words = ['transparent', 'current', 'inherit',
                              'auto', 'none', 'full', 'screen']
            if color not in excluded_words:
                return color
        
        return None
    
    def choose_best_background_color(self, current_color, available_colors):
        """Choose the best matching background color from available options"""
        if not current_color:
            return available_colors[0]  # Default to first option
        
        # Direct mapping from config
        if current_color in self.background_color_mapping:
            mapped_color = self.background_color_mapping[current_color]
            if mapped_color in available_colors:
                return mapped_color
        
        # Fallback to first available color
        return available_colors[0]
    
    def standardize_background_boxes(self, content):
        """Standardize background colors in content boxes"""
        if not hasattr(self, 'background_templates'):
            return content
        
        box_backgrounds = self.background_templates.get('box_backgrounds', [])
        if not box_backgrounds:
            return content
        
        # Pattern to match elements with background, padding, and rounded
        # corners - this targets content boxes, not just any background
        patterns = [
            # div/li with bg-color-shade + padding + rounded
            (r'(<(?:div|li)[^>]*class="[^"]*)(bg-\w+-\d+)'
             r'([^"]*p-\d+[^"]*rounded[^"]*")([^>]*>)'),
            # div/li with bg-color-shade in any order with padding and rounded
            (r'(<(?:div|li)[^>]*class="[^"]*)(bg-\w+-\d+)'
             r'([^"]*(?=.*p-\d+)(?=.*rounded)[^"]*")([^>]*>)'),
        ]
        
        def replace_background(match):
            before_bg = match.group(1)
            old_bg = match.group(2)
            middle_classes = match.group(3)
            after_classes = match.group(4)
            
            # Extract the current background color
            current_color = self.extract_background_color(old_bg)
            
            # Choose the best matching new background color
            new_bg = self.choose_best_background_color(current_color,
                                                       box_backgrounds)
            
            return f'{before_bg}{new_bg}{middle_classes}{after_classes}'
        
        # Apply all patterns
        for pattern in patterns:
            content = re.sub(pattern, replace_background, content)
        
        return content
    
    def process_file(self, file_path):
        """Process a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply heading standardization
            content = self.standardize_headings(content)
            
            # Apply background box standardization
            content = self.standardize_background_boxes(content)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✓ Updated headings and backgrounds in: "
                      f"{os.path.basename(file_path)}")
                return True
            else:
                print(f"- No changes needed: "
                      f"{os.path.basename(file_path)}")
                return False
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            return False
    
    def standardize_files(self, start_page, end_page):
        """Standardize headings in all files in the specified range"""
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
        
        print(f"\nCompleted! Updated headings and backgrounds in "
              f"{updated_count} out of {len(files)} files.")


def main():
    parser = argparse.ArgumentParser(
        description="Standardize HTML headings with consistent Tailwind "
                    "classes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standardize_headings.py 6 58    # Process files from 6_0_adt.html to 58_0_adt.html
  python standardize_headings.py 10 15   # Process files from 10_0_adt.html to 15_0_adt.html
  python standardize_headings.py 6 58 --template custom.json  # Use custom template
        """
    )
    
    parser.add_argument('start_page', type=int,
                        help='Starting page number (e.g., 6 for 6_0_adt.html)')
    parser.add_argument('end_page', type=int,
                        help='Ending page number (e.g., 58 for 58_0_adt.html)')
    parser.add_argument('--output-dir', default='./output',
                        help='Directory containing HTML files '
                        '(default: ./output)')
    parser.add_argument('--template', default='heading_templates.json',
                        help='Template file with heading configurations '
                        '(default: heading_templates.json)')
    
    args = parser.parse_args()
    
    if args.start_page > args.end_page:
        print("Error: Start page must be less than or equal to end page")
        return 1
    
    try:
        standardizer = HeadingStandardizer(args.output_dir, args.template)
        standardizer.standardize_files(args.start_page, args.end_page)
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
