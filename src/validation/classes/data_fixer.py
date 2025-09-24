"""
Production data fixer implementation following standardized interfaces.
"""

import json
import os
import shutil
import subprocess
import time
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
        self.translation_cache: Dict[Tuple[str, str], str] = {}
        self.available_languages: Set[str] = set()
        self.language_updates: Dict[str, Set[str]] = {}
        self.verbose: bool = False
        self.auto_format: bool = False
        self.prettier_command: Optional[List[str]] = None
        self.prettier_batch_size: int = 50
        self._html_files_to_format: Set[Path] = set()
        self.formatted_files: Set[Path] = set()
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
        self.language_updates = {}
        self._html_files_to_format = set()
        self.formatted_files = set()

    def _initialize_languages(self, target_dir: Path):
        i18n_dir = target_dir / "content" / "i18n"
        if not i18n_dir.exists():
            return

        for lang_dir in i18n_dir.iterdir():
            if lang_dir.is_dir():
                self._log(f"Discovered language directory: {lang_dir.name}")
                self._ensure_language_loaded(target_dir, lang_dir.name)

    def _ensure_language_loaded(self, target_dir: Path, lang_code: str):
        if lang_code not in self.json_cache:
            self._load_json_file(target_dir, lang_code)
        self.available_languages.add(lang_code)
        self.language_updates.setdefault(lang_code, set())

    def _detect_prettier_command(self) -> Optional[List[str]]:
        prettier_path = shutil.which("prettier")
        if prettier_path:
            self._log(f"Detected Prettier executable at {prettier_path}")
            return [prettier_path, "--write"]

        npx_path = shutil.which("npx")
        if npx_path:
            self._log(f"Detected npx at {npx_path}; will invoke Prettier via npx")
            return [npx_path, "prettier", "--write"]

        self._log(
            "Prettier command could not be located; HTML formatting will be skipped",
            force=True,
        )
        return None

    def _log(self, message: str, force: bool = False):
        if self.verbose or force:
            print(f"[ADTDataFixer] {message}", flush=True)

    def process_page_range(self, config: PageProcessConfig, **kwargs) -> ProcessResult:
        """Process data fixing for a range of pages."""
        errors = self.validate_config(config)
        if errors:
            return ProcessResult(success=False, errors=errors)

        self.verbose = bool(getattr(config, 'verbose', False))
        self.auto_format = bool(kwargs.get("auto_format", False))
        target_dir = Path(config.target_dir) if config.target_dir else Path.cwd()
        self._log(f"Starting data fixing in {target_dir}")

        result = ProcessResult(success=True)

        self._reset_state()
        self._initialize_languages(target_dir)

        if not self.available_languages:
            self._log("No languages detected; aborting data fixing", force=True)
            return ProcessResult(
                success=False,
                errors=[
                    f"No language subdirectories found in {target_dir / 'content' / 'i18n'}"
                ],
            )

        # Find HTML files only in the root directory (not subdirectories)
        html_files = list(target_dir.glob("*.html"))
        if not html_files:
            return ProcessResult(success=False, errors=["No HTML files found"])

        # Filter out non-content files (assets, tests, navigation, etc.)
        html_files = self.validator._filter_content_files(html_files)

        # Filter by page range if specified
        if config.start_page != -1 or config.end_page != -1:
            html_files = self.validator._filter_by_page_range(
                html_files, config.start_page, config.end_page
            )

        total_fixes = 0
        json_files_updated = set()

        for html_file in html_files:
            try:
                self._log(f"Processing HTML file: {html_file}")
                page_result = self.fix_page(
                    self.validator._extract_page_number(html_file), html_file
                )
                if page_result.get("fixes", 0) > 0:
                    total_fixes += page_result["fixes"]
                    if page_result.get("json_files_updated"):
                        json_files_updated.update(page_result["json_files_updated"])
                result.processed_pages.append(page_result.get("page_number", 0))
                self._log(
                    f"Finished {html_file}: fixes={page_result.get('fixes', 0)}, updated_languages={page_result.get('json_files_updated', set())}"
                )
            except Exception as e:
                result.errors.append(f"Error fixing {html_file}: {str(e)}")

        try:
            self._log("Synchronizing missing translations across languages")
            sync_updates = self._sync_missing_translations(target_dir)
            json_files_updated.update(sync_updates)
        except Exception as exc:
            result.errors.append(str(exc))
            result.success = False

        # Save updated JSON files
        if json_files_updated and not kwargs.get("dry_run", False):
            self._save_json_files(target_dir, json_files_updated)

        self._format_pending_html_files(dry_run=kwargs.get("dry_run", False))

        result.metadata = {
            "total_files": len(html_files),
            "total_fixes": total_fixes,
            "json_files_updated": len(json_files_updated),
            "updated_languages": sorted(json_files_updated),
        }

        added_translations = {
            language: sorted(data_ids)
            for language, data_ids in self.language_updates.items()
            if data_ids
        }

        if added_translations:
            result.metadata["added_translations"] = added_translations

        if self.formatted_files:
            result.metadata["formatted_files"] = [
                str(path) for path in sorted(self.formatted_files, key=lambda p: str(p))
            ]

        return result

    def fix_page(self, page_number: int, page_path: Path) -> Dict[str, Any]:
        """Fix issues in a single HTML page."""
        try:
            with open(page_path, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")

            page_id = str(page_number) if page_number > 0 else "0"

            # Fix elements
            fixes = 0
            json_files_updated: Set[str] = set()

            for element in soup.find_all(True):
                if self._should_fix_element(element):
                    did_fix, updated_languages = self._fix_element_data_id(
                        element, page_id, page_path.parent
                    )
                    if did_fix:
                        fixes += 1
                        json_files_updated.update(updated_languages)

            # Save HTML file if changes were made
            if fixes > 0:
                with open(page_path, "w", encoding="utf-8") as f:
                    f.write(str(soup))
                self._html_files_to_format.add(page_path)
                self._log(f"Queued {page_path} for formatting")

            return {
                "page_number": page_number,
                "file_path": str(page_path),
                "fixes": fixes,
                "json_files_updated": json_files_updated,
            }

        except Exception as e:
            raise ProcessingError(f"Failed to fix page {page_number}: {str(e)}")

    def _format_pending_html_files(self, dry_run: bool):
        if not self.auto_format:
            if self._html_files_to_format and self.verbose:
                self._log(
                    "Skipping HTML formatting because --auto-format was not enabled"
                )
            self._html_files_to_format.clear()
            return

        self._log(
            f"Preparing to format {len(self._html_files_to_format)} HTML file(s); dry_run={dry_run}"
        )
        if dry_run:
            if self._html_files_to_format:
                self._log(
                    "Skipping HTML formatting because dry-run mode is enabled"
                )
            self._html_files_to_format.clear()
            return

        if not self.prettier_command:
            self.prettier_command = self._detect_prettier_command()

        if not self.prettier_command or not self._html_files_to_format:
            if not self.prettier_command and self._html_files_to_format:
                self._log(
                    "Cannot format HTML files because Prettier command was not found",
                    force=True,
                )
            self._html_files_to_format.clear()
            return

        files_to_format = sorted(self._html_files_to_format, key=lambda p: str(p))
        total_files = len(files_to_format)
        if total_files == 0:
            self._html_files_to_format.clear()
            return

        self._log(
            f"Formatting {total_files} HTML file(s) with Prettier in batches of {self.prettier_batch_size}"
        )

        success = True
        for batch_index in range(0, total_files, self.prettier_batch_size):
            batch = files_to_format[batch_index : batch_index + self.prettier_batch_size]
            batch_number = (batch_index // self.prettier_batch_size) + 1
            total_batches = (total_files + self.prettier_batch_size - 1) // self.prettier_batch_size
            self._log(
                f"Running Prettier batch {batch_number}/{total_batches} containing {len(batch)} file(s)"
            )
            if not self._run_prettier_batch(batch):
                success = False
                break

        if not success:
            self._log(
                "Prettier formatting aborted; some files may remain unformatted", force=True
            )

        self._html_files_to_format.clear()

    def _run_prettier_batch(self, files: List[Path]) -> bool:
        if not self.prettier_command or not files:
            return False

        command = [*self.prettier_command, *[str(path) for path in files]]
        self._log(f"Executing: {' '.join(command)}")
        start_time = time.time()

        try:
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                text=True,
                timeout=300,
            )
        except FileNotFoundError:
            self.prettier_command = None
            return False
        except subprocess.TimeoutExpired:
            self._log(
                "Prettier formatting timed out after 300 seconds; disabling further formatting",
                force=True,
            )
            self.prettier_command = None
            return False
        except Exception:
            self._log("Unexpected error while running Prettier; skipping formatting", force=True)
            return False

        duration = time.time() - start_time

        if completed.returncode == 0:
            self.formatted_files.update(files)
            if completed.stdout.strip():
                self._log(f"Prettier output:\n{completed.stdout.strip()}")
            self._log(
                f"Prettier formatted {len(files)} file(s) in {duration:.2f} seconds"
            )
            return True

        self._log(
            f"Prettier exited with code {completed.returncode}; disabling formatting",
            force=True,
        )
        if completed.stderr.strip():
            self._log(
                f"Prettier error output:\n{completed.stderr.strip()}", force=True
            )
        self.prettier_command = None
        return False

    def _should_fix_element(self, element) -> bool:
        """Check if element should be fixed (needs data-id)."""
        if not hasattr(element, "name"):
            return False

        # Skip these tags completely (don't process)
        if element.name.lower() in self.validator.skip_tags:
            return False

        # Already has data-id, no need to fix
        if element.get("data-id"):
            return False

        # Check for meaningful direct text
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(
                content, Comment
            ):
                direct_text += str(content)

        # Only fix if element has text content AND is not a container tag
        return (
            bool(direct_text.strip())
            and element.name.lower() not in self.validator.container_tags
        )

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
            with open(json_path, "r", encoding="utf-8") as f:
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
        return " ".join(text.strip().split())

    def _record_language_update(self, language: str, data_id: str):
        if not data_id:
            return
        self.language_updates.setdefault(language, set()).add(data_id)

    def _find_existing_data_id(self, text: str) -> Optional[str]:
        """Find existing data-id for text in any language."""
        normalized_text = self._normalize_text(text)
        for reverse_map in self.json_reverse_cache.values():
            data_id = reverse_map.get(normalized_text)
            if data_id:
                return data_id
        return None

    def _get_next_incremental_id(self, page_id: str) -> int:
        """Get next available incremental ID."""
        pattern = f"text-{page_id}-"

        existing_nums = []
        for data in self.json_cache.values():
            for key in data.keys():
                if key.startswith(pattern):
                    try:
                        num_part = key[len(pattern) :]
                        existing_nums.append(int(num_part))
                    except ValueError:
                        continue

        return max(existing_nums, default=-1) + 1

    def _backfill_translations_for_key(
        self, data_id: str, base_text: str, languages: Set[str], target_dir: Path
    ) -> Set[str]:
        languages_updated: Set[str] = set()

        for language in languages:
            self._ensure_language_loaded(target_dir, language)
            if data_id in self.json_cache.get(language, {}):
                continue

            if not self._normalize_text(base_text):
                translated_value = base_text
            else:
                translated_value = self._translate_text(base_text, language)
            self.json_cache[language][data_id] = translated_value
            self._record_language_update(language, data_id)
            normalized = self._normalize_text(translated_value)
            if language not in self.json_reverse_cache:
                self.json_reverse_cache[language] = {}
            if normalized:
                self.json_reverse_cache[language][normalized] = data_id
            languages_updated.add(language)

        return languages_updated

    def _add_translations_for_new_key(
        self, new_key: str, base_text: str, target_dir: Path
    ) -> Set[str]:
        languages_to_update = set(self.available_languages)

        for language in languages_to_update:
            self._ensure_language_loaded(target_dir, language)

        languages_updated: Set[str] = set()
        for language in languages_to_update:
            if new_key in self.json_cache.get(language, {}):
                continue

            if not self._normalize_text(base_text):
                translated_value = base_text
            else:
                translated_value = self._translate_text(base_text, language)

            self.json_cache[language][new_key] = translated_value
            self._record_language_update(language, new_key)
            normalized = self._normalize_text(translated_value)
            if language not in self.json_reverse_cache:
                self.json_reverse_cache[language] = {}
            if normalized:
                self.json_reverse_cache[language][normalized] = new_key
            languages_updated.add(language)

        return languages_updated

    def _translate_text(self, text: str, target_lang: str) -> str:
        if not self.openai_client:
            raise ProcessingError(
                "OpenAI API key is required to generate translations for other languages"
            )

        cache_key = (target_lang, text)
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Preserve placeholders, HTML entities, and meaning.",
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Translate the following text to language code '{target_lang}'. "
                            "If the text is already in that language, return it unchanged. "
                            "Preserve numbers, HTML entities, placeholders, and formatting.\n\n"
                            "Only return the translation, no other text or comments."
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
        self, element, page_id: str, target_dir: Path
    ) -> Tuple[bool, Set[str]]:
        """Fix missing data-id for element."""
        # Get element text
        direct_text = ""
        for content in element.contents:
            if isinstance(content, NavigableString) and not isinstance(
                content, Comment
            ):
                direct_text += str(content)

        text = self._normalize_text(direct_text)
        if not text:
            return False, set()

        # Try to find existing data-id
        existing_data_id = self._find_existing_data_id(text)

        if existing_data_id:
            missing_languages = {
                language
                for language in self.available_languages
                if existing_data_id not in self.json_cache.get(language, {})
            }
            languages_updated = set()
            if missing_languages:
                languages_updated = self._backfill_translations_for_key(
                    existing_data_id, text, missing_languages, target_dir
                )

            element["data-id"] = existing_data_id
            return True, languages_updated

        incremental = self._get_next_incremental_id(page_id)
        new_key = f"text-{page_id}-{incremental}"

        updated_languages = self._add_translations_for_new_key(
            new_key, text, target_dir
        )

        element["data-id"] = new_key
        return True, updated_languages

    def _select_source_translation(self, texts: Dict[str, str]) -> Tuple[str, str]:
        preferred_order = ["es", "en"]
        for lang in preferred_order:
            if lang in texts and self._normalize_text(texts[lang]):
                return lang, texts[lang]

        for lang in sorted(texts.keys()):
            if self._normalize_text(texts[lang]):
                return lang, texts[lang]

        # fallback to first entry (even if empty)
        lang, text = next(iter(texts.items()))
        return lang, text

    def _sync_missing_translations(self, target_dir: Path) -> Set[str]:
        languages = sorted(self.available_languages)
        if not languages:
            return set()

        for language in languages:
            self._ensure_language_loaded(target_dir, language)

        all_keys: Set[str] = set()
        for language in languages:
            all_keys.update(self.json_cache.get(language, {}).keys())

        self._log(
            f"Checking {len(all_keys)} data-id key(s) across {len(languages)} language(s)"
        )

        languages_updated: Set[str] = set()

        for data_id in all_keys:
            existing_texts = {
                language: self.json_cache.get(language, {}).get(data_id, "")
                for language in languages
                if data_id in self.json_cache.get(language, {})
            }

            if not existing_texts:
                continue

            source_lang, source_text = self._select_source_translation(existing_texts)

            for language in languages:
                cache = self.json_cache.setdefault(language, {})
                reverse_cache = self.json_reverse_cache.setdefault(language, {})

                if data_id in cache:
                    normalized_existing = self._normalize_text(cache[data_id])
                    if normalized_existing:
                        reverse_cache[normalized_existing] = data_id
                    continue

                if not self._normalize_text(source_text):
                    translated_value = source_text
                elif language == source_lang:
                    translated_value = source_text
                else:
                    translated_value = self._translate_text(source_text, language)

                cache[data_id] = translated_value
                self._record_language_update(language, data_id)
                normalized = self._normalize_text(translated_value)
                if normalized:
                    reverse_cache[normalized] = data_id
                languages_updated.add(language)

        return languages_updated

    def _save_json_files(self, target_dir: Path, lang_codes: set):
        """Save updated JSON files."""
        for lang_code in lang_codes:
            json_path = target_dir / "content" / "i18n" / lang_code / "texts.json"
            json_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                sorted_data = dict(sorted(self.json_cache[lang_code].items()))
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(sorted_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass  # Continue with other files
