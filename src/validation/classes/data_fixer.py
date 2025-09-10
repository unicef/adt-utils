"""
Production data fixer implementation following standardized interfaces.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List
from bs4 import BeautifulSoup, NavigableString, Comment

from ...core import DataFixer, PageProcessConfig, ProcessResult, ProcessingError
from .adt_validator import ADTValidator


class ADTDataFixer(DataFixer):
    """Production ADT data-id fixer."""
    
    def __init__(self):
        self.validator = ADTValidator()
        self.json_cache = {}
        self.json_reverse_cache = {}
        
    def validate_config(self, config: PageProcessConfig) -> List[str]:
        """Validate configuration before processing."""
        errors = []
        if config.target_dir and not Path(config.target_dir).exists():
            errors.append(f"Target directory does not exist: {config.target_dir}")
        
        # Check if i18n structure exists
        if config.target_dir:
            i18n_dir = Path(config.target_dir) / "content" / "i18n"
            if not i18n_dir.exists():
                errors.append(f"I18n directory not found: {i18n_dir}")
        
        return errors
    
    def process_page_range(self, config: PageProcessConfig, **kwargs) -> ProcessResult:
        """Process data fixing for a range of pages."""
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
            html_files = self.validator._filter_by_page_range(html_files, config.start_page, config.end_page)
        
        total_fixes = 0
        json_files_updated = set()
        
        for html_file in html_files:
            try:
                page_result = self.fix_page(self.validator._extract_page_number(html_file), html_file)
                if page_result.get('fixes', 0) > 0:
                    total_fixes += page_result['fixes']
                    if page_result.get('json_files_updated'):
                        json_files_updated.update(page_result['json_files_updated'])
                result.processed_pages.append(page_result.get('page_number', 0))
            except Exception as e:
                result.errors.append(f"Error fixing {html_file}: {str(e)}")
        
        # Save updated JSON files
        if json_files_updated and not kwargs.get('dry_run', False):
            self._save_json_files(target_dir, json_files_updated)
        
        result.metadata = {
            'total_files': len(html_files),
            'total_fixes': total_fixes,
            'json_files_updated': len(json_files_updated),
            'updated_languages': list(json_files_updated)
        }
        
        return result
    
    def fix_page(self, page_number: int, page_path: Path) -> Dict[str, Any]:
        """Fix issues in a single HTML page."""
        try:
            with open(page_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Get language and page ID
            lang_code = self._get_html_lang(soup)
            page_id = str(page_number) if page_number > 0 else "0"
            
            # Load JSON file
            self._load_json_file(page_path.parent, lang_code)
            
            # Fix elements
            fixes = 0
            json_files_updated = set()
            
            for element in soup.find_all(True):
                if self._should_fix_element(element):
                    if self._fix_element_data_id(element, lang_code, page_id, page_path.parent):
                        fixes += 1
                        json_files_updated.add(lang_code)
            
            # Save HTML file if changes were made
            if fixes > 0:
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            
            return {
                'page_number': page_number,
                'file_path': str(page_path),
                'fixes': fixes,
                'json_files_updated': json_files_updated
            }
            
        except Exception as e:
            raise ProcessingError(f"Failed to fix page {page_number}: {str(e)}")
    
    def _should_fix_element(self, element) -> bool:
        """Check if element should be fixed (needs data-id)."""
        if not hasattr(element, 'name') or element.name in self.validator.exempt_tags:
            return False
        
        if element.get('data-id'):
            return False
        
        # Check for meaningful direct text
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(content, Comment):
                direct_text += str(content)
        
        return bool(direct_text.strip())
    
    def _get_html_lang(self, soup) -> str:
        """Extract language code from HTML."""
        html_element = soup.find('html')
        if html_element and html_element.get('lang'):
            return html_element['lang']
        return 'es'  # Default to Spanish
    
    def _load_json_file(self, target_dir: Path, lang_code: str):
        """Load and cache JSON file for a language."""
        if lang_code in self.json_cache:
            return
        
        json_path = target_dir / "content" / "i18n" / lang_code / "texts.json"
        
        if not json_path.exists():
            self.json_cache[lang_code] = {}
            self.json_reverse_cache[lang_code] = {}
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create reverse mapping
            reverse_map = {}
            for key, value in data.items():
                if isinstance(value, str) and key.startswith("text-"):
                    normalized_text = self._normalize_text(value)
                    reverse_map[normalized_text] = key
            
            self.json_cache[lang_code] = data
            self.json_reverse_cache[lang_code] = reverse_map
            
        except Exception:
            self.json_cache[lang_code] = {}
            self.json_reverse_cache[lang_code] = {}
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        return ' '.join(text.strip().split())
    
    def _find_existing_data_id(self, text: str, lang_code: str) -> str:
        """Find existing data-id for text."""
        normalized_text = self._normalize_text(text)
        return self.json_reverse_cache.get(lang_code, {}).get(normalized_text)
    
    def _get_next_incremental_id(self, lang_code: str, page_id: str) -> int:
        """Get next available incremental ID."""
        data = self.json_cache.get(lang_code, {})
        pattern = f"text-{page_id}-"
        
        existing_nums = []
        for key in data.keys():
            if key.startswith(pattern):
                try:
                    num_part = key[len(pattern):]
                    existing_nums.append(int(num_part))
                except ValueError:
                    continue
        
        return max(existing_nums, default=-1) + 1
    
    def _fix_element_data_id(self, element, lang_code: str, page_id: str, target_dir: Path) -> bool:
        """Fix missing data-id for element."""
        # Get element text
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(content, Comment):
                direct_text += str(content)
        
        text = self._normalize_text(direct_text)
        if not text:
            return False
        
        # Try to find existing data-id
        existing_data_id = self._find_existing_data_id(text, lang_code)
        
        if existing_data_id:
            element['data-id'] = existing_data_id
            return True
        else:
            # Create new data-id
            incremental = self._get_next_incremental_id(lang_code, page_id)
            new_key = f"text-{page_id}-{incremental}"
            
            # Add to cache
            self.json_cache[lang_code][new_key] = text
            self.json_reverse_cache[lang_code][self._normalize_text(text)] = new_key
            
            element['data-id'] = new_key
            return True
    
    def _save_json_files(self, target_dir: Path, lang_codes: set):
        """Save updated JSON files."""
        for lang_code in lang_codes:
            json_path = target_dir / "content" / "i18n" / lang_code / "texts.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                sorted_data = dict(sorted(self.json_cache[lang_code].items()))
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(sorted_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass  # Continue with other files