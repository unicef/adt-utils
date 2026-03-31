"""Audio timecode generation using Whisper transcription."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup
from openai import OpenAI

from ...core import PageRangeProcessor, ProcessResult, TimecodeGenerationConfig


class AudioTimecodeGenerator(PageRangeProcessor):
    """Generate ADT timecode JSON files from language audio files."""

    SUPPORTED_AUDIO_EXTENSIONS = {
        ".m4a",
        ".mp3",
        ".wav",
        ".ogg",
        ".flac",
        ".mpga",
        ".mpeg",
        ".webm",
    }

    def __init__(
        self,
        openai_api_key: str,
        logger: Optional[logging.Logger] = None,
        model: str = "whisper-1",
    ):
        self.client = OpenAI(api_key=openai_api_key)
        self.logger = logger or logging.getLogger(__name__)
        self.model = model

    def validate_config(self, config: TimecodeGenerationConfig) -> List[str]:
        """Validate configuration before processing."""
        errors: List[str] = []

        if not config.target_dir:
            errors.append("target_dir is required")
            return errors

        target_dir = Path(config.target_dir)
        if not target_dir.exists():
            errors.append(f"Target directory does not exist: {target_dir}")

        if not config.language or not config.language.strip():
            errors.append("language is required")

        audio_dir = self._audio_dir_for_config(config)
        if not audio_dir.exists():
            errors.append(f"Audio directory does not exist: {audio_dir}")

        return errors

    def process_page_range(
        self, config: TimecodeGenerationConfig, **kwargs: Any
    ) -> ProcessResult:
        """Generate timecode files for audio files inside a page range."""
        self.model = config.model
        errors = self.validate_config(config)
        if errors:
            return ProcessResult(success=False, errors=errors)

        audio_dir = self._audio_dir_for_config(config)
        timecode_dir = self._timecode_dir_for_config(config)
        texts_dict = self._load_texts_dict(config)
        html_page_map = self._build_html_page_map(config.target_dir)

        files = self._find_audio_files(audio_dir)
        files = self._filter_audio_files_by_page_range(
            files,
            config.start_page,
            config.end_page,
        )

        result = ProcessResult(success=True)
        generated_files = 0
        failed_files = 0
        seen_pages = set()

        for audio_path in files:
            try:
                page_id = audio_path.stem
                page_number = self._extract_page_number_from_audio_name(audio_path)
                if page_number is not None:
                    seen_pages.add(page_number)

                if page_id in html_page_map:
                    page_text_entries = self._load_text_entries_from_html(
                        html_page_map[page_id], texts_dict
                    )
                else:
                    self.logger.warning(
                        "No HTML found for page %s, falling back to texts.json", page_id
                    )
                    page_text_entries = self._load_text_entries_from_texts_dict(
                        page_number, texts_dict
                    )

                payload = self._generate_timecode_payload(
                    audio_path=audio_path,
                    page_id=page_id,
                    page_number=page_number,
                    language=config.language,
                    page_text_entries=page_text_entries,
                    strict_data_ids=config.strict_data_ids,
                )

                output_file = timecode_dir / f"{audio_path.stem}.json"
                if config.dry_run:
                    self.logger.info("Dry run: would write %s", output_file)
                else:
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)

                generated_files += 1
            except Exception as exc:
                failed_files += 1
                result.errors.append(f"Failed for {audio_path.name}: {exc}")
                self.logger.exception("Failed to generate timecode for %s", audio_path)

        result.processed_pages = sorted(seen_pages)
        result.metadata = {
            "audio_dir": str(audio_dir),
            "timecode_dir": str(timecode_dir),
            "matched_audio_files": len(files),
            "generated_files": generated_files,
            "failed_files": failed_files,
            "dry_run": config.dry_run,
            "language": config.language,
            "model": config.model,
            "strict_data_ids": config.strict_data_ids,
            "texts_data_ids_loaded": len(texts_dict),
            "html_pages_found": len(html_page_map),
        }

        if failed_files > 0:
            result.success = False

        return result

    def _audio_dir_for_config(self, config: TimecodeGenerationConfig) -> Path:
        return Path(config.target_dir) / "content" / "i18n" / config.language / "audio"

    def _timecode_dir_for_config(self, config: TimecodeGenerationConfig) -> Path:
        return Path(config.target_dir) / "content" / "i18n" / config.language / "timecode"

    def _find_audio_files(self, audio_dir: Path) -> List[Path]:
        audio_files = [
            file_path
            for file_path in audio_dir.glob("*")
            if file_path.is_file()
            and file_path.suffix.lower() in self.SUPPORTED_AUDIO_EXTENSIONS
        ]
        return sorted(audio_files)

    def _filter_audio_files_by_page_range(
        self,
        files: List[Path],
        start_page: int,
        end_page: int,
    ) -> List[Path]:
        if start_page == -1 and end_page == -1:
            return files

        filtered: List[Path] = []
        for file_path in files:
            page_number = self._extract_page_number_from_audio_name(file_path)

            if page_number is None:
                continue
            if start_page != -1 and page_number < start_page:
                continue
            if end_page != -1 and page_number > end_page:
                continue
            filtered.append(file_path)

        return filtered

    def _extract_page_number_from_audio_name(self, file_path: Path) -> Optional[int]:
        """Extract page from names like 7_0.m4a, where 7 is the page."""
        stem = file_path.stem
        first_part = stem.split("_", 1)[0]
        if first_part.isdigit():
            return int(first_part)
        return None

    def _generate_timecode_payload(
        self,
        audio_path: Path,
        page_id: str,
        page_number: Optional[int],
        language: str,
        page_text_entries: List[Dict[str, str]],
        strict_data_ids: bool,
    ) -> Dict[str, Any]:
        transcription = self._transcribe_audio(audio_path, language)
        return self._build_timecode_payload(
            page_id=page_id,
            page_number=page_number,
            transcription=transcription,
            page_text_entries=page_text_entries,
            strict_data_ids=strict_data_ids,
        )

    def _load_text_entries_by_page(
        self,
        config: TimecodeGenerationConfig,
    ) -> Dict[int, List[Dict[str, str]]]:
        """Load data-id keys and text values from texts.json grouped by page."""
        texts_json = (
            Path(config.target_dir)
            / "content"
            / "i18n"
            / config.language
            / "texts.json"
        )

        if not texts_json.exists():
            self.logger.warning("texts.json not found at %s", texts_json)
            return {}

        try:
            with open(texts_json, "r", encoding="utf-8") as f:
                texts = json.load(f)
        except Exception as exc:
            self.logger.warning("Failed to read texts.json at %s: %s", texts_json, exc)
            return {}

        if not isinstance(texts, dict):
            self.logger.warning("texts.json at %s is not an object", texts_json)
            return {}

        grouped: Dict[int, List[Dict[str, str]]] = {}
        for key, value in texts.items():
            if not isinstance(key, str):
                continue
            page_number = self._extract_page_number_from_data_id(key)
            if page_number is None:
                continue
            grouped.setdefault(page_number, []).append(
                {
                    "id": key,
                    "text": str(value) if value is not None else "",
                }
            )

        for page_number, entries in grouped.items():
            grouped[page_number] = sorted(
                entries,
                key=lambda entry: self._data_id_sort_key(entry["id"]),
            )

        self.logger.info(
            "Loaded %s data-id keys from %s",
            sum(len(ids) for ids in grouped.values()),
            texts_json,
        )
        return grouped

    def _load_texts_dict(self, config: TimecodeGenerationConfig) -> Dict[str, str]:
        """Load texts.json as a flat data_id → text mapping."""
        texts_json = (
            Path(config.target_dir)
            / "content"
            / "i18n"
            / config.language
            / "texts.json"
        )
        if not texts_json.exists():
            self.logger.warning("texts.json not found at %s", texts_json)
            return {}
        try:
            with open(texts_json, "r", encoding="utf-8") as f:
                texts = json.load(f)
        except Exception as exc:
            self.logger.warning("Failed to read texts.json at %s: %s", texts_json, exc)
            return {}
        if not isinstance(texts, dict):
            return {}
        return {
            k: str(v) if v is not None else ""
            for k, v in texts.items()
            if isinstance(k, str)
        }

    def _build_html_page_map(self, target_dir: str) -> Dict[str, Path]:
        """Scan root HTML files and build a page_id → html_path map via page-section-id meta."""
        page_map: Dict[str, Path] = {}
        for html_path in sorted(Path(target_dir).glob("*.html")):
            try:
                with open(html_path, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f, "html.parser")
                meta = soup.find("meta", attrs={"name": "page-section-id"})
                if meta and meta.get("content"):
                    page_map[str(meta["content"])] = html_path
            except Exception as exc:
                self.logger.warning("Failed to read HTML %s: %s", html_path, exc)
        self.logger.info("Found %d HTML pages in %s", len(page_map), target_dir)
        return page_map

    def _load_text_entries_from_html(
        self,
        html_path: Path,
        texts_dict: Dict[str, str],
    ) -> List[Dict[str, str]]:
        """Extract text data-ids in DOM order from an HTML page, resolved against texts.json."""
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f, "html.parser")
        except Exception as exc:
            self.logger.warning("Failed to parse HTML %s: %s", html_path, exc)
            return []

        entries = []
        seen: set = set()
        for element in soup.find_all(attrs={"data-id": True}):
            data_id = str(element.get("data-id", "")).strip()
            if not data_id or data_id in seen:
                continue
            if self._extract_page_number_from_data_id(data_id) is None:
                continue  # skip section IDs, aria IDs, img IDs, etc.
            seen.add(data_id)
            text = texts_dict.get(
                data_id, element.get_text(separator=" ").strip()
            )
            entries.append({"id": data_id, "text": text})

        self.logger.debug("Extracted %d text entries from %s", len(entries), html_path)
        return entries

    def _load_text_entries_from_texts_dict(
        self,
        page_number: Optional[int],
        texts_dict: Dict[str, str],
    ) -> List[Dict[str, str]]:
        """Fallback: filter texts_dict by page number and return sorted entries."""
        if page_number is None:
            return []
        entries = [
            {"id": k, "text": v}
            for k, v in texts_dict.items()
            if self._extract_page_number_from_data_id(k) == page_number
        ]
        return sorted(entries, key=lambda e: self._data_id_sort_key(e["id"]))

    def _extract_page_number_from_data_id(self, data_id: str) -> Optional[int]:
        """Extract page number from data-id values like text-7-0 or txt_p63_g0_t0."""
        if data_id.startswith("text-"):
            parts = data_id.split("-")
            if len(parts) >= 2 and parts[1].isdigit():
                return int(parts[1])

        if data_id.startswith("txt_p"):
            remainder = data_id[len("txt_p") :]
            page_part = remainder.split("_", 1)[0]
            if page_part.isdigit():
                return int(page_part)

        return None

    def _data_id_sort_key(self, data_id: str) -> Any:
        if data_id.startswith("text-"):
            parts = data_id.split("-")
            index = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 10**9
            return (0, index, data_id)

        if data_id.startswith("txt_p"):
            g_index = 10**9
            t_index = 10**9
            for part in data_id.split("_"):
                if part.startswith("g") and part[1:].isdigit():
                    g_index = int(part[1:])
                if part.startswith("t") and part[1:].isdigit():
                    t_index = int(part[1:])
            return (1, g_index, t_index, data_id)

        return (2, data_id)

    def _transcribe_audio(self, audio_path: Path, language: str) -> Dict[str, Any]:
        transcription_language = self._transcription_language(language)

        with open(audio_path, "rb") as audio_file:
            try:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=transcription_language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"],
                )
            except Exception:
                audio_file.seek(0)
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=transcription_language,
                    response_format="verbose_json",
                )

        if hasattr(response, "model_dump"):
            return response.model_dump()
        if isinstance(response, dict):
            return response
        if hasattr(response, "to_dict"):
            return response.to_dict()

        return json.loads(str(response))

    def _transcription_language(self, language: str) -> str:
        """Convert locale-style language codes to ISO-639-1 for Whisper."""
        normalized = language.strip().lower()
        if "-" in normalized:
            return normalized.split("-", 1)[0]
        if "_" in normalized:
            return normalized.split("_", 1)[0]
        return normalized

    def _build_timecode_payload(
        self,
        page_id: str,
        page_number: Optional[int],
        transcription: Dict[str, Any],
        page_text_entries: List[Dict[str, str]],
        strict_data_ids: bool,
    ) -> Dict[str, Any]:
        page_data_ids = [entry["id"] for entry in page_text_entries]
        segments: List[Dict[str, Any]] = transcription.get("segments") or []
        words: List[Dict[str, Any]] = transcription.get("words") or []

        if segments:
            elements = self._elements_from_segments(
                segments,
                words,
                page_number,
                page_data_ids,
                strict_data_ids,
            )
        elif words:
            elements = [
                self._single_element_from_words(
                    words,
                    page_number,
                    page_data_ids,
                    strict_data_ids,
                )
            ]
        else:
            full_text = str(transcription.get("text") or "").strip()
            elements = [
                self._single_element_from_text(
                    full_text,
                    page_number,
                    page_data_ids,
                    strict_data_ids,
                )
            ]

        if strict_data_ids:
            self._validate_data_id_count(page_id, page_data_ids, len(elements))

        if page_text_entries:
            elements = self._apply_reference_text(elements, page_text_entries)

        return {
            "page_id": page_id,
            "elements": elements,
        }

    def _apply_reference_text(
        self,
        transcribed_elements: List[Dict[str, Any]],
        page_text_entries: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Use texts.json wording and map OpenAI timing onto that wording."""
        openai_words: List[Dict[str, Any]] = []
        for element in transcribed_elements:
            for word in element.get("word_timestamps", []):
                openai_words.append(self._normalize_word(word))

        if openai_words:
            return self._build_elements_from_openai_words(page_text_entries, openai_words)

        return self._build_elements_from_time_window(page_text_entries, transcribed_elements)

    def _build_elements_from_openai_words(
        self,
        page_text_entries: List[Dict[str, str]],
        openai_words: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        token_lists = [
            self._split_reference_words(entry["text"]) for entry in page_text_entries
        ]
        weights = [max(len(tokens), 1) for tokens in token_lists]
        counts = self._allocate_counts(len(openai_words), weights)

        elements: List[Dict[str, Any]] = []
        cursor = 0
        previous_end = openai_words[0]["start"] if openai_words else 0.0

        for entry, tokens, count in zip(page_text_entries, token_lists, counts):
            assigned = openai_words[cursor : cursor + count]
            cursor += count

            if assigned:
                start = float(assigned[0]["start"])
                end = float(assigned[-1]["end"])
                previous_end = end
            else:
                start = previous_end
                end = previous_end

            word_timestamps = self._tokens_with_interpolated_timing(tokens, start, end)
            elements.append(
                {
                    "id": entry["id"],
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "word_timestamps": word_timestamps,
                }
            )

        return elements

    def _build_elements_from_time_window(
        self,
        page_text_entries: List[Dict[str, str]],
        transcribed_elements: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if transcribed_elements:
            global_start = float(transcribed_elements[0].get("start", 0.0))
            global_end = float(transcribed_elements[-1].get("end", global_start))
        else:
            global_start = 0.0
            global_end = 0.0

        if global_end < global_start:
            global_end = global_start

        token_lists = [
            self._split_reference_words(entry["text"]) for entry in page_text_entries
        ]
        weights = [max(len(tokens), 1) for tokens in token_lists]

        total_weight = sum(weights) if weights else 1
        total_duration = global_end - global_start
        elapsed = 0.0

        elements: List[Dict[str, Any]] = []
        for index, (entry, tokens, weight) in enumerate(
            zip(page_text_entries, token_lists, weights)
        ):
            start = global_start + elapsed
            if index == len(page_text_entries) - 1:
                end = global_end
            else:
                end = start + (total_duration * (weight / total_weight))

            elapsed = end - global_start
            word_timestamps = self._tokens_with_interpolated_timing(tokens, start, end)
            elements.append(
                {
                    "id": entry["id"],
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "word_timestamps": word_timestamps,
                }
            )

        return elements

    @staticmethod
    def _strip_html(text: str) -> str:
        """Strip HTML tags and decode HTML entities from text."""
        return BeautifulSoup(text, "html.parser").get_text()

    def _split_reference_words(self, text: str) -> List[str]:
        clean = self._strip_html(text)
        return [token for token in clean.split() if token]

    def _tokens_with_interpolated_timing(
        self,
        tokens: List[str],
        start: float,
        end: float,
    ) -> List[Dict[str, Any]]:
        if not tokens:
            return []

        if end < start:
            end = start

        if end == start:
            end = start + (0.2 * len(tokens))

        duration = end - start
        step = duration / len(tokens)
        mapped: List[Dict[str, Any]] = []

        for index, token in enumerate(tokens):
            token_start = start + (index * step)
            token_end = start + ((index + 1) * step)
            mapped.append(
                {
                    "text": token,
                    "start": round(token_start, 3),
                    "end": round(token_end, 3),
                }
            )

        return mapped

    def _allocate_counts(self, total: int, weights: List[int]) -> List[int]:
        if not weights:
            return []

        if total <= 0:
            return [0 for _ in weights]

        total_weight = sum(weights)
        raw = [(total * weight) / total_weight for weight in weights]
        base = [int(value) for value in raw]
        remainder = total - sum(base)

        ranked_indices = sorted(
            range(len(weights)),
            key=lambda idx: (raw[idx] - base[idx]),
            reverse=True,
        )

        for idx in ranked_indices[:remainder]:
            base[idx] += 1

        return base

    def _validate_data_id_count(
        self,
        page_id: str,
        page_data_ids: List[str],
        element_count: int,
    ) -> None:
        if not page_data_ids:
            raise ValueError(
                f"No matching data-ids found in texts.json for page_id '{page_id}'"
            )

        if len(page_data_ids) != element_count:
            raise ValueError(
                "Mismatch between texts.json data-ids "
                f"({len(page_data_ids)}) and generated elements ({element_count}) "
                f"for page_id '{page_id}'"
            )

    def _elements_from_segments(
        self,
        segments: List[Dict[str, Any]],
        words: List[Dict[str, Any]],
        page_number: Optional[int],
        page_data_ids: List[str],
        strict_data_ids: bool,
    ) -> List[Dict[str, Any]]:
        elements: List[Dict[str, Any]] = []
        epsilon = 0.001

        for index, segment in enumerate(segments, start=1):
            seg_start = float(segment.get("start", 0.0))
            seg_end = float(segment.get("end", seg_start))
            seg_text = str(segment.get("text") or "").strip()

            segment_words = [
                self._normalize_word(word)
                for word in words
                if self._word_inside_segment(word, seg_start, seg_end, epsilon)
            ]

            if not segment_words and seg_text:
                segment_words = self._estimate_word_timestamps(seg_text, seg_start, seg_end)

            element = {
                "id": self._element_id(
                    page_number,
                    index,
                    page_data_ids,
                    strict_data_ids,
                ),
                "start": round(seg_start, 3),
                "end": round(seg_end, 3),
                "word_timestamps": segment_words,
            }
            elements.append(element)

        return elements

    def _single_element_from_words(
        self,
        words: List[Dict[str, Any]],
        page_number: Optional[int],
        page_data_ids: List[str],
        strict_data_ids: bool,
    ) -> Dict[str, Any]:
        normalized_words = [self._normalize_word(word) for word in words]
        start = normalized_words[0]["start"] if normalized_words else 0.0
        end = normalized_words[-1]["end"] if normalized_words else 0.0

        return {
            "id": self._element_id(
                page_number,
                1,
                page_data_ids,
                strict_data_ids,
            ),
            "start": round(start, 3),
            "end": round(end, 3),
            "word_timestamps": normalized_words,
        }

    def _single_element_from_text(
        self,
        full_text: str,
        page_number: Optional[int],
        page_data_ids: List[str],
        strict_data_ids: bool,
    ) -> Dict[str, Any]:
        words = self._estimate_word_timestamps(full_text, 0.0, 0.0)
        return {
            "id": self._element_id(
                page_number,
                1,
                page_data_ids,
                strict_data_ids,
            ),
            "start": 0.0,
            "end": 0.0,
            "word_timestamps": words,
        }

    def _element_id(
        self,
        page_number: Optional[int],
        index: int,
        page_data_ids: List[str],
        strict_data_ids: bool,
    ) -> str:
        if index - 1 >= len(page_data_ids):
            if not strict_data_ids:
                page_component = str(page_number) if page_number is not None else "0"
                return f"text-{page_component}-{index}"

            raise ValueError(
                "Missing data-id for generated element "
                f"{index} on page {page_number if page_number is not None else 'unknown'}"
            )

        return page_data_ids[index - 1]

    def _word_inside_segment(
        self,
        word: Dict[str, Any],
        segment_start: float,
        segment_end: float,
        epsilon: float,
    ) -> bool:
        start = float(word.get("start", 0.0))
        end = float(word.get("end", start))
        return start >= segment_start - epsilon and end <= segment_end + epsilon

    def _normalize_word(self, word: Dict[str, Any]) -> Dict[str, Any]:
        text = str(word.get("word") or word.get("text") or "").strip()
        start = float(word.get("start", 0.0))
        end = float(word.get("end", start))
        return {
            "text": text,
            "start": round(start, 3),
            "end": round(end, 3),
        }

    def _estimate_word_timestamps(
        self,
        text: str,
        segment_start: float,
        segment_end: float,
    ) -> List[Dict[str, Any]]:
        tokens = [token for token in text.split() if token]
        if not tokens:
            return []

        if segment_end <= segment_start:
            segment_end = segment_start + (0.2 * len(tokens))

        duration = segment_end - segment_start
        step = duration / max(len(tokens), 1)

        estimated: List[Dict[str, Any]] = []
        for index, token in enumerate(tokens):
            start = segment_start + index * step
            end = segment_start + (index + 1) * step
            estimated.append(
                {
                    "text": token,
                    "start": round(start, 3),
                    "end": round(end, 3),
                }
            )

        return estimated