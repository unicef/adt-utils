#!/usr/bin/env python3
"""
Test script to run image/text layout standardization on a single file
"""

import sys
from standardize_image_text_layouts import standardize_image_text_layout

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_single_layout.py <file_path>")
        return
    
    file_path = sys.argv[1]
    standardize_image_text_layout(file_path)
    print(f"Processed: {file_path}")

if __name__ == "__main__":
    main()
