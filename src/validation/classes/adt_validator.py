"""
Production ADT validator implementation following standardized interfaces.
"""

import re
from pathlib import Path
from typing import Dict, Any, List
from bs4 import BeautifulSoup, NavigableString, Comment

from ...core import Validator, ValidationConfig, ProcessResult, ValidationError


class ADTValidator(Validator):
    """Production ADT HTML validator."""
    
    def __init__(self):
        self.exempt_tags = {
            'script', 'style', 'meta', 'title', 'head',
            'html', 'body', 'br', 'hr'
        }
    
    def validate_config(self, config: ValidationConfig) -> List[str]:
        """Validate configuration before processing."""
        errors = []
        if config.target_dir and not Path(config.target_dir).exists():
            errors.append(f"Target directory does not exist: {config.target_dir}")
        return errors
    
    def process_page_range(self, config: ValidationConfig, **kwargs) -> ProcessResult:
        """Process validation for a range of pages."""
        errors = self.validate_config(config)
        if errors:
            return ProcessResult(success=False, errors=errors)
        
        result = ProcessResult(success=True)
        target_dir = Path(config.target_dir) if config.target_dir else Path.cwd()
        
        # Find HTML files only in the root directory (not subdirectories)
        html_files = list(target_dir.glob("*.html"))
        if not html_files:
            return ProcessResult(success=False, errors=["No HTML files found"])
        
        # Filter out non-content files (assets, tests, navigation, etc.)
        html_files = self._filter_content_files(html_files)
        
        # Filter by page range if specified
        if config.start_page != -1 or config.end_page != -1:
            html_files = self._filter_by_page_range(html_files, config.start_page, config.end_page)
        
        total_issues = 0
        for html_file in html_files:
            try:
                page_result = self.validate_page(self._extract_page_number(html_file), html_file)
                if page_result.get('issues', 0) > 0:
                    total_issues += page_result['issues']
                    result.warnings.extend(page_result.get('warnings', []))
                result.processed_pages.append(page_result.get('page_number', 0))
            except Exception as e:
                result.errors.append(f"Error validating {html_file}: {str(e)}")
        
        result.metadata = {
            'total_files': len(html_files),
            'total_issues': total_issues
        }
        
        if config.verbose:
            result.metadata['verbose'] = True
            
        return result
    
    def validate_page(self, page_number: int, page_path: Path) -> Dict[str, Any]:
        """Validate a single HTML page."""
        try:
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            issues = []
            
            def check_element(element, path=""):
                nonlocal issues
                
                if hasattr(element, 'name') and element.name:
                    current_path = f"{path} > {element.name}" if path else element.name
                    
                    if element.name.lower() in self.exempt_tags:
                        return
                    
                    has_text_content = False
                    direct_text = ""
                    
                    for child in element.children:
                        if isinstance(child, NavigableString) and not isinstance(child, Comment):
                            text = child.strip()
                            if text:
                                has_text_content = True
                                direct_text += text + " "
                    
                    if has_text_content:
                        data_id = element.get('data-id')
                        if not data_id or not data_id.strip():
                            issues.append({
                                'element': element.name,
                                'path': current_path,
                                'text_preview': direct_text[:100].strip(),
                                'issue': 'Missing or empty data-id attribute'
                            })
                    
                    for child in element.children:
                        if hasattr(child, 'name'):
                            check_element(child, current_path)
            
            # Start validation from body element to avoid document-level issues
            body = soup.find('body')
            if body:
                check_element(body)
            else:
                # Fallback to full document if no body found
                check_element(soup)
            
            return {
                'page_number': page_number,
                'file_path': str(page_path),
                'issues': len(issues),
                'warnings': [f"Page {page_number}: {issue['issue']} in {issue['element']}" for issue in issues],
                'details': issues
            }
            
        except Exception as e:
            raise ValidationError(f"Failed to validate page {page_number}: {str(e)}")
    
    def _extract_page_number(self, file_path: Path) -> int:
        """Extract page number from file path."""
        # First try the original pattern for files like "page10_0_adt.html"
        match = re.search(r'page[\-_]?(\d+)', file_path.name, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Then try pattern for files like "10_0_adt.html" (number at start)
        match = re.search(r'^(\d+)', file_path.name)
        return int(match.group(1)) if match else 0
    
    def _filter_content_files(self, files: List[Path]) -> List[Path]:
        """Filter out non-content files (assets, navigation, tests, etc.)."""
        content_files = []
        exclude_patterns = [
            '**/assets/**',
            '**/old/**', 
            '**/node_modules/**',
            '**/test*',
            '**/nav*',
            '**/*test*',
            '**/*nav*'
        ]
        
        for file_path in files:
            # Convert to relative path for pattern matching
            try:
                # Check if file matches any exclude pattern
                should_exclude = False
                file_str = str(file_path)
                
                for pattern in exclude_patterns:
                    if pattern.replace('**/', '') in file_str or pattern.replace('*', '') in file_str:
                        should_exclude = True
                        break
                
                if not should_exclude:
                    content_files.append(file_path)
                    
            except Exception:
                # If there's any issue, include the file to be safe
                content_files.append(file_path)
        
        return content_files
    
    def _filter_by_page_range(self, files: List[Path], start_page: int, end_page: int) -> List[Path]:
        """Filter files by page range."""
        filtered = []
        for file_path in files:
            page_num = self._extract_page_number(file_path)
            if start_page != -1 and page_num < start_page:
                continue
            if end_page != -1 and page_num > end_page:
                continue
            filtered.append(file_path)
        return filtered