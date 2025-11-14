"""
HTML Text Override implementation for replacing text content using translations.
"""

import json
import logging
import re
import sys
import html
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, NavigableString
from src.utils.page_utils import filter_files_by_page_range, extract_page_number_from_data_id

# Ensure UTF-8 encoding for stdout
sys.stdout.reconfigure(encoding='utf-8')

class HTMLTextOverrider:
    """HTML text content overrider using translations from texts.json."""
    
    def __init__(
        self,
        target_dir: Path,
        logger: logging.Logger = None,
        dry_run: bool = False
    ):
        self.target_dir = target_dir
        self.logger = logger or logging.getLogger(__name__)
        self.dry_run = dry_run
        
        # Load configuration and texts
        self.config = self.load_config()
        self.default_language = self.get_default_language()
        self.texts = self.load_texts()
        
    def load_config(self) -> Dict:
        """Load configuration from assets/content/config.json."""
        config_path = self.target_dir / "assets" / "config.json"
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.logger.info(f"Loaded configuration from {config_path}")
            return config
        except Exception as e:
            raise Exception(f"Error loading configuration: {e}")
    
    def get_default_language(self) -> str:
        """Extract default language from configuration."""
        try:
            default_lang = self.config['languages']['default']
            self.logger.info(f"Default language: {default_lang}")
            return default_lang
        except KeyError:
            raise Exception("Default language not found in configuration")
    
    def load_texts(self) -> Dict[str, str]:
        """Load texts from the default language texts.json file."""
        texts_path = self.target_dir / "content" / "i18n" / self.default_language / "texts.json"
        if not texts_path.exists():
            raise FileNotFoundError(f"Texts file not found: {texts_path}")
        
        try:
            with open(texts_path, 'r', encoding='utf-8') as f:
                texts = json.load(f)
            self.logger.info(f"Loaded {len(texts)} text entries from {texts_path}")
            return texts
        except Exception as e:
            raise Exception(f"Error loading texts: {e}")
    
    def get_html_files(self, start_page: Optional[int] = None, end_page: Optional[int] = None) -> List[Path]:
        """Get list of HTML files to process, optionally filtered by page range using data-id attributes."""
        html_files = list(self.target_dir.glob("*.html"))
        
        # Use the utility function instead of duplicated filtering logic
        filtered_files = filter_files_by_page_range(
            files=html_files,
            start_page=start_page or -1,
            end_page=end_page or -1,
            use_data_id=True
        )
        
        self.logger.info(f"Found {len(filtered_files)} HTML files to process")
        return filtered_files
    
    def override_html_file(self, html_file: Path) -> Tuple[int, int]:
        """Override text content in a single HTML file for elements with txt_ or text- data-id attributes."""
        self.logger.info(f"Processing file: {html_file.name}")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            overrides_count = 0
            warnings_count = 0
            
            # Find elements with data-id attributes that start with txt_ or text-
            elements_with_data_id = soup.find_all(attrs={'data-id': re.compile(r'^(txt_|text-)')})
            
            self.logger.debug(f"  Found {len(elements_with_data_id)} elements with txt_/text- data-id attributes")
            
            for element in elements_with_data_id:
                data_id = element.get('data-id')
                
                if data_id in self.texts:
                    old_text = element.get_text().strip()
                    new_text = self.texts[data_id].strip()
                    
                    if old_text != new_text:
                        self.logger.debug(f"  {data_id}: '{old_text}' -> '{new_text}'")
                        
                        # Clear the element
                        element.clear()
                        
                        # Check if new_text contains HTML markup using BeautifulSoup
                        temp_soup = BeautifulSoup(new_text, 'html.parser')
                        has_html = any(getattr(node, 'name', None) is not None for node in temp_soup.contents)
                        
                        if has_html:
                            # Parse as HTML and insert the parsed content
                            self.logger.debug(f"    Detected HTML markup in: {data_id}")
                            for content_node in temp_soup.contents:
                                if isinstance(content_node, NavigableString):
                                    element.append(NavigableString(str(content_node)))
                                else:
                                    element.append(content_node)
                        else:
                            # Plain text - use NavigableString
                            self.logger.debug(f"    Plain text content: {data_id}")
                            element.append(NavigableString(new_text))
                        
                        overrides_count += 1
                    else:
                        self.logger.debug(f"  {data_id}: text already matches")
                else:
                    warning_msg = f"No translation found for data-id: {data_id}"
                    self.logger.warning(f"  {html_file.name}: {warning_msg}")
                    warnings_count += 1
            
            # Save the modified HTML
            if overrides_count > 0 and not self.dry_run:
                formatted_html = self.format_html(soup)
                with open(html_file, 'w', encoding='utf-8', newline='') as f:
                    f.write(formatted_html)
                self.logger.info(f"  Applied {overrides_count} text overrides to {html_file.name}")
            elif self.dry_run and overrides_count > 0:
                self.logger.info(f"  [DRY RUN] Would apply {overrides_count} text overrides to {html_file.name}")
            else:
                self.logger.info(f"  No changes needed for {html_file.name}")
            
            if warnings_count > 0:
                self.logger.info(f"  {warnings_count} warnings for missing translations in {html_file.name}")
            
            return overrides_count, warnings_count
            
        except Exception as e:
            error_msg = f"Error processing {html_file.name}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    def format_html(self, soup: BeautifulSoup) -> str:
        """Format HTML with prettify but preserve UTF-8 characters."""
        # Use prettify but then decode HTML entities back to UTF-8
        
        formatted = soup.prettify(formatter='html5', encoding=None)
        
        # Decode HTML entities back to UTF-8 characters
        # This converts &aacute; back to á, &ntilde; back to ñ, etc.
        decoded = html.unescape(formatted)
        
        return decoded
    
    def override_html_texts(
        self,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None
    ) -> Dict[str, int]:
        """Override text content in HTML files using texts.json translations."""
        self.logger.info(f"Starting HTML text override for default language: {self.default_language}")
        
        if start_page is not None and end_page is not None:
            self.logger.info(f"Processing pages {start_page} to {end_page}")
        elif start_page is not None:
            self.logger.info(f"Processing pages from {start_page}")
        elif end_page is not None:
            self.logger.info(f"Processing pages up to {end_page}")
        
        html_files = self.get_html_files(start_page, end_page)
        
        if not html_files:
            self.logger.warning("No HTML files found to process")
            return {
                'files_processed': 0,
                'total_overrides': 0,
                'total_warnings': 0,
                'errors': 0
            }
        
        total_overrides = 0
        total_warnings = 0
        files_processed = 0
        errors = 0
        
        for html_file in html_files:
            try:
                overrides_count, warnings_count = self.override_html_file(html_file)
                total_overrides += overrides_count
                total_warnings += warnings_count
                files_processed += 1
                
            except Exception as e:
                self.logger.error(f"Failed to process {html_file.name}: {e}")
                errors += 1
                continue
        
        results = {
            'files_processed': files_processed,
            'total_overrides': total_overrides,
            'total_warnings': total_warnings,
            'errors': errors
        }
        
        self.logger.info(f"HTML text override completed: {results}")
        return results