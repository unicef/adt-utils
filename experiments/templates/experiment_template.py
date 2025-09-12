#!/usr/bin/env python3
"""
Experiment Template Script

Template for creating new experimental scripts with standardized arguments.
Copy this file and modify it for your specific experiment.

Usage:
    python experiment_script.py target_dir --start-page 1 --end-page 10
    python experiment_script.py target_dir  # Process all pages
"""

import argparse
import sys
from pathlib import Path

# Add src to path for production class imports (if needed)
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.utils import add_standard_args, parse_page_range


def main():
    parser = argparse.ArgumentParser(description="Description of your experiment")
    
    # Add standard page range arguments
    parser = add_standard_args(parser)
    
    # Add your custom arguments here
    parser.add_argument(
        '--custom-option',
        type=str,
        help='Description of your custom option'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate page range
    try:
        start_page, end_page = parse_page_range(args.start_page, args.end_page)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate target directory
    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Your experiment logic here
    print(f"Running experiment on {target_dir}")
    print(f"Page range: {start_page} to {end_page}")
    
    if args.verbose:
        print("Verbose mode enabled")
    
    # Process pages in range
    if start_page == -1 and end_page == -1:
        print("Processing all pages")
        # Add logic to process all pages
    else:
        print(f"Processing pages {start_page} to {end_page}")
        # Add logic to process specific page range
    
    print("Experiment completed successfully")


if __name__ == "__main__":
    main()