"""
Utility functions for page range handling and common operations.
"""

import argparse
import re
from pathlib import Path
from typing import List, Tuple, Optional
from bs4 import BeautifulSoup

# Compile regex patterns once at module level for better performance
_FILENAME_PATTERNS = [
    re.compile(r'page[\-_]?(\d+)', re.IGNORECASE),
    re.compile(r'p(\d+)', re.IGNORECASE),
    re.compile(r'(\d+)\.html?$', re.IGNORECASE)
]

_DATA_ID_FILTER_PATTERN = re.compile(r'^(txt_|text-)')

_DATA_ID_PAGE_PATTERNS = [
    re.compile(r'txt_p(\d+)_'),      # txt_p56_g0_t0 -> 56
    re.compile(r'text-(\d+)-'),      # text-24-0 -> 24
    re.compile(r'txt_(\d+)_'),       # txt_56_g0_t0 -> 56 (alternative pattern)
    re.compile(r'text_(\d+)_'),      # text_56_g0_t0 -> 56 (alternative pattern)
]


def add_standard_args(parser: argparse.ArgumentParser = None) -> argparse.ArgumentParser:
    """
    Add standard start_page and end_page arguments to any script.
    
    Args:
        parser: ArgumentParser instance (creates new one if None)
        
    Returns:
        Modified parser with standard arguments
    """
    if parser is None:
        parser = argparse.ArgumentParser()
        
    parser.add_argument(
        'target_dir',
        type=str,
        help='Target directory path'
    )
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
    for pattern in _FILENAME_PATTERNS:
        match = pattern.search(file_path.name)
        if match:
            return int(match.group(1))
    
    return 0


def extract_page_number_from_data_id(file_path: Path) -> Optional[int]:
    """
    Extract page number from data-id attributes in HTML content.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        Extracted page number or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find elements with data-id attributes that start with txt_ or text-
        elements = soup.find_all(attrs={'data-id': _DATA_ID_FILTER_PATTERN})
        
        for element in elements:
            data_id = element.get('data-id')
            
            # Extract page number using pre-compiled patterns
            for pattern in _DATA_ID_PAGE_PATTERNS:
                match = pattern.search(data_id)
                if match:
                    return int(match.group(1))
        
        return None
        
    except Exception:
        return None


def filter_files_by_page_range(files: List[Path], start_page: int, end_page: int, use_data_id: bool = False) -> List[Path]:
    """
    Filter list of files by page range.
    
    Args:
        files: List of file paths
        start_page: Starting page (-1 for all)
        end_page: Ending page (-1 for all)
        use_data_id: If True, extract page numbers from data-id attributes instead of filenames
        
    Returns:
        Filtered list of files
    """
    if start_page == -1 and end_page == -1:
        return files
    
    filtered = []
    for file_path in files:
        if use_data_id:
            page_num = extract_page_number_from_data_id(file_path)
        else:
            page_num = extract_page_number(file_path)
            # Convert 0 to None for consistent handling
            page_num = None if page_num == 0 else page_num
            
        # Consistent handling: files without detectable page numbers are always included
        if page_num is None:
            filtered.append(file_path)
            continue
            
        # Apply page range filtering
        if start_page != -1 and page_num < start_page:
            continue
        if end_page != -1 and page_num > end_page:
            continue
        filtered.append(file_path)
    
    return filtered