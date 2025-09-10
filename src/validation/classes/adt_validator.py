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
        
        # Find HTML files
        html_files = list(target_dir.glob("**/*.html"))
        if not html_files:
            return ProcessResult(success=False, errors=["No HTML files found"])
        
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
        match = re.search(r'page[\-_]?(\d+)', file_path.name, re.IGNORECASE)
        return int(match.group(1)) if match else 0
    
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