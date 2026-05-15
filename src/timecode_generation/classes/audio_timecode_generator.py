"""Audio timecode generation using Whisper transcription."""

import json
import logging
import re
import subprocess
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast

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
        text_model: Optional[str] = None,
    ):
        self.client = OpenAI(api_key=openai_api_key)
        self.logger = logger or logging.getLogger(__name__)
        self.model = model
        self.text_model = text_model

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
        self.text_model = config.text_model
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

                output_file = timecode_dir / f"{audio_path.stem}.json"

                # Honor manual corrections: if the existing file has
                # "locked": true at the top level, skip generation so
                # hand-edits aren't overwritten.
                if output_file.exists():
                    try:
                        with open(output_file, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                        if isinstance(existing, dict) and existing.get("locked") is True:
                            self.logger.info("Skipping %s (locked)", output_file.name)
                            generated_files += 1
                            continue
                    except Exception:
                        pass  # unreadable — fall through and regenerate

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

                if config.use_char_timing:
                    payload = self._generate_char_timing_payload(
                        page_id=page_id,
                        page_text_entries=page_text_entries,
                    )
                else:
                    payload = self._generate_timecode_payload(
                        audio_path=audio_path,
                        page_id=page_id,
                        page_number=page_number,
                        language=config.language,
                        page_text_entries=page_text_entries,
                        strict_data_ids=config.strict_data_ids,
                    )

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
            "char_timing": config.use_char_timing,
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
        initial_prompt = self._build_whisper_prompt(page_text_entries)
        transcription = self._transcribe_audio(audio_path, language, initial_prompt=initial_prompt)
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
            k: unicodedata.normalize("NFC", str(v)) if v is not None else ""
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
            if self._is_hidden(element):
                self.logger.debug(
                    "Skipping hidden data-id %s in %s", data_id, html_path.name
                )
                continue
            seen.add(data_id)
            text = unicodedata.normalize(
                "NFC",
                texts_dict.get(data_id, element.get_text(separator=" ").strip()),
            )
            entries.append({"id": data_id, "text": text})

        self.logger.debug("Extracted %d text entries from %s", len(entries), html_path)
        return entries

    @staticmethod
    def _is_hidden(element: Any) -> bool:
        """Return True if the element or any ancestor is visually hidden.

        Treats the Tailwind `hidden` class, the HTML `hidden` attribute, and
        inline `display: none` as hidden. Audio narrations don't cover hidden
        content (e.g. activity panels revealed only after user interaction),
        so their data-ids must be excluded from timecode generation.
        """
        for ancestor in [element, *element.parents]:
            if getattr(ancestor, "name", None) is None:
                continue
            classes = ancestor.get("class") or []
            if "hidden" in classes:
                return True
            if ancestor.has_attr("hidden"):
                return True
            style = ancestor.get("style") or ""
            if "display:none" in style.replace(" ", "").lower():
                return True
        return False

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

    def _build_whisper_prompt(
        self,
        page_text_entries: List[Dict[str, str]],
        max_chars: int = 900,
    ) -> str:
        """Concatenate page reference texts as a Whisper prompt.

        Guiding Whisper with the page vocabulary improves accent handling and
        ensures numbers/proper nouns are transcribed in the expected form.
        """
        parts = [self._strip_html(e["text"]) for e in page_text_entries]
        prompt = " ".join(parts)
        if len(prompt) > max_chars:
            prompt = prompt[:max_chars]
        return prompt

    def _transcribe_audio(
        self,
        audio_path: Path,
        language: str,
        initial_prompt: str = "",
    ) -> Dict[str, Any]:
        """Transcribe one audio file. Hybrid when self.text_model is set."""
        if self.text_model and self.text_model != self.model:
            return self._hybrid_transcribe(audio_path, language, initial_prompt)
        return self._transcribe_single(
            audio_path, language, initial_prompt, model=self.model
        )

    def _transcribe_single(
        self,
        audio_path: Path,
        language: str,
        initial_prompt: str,
        model: str,
    ) -> Dict[str, Any]:
        transcription_language = self._transcription_language(language)
        # Only whisper models support verbose_json / word-level timestamps.
        # gpt-4o-transcribe and gpt-4o-mini-transcribe accept only "json"/"text"
        # and return no segment/word timings at all.
        supports_verbose = "whisper" in model.lower()

        with open(audio_path, "rb") as audio_file:
            if supports_verbose:
                try:
                    response = self.client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        language=transcription_language,
                        response_format="verbose_json",
                        timestamp_granularities=["segment", "word"],
                        temperature=0,
                        prompt=initial_prompt or None,
                    )
                except Exception:
                    audio_file.seek(0)
                    response = self.client.audio.transcriptions.create(
                        model=model,
                        file=audio_file,
                        language=transcription_language,
                        response_format="verbose_json",
                        temperature=0,
                        prompt=initial_prompt or None,
                    )
            else:
                response = self.client.audio.transcriptions.create(
                    model=model,
                    file=audio_file,
                    language=transcription_language,
                    response_format="json",
                    temperature=0,
                    prompt=initial_prompt or None,
                )

        if hasattr(response, "model_dump"):
            payload = response.model_dump()
        elif isinstance(response, dict):
            payload = response
        elif hasattr(response, "to_dict"):
            payload = response.to_dict()
        else:
            payload = json.loads(str(response))

        # Synthesize a single full-duration segment when the model returned only
        # text (e.g. gpt-4o-transcribe).  Downstream alignment then does
        # proportional allocation across the audio duration instead of failing.
        if not payload.get("segments") and not payload.get("words"):
            text = str(payload.get("text") or "").strip()
            duration = self._audio_duration(audio_path)
            if text and duration > 0:
                payload["segments"] = [
                    {"start": 0.0, "end": duration, "text": text}
                ]
                payload["duration"] = duration
                self.logger.info(
                    "Model %s returned no word timings; using proportional "
                    "allocation over audio duration (%.2fs)",
                    model,
                    duration,
                )

        return payload

    def _hybrid_transcribe(
        self,
        audio_path: Path,
        language: str,
        initial_prompt: str,
    ) -> Dict[str, Any]:
        """Combine a text model (e.g. gpt-4o-transcribe) for canonical word
        order with a timing model (e.g. whisper-1) for word-level timestamps.

        The text model's tokens are treated as the reference order, and
        whisper-1's timed words are matched to them via SequenceMatcher.
        Unmatched text tokens get timings interpolated between neighbours.
        The result is a synthetic transcription with content + order from
        gpt-4o and timing from whisper, consumed by the existing pipeline.

        Doubles the API cost per page.
        """
        self.logger.info(
            "Hybrid transcription: text=%s, timing=%s", self.text_model, self.model
        )
        # Deliberately pass an empty prompt to gpt-4o-transcribe: LLM-style
        # transcription models tend to echo a directive prompt instead of
        # faithfully transcribing the audio, which defeats the point of using
        # it for canonical audio-order word sequence.  Whisper-1 still gets
        # the vocabulary prompt (it handles it as a hint, not a template).
        text_resp = self._transcribe_single(
            audio_path, language, "", model=self.text_model  # type: ignore[arg-type]
        )
        timing_resp = self._transcribe_single(
            audio_path, language, initial_prompt, model=self.model
        )

        gpt_text = str(text_resp.get("text") or "").strip()
        gpt_tokens = gpt_text.split()
        whisper_words = [
            self._normalize_word(w) for w in (timing_resp.get("words") or [])
        ]
        duration = (
            float(text_resp.get("duration") or 0.0)
            or float(timing_resp.get("duration") or 0.0)
            or self._audio_duration(audio_path)
        )

        if not gpt_tokens or not whisper_words:
            # Fall back to whichever response has the most structure
            return timing_resp if whisper_words else text_resp

        # Map gpt tokens to whisper timings (SequenceMatcher + interpolation)
        unified = self._align_tokens_to_whisper_words(
            gpt_tokens, whisper_words, time_window_end=duration or None
        )

        return {
            "text": gpt_text,
            "words": unified,
            "segments": [
                {"start": 0.0, "end": duration or (unified[-1]["end"] if unified else 0.0), "text": gpt_text}
            ],
            "duration": duration,
        }

    def _audio_duration(self, audio_path: Path) -> float:
        """Return audio duration in seconds via ffprobe, or 0.0 if unavailable."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_path),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return float(result.stdout.strip())
        except Exception as exc:
            self.logger.warning(
                "Could not determine audio duration for %s: %s", audio_path, exc
            )
            return 0.0

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
        ordered, boundaries, reliable = self._reorder_entries_by_audio(
            page_text_entries, openai_words
        )

        if not reliable:
            self.logger.debug(
                "Audio alignment score too low — using DOM order with proportional allocation"
            )
            ordered = page_text_entries
            token_lists = [self._split_reference_words(e["text"]) for e in ordered]
            weights = [max(len(t), 1) for t in token_lists]
            counts = self._allocate_counts(len(openai_words), weights)
            boundaries_list: List[int] = [0]
            c = 0
            for count in counts[:-1]:
                c += count
                boundaries_list.append(c)
        else:
            token_lists = [self._split_reference_words(e["text"]) for e in ordered]
            boundaries_list = [0] + boundaries[1:]

        elements: List[Dict[str, Any]] = []
        previous_end = openai_words[0]["start"] if openai_words else 0.0

        for i, (entry, tokens) in enumerate(zip(ordered, token_lists)):
            w_start = boundaries_list[i]
            w_end = (
                boundaries_list[i + 1]
                if i + 1 < len(boundaries_list)
                else len(openai_words)
            )
            assigned = openai_words[w_start:w_end]

            # Element end = start of the next boundary word (continuous coverage).
            # This gives trailing unmatched tokens the full gap to fill, not just
            # until the last assigned Whisper word.
            if w_end < len(openai_words):
                element_time_end = float(openai_words[w_end]["start"])
            else:
                element_time_end = float(openai_words[-1]["end"]) if openai_words else 0.0

            if assigned:
                start = float(assigned[0]["start"])
                end = element_time_end
                previous_end = end
                word_timestamps = self._align_tokens_to_whisper_words(
                    tokens, assigned, time_window_end=element_time_end
                )
            else:
                start = previous_end
                end = previous_end
                word_timestamps = self._tokens_with_interpolated_timing(tokens, start, end)
            # Cap monotonicity padding unless tail overflow occurred.
            # When char-count durations (or min-dur cascades from tight Whisper
            # anchors) push the last word past element_time_end, passing max_end
            # would re-collapse the overflowed words. Instead, let them extend
            # naturally; Safety nets 1 and 2 below expand the element boundary
            # and push the next element's start forward to absorb the extension.
            wt_last_end = float(word_timestamps[-1]["end"]) if word_timestamps else end
            tail_overflowed = wt_last_end > end
            word_timestamps = self._enforce_word_monotonicity(
                word_timestamps,
                max_end=None if tail_overflowed else (end if end > start else None),
            )

            # Post-processing safety net: redistribute any trailing run of
            # Post-processing safety net: redistribute any trailing run of
            # truly zero-duration words (start == end). Short-but-nonzero Whisper
            # anchors (e.g. "triste" at 0.02 s) are left untouched. This catches
            # any residual collapses that survive _enforce_word_monotonicity.
            last_good_end = start
            for w in word_timestamps:
                if float(w["end"]) > float(w["start"]):
                    last_good_end = float(w["end"])
            collapsed_tail_start: Optional[int] = None
            for wi, w in enumerate(word_timestamps):
                if float(w["end"]) <= float(w["start"]) + 1e-6:
                    if collapsed_tail_start is None:
                        collapsed_tail_start = wi
                else:
                    collapsed_tail_start = None
            if collapsed_tail_start is not None:
                t = last_good_end
                for w in word_timestamps[collapsed_tail_start:]:
                    dur = self._char_duration_for_word(w["text"])
                    w["start"] = round(t, 3)
                    w["end"] = round(t + dur, 3)
                    t += dur
                wt_last_end = float(word_timestamps[-1]["end"])
                if wt_last_end > end:
                    end = wt_last_end

            elements.append(
                {
                    "id": entry["id"],
                    "start": round(start, 3),
                    "end": round(end, 3),
                    "word_timestamps": word_timestamps,
                }
            )

        # Spread zero-duration spans across remaining audio time.
        # Weak entries (no Whisper words assigned, e.g. form-field labels
        # placed past the end of the sequence) collapse to start == end.
        # Find each run of consecutive collapsed elements and distribute them
        # proportionally across the available time window so they all get
        # non-empty highlight slots.
        audio_end = (
            float(openai_words[-1]["end"]) if openai_words else 0.0
        )
        i = 0
        while i < len(elements):
            if elements[i]["end"] > elements[i]["start"] + 1e-6:
                i += 1
                continue
            span_start = i
            while (
                i < len(elements)
                and elements[i]["end"] <= elements[i]["start"] + 1e-6
            ):
                i += 1
            span_end = i  # exclusive
            t_start = (
                elements[span_start - 1]["end"]
                if span_start > 0
                else 0.0
            )
            t_end = (
                elements[span_end]["start"]
                if span_end < len(elements)
                else audio_end
            )
            # Guarantee a minimum per-entry slot so nothing stays collapsed
            min_slot = 0.3
            t_end = max(t_end, t_start + min_slot * (span_end - span_start))
            counts = [
                max(len(elements[k]["word_timestamps"]), 1)
                for k in range(span_start, span_end)
            ]
            total = sum(counts) or 1
            elapsed = 0.0
            for j, k in enumerate(range(span_start, span_end)):
                dur = (t_end - t_start) * counts[j] / total
                new_start = t_start + elapsed
                new_end = new_start + dur
                elements[k]["start"] = round(new_start, 3)
                elements[k]["end"] = round(new_end, 3)
                wts = elements[k]["word_timestamps"]
                if wts:
                    wstep = dur / len(wts)
                    for wi, w in enumerate(wts):
                        w["start"] = round(new_start + wi * wstep, 3)
                        w["end"] = round(new_start + (wi + 1) * wstep, 3)
                elapsed += dur

        # Safety net 1: ensure each element's window covers its own word
        # timestamps.  Whisper word-index boundaries can fall inside a word's
        # time range in fast speech, leaving trailing words unhighlightable
        # (tts_highlighter.js deactivates at element.end).
        for el in elements:
            wts = el["word_timestamps"]
            if wts:
                el["start"] = round(min(el["start"], float(wts[0]["start"])), 3)
                el["end"] = round(max(el["end"], float(wts[-1]["end"])), 3)

        # Safety net 2: prevent overlap.  tts_highlighter.js loops elements
        # and breaks on the first match — overlapping elements would hide the
        # later one entirely.  If safety-net 1 extended an element's end past
        # the next element's start, shift the next element's start forward,
        # and push its end along so we never produce end < start.
        for i in range(1, len(elements)):
            if elements[i]["start"] < elements[i - 1]["end"]:
                elements[i]["start"] = elements[i - 1]["end"]
            if elements[i]["end"] < elements[i]["start"]:
                elements[i]["end"] = elements[i]["start"]

        return elements

    def _reorder_entries_by_audio(
        self,
        page_text_entries: List[Dict[str, str]],
        whisper_words: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, str]], List[int], bool]:
        """Return (ordered_entries, boundary_positions, reliable).

        Strong/weak split alignment:

        - Pass 1 — compute each entry's best unconstrained anchor and score.
        - Entries with score >= MATCH_THRESHOLD are "strong" (likely present
          in the audio); the rest are "weak" (form-field placeholders or
          other non-spoken data-ids).
        - Strong entries are sorted by Pass 1 anchor to establish audio order,
          then re-anchored sequentially in Pass 2 to avoid overlap when two
          entries share a rare word (e.g. "Guazubirá" appearing in both).
        - Weak entries are inserted back at their DOM-relative positions
          between strong neighbours — so form labels don't bubble to the
          front and don't trigger an all-or-nothing fallback.
        """
        if len(page_text_entries) <= 1 or not whisper_words:
            return page_text_entries, [0], True

        whisper_normalized = [
            self._normalize_token(w["text"]) for w in whisper_words
        ]

        match_threshold = 0.2

        # Pass 1: raw anchors per entry (keyed by DOM index so we can weave
        # unmatched entries back in by their original position).
        raw: List[Tuple[int, int, float, Dict[str, str], List[str]]] = []
        for dom_idx, entry in enumerate(page_text_entries):
            tokens = [
                self._normalize_token(t)
                for t in self._split_reference_words(entry["text"])
            ]
            pos, score = self._find_best_whisper_match(tokens, whisper_normalized)
            raw.append((dom_idx, pos, score, entry, tokens))

        strong = [r for r in raw if r[2] >= match_threshold]
        weak = [r for r in raw if r[2] < match_threshold]

        # Detect substring anchors: a strong entry whose Pass 1 anchor falls
        # inside an earlier strong entry's claimed word-index range is matching
        # a subsequence of that entry, not an independent audio phrase.
        # Classic case: "Cuando corre" (2 tokens) anchoring inside
        # "Corazón que late rápido cuando corre" (6 tokens).  Leaving it
        # strong causes the longer entry to inherit a huge time window
        # (from its own start to where the short entry re-anchors in Pass 2),
        # freezing the highlighter for seconds between elements.
        occupied_ranges: List[Tuple[int, int]] = []  # (w_start, w_end)
        strong_clean: List[Tuple[int, int, float, Dict[str, str], List[str]]] = []
        extra_weak: List[Tuple[int, int, float, Dict[str, str], List[str]]] = []
        for r in strong:  # DOM order preserved from raw
            _dom_idx, pos, _score, entry, tokens = r
            # Only demote if the entry is shorter than the occupied range it
            # overlaps — a genuine substring must fit inside the claimant's
            # window.  A 24-token entry cannot be a substring of a 9-token
            # range; requiring len(tokens) < range_width prevents false
            # positives when two entries share a common opening word (e.g.
            # "—Tiene" in text-13-20 matching the "tiene" inside text-13-19).
            if any(ws <= pos < we and len(tokens) < (we - ws) for ws, we in occupied_ranges):
                extra_weak.append(r)
                self.logger.debug(
                    "Reclassified %s as weak: anchor %d overlaps an earlier entry's word range",
                    entry["id"],
                    pos,
                )
            else:
                strong_clean.append(r)
                occupied_ranges.append((pos, pos + len(tokens)))
        strong = strong_clean
        weak = sorted(weak + extra_weak, key=lambda r: r[0])

        if len(strong) < 2:
            # Not enough signal to reorder reliably — keep DOM order and let
            # the caller fall through to proportional allocation.
            return (
                page_text_entries,
                list(range(len(page_text_entries))),
                False,
            )

        if weak:
            self.logger.debug(
                "Reorder: %d strong / %d weak entries (%s)",
                len(strong),
                len(weak),
                ", ".join(w[3]["id"] for w in weak),
            )

        # Sort strong entries by Pass 1 anchor to establish audio order
        strong_sorted = sorted(strong, key=lambda r: r[1])

        # Pass 2: sequential re-anchor on strong entries only
        strong_seq: List[Tuple[int, int, float, Dict[str, str], List[str]]] = []
        search_from = 0
        for dom_idx, _, _, entry, tokens in strong_sorted:
            rel_pos, score = self._find_best_whisper_match(
                tokens, whisper_normalized[search_from:]
            )
            abs_pos = search_from + rel_pos
            strong_seq.append((dom_idx, abs_pos, score, entry, tokens))
            search_from = abs_pos + max(len(tokens), 1)

        # Weave weak entries back in at their DOM-relative positions
        final = list(strong_seq)
        # Iterate weak entries in DOM order so their relative order is preserved
        for um in sorted(weak, key=lambda r: r[0]):
            insert_at = len(final)
            for i, m in enumerate(final):
                if m[0] > um[0]:
                    insert_at = i
                    break
            # Give weak entry a sequential position just after its predecessor
            # so the boundary list remains strictly increasing.
            prev_abs = final[insert_at - 1][1] if insert_at > 0 else 0
            prev_tokens = final[insert_at - 1][4] if insert_at > 0 else []
            new_abs = prev_abs + max(len(prev_tokens), 1)
            final.insert(insert_at, (um[0], new_abs, um[2], um[3], um[4]))

        # Enforce strictly increasing boundary positions for downstream use
        for i in range(1, len(final)):
            if final[i][1] <= final[i - 1][1]:
                final[i] = (
                    final[i][0],
                    final[i - 1][1] + 1,
                    final[i][2],
                    final[i][3],
                    final[i][4],
                )

        ordered = [r[3] for r in final]
        boundaries = [r[1] for r in final]
        # We got here with at least 2 strong matches, so ordering is reliable.
        reliable = True
        return ordered, boundaries, reliable

    @staticmethod
    def _find_best_whisper_match(
        entry_tokens: List[str],
        whisper_normalized: List[str],
    ) -> Tuple[int, float]:
        """Slide a window over the Whisper word list and return the position and
        normalized score of the best-matching window for the given entry tokens.

        Multiplying ratio by len(entry_tokens) ensures a 10-word perfect match
        outscores a 1-word coincidental match.
        """
        n = len(entry_tokens)
        if not n or not whisper_normalized:
            return 0, 0.0

        best_pos = 0
        best_score = 0.0
        window_extra = max(2, n // 2)
        first_ref = entry_tokens[0]

        for start in range(len(whisper_normalized)):
            window = whisper_normalized[start : start + n + window_extra]
            if not window:
                break
            raw = SequenceMatcher(None, entry_tokens, window).ratio()
            score = raw * n
            # Head-match bonus: phrases almost always start at a phrase
            # boundary in the audio.  Reward windows whose first token equals
            # the entry's first reference token so ties and near-ties resolve
            # to the correct phrase start, not an earlier position where a
            # common middle word happens to align.  Require first_ref to be
            # non-empty — otherwise punctuation-only entries (e.g. "—") would
            # spuriously anchor wherever Whisper has empty-normalized tokens.
            if first_ref and window[0] == first_ref:
                score += 1.0

            if score > best_score:
                best_score = score
                best_pos = start

        normalized = best_score / n if n else 0.0
        return best_pos, normalized

    @staticmethod
    def _strip_diacritics(text: str) -> str:
        """Remove combining diacritic characters via NFD decomposition."""
        return "".join(
            ch for ch in unicodedata.normalize("NFD", text)
            if unicodedata.category(ch) != "Mn"
        )

    @staticmethod
    def _normalize_token(token: str) -> str:
        """Lowercase, strip punctuation, and strip diacritics for robust comparison.

        Whisper often drops accents for Spanish (está → esta), so stripping
        diacritics from both sides prevents spurious mismatches.
        """
        lowered = token.lower()
        no_punct = re.sub(r'[^\w\s]', '', lowered, flags=re.UNICODE).strip()
        return AudioTimecodeGenerator._strip_diacritics(no_punct)

    @staticmethod
    def _char_duration_for_word(word: str) -> float:
        """Return duration in seconds for a word based on stripped letter count.

        Strips punctuation before counting: 1–3 letters → 0.2 s, 4–7 → 0.4 s, 8+ → 0.6 s.
        """
        stripped = re.sub(r'[«».,!?;:"\'\-\(\)\[\]]', '', word)
        n = len(stripped)
        if n <= 3:
            return 0.2
        if n <= 7:
            return 0.4
        return 0.6

    def _build_elements_from_char_durations(
        self,
        page_text_entries: List[Dict[str, str]],
        start_time: float = 0.0,
        inter_element_gap: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """Build timecode elements using character-count-based word durations.

        Does not require audio or API access. Each word's duration is derived from
        its letter count; a fixed gap separates consecutive elements.
        """
        elements: List[Dict[str, Any]] = []
        current = start_time
        for entry in page_text_entries:
            tokens = self._split_reference_words(entry["text"])
            if not tokens:
                continue
            el_start = current
            word_timestamps: List[Dict[str, Any]] = []
            for token in tokens:
                dur = self._char_duration_for_word(token)
                word_timestamps.append(
                    {
                        "text": token,
                        "start": round(current, 3),
                        "end": round(current + dur, 3),
                    }
                )
                current += dur
            elements.append(
                {
                    "id": entry["id"],
                    "start": round(el_start, 3),
                    "end": round(current, 3),
                    "word_timestamps": word_timestamps,
                }
            )
            current += inter_element_gap
        return elements

    def _generate_char_timing_payload(
        self,
        page_id: str,
        page_text_entries: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        """Build a timecode payload from character-count durations (no API call)."""
        elements = self._build_elements_from_char_durations(page_text_entries)
        return {"page_id": page_id, "elements": elements}

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

    def _align_tokens_to_whisper_words(
        self,
        tokens: List[str],
        whisper_words: List[Dict[str, Any]],
        time_window_end: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Map reference text tokens to actual Whisper word timestamps.

        Uses SequenceMatcher to align tokens against the Whisper words.
        Matched tokens get the real Whisper timestamp; unmatched tokens
        (punctuation variants, elisions, etc.) are interpolated linearly
        between their neighbouring anchor points.

        time_window_end: if provided, trailing unmatched tokens spread into
        the window [last_anchor_end, time_window_end] rather than collapsing
        to a zero-duration point.  Prevents trailing words from being skipped
        by the tts_highlighter's strict `currentTime < element.end` check.
        """
        if not tokens:
            return []
        if not whisper_words:
            return self._tokens_with_interpolated_timing(tokens, 0.0, 0.0)

        global_start = float(whisper_words[0]["start"])
        global_end = (
            time_window_end
            if time_window_end is not None
            else float(whisper_words[-1]["end"])
        )

        ref_norm = [self._normalize_token(t) for t in tokens]
        wh_norm = [self._normalize_token(w["text"]) for w in whisper_words]

        # Build anchor map: token_index → (start, end) from matched Whisper word.
        # Cap anchor durations that exceed max(4 × char_dur, 1.0) seconds to avoid
        # Whisper's "end = next_word_start" convention inflating short words across
        # long silences (e.g. "se" spanning 7 s of silence → capped to 0.2 s).
        anchors: Dict[int, Tuple[float, float]] = {}
        for a, b, size in SequenceMatcher(None, ref_norm, wh_norm).get_matching_blocks():
            for k in range(size):
                w_start = float(whisper_words[b + k]["start"])
                w_end = float(whisper_words[b + k]["end"])
                char_dur = self._char_duration_for_word(tokens[a + k])
                threshold = max(4.0 * char_dur, 1.0)
                if w_end - w_start > threshold:
                    w_end = w_start + char_dur
                anchors[a + k] = (w_start, w_end)

        # Fill in timings for all tokens using char-count-based durations.
        #
        # Replacing equal-step interpolation fixes two failure modes:
        #
        # 1. Gap bloat: a single short token (e.g. the clitic "se") between two
        #    far-apart Whisper anchors previously inherited the entire gap
        #    (e.g. 7 seconds). Now it gets its natural char-count duration
        #    (0.2 s) and the remaining silence stays silent.
        #
        # 2. Tail collapse: when more reference words follow the last anchor
        #    than fit in the remaining element window, words previously piled
        #    up at the element boundary. Now each word gets at least
        #    MIN_WORD_DURATION_S. The small overflow past global_end is
        #    intentional — Safety nets 1 and 2 in the outer loop will expand
        #    the element boundary and push the next element's start forward.
        timings: List[Optional[Tuple[float, float]]] = [None] * len(tokens)
        for idx, timing in anchors.items():
            timings[idx] = timing

        i = 0
        while i < len(tokens):
            if timings[i] is not None:
                i += 1
                continue
            # Locate the gap boundaries
            prev_end = global_start
            for p in range(i - 1, -1, -1):
                if timings[p] is not None:
                    prev_end = timings[p][1]
                    break
            next_start = global_end
            gap_end = len(tokens)
            for n in range(i, len(tokens)):
                if timings[n] is not None:
                    next_start = timings[n][0]
                    gap_end = n
                    break
            gap_len = gap_end - i
            is_tail = gap_end == len(tokens)  # no next anchor; gap runs to global_end
            duration = next_start - prev_end

            char_durs = [self._char_duration_for_word(tokens[i + j]) for j in range(gap_len)]
            total_char = sum(char_durs)

            t = prev_end
            if duration <= 0:
                # No time window at all; stack tokens with char durations from prev_end
                for j in range(gap_len):
                    timings[i + j] = (t, t + char_durs[j])
                    t += char_durs[j]
            elif total_char <= duration:
                # Tokens fit within the window; use char durations and leave
                # the remaining gap as silence before the next anchor.
                for j in range(gap_len):
                    timings[i + j] = (t, t + char_durs[j])
                    t += char_durs[j]
            elif is_tail:
                # Tail overflow: content exceeds the remaining window.
                # Assign MIN_WORD_DURATION_S per token starting from prev_end;
                # each word gets the smallest distinguishable slot and the
                # bounded extension past global_end is handled by Safety nets.
                for j in range(gap_len):
                    timings[i + j] = (t, t + self.MIN_WORD_DURATION_S)
                    t += self.MIN_WORD_DURATION_S
            else:
                # Interior overflow: more content than fits between two anchors.
                # Compress proportionally by char-count weights so short words
                # still get less time than long ones.
                scale = duration / total_char
                for j in range(gap_len):
                    d = char_durs[j] * scale
                    timings[i + j] = (t, t + d)
                    t += d
            i = gap_end

        return [
            {
                "text": token,
                "start": round(cast(Tuple[float, float], t)[0], 3),
                "end": round(cast(Tuple[float, float], t)[1], 3),
            }
            for token, t in zip(tokens, timings)
        ]

    # Minimum word duration (seconds) enforced on every generated word.
    # tts_highlighter.js silently drops words whose `end - start` is below
    # ~0.06 s, so we clamp to a slightly larger floor to guarantee every
    # word gets a render slot.
    MIN_WORD_DURATION_S = 0.08

    @staticmethod
    def _enforce_word_monotonicity(
        word_timestamps: List[Dict[str, Any]],
        max_end: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Clamp word timestamps so start times are non-decreasing,
        start <= end, and every word has at least MIN_WORD_DURATION_S between
        its start and end.

        When ``max_end`` is provided, word ends are capped at that value so
        the MIN_WORD_DURATION padding can't cascade past the containing
        element's intended boundary (which previously caused elements to
        over-extend, forcing downstream elements to collapse to zero duration).

        tts_highlighter.js scans backwards to find the last word where
        currentTime >= word.start, so non-monotone timestamps cause stale
        highlights. It also drops zero- or near-zero-duration words — the
        minimum-duration clamp prevents fast-speech words from vanishing.
        """
        min_dur = AudioTimecodeGenerator.MIN_WORD_DURATION_S
        result = []
        prev_end = 0.0
        for word in word_timestamps:
            start = max(float(word["start"]), prev_end)
            end = max(float(word["end"]), start + min_dur)
            # Only apply max_end capping while start is strictly before the
            # boundary. Once a word starts at or past max_end (because prev_end
            # cascaded beyond it), let the word overflow freely so that Safety
            # nets 1 & 2 can extend the element's window rather than collapsing
            # the word to zero duration.
            if max_end is not None and start < max_end:
                if end > max_end:
                    end = max_end
                if end < start:
                    end = start
            result.append({"text": word["text"], "start": round(start, 3), "end": round(end, 3)})
            prev_end = end
        return result

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