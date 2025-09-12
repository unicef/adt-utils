#!/usr/bin/env python3
"""
ADT HTML Validation Script (Production)

Validates HTML files using the standardized ADT validation interface.
This is a production script that uses the classes from src/.

Usage:
    python validate_adt.py target_dir --start-page 1 --end-page 10
    python validate_adt.py target_dir --verbose
    python validate_adt.py target_dir --output report.txt
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.validation import ADTValidator
from src.core import ValidationConfig
from src.utils import add_standard_args, parse_page_range


def main():
    parser = argparse.ArgumentParser(description="Validate ADT HTML files")
    parser = add_standard_args(parser)
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--output', 
        type=str,
        help='Output report to file'
    )
    parser.add_argument(
        '--fix',
        action='store_true', 
        help='Attempt to auto-fix validation issues'
    )
    
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
    config = ValidationConfig(
        start_page=start_page,
        end_page=end_page,
        target_dir=target_dir,
        verbose=args.verbose,
        generate_report=bool(args.output),
        fix_issues=args.fix
    )
    
    # Run validation
    validator = ADTValidator()
    result = validator.process_page_range(config)
    
    # Output results
    if result.success:
        print(f"✅ Validation completed successfully")
        print(f"📄 Processed {len(result.processed_pages)} pages")
        
        if result.metadata.get('total_issues', 0) > 0:
            print(f"⚠️  Found {result.metadata['total_issues']} issues")
            
        if args.verbose and result.warnings:
            print("\nWarnings:")
            for warning in result.warnings[:10]:  # Limit output
                print(f"  - {warning}")
            if len(result.warnings) > 10:
                print(f"  ... and {len(result.warnings) - 10} more")
                
    else:
        print("❌ Validation failed")
        for error in result.errors:
            print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
    
    # Write report if requested
    if args.output:
        with open(args.output, 'w') as f:
            f.write(f"ADT Validation Report\n")
            f.write(f"====================\n\n")
            f.write(f"Target Directory: {target_dir}\n")
            f.write(f"Page Range: {start_page} to {end_page}\n")
            f.write(f"Processed Pages: {len(result.processed_pages)}\n")
            f.write(f"Total Issues: {result.metadata.get('total_issues', 0)}\n\n")
            
            if result.warnings:
                f.write("Issues Found:\n")
                for warning in result.warnings:
                    f.write(f"  - {warning}\n")
        
        print(f"📋 Report saved to {args.output}")


if __name__ == "__main__":
    main()