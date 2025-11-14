#!/usr/bin/env python3
"""
HTML Text Override Script

This script overrides HTML text content using translations from texts.json files.
It reads the default language from config.json and replaces text in HTML elements
that have data-id attributes with corresponding values from the texts.json file.

Usage:
    python language_flattening.py target_dir
    python language_flattening.py target_dir --start-page 1 --end-page 10
    python language_flattening.py target_dir --verbose --dry-run
"""

import logging
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.language_flattening.classes.html_text_overrider import HTMLTextOverrider
from src.utils.page_utils import add_standard_args, parse_page_range

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('html_override.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = add_standard_args()
    parser.description = "Override HTML text content using texts.json translations"
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without modifying files")

    args = parser.parse_args()

    target_dir = Path(args.target_dir)
    if not target_dir.exists():
        print(f"Error: Target directory does not exist: {target_dir}", file=sys.stderr)
        sys.exit(1)

    # Parse and validate page range
    try:
        start_page, end_page = parse_page_range(args.start_page, args.end_page)
        # Convert -1 to None for the class method
        start_page = None if start_page == -1 else start_page
        end_page = None if end_page == -1 else end_page
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Set logging level based on verbose flag
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        overrider = HTMLTextOverrider(
            target_dir=target_dir,
            logger=logger,
            dry_run=args.dry_run
        )
        
        results = overrider.override_html_texts(
            start_page=start_page,
            end_page=end_page
        )

        # Print summary
        print("\n" + "="*50)
        print("HTML TEXT OVERRIDE SUMMARY")
        print("="*50)

        total_files = results.get('files_processed', 0)
        total_overrides = results.get('total_overrides', 0)
        total_warnings = results.get('total_warnings', 0)
        total_errors = results.get('errors', 0)

        print(f"Files processed: {total_files}")
        print(f"Text overrides applied: {total_overrides}")
        print(f"Warnings: {total_warnings}")
        print(f"Errors: {total_errors}")

        if args.dry_run:
            print("\n🔍 DRY RUN - No files were actually modified")

        if total_errors > 0:
            print("\n⚠️  Check html_override.log for detailed error information")
            return 1

        print("\n✅ HTML text override completed successfully!")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())