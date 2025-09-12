#!/usr/bin/env python3
"""
ADT Data-ID Auto-Fixer Script (Production)

This script automatically adds missing data-id attributes to HTML elements by:
1. Finding elements without data-id that contain text
2. Searching for matching text in the corresponding i18n JSON files
3. Adding existing data-id if text is found, or creating new entries
4. Following the text-[page_id]-[incremental] naming convention

Usage:
    python fix_missing_data_ids.py <target_dir>
    python fix_missing_data_ids.py <target_dir> --start-page 1 --end-page 10
    python fix_missing_data_ids.py <target_dir> --dry-run
    python fix_missing_data_ids.py <target_dir> --verbose
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.validation import ADTDataFixer
from src.core import PageProcessConfig
from src.utils import add_standard_args, parse_page_range


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
    
    parser = add_standard_args(parser)
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview changes without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Show detailed information about each fix')
    
    args = parser.parse_args()
    
    # Validate arguments
    try:
        start_page, end_page = parse_page_range(args.start_page, args.end_page)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Create configuration
    config = PageProcessConfig(
        start_page=start_page,
        end_page=end_page,
        target_dir=target_dir,
        verbose=args.verbose
    )
    
    # Run data fixing
    fixer = ADTDataFixer()
    result = fixer.process_page_range(config, dry_run=args.dry_run)
    
    # Output results
    if result.success:
        total_fixes = result.metadata.get('total_fixes', 0)
        total_files = result.metadata.get('total_files', 0)
        json_files_updated = result.metadata.get('json_files_updated', 0)
        
        if args.dry_run:
            print(f"🔍 DRY RUN: Would fix {total_fixes} elements across {total_files} files")
            if json_files_updated > 0:
                print(f"📄 Would update {json_files_updated} JSON files")
                print(f"   Languages: {', '.join(result.metadata.get('updated_languages', []))}")
            print("\nRemove --dry-run to apply changes")
        else:
            if total_fixes > 0:
                print(f"✅ Fixed {total_fixes} missing data-id attributes across {total_files} files")
                if json_files_updated > 0:
                    print(f"📄 Updated {json_files_updated} JSON files")
                    print(f"   Languages: {', '.join(result.metadata.get('updated_languages', []))}")
                print("Run validate_adt.py again to verify all issues are resolved")
            else:
                print(f"✅ No missing data-id attributes found in {total_files} files - all valid!")
        
        print(f"📄 Processed {len(result.processed_pages)} pages")
        
    else:
        print("❌ Data fixing failed")
        for error in result.errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()