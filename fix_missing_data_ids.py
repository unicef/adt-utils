#!/usr/bin/env python3
"""
ADT Data-ID Auto-Fixer Script

This script automatically adds missing data-id attributes to HTML elements by:
1. Finding elements without data-id that contain text
2. Searching for matching text in the corresponding i18n JSON files
3. Adding existing data-id if text is found, or creating new entries
4. Following the text-[page_id]-[incremental] naming convention

Usage:
    python fix_missing_data_ids.py <target_dir>
    python fix_missing_data_ids.py <target_dir> --dry-run
    python fix_missing_data_ids.py <target_dir> --verbose
"""

import argparse
import json
import os
import re
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Comment

# Import shared validation logic
from validate_adt import ADTValidationMixin


class DataIDFixer(ADTValidationMixin):
    def __init__(self, target_dir, dry_run=False, verbose=False):
        # Initialize the validation mixin
        super().__init__()
        
        self.target_dir = Path(target_dir)
        self.dry_run = dry_run
        self.verbose = verbose
        self.i18n_dir = self.target_dir / "content" / "i18n"
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'elements_fixed': 0,
            'existing_matches': 0,
            'new_entries_created': 0,
            'json_files_updated': set()
        }
        
        # Cache for JSON files
        self.json_cache = {}
        self.json_reverse_cache = {}  # text -> key mapping
    
    def extract_page_id_from_filename(self, filename):
        """Extract page ID from HTML filename (e.g., '25_0_adt.html' -> '25', 'index.html' -> '0')"""
        if filename == "index.html":
            return "0"
        match = re.match(r'(\d+)_.*\.html$', filename)
        return match.group(1) if match else None
    
    def load_json_file(self, lang_code):
        """Load and cache JSON file for a language"""
        if lang_code in self.json_cache:
            return self.json_cache[lang_code]
        
        json_path = self.i18n_dir / lang_code / "texts.json"
        
        if not json_path.exists():
            if self.verbose:
                print(f"  ℹ️  JSON file not found: {json_path}")
            self.json_cache[lang_code] = {}
            self.json_reverse_cache[lang_code] = {}
            return {}
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create reverse mapping (text -> key) - only for keys starting with "text-"
            reverse_map = {}
            for key, value in data.items():
                if isinstance(value, str) and key.startswith("text-"):
                    # Normalize text for comparison
                    normalized_text = self.normalize_text(value)
                    reverse_map[normalized_text] = key
            
            self.json_cache[lang_code] = data
            self.json_reverse_cache[lang_code] = reverse_map
            
            if self.verbose:
                print(f"  📁 Loaded {len(data)} entries from {json_path}")
            
            return data
            
        except Exception as e:
            print(f"  ❌ Error loading {json_path}: {e}")
            self.json_cache[lang_code] = {}
            self.json_reverse_cache[lang_code] = {}
            return {}
    
    def normalize_text(self, text):
        """Normalize text for comparison (remove extra whitespace, etc.)"""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def find_existing_data_id(self, text, lang_code):
        """Find existing data-id for text in JSON file"""
        if lang_code not in self.json_reverse_cache:
            self.load_json_file(lang_code)
        
        normalized_text = self.normalize_text(text)
        return self.json_reverse_cache[lang_code].get(normalized_text)
    
    def get_next_incremental_id(self, lang_code, page_id):
        """Get the next available incremental ID for a page"""
        if lang_code not in self.json_cache:
            self.load_json_file(lang_code)
        
        data = self.json_cache[lang_code]
        pattern = f"text-{page_id}-"
        
        # Find existing incremental values for this page - only for keys starting with "text-"
        existing_nums = []
        for key in data.keys():
            if key.startswith(pattern):
                try:
                    num_part = key[len(pattern):]
                    existing_nums.append(int(num_part))
                except ValueError:
                    continue
        
        # Return next available number
        return max(existing_nums, default=-1) + 1
    
    def create_new_data_id_entry(self, text, lang_code, page_id):
        """Create a new data-id entry in the JSON file"""
        if lang_code not in self.json_cache:
            self.load_json_file(lang_code)
        
        # Generate new key
        incremental = self.get_next_incremental_id(lang_code, page_id)
        new_key = f"text-{page_id}-{incremental}"
        
        # Add to cache
        self.json_cache[lang_code][new_key] = text
        
        # Add to reverse cache
        normalized_text = self.normalize_text(text)
        self.json_reverse_cache[lang_code][normalized_text] = new_key
        
        # Mark JSON file as updated
        self.stats['json_files_updated'].add(lang_code)
        
        if self.verbose:
            print(f"    🆕 Created new entry: {new_key} = \"{text[:50]}...\"")
        
        return new_key
    
    def save_json_files(self):
        """Save all modified JSON files"""
        for lang_code in self.stats['json_files_updated']:
            json_path = self.i18n_dir / lang_code / "texts.json"
            
            # Ensure directory exists
            json_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # Sort keys for consistent output
                sorted_data = dict(sorted(self.json_cache[lang_code].items()))
                
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(sorted_data, f, ensure_ascii=False, indent=2)
                
                print(f"  💾 Updated JSON file: {json_path}")
                
            except Exception as e:
                print(f"  ❌ Error saving {json_path}: {e}")
    
    def get_element_text(self, element):
        """Get the DIRECT text content of an element (not from children), excluding comments"""
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(content, Comment):
                direct_text += str(content)
        return self.normalize_text(direct_text)
    
    def fix_element_data_id(self, element, lang_code, page_id):
        """Fix missing data-id for a single element using shared validation logic"""
        # Use the shared validation logic from ADTValidationMixin
        if not self.should_validate_element(element):
            return False
        
        # Get element text (direct text only)
        text = self.get_element_text(element)
        if not text:
            return False
        
        # Try to find existing data-id
        existing_data_id = self.find_existing_data_id(text, lang_code)
        
        if existing_data_id:
            # Use existing data-id
            if not self.dry_run:
                element['data-id'] = existing_data_id
            
            if self.verbose:
                print(f"    ✅ Found existing: {existing_data_id} for \"{text[:50]}...\"")
            
            self.stats['existing_matches'] += 1
            return True
        else:
            # Create new data-id entry
            new_data_id = self.create_new_data_id_entry(text, lang_code, page_id)
            
            if not self.dry_run:
                element['data-id'] = new_data_id
            
            if self.verbose:
                print(f"    🆕 Created new: {new_data_id} for \"{text[:50]}...\"")
            
            self.stats['new_entries_created'] += 1
            return True
    
    def get_html_lang(self, soup):
        """Extract language code from HTML lang attribute"""
        html_element = soup.find('html')
        if html_element and html_element.get('lang'):
            return html_element['lang']
        return 'es'  # Default to Spanish if not found
    
    def fix_file(self, file_path):
        """Fix missing data-ids in a single HTML file"""
        try:
            filename = os.path.basename(file_path)
            page_id = self.extract_page_id_from_filename(filename)
            
            if not page_id:
                print(f"  ⚠️  Could not extract page ID from {filename}")
                return False
            
            print(f"🔧 Processing: {filename} (page {page_id})")
            
            # Read file
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get language code
            lang_code = self.get_html_lang(soup)
            if self.verbose:
                print(f"  🌐 Language: {lang_code}")
            
            # Load corresponding JSON file
            self.load_json_file(lang_code)
            
            # Find body element
            body = soup.find('body')
            if not body:
                print(f"  ⚠️  No body element found in {filename}")
                return False
            
            # Fix all elements in body
            elements_fixed = 0
            for element in body.find_all(True):  # Find all tags
                if self.fix_element_data_id(element, lang_code, page_id):
                    elements_fixed += 1
            
            # Save file if changes were made and not dry run
            if elements_fixed > 0 and not self.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            
            if elements_fixed > 0:
                action = "Would fix" if self.dry_run else "Fixed"
                print(f"  ✅ {action} {elements_fixed} elements")
                self.stats['elements_fixed'] += elements_fixed
                return True
            else:
                print("  ℹ️  No missing data-ids found")
                return False
                
        except Exception as e:
            print(f"  ❌ Error processing {file_path}: {e}")
            return False
    
    def fix_directory(self):
        """Fix all HTML files in the target directory"""
        # Find all HTML files
        html_files = list(self.target_dir.glob("*.html"))
        
        if not html_files:
            print(f"❌ No HTML files found in {self.target_dir}")
            return False
        
        print(f"🔍 Found {len(html_files)} HTML files to process")
        
        if self.dry_run:
            print("🔍 DRY RUN MODE - No changes will be made")
        
        print("-" * 60)
        
        # Process each file
        for file_path in sorted(html_files):
            self.stats['files_processed'] += 1
            self.fix_file(file_path)
        
        # Save JSON files if not dry run
        if not self.dry_run and self.stats['json_files_updated']:
            print("\n" + "=" * 60)
            print("Saving updated JSON files...")
            self.save_json_files()
        
        return True
    
    def print_summary(self):
        """Print summary of operations"""
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Elements fixed: {self.stats['elements_fixed']}")
        print(f"Existing matches found: {self.stats['existing_matches']}")
        print(f"New entries created: {self.stats['new_entries_created']}")
        print(f"JSON files updated: {len(self.stats['json_files_updated'])}")
        
        if self.stats['json_files_updated']:
            print(f"Updated languages: {', '.join(sorted(self.stats['json_files_updated']))}")
        
        if self.dry_run:
            print("\n🔍 This was a DRY RUN - no changes were actually made")
            print("Remove --dry-run to apply changes")
        elif self.stats['elements_fixed'] > 0:
            print(f"\n🎉 Successfully fixed {self.stats['elements_fixed']} missing data-id attributes!")
            print("Run validate_adt.py again to verify all issues are resolved")
        else:
            print("\n✅ No missing data-id attributes found - all files are valid!")


def main():
    parser = argparse.ArgumentParser(
        description="Automatically fix missing data-id attributes in HTML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fix_missing_data_ids.py ../target-folder              # Fix missing data-ids
  python fix_missing_data_ids.py ../target-folder --dry-run    # Preview changes
  python fix_missing_data_ids.py ../target-folder --verbose    # Detailed output
  
Workflow:
  1. python validate_adt.py ../target-folder                   # Find issues
  2. python fix_missing_data_ids.py ../target-folder          # Fix issues  
  3. python validate_adt.py ../target-folder                   # Verify fixes
        """
    )
    
    parser.add_argument('target_dir',
                        help='Directory containing HTML files and content/i18n/ structure')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed information about each fix')
    
    args = parser.parse_args()
    
    # Validate target directory
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"❌ Error: Directory '{target_dir}' does not exist")
        return 1
    
    if not target_dir.is_dir():
        print(f"❌ Error: '{target_dir}' is not a directory")
        return 1
    
    try:
        # Create fixer and run
        fixer = DataIDFixer(target_dir, args.dry_run, args.verbose)
        success = fixer.fix_directory()
        
        # Print summary
        fixer.print_summary()
        
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
