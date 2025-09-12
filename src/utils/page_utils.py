"""
Utility functions for page range handling and common operations.
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple


def add_standard_args(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add standard start_page and end_page arguments to any script.
    
    Args:
        parser: ArgumentParser instance
        
    Returns:
        Modified parser with standard arguments
    """
    parser.add_argument(
        '--start-page', 
        type=int, 
        default=-1,
        help='Starting page number (-1 for all pages, default: -1)'
    )
    parser.add_argument(
        '--end-page', 
        type=int, 
        default=-1,
        help='Ending page number (-1 for all pages, default: -1)'
    )
    parser.add_argument(
        'target_dir',
        type=str,
        help='Target directory path'
    )
    return parser


def parse_page_range(start_page: int, end_page: int) -> Tuple[int, int]:
    """
    Validate and normalize page range.
    
    Args:
        start_page: Starting page (-1 for all)
        end_page: Ending page (-1 for all)
        
    Returns:
        Tuple of (start_page, end_page)
        
    Raises:
        ValueError: If page range is invalid
    """
    if start_page < -1 or end_page < -1:
        raise ValueError("Page numbers must be -1 or positive")
    
    if start_page != -1 and end_page != -1 and end_page < start_page:
        raise ValueError("end_page must be >= start_page")
    
    return start_page, end_page


def extract_page_number(file_path: Path) -> int:
    """
    Extract page number from file path using common patterns.
    
    Args:
        file_path: Path to file
        
    Returns:
        Extracted page number or 0 if not found
    """
    patterns = [
        r'page[\-_]?(\d+)',
        r'p(\d+)',
        r'(\d+)\.html?$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, file_path.name, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 0


def filter_files_by_page_range(files: List[Path], start_page: int, end_page: int) -> List[Path]:
    """
    Filter list of files by page range.
    
    Args:
        files: List of file paths
        start_page: Starting page (-1 for all)
        end_page: Ending page (-1 for all)
        
    Returns:
        Filtered list of files
    """
    if start_page == -1 and end_page == -1:
        return files
    
    filtered = []
    for file_path in files:
        page_num = extract_page_number(file_path)
        if start_page != -1 and page_num < start_page:
            continue
        if end_page != -1 and page_num > end_page:
            continue
        filtered.append(file_path)
    
    return filtered