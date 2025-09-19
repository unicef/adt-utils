import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from openai import OpenAI
from datetime import datetime
import tempfile
import os

class ADTTTSRegenerator:
    def __init__(self, openai_api_key: str, output_dir: Path = Path("content/i18n"), logger: logging.Logger = None):
        self.api_key = openai_api_key
        self.client = OpenAI(api_key=openai_api_key)
        self.output_dir = output_dir
        self.max_concurrent_requests = 5
        self.semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        self.logger = logger or logging.getLogger(__name__)

    def load_texts(self, language: str) -> Dict[str, str]:
        texts_file = self.output_dir / language / "texts.json"
        if not texts_file.exists():
            self.logger.error(f"Texts file not found: {texts_file}")
            return {}
        try:
            with open(texts_file, 'r', encoding='utf-8') as f:
                texts = json.load(f)
            self.logger.info(f"Loaded {len(texts)} texts for language: {language}")
            return texts
        except Exception as e:
            self.logger.error(f"Error loading texts for {language}: {e}")
            return {}

    def filter_texts_by_page_range(self, texts: Dict[str, str], start_page: int, end_page: int) -> Dict[str, str]:
        filtered_texts = {}
        for key, text in texts.items():
            if key.startswith('text-'):
                try:
                    parts = key.split('-')
                    if len(parts) >= 2:
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
            elif key.startswith('easyread-text-'):
                try:
                    parts = key.split('-')
                    if len(parts) >= 3:
                        page_num = int(parts[2])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
            else:
                try:
                    parts = key.split('-')
                    if len(parts) >= 2:
                        page_num = int(parts[1])
                        if start_page <= page_num <= end_page:
                            filtered_texts[key] = text
                except (ValueError, IndexError):
                    continue
        self.logger.info(f"Filtered to {len(filtered_texts)} texts for pages {start_page}-{end_page}")
        return filtered_texts

    def get_voice_and_instructions(self, language: str) -> Tuple[str, str]:
        if language == 'es':
            voice = "nova"
            instructions = (
                "Lee este texto como si fueras un maestro paciente y cálido "
                "enseñando a niños. Usa el acento y entonación característica "
                "de El Salvador, incluyendo la pronunciación suave y las "
                "características fonéticas típicas de la región salvadoreña. "
                "Mantén un tono educativo, amigable y accesible apropiado "
                "para contenido educativo dirigido a niños."
            )
        else:
            voice = "alloy"
            instructions = (
                "Speak clearly with a warm, patient teacher tone "
                "appropriate for educational content for children."
            )
        return voice, instructions

    async def generate_audio(self, text: str, output_path: Path, language: str) -> bool:
        if not text.strip():
            self.logger.warning(f"Empty text for {output_path}, skipping")
            return False
        voice, instructions = self.get_voice_and_instructions(language)
        async with self.semaphore:
            try:
                self.logger.info(f"Generating audio for: {output_path.name}")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                loop = asyncio.get_event_loop()
                def generate_sync():
                    with self.client.audio.speech.with_streaming_response.create(
                        model="gpt-4o-mini-tts",
                        voice=voice,
                        input=text,
                        instructions=instructions,
                        response_format="mp3"
                    ) as response:
                        response.stream_to_file(output_path)
                        return True
                success = await loop.run_in_executor(None, generate_sync)
                if success:
                    self.logger.info(f"Successfully generated: {output_path.name}")
                    return True
                else:
                    self.logger.error(f"Failed to generate: {output_path.name}")
                    return False
            except Exception as e:
                self.logger.error(f"Error generating audio for {output_path.name}: {e}")
                return False

    def get_audio_filename(self, text_key: str, language: str) -> str:
        return f"{text_key}_{language}.mp3"

    async def regenerate_for_language(self, language: str, start_page: int, end_page: int) -> Tuple[int, int]:
        self.logger.info(f"Starting regeneration for {language}, pages {start_page}-{end_page}")
        texts = self.load_texts(language)
        if not texts:
            return 0, 0
        filtered_texts = self.filter_texts_by_page_range(texts, start_page, end_page)
        if not filtered_texts:
            self.logger.warning(f"No texts found for pages {start_page}-{end_page} in {language}")
            return 0, 0
        audio_dir = self.output_dir / language / "audio"
        tasks = []
        for text_key, text_content in filtered_texts.items():
            audio_filename = self.get_audio_filename(text_key, language)
            output_path = audio_dir / audio_filename
            task = self.generate_audio(text_content, output_path, language)
            tasks.append(task)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        successes = sum(1 for result in results if result is True)
        failures = sum(1 for result in results if result is not True)
        self.logger.info(f"Completed {language}: {successes} successful, {failures} failed")
        return successes, failures

    async def regenerate(
        self,
        start_page: int = 0,
        end_page: int = 0,
        languages: List[str] = None,
        input_json: str = None,
        data_ids: List[str] = None,
    ) -> Dict[str, Tuple[int, int]]:
        """
        Unified regeneration entry point.
        - If input_json is provided, regenerate from JSON.
        - If data_ids is provided, regenerate only those keys from texts.json.
        - Otherwise, regenerate by page range.
        """
        languages = languages or []
        results = {}

        if input_json:
            return await self.regenerate_from_json(input_json, languages)

        if data_ids:
            for language in languages:
                texts = self.load_texts(language)
                filtered_texts = {k: v for k, v in texts.items() if k in data_ids}
                if not filtered_texts:
                    self.logger.warning(f"No matching data IDs found for language '{language}'")
                    results[language] = (0, 0)
                    continue
                with tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False) as tmp_json:
                    json.dump(filtered_texts, tmp_json, ensure_ascii=False, indent=2)
                    tmp_json_path = tmp_json.name
                lang_result = await self.regenerate_from_json(tmp_json_path, [language])
                results.update(lang_result)
                os.remove(tmp_json_path)
            return results

        # Default: regenerate by page range
        return await self.regenerate_by_page_range(start_page, end_page, languages)

    async def regenerate_by_page_range(self, start_page: int, end_page: int, languages: List[str]) -> Dict[str, Tuple[int, int]]:
        self.logger.info(f"Starting TTS regeneration for pages {start_page}-{end_page}, languages: {languages}")
        start_time = datetime.now()
        results = {}
        for language in languages:
            try:
                success_count, failure_count = await self.regenerate_for_language(
                    language, start_page, end_page
                )
                results[language] = (success_count, failure_count)
            except Exception as e:
                self.logger.error(f"Error processing language {language}: {e}")
                results[language] = (0, 1)
        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(f"TTS regeneration completed in {duration}")
        return results

    async def regenerate_from_json(self, input_json: str, languages: List[str]) -> Dict[str, Tuple[int, int]]:
        """
        Regenerate TTS audio files from a provided JSON file for the specified languages.
        The JSON file should contain a dictionary of text keys and their content.
        """
        self.logger.info(f"Starting TTS regeneration from JSON: {input_json} for languages: {languages}")
        start_time = datetime.now()
        results = {}

        # Load texts from JSON
        try:
            with open(input_json, 'r', encoding='utf-8') as f:
                all_texts = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading input JSON file: {e}")
            return {lang: (0, 1) for lang in languages}

        for language in languages:
            # If the JSON is structured as {lang: {key: text}}, use that
            texts = all_texts.get(language, all_texts) if isinstance(all_texts, dict) else all_texts
            if not isinstance(texts, dict):
                self.logger.error(f"Invalid JSON structure for language '{language}'")
                results[language] = (0, 1)
                continue

            audio_dir = self.output_dir / language / "audio"
            tasks = []
            for text_key, text_content in texts.items():
                audio_filename = self.get_audio_filename(text_key, language)
                output_path = audio_dir / audio_filename
                task = self.generate_audio(text_content, output_path, language)
                tasks.append(task)
            res = await asyncio.gather(*tasks, return_exceptions=True)
            successes = sum(1 for r in res if r is True)
            failures = sum(1 for r in res if r is not True)
            self.logger.info(f"Completed {language}: {successes} successful, {failures} failed")
            results[language] = (successes, failures)

        end_time = datetime.now()
        duration = end_time - start_time
        self.logger.info(f"TTS regeneration from JSON completed in {duration}")
        return results