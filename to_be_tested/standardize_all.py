#!/usr/bin/env python3
"""
Complete Standardization Suite

This script runs all standardization tools in sequence:
1. HTML structure standardization (body, container, sections)
2. Heading and background color standardization
3. JSON text cleanup (remove unwanted newlines)

Usage:
    python standardize_all.py <start_page> <end_page> [options]
"""

import argparse
import subprocess
import sys
import os


def run_script(script_name, args, description):
    """Run a standardization script and report results"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, script_name] + args
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                check=True)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
            
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Complete HTML and JSON standardization suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python standardize_all.py 6 58          # Complete standardization
  python standardize_all.py 10 15 --skip-json  # Skip JSON cleaning
        """
    )
    
    parser.add_argument('start_page', type=int,
                        help='Starting page number')
    parser.add_argument('end_page', type=int,
                        help='Ending page number')
    parser.add_argument('--skip-json', action='store_true',
                        help='Skip JSON text cleaning')
    parser.add_argument('--output-dir', default='./output',
                        help='Output directory (default: ./output)')
    
    args = parser.parse_args()
    
    print("🚀 COMPLETE STANDARDIZATION SUITE")
    print(f"Processing files from {args.start_page}_*_adt.html to "
          f"{args.end_page}_*_adt.html")
    
    results = []
    
    # Step 1: HTML structure standardization
    success1 = run_script('standardize_html.py', 
                         [str(args.start_page), str(args.end_page),
                          '--output-dir', args.output_dir],
                         "HTML Structure Standardization")
    results.append(("HTML Structure", success1))
    
    # Step 2: Heading and background standardization
    success2 = run_script('standardize_headings.py',
                         [str(args.start_page), str(args.end_page),
                          '--output-dir', args.output_dir],
                         "Heading & Background Color Standardization")
    results.append(("Headings & Backgrounds", success2))
    
    # Step 3: Text restructuring (spans and paragraphs)
    success3 = run_script('restructure_text_simple.py',
                         [str(args.start_page), str(args.end_page),
                          '--output-dir', args.output_dir],
                         "Text Restructuring (Spans & Paragraphs)")
    results.append(("Text Restructuring", success3))
    
    # Step 4: Image and text layout standardization
    success4 = run_script(
        'standardize_image_text_layouts.py',
        [],  # No args needed, processes all files
        "Image & Text Layout Standardization"
    )
    results.append(("Image & Text Layouts", success4))
    
    # Step 5: JSON text cleanup (optional)
    if not args.skip_json:
        json_dir = os.path.join(args.output_dir, 'content', 'i18n')
        if os.path.exists(json_dir):
            success_json = run_script(
                'clean_json_texts.py',
                ['--dir', json_dir],
                "JSON Text Cleanup"
            )
            results.append(("JSON Text Cleanup", success_json))
        else:
            print(f"\n⚠️ JSON directory {json_dir} not found, skipping...")
            results.append(("JSON Text Cleanup", None))
    
    # Final summary
    print(f"\n{'='*60}")
    print("🏁 STANDARDIZATION COMPLETE")
    print(f"{'='*60}")
    
    print("\nResults Summary:")
    for task, success in results:
        if success is True:
            print(f"  ✅ {task}: SUCCESS")
        elif success is False:
            print(f"  ❌ {task}: FAILED")
        else:
            print(f"  ⏭️ {task}: SKIPPED")
    
    all_success = all(result[1] is not False for result in results)
    
    if all_success:
        print("\n🎉 All standardization tasks completed successfully!")
        print("\nYour project now has:")
        print("  • Consistent HTML structure and styling")
        print("  • Standardized heading typography and colors")
        print("  • Unified background colors for content boxes")
        print("  • Text wrapped in spans with proper data-id attributes")
        print("  • Intelligently grouped paragraphs")
        print("  • Responsive image and text layouts")
        print("  • Clean JSON text files without formatting artifacts")
        print("  • Preserved accessibility attributes and data IDs")
    else:
        print("\n⚠️ Some tasks encountered issues. Check the logs above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
