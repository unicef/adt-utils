# CLAUDE.md

## Project Overview

adt-utils is a UNICEF Python toolkit for processing Accessible Digital Textbooks (ADT). It handles HTML validation, data-id fixing, language flattening (overriding HTML text from i18n JSON), and TTS audio regeneration via OpenAI.

## Repository Structure

```
src/                          # Production code (installed as package)
  core/                       # interfaces.py (ABCs), models.py (Pydantic), exceptions.py
  validation/
    classes/                  # adt_validator.py, data_fixer.py
    scripts/                  # validate_adt.py, fix_missing_data_ids.py
  language_flattening/
    classes/                  # html_text_overrider.py
    scripts/                  # language_flattening.py
  regeneration/
    classes/                  # adt_tts_regenerator.py
    scripts/                  # regenerate_tts.py
  utils/                      # page_utils.py (shared page range filtering)
  structs/                    # script.py (Script/ScriptCategory models)
  script_registry.py          # Registry of all production scripts
experiments/                  # Development/experimental scripts (not production)
configs/                      # tts_config.yaml
docs/                         # Documentation including production-deployment.md
```

## Build & Run

```bash
pip install -e .              # Local install
pip install -e .[dev]         # With dev dependencies (pytest, black, isort, mypy)
make build                    # Docker image
make validate TARGET_DIR=../target-folder
make fix-data-ids TARGET_DIR=../target-folder
make translate-gpt5 START=6 END=58 SOURCE_LANG=es TARGET_LANG=en
```

Requires `OPENAI_API_KEY` env var for translation and TTS features. Python >=3.8, <4.0.

## Data Pipeline Order

```
validate_adt.py → fix_missing_data_ids.py → language_flattening.py → regenerate_tts.py
```

## Architecture Patterns

- **Module layout**: Each `src/` module has `classes/` (business logic) and `scripts/` (CLI entry points)
- **Interfaces**: Production classes implement ABCs from `src/core/interfaces.py` (`PageRangeProcessor`, `Validator`, `DataFixer`, `ContentProcessor`, `Translator`)
- **Config models**: Use Pydantic models extending `PageProcessConfig` from `src/core/models.py`; return `ProcessResult`
- **Exceptions**: Use `ADTUtilsError` hierarchy from `src/core/exceptions.py`
- **Page range filtering**: Use `src/utils/page_utils.py` helpers (`add_standard_args`, `filter_files_by_page_range`); all processors support `--start-page`/`--end-page`
- **Script registry**: Register new production scripts in `src/script_registry.py` using `Script` model from `src/structs/script.py`
- **HTML parsing**: BeautifulSoup with `'html.parser'` backend
- **TTS**: Async processing with asyncio, max 5 concurrent OpenAI requests
- **Dry-run**: Support `--dry-run` flag where applicable

## Coding Conventions

- snake_case for variables/functions, PascalCase for classes, UPPER_SNAKE_CASE for constants
- Type hints on all production code
- Logging via stdlib `logging` (not print)
- Always use `encoding='utf-8'` explicitly in file I/O
- Use `pathlib.Path` for file paths
- Data-id format: `text-[page]-[incremental]` (e.g., `text-12-3`) or `txt_p[page]_*`

## Promotion Workflow

Scripts start in `experiments/` and promote to `src/` when production-ready. See `docs/production-deployment.md` for the full checklist:

1. Move to appropriate `src/` subfolder with `classes/` + `scripts/` structure
2. Implement relevant ABC from `core/interfaces.py`
3. Use Pydantic config models from `core/models.py`
4. Register in `script_registry.py`
5. Add Makefile target and Docker integration
6. Run `black`, `isort`, `mypy` before merging

## Testing

Dev dependencies include pytest and pytest-cov. No test suite exists yet. When adding tests, place them in a `tests/` directory mirroring `src/` structure.

## Key Dependencies

- `pydantic` >= 2.0.0 — data validation and config models
- `beautifulsoup4` >= 4.11.0 — HTML parsing
- `lxml` >= 4.9.0 — XML/HTML processing
- `openai` — TTS generation and GPT translations
- `pyyaml` >= 6.0.0 — YAML config parsing
