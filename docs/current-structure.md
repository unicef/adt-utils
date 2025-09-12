# Current Project Structure (September 2024)

This document reflects the current organization of the ADT Utils project after the major restructuring.

## Recent Changes

### Scripts Moved to Production (`src/`)
- ✅ `validate_adt.py` → `src/validation/scripts/validate_adt.py`
- ✅ `fix_missing_data_ids.py` → `src/validation/scripts/fix_missing_data_ids.py`

These scripts are now fully production-ready with:
- Proper structured data models in `src/structs/script.py`
- Registration in `src/script_registry.py`
- Comprehensive validation classes in `src/validation/classes/`

### Scripts Reorganized in Experiments

From the old `to_be_tested/` folder, scripts have been reorganized into logical groups:

#### HTML Processing (`experiments/html_standardization/`)
- `standardize_all.py` - Master standardization pipeline
- `standardize_html.py` - HTML structure processing
- `standardize_headings.py` - Typography and heading styles  
- `standardize_image_text_layouts.py` - Responsive layout engine

#### Content Generation (`experiments/content_generation/`)
- `generate-eli5.py` - ELI5 explanations generator
- `generate-image-descriptions.py` - Alt text and descriptions
- `regenerate-easy-read-v2.py` - Easy-read content transformation

#### Translation Tools (`experiments/translation_tools/regenerate_translations/`)
- `translate_gpt5.py` - Advanced GPT translation
- `translate_page_range.py` - Simple range translation

#### TTS Generation (`experiments/tts_generation/regenerate_tts_es/`)
- Complete Spanish TTS pipeline with regional accent support

#### Root Level Utilities (`experiments/`)
- `clean_json_texts.py` - JSON cleanup utility
- `restructure_text.py` - Advanced text restructuring
- `restructure_text_simple.py` - Basic text restructuring  
- `test_single_layout.py` - Single file layout testing
- `config.py` - Configuration management

## Production Architecture

### Core Production Components (`src/`)

```
src/
├── core/                    # Business logic interfaces
│   ├── interfaces.py        # Abstract interfaces
│   ├── models.py           # Data models  
│   ├── exceptions.py       # Custom exceptions
│   └── __init__.py         # Core exports
├── utils/                  # Utility functions
│   ├── page_utils.py       # Page processing utilities
│   └── __init__.py         # Utils exports
├── validation/             # HTML validation system
│   ├── classes/            # Validation classes
│   │   ├── adt_validator.py # Main validator
│   │   ├── data_fixer.py    # Auto-fix functionality
│   │   └── __init__.py      # Classes exports
│   ├── scripts/            # Production validation scripts
│   │   ├── validate_adt.py  # Validation script
│   │   └── fix_missing_data_ids.py # Auto-fix script
│   └── __init__.py         # Validation exports
├── structs/                # Data structures
│   ├── script.py           # Script metadata structures
│   └── __init__.py         # Structs exports
├── script_registry.py     # Production script registry
└── __init__.py             # Package exports
```

## Registry System

The `src/script_registry.py` provides structured metadata for all production scripts:

- **Script Discovery**: External repositories can import and discover available scripts
- **Argument Validation**: Type-safe argument definitions
- **Usage Examples**: Built-in examples for each script
- **Category Organization**: Scripts organized by function (VALIDATION, FIXING, etc.)

## Next Steps

Scripts ready for promotion to production should follow the workflow in `docs/production-deployment.md`:

1. **Content Generation Scripts** - These are well-tested and could be promoted next
2. **HTML Standardization Scripts** - Core functionality ready for structured promotion  
3. **Translation Tools** - May need API key management before production promotion
4. **TTS Generation** - Similar to translation, needs environment setup

## Docker Integration

Production scripts are integrated with the Makefile system:
- `make validate` - Run HTML validation
- `make fix-data-ids` - Auto-fix missing data IDs  
- `make translate-gpt5` - GPT translation workflow

Experimental scripts can still be run directly from their locations or via Docker with custom commands.