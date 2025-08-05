#!/usr/bin/env python3
"""
JSON Text Cleanup Script

This script cleans up JSON text files by:
1. Removing unwanted newline characters (\\n) followed by spaces
2. Replacing them with single spaces for proper text flow
3. Preserving the JSON structure and formatting

Usage:
    python clean_json_texts.py [options]
    
Examples:
    python clean_json_texts.py                    # Clean default texts.json
    python clean_json_texts.py --file custom.json # Clean specific file
    python clean_json_texts.py --dir ./i18n/      # Clean all JSON files
"""

import argparse
import json
import os
import re
import glob
from pathlib import Path


class JSONTextCleaner:
    def __init__(self):
        self.patterns_to_clean = [
            # Pattern 1: \n followed by multiple spaces (most common)
            r'\\n\s+',
            # Pattern 2: \n followed by any whitespace characters
            r'\\n\s*',
            # Pattern 3: Multiple consecutive spaces (cleanup leftover spacing)
            r'\s{2,}'
        ]
    
    def clean_text_value(self, text):
        """Clean a single text value by removing unwanted newlines and
        spaces"""
        if not isinstance(text, str):
            return text
        
        cleaned_text = text
        
        # Apply each cleaning pattern
        # Only first two patterns for \n cleanup
        for pattern in self.patterns_to_clean[:2]:
            cleaned_text = re.sub(pattern, ' ', cleaned_text)
        
        # Clean up multiple consecutive spaces (but preserve single spaces)
        cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
        
        # Trim leading and trailing whitespace
        cleaned_text = cleaned_text.strip()
        
        return cleaned_text
    
    def clean_json_data(self, data):
        """Recursively clean all text values in JSON data"""
        if isinstance(data, dict):
            return {key: self.clean_json_data(value)
                    for key, value in data.items()}
        elif isinstance(data, list):
            return [self.clean_json_data(item) for item in data]
        elif isinstance(data, str):
            return self.clean_text_value(data)
        else:
            return data
    
    def process_file(self, file_path):
        """Process a single JSON file"""
        try:
            print(f"Processing: {os.path.basename(file_path)}")
            
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Parse JSON
            try:
                data = json.loads(original_content)
            except json.JSONDecodeError as e:
                print(f"  ✗ Invalid JSON in {file_path}: {e}")
                return False
            
            # Clean the data
            cleaned_data = self.clean_json_data(data)
            # Convert back to JSON with proper formatting
            cleaned_content = json.dumps(
                cleaned_data,
                ensure_ascii=False,
                indent=2,
                separators=(',', ': ')
            )
            
            # Only write if content changed
            if cleaned_content != original_content:
                # Create backup
                backup_path = f"{file_path}.backup"
                if not os.path.exists(backup_path):
                    with open(backup_path, 'w', encoding='utf-8') as f:
                        f.write(original_content)
                    print(f"  📁 Created backup: {os.path.basename(backup_path)}")
                
                # Write cleaned content
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)
                
                # Count changes
                original_newlines = original_content.count('\\n')
                cleaned_newlines = cleaned_content.count('\\n')
                removed_newlines = original_newlines - cleaned_newlines
                
                print(f"  ✓ Cleaned! Removed {removed_newlines} unwanted \\n sequences")
                return True
            else:
                print("  - No changes needed")
                return False
                
        except Exception as e:
            print(f"  ✗ Error processing {file_path}: {e}")
            return False
    
    def find_json_files(self, directory):
        """Find all JSON files in a directory"""
        json_files = []
        for pattern in ['*.json', '**/*.json']:
            json_files.extend(glob.glob(str(Path(directory) / pattern), recursive=True))
        return sorted(json_files)
    
    def clean_files(self, file_paths):
        """Clean multiple JSON files"""
        if not file_paths:
            print("No JSON files found to process")
            return
        
        print(f"Found {len(file_paths)} JSON file(s) to process:")
        for file_path in file_paths:
            print(f"  - {os.path.basename(file_path)}")
        
        print("\nProcessing files...")
        
        cleaned_count = 0
        for file_path in file_paths:
            if self.process_file(file_path):
                cleaned_count += 1
        
        print(f"\nCompleted! Cleaned {cleaned_count} out of {len(file_paths)} files.")
        if cleaned_count > 0:
            print(f"💾 Backups created with .backup extension")


def main():
    parser = argparse.ArgumentParser(
        description="Clean unwanted newlines and spaces from JSON text files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clean_json_texts.py                           # Clean default texts.json
  python clean_json_texts.py --file custom.json        # Clean specific file  
  python clean_json_texts.py --dir ./content/i18n/     # Clean all JSON in directory
  python clean_json_texts.py --file texts.json --no-backup  # Don't create backups
        """
    )
    
    parser.add_argument('--file', 
                        help='Specific JSON file to clean (default: ./output/content/i18n/es/texts.json)')
    parser.add_argument('--dir', 
                        help='Directory to search for JSON files (recursive)')
    parser.add_argument('--pattern', default='*.json',
                        help='File pattern to match (default: *.json)')
    
    args = parser.parse_args()
    
    cleaner = JSONTextCleaner()
    
    # Determine which files to process
    if args.dir:
        # Process all JSON files in directory
        file_paths = cleaner.find_json_files(args.dir)
    elif args.file:
        # Process specific file
        if os.path.exists(args.file):
            file_paths = [args.file]
        else:
            print(f"Error: File {args.file} not found")
            return 1
    else:
        # Default: process texts.json
        default_file = "./output/content/i18n/es/texts.json"
        if os.path.exists(default_file):
            file_paths = [default_file]
        else:
            print(f"Error: Default file {default_file} not found")
            print("Use --file or --dir to specify files to clean")
            return 1
    
    cleaner.clean_files(file_paths)
    return 0


if __name__ == "__main__":
    exit(main())
