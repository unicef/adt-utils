#!/usr/bin/env python3
"""
ADT HTML Validation Script

This script validates HTML files in the ADT project by checking that:
- Every element with text content has a data-id attribute with a value
- Reports missing data-id attributes for debugging
- Provides summary statistics of validation results

Usage:
    python validate_adt.py <folder_path>
    python validate_adt.py <folder_path> --verbose
    python validate_adt.py <folder_path> --output report.txt
"""

import argparse
import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString
import glob


class ADTValidator:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.total_files = 0
        self.valid_files = 0
        self.total_violations = 0
        self.validation_results = []
        
        # Elements that typically don't need data-id (can be configured)
        self.exempt_tags = {
            'script', 'style', 'meta', 'title', 'head', 
            'html', 'body', 'br', 'hr'
        }
    
    def has_meaningful_text(self, element):
        """Check if element has meaningful text content (not just whitespace)"""
        if not element.get_text():
            return False
        
        # Get direct text content (not from children)
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString):
                direct_text += str(content)
        
        # Check if there's meaningful text (not just whitespace)
        return direct_text.strip() != ""
    
    def validate_element(self, element, file_path):
        """Validate a single element for data-id requirement"""
        violations = []
        
        # Skip exempt tags
        if element.name in self.exempt_tags:
            return violations
        
        # Check if element has meaningful text
        if self.has_meaningful_text(element):
            data_id = element.get('data-id')
            
            # Check if data-id is missing or empty
            if not data_id or data_id.strip() == "":
                violation = {
                    'file': file_path,
                    'tag': element.name,
                    'text': element.get_text()[:100] + "..." if len(element.get_text()) > 100 else element.get_text(),
                    'line': getattr(element, 'sourceline', 'unknown'),
                    'classes': element.get('class', []),
                    'id': element.get('id', ''),
                    'has_data_id': bool(data_id),
                    'data_id_value': data_id
                }
                violations.append(violation)
        
        return violations
    
    def validate_file(self, file_path):
        """Validate a single HTML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            body = soup.find('body')
            
            if not body:
                return {
                    'file': file_path,
                    'status': 'error',
                    'message': 'No body tag found',
                    'violations': []
                }
            
            violations = []
            
            # Check all elements within body
            for element in body.find_all(True):  # True finds all tags
                element_violations = self.validate_element(element, file_path)
                violations.extend(element_violations)
            
            status = 'valid' if len(violations) == 0 else 'invalid'
            
            return {
                'file': file_path,
                'status': status,
                'violations_count': len(violations),
                'violations': violations
            }
            
        except Exception as e:
            return {
                'file': file_path,
                'status': 'error',
                'message': str(e),
                'violations': []
            }
    
    def validate_folder(self, folder_path):
        """Validate all HTML files in the specified folder"""
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            print(f"❌ Error: Folder '{folder_path}' does not exist")
            return False
        
        # Find all HTML files in the folder (not subdirectories)
        html_files = list(folder_path.glob("*.html"))
        
        if not html_files:
            print(f"❌ No HTML files found in '{folder_path}'")
            return False
        
        print(f"🔍 Validating {len(html_files)} HTML files in '{folder_path}'")
        print("=" * 60)
        
        for html_file in sorted(html_files):
            self.total_files += 1
            result = self.validate_file(html_file)
            self.validation_results.append(result)
            
            if result['status'] == 'valid':
                self.valid_files += 1
                if self.verbose:
                    print(f"✅ {html_file.name} - VALID")
            elif result['status'] == 'invalid':
                violations_count = result['violations_count']
                self.total_violations += violations_count
                print(f"❌ {html_file.name} - {violations_count} violations")
                
                if self.verbose:
                    for violation in result['violations']:
                        print(f"   🔸 <{violation['tag']}> missing data-id")
                        print(f"      Text: \"{violation['text'][:50]}...\"")
                        if violation['classes']:
                            print(f"      Classes: {violation['classes']}")
                        print()
            else:
                print(f"⚠️  {html_file.name} - ERROR: {result.get('message', 'Unknown error')}")
        
        return True
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total files processed: {self.total_files}")
        print(f"Valid files: {self.valid_files}")
        print(f"Invalid files: {self.total_files - self.valid_files}")
        print(f"Total violations: {self.total_violations}")
        
        if self.total_files > 0:
            success_rate = (self.valid_files / self.total_files) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        if self.total_violations == 0:
            print("\n🎉 All files are valid! Every text element has a data-id attribute.")
        else:
            print(f"\n⚠️  Found {self.total_violations} elements missing data-id attributes.")
            print("   Consider running restructure_text.py to add missing data-id attributes.")
    
    def save_report(self, output_file):
        """Save detailed validation report to file"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("ADT HTML Validation Report\n")
                f.write("=" * 50 + "\n\n")
                
                for result in self.validation_results:
                    f.write(f"File: {result['file']}\n")
                    f.write(f"Status: {result['status']}\n")
                    
                    if result['status'] == 'invalid':
                        f.write(f"Violations: {result['violations_count']}\n\n")
                        
                        for i, violation in enumerate(result['violations'], 1):
                            f.write(f"  Violation {i}:\n")
                            f.write(f"    Tag: <{violation['tag']}>\n")
                            f.write(f"    Text: \"{violation['text']}\"\n")
                            f.write(f"    Line: {violation['line']}\n")
                            if violation['classes']:
                                f.write(f"    Classes: {violation['classes']}\n")
                            if violation['id']:
                                f.write(f"    ID: {violation['id']}\n")
                            f.write(f"    Has data-id: {violation['has_data_id']}\n")
                            f.write(f"    Data-id value: '{violation['data_id_value']}'\n\n")
                    
                    elif result['status'] == 'error':
                        f.write(f"Error: {result['message']}\n")
                    
                    f.write("-" * 30 + "\n\n")
                
                # Summary
                f.write("\nSUMMARY\n")
                f.write("-" * 10 + "\n")
                f.write(f"Total files: {self.total_files}\n")
                f.write(f"Valid files: {self.valid_files}\n")
                f.write(f"Invalid files: {self.total_files - self.valid_files}\n")
                f.write(f"Total violations: {self.total_violations}\n")
                
            print(f"📄 Detailed report saved to: {output_file}")
            
        except Exception as e:
            print(f"❌ Error saving report: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Validate ADT HTML files for data-id attributes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_adt.py ./output                    # Validate files in output folder
  python validate_adt.py ./output --verbose          # Show detailed violations
  python validate_adt.py ./output --output report.txt # Save detailed report
  python validate_adt.py ../target-folder            # Validate external folder
        """
    )
    
    parser.add_argument('folder_path', 
                        help='Path to folder containing HTML files to validate')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed violation information')
    parser.add_argument('--output', '-o', 
                        help='Save detailed report to specified file')
    parser.add_argument('--exempt-tags',
                        help='Comma-separated list of tags to exempt from validation')
    
    args = parser.parse_args()
    
    # Create validator
    validator = ADTValidator(verbose=args.verbose)
    
    # Add custom exempt tags if provided
    if args.exempt_tags:
        custom_exempt = set(tag.strip() for tag in args.exempt_tags.split(','))
        validator.exempt_tags.update(custom_exempt)
        print(f"ℹ️  Additional exempt tags: {custom_exempt}")
    
    # Run validation
    success = validator.validate_folder(args.folder_path)
    
    if success:
        validator.print_summary()
        
        # Save report if requested
        if args.output:
            validator.save_report(args.output)
        
        # Exit with error code if violations found
        return 0 if validator.total_violations == 0 else 1
    else:
        return 1


if __name__ == "__main__":
    exit(main())