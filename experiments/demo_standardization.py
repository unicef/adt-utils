#!/usr/bin/env python3
"""
Complete HTML Standardization Demo

This script demonstrates both HTML body/container standardization
and heading standardization working together.

Usage:
    python demo_standardization.py <start_page> <end_page>
"""

import argparse
import subprocess
import sys


def run_script(script_name, start_page, end_page, description):
    """Run a standardization script and report results"""
    print(f"\n{'='*60}")
    print(f"Running {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run([
            sys.executable, script_name, str(start_page), str(end_page)
        ], capture_output=True, text=True, check=True)
        
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
        description="Complete HTML standardization demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python demo_standardization.py 6 10    # Demo on files 6-10
  python demo_standardization.py 47 47   # Demo on just file 47
        """
    )
    
    parser.add_argument('start_page', type=int,
                        help='Starting page number')
    parser.add_argument('end_page', type=int,
                        help='Ending page number')
    
    args = parser.parse_args()
    
    print("HTML Standardization Demo")
    print(f"Processing files from {args.start_page}_*_adt.html to "
          f"{args.end_page}_*_adt.html")
    
    # Run body/container standardization
    success1 = run_script('standardize_html.py', args.start_page,
                          args.end_page,
                          "Body & Container Standardization")
    
    # Run heading and background standardization
    success2 = run_script('standardize_headings.py', args.start_page,
                          args.end_page,
                          "Heading & Background Color Standardization")
    
    print(f"\n{'='*60}")
    print("DEMO COMPLETE")
    print(f"{'='*60}")
    
    if success1 and success2:
        print("✅ Both standardization scripts completed successfully!")
        print("\nYour HTML files now have:")
        print("  • Consistent body and container classes")
        print("  • Standardized heading typography and colors")
        print("  • Unified background colors for content boxes")
        print("  • Clean section tags without classes")
        print("  • Preserved important attributes")
    else:
        print("❌ Some scripts encountered errors")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
