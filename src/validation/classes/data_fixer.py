"""
Production data fixer implementation following standardized interfaces.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from bs4 import BeautifulSoup, NavigableString, Comment

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ...core import DataFixer, PageProcessConfig, ProcessResult, ProcessingError
from .adt_validator import ADTValidator


class ADTDataFixer(DataFixer):
    """Production ADT data-id fixer."""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.validator = ADTValidator()
        self.json_cache: Dict[str, Dict[str, str]] = {}
        self.json_reverse_cache: Dict[str, Dict[str, str]] = {}
        self.translation_cache: Dict[Tuple[str, str, str], str] = {}
        self.available_languages: Set[str] = set()
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.openai_client = None

        if self.openai_api_key:
            if OpenAI is None:
                raise ProcessingError(
                    "openai package is required to translate texts but is not installed"
                )
            self.openai_client = OpenAI(api_key=self.openai_api_key)
        
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

    def _reset_state(self):
        self.json_cache = {}
        self.json_reverse_cache = {}
        self.translation_cache = {}
        self.available_languages = set()

    def _initialize_languages(self, target_dir: Path):
        i18n_dir = target_dir / "content" / "i18n"
        if not i18n_dir.exists():
            return

        for lang_dir in i18n_dir.iterdir():
            if lang_dir.is_dir():
                self._ensure_language_loaded(target_dir, lang_dir.name)

    def _ensure_language_loaded(self, target_dir: Path, lang_code: str):
        if lang_code not in self.json_cache:
            self._load_json_file(target_dir, lang_code)
        self.available_languages.add(lang_code)
    
    def process_page_range(self, config: PageProcessConfig, **kwargs) -> ProcessResult:
        """Process data fixing for a range of pages."""
        errors = self.validate_config(config)
        if errors:
            return ProcessResult(success=False, errors=errors)
        
        result = ProcessResult(success=True)
        target_dir = Path(config.target_dir) if config.target_dir else Path.cwd()

        self._reset_state()
        self._initialize_languages(target_dir)
        
        # Find HTML files only in the root directory (not subdirectories)
        html_files = list(target_dir.glob("*.html"))
        if not html_files:
            return ProcessResult(success=False, errors=["No HTML files found"])
        
        # Filter out non-content files (assets, tests, navigation, etc.)
        html_files = self.validator._filter_content_files(html_files)
        
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
            
            self._ensure_language_loaded(page_path.parent, lang_code)

            # Fix elements
            fixes = 0
            json_files_updated: Set[str] = set()

            for element in soup.find_all(True):
                if self._should_fix_element(element):
                    did_fix, updated_languages = self._fix_element_data_id(
                        element, lang_code, page_id, page_path.parent
                    )
                    if did_fix:
                        fixes += 1
                        json_files_updated.update(updated_languages)
            
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
        if not hasattr(element, 'name'):
            return False
            
        # Skip these tags completely (don't process)
        if element.name.lower() in self.validator.skip_tags:
            return False
        
        # Already has data-id, no need to fix
        if element.get('data-id'):
            return False
        
        # Check for meaningful direct text
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(content, Comment):
                direct_text += str(content)
        
        # Only fix if element has text content AND is not a container tag
        return bool(direct_text.strip()) and element.name.lower() not in self.validator.container_tags
    
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
        pattern = f"text-{page_id}-"
        
        existing_nums = []
        for data in self.json_cache.values():
            for key in data.keys():
                if key.startswith(pattern):
                    try:
                        num_part = key[len(pattern):]
                        existing_nums.append(int(num_part))
                    except ValueError:
                        continue

        return max(existing_nums, default=-1) + 1

    def _add_translations_for_new_key(
        self, new_key: str, source_text: str, source_lang: str, target_dir: Path
    ) -> Set[str]:
        languages_to_update = set(self.available_languages)
        languages_to_update.add(source_lang)

        for language in languages_to_update:
            self._ensure_language_loaded(target_dir, language)

        languages_updated: Set[str] = set()
        for language in languages_to_update:
            if new_key in self.json_cache.get(language, {}):
                continue

            if language == source_lang:
                translated_value = source_text
            else:
                translated_value = self._translate_text(source_text, source_lang, language)

            self.json_cache[language][new_key] = translated_value
            normalized = self._normalize_text(translated_value)
            if language not in self.json_reverse_cache:
                self.json_reverse_cache[language] = {}
            if normalized:
                self.json_reverse_cache[language][normalized] = new_key
            languages_updated.add(language)

        return languages_updated

    def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        if source_lang == target_lang:
            return text

        if not self.openai_client:
            raise ProcessingError(
                "OpenAI API key is required to generate translations for other languages"
            )

        cache_key = (source_lang, target_lang, text)
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Preserve placeholders, HTML entities, and meaning.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate the following text from {source_lang} to {target_lang}. "
                            "Return only the translated text without additional commentary:\n\n"
                            f"{text}"
                        ),
                    },
                ],
                temperature=0.2,
            )
        except Exception as exc:
            raise ProcessingError(
                f"Translation failed for language '{target_lang}': {exc}"
            ) from exc

        try:
            translated_text = response.choices[0].message.content.strip()
        except (AttributeError, IndexError, KeyError) as exc:
            raise ProcessingError(
                f"Unexpected translation response structure for language '{target_lang}'"
            ) from exc

        if not translated_text:
            translated_text = text

        self.translation_cache[cache_key] = translated_text
        return translated_text
    
    def _fix_element_data_id(
        self, element, lang_code: str, page_id: str, target_dir: Path
    ) -> Tuple[bool, Set[str]]:
        """Fix missing data-id for element."""
        # Get element text
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(content, Comment):
                direct_text += str(content)

        text = self._normalize_text(direct_text)
        if not text:
            return False, set()

        # Try to find existing data-id
        existing_data_id = self._find_existing_data_id(text, lang_code)

        if existing_data_id:
            element['data-id'] = existing_data_id
            return True, set()

        incremental = self._get_next_incremental_id(lang_code, page_id)
        new_key = f"text-{page_id}-{incremental}"

        updated_languages = self._add_translations_for_new_key(
            new_key, text, lang_code, target_dir
        )

        element['data-id'] = new_key
        return True, updated_languages
    
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
