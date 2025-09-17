# ADT Utils

A comprehensive Python toolkit for HTML standardization, validation, translation, and TTS generation in the ADT (Accessible Digital Textbooks) project by UNICEF.

## 🎯 Purpose

ADT Utils processes HTML educational content to ensure consistent styling, accessibility, and multi-language support using Tailwind CSS. It standardizes document structure, validates data integrity, generates translations, and creates text-to-speech audio files.

## 🚀 Features

- **HTML Standardization**: Consistent styling, structure, and responsive layouts using Tailwind CSS
- **Content Validation**: Validate and auto-fix data-id attributes in HTML files  
- **Multi-language Translation**: AI-powered translation with GPT models (Spanish ↔ English, French, Portuguese)
- **TTS Generation**: Text-to-speech audio generation for multiple languages
- **Layout Intelligence**: Automatic responsive layouts based on content analysis
- **Content Generation**: ELI5 explanations and image descriptions for accessibility

## 📁 Project Structure

```
adt-utils/
├── src/                          # Production-ready core library
│   ├── core/                     # Core business logic and interfaces  
│   ├── utils/                    # Utility functions and helpers
│   ├── validation/               # HTML validation tools and classes
│   └── structs/                  # Data structures and models
├── experiments/                  # Development and testing scripts
│   ├── html_standardization/     # HTML processing experiments
│   │   ├── standardize_all.py    # Master standardization script
│   │   ├── standardize_html.py   # HTML structure standardization
│   │   ├── standardize_headings.py # Typography and heading styles
│   │   └── standardize_image_text_layouts.py # Responsive layout engine
│   ├── content_generation/       # Content generation tools
│   │   ├── generate-eli5.py      # Generate ELI5 explanations
│   │   ├── generate-image-descriptions.py # Alt text generation
│   │   └── regenerate-easy-read-v2.py # Easy-read content
│   ├── translation_tools/        # Translation experiments
│   │   └── regenerate_translations/ # GPT-powered translation
│   │       ├── translate_gpt5.py # Advanced GPT translation
│   │       └── translate_page_range.py # Simple range translation
│   ├── tts_generation/          # Text-to-speech tools
│   │   └── regenerate_tts_es/    # Spanish TTS generation
│   ├── templates/               # Script templates
│   ├── clean_json_texts.py      # JSON text cleanup utility
│   ├── restructure_text.py      # Advanced text restructuring
│   ├── restructure_text_simple.py # Simplified text restructuring
│   ├── test_single_layout.py    # Single file layout testing
│   └── config.py                # Configuration management
├── docs/                        # Documentation
│   ├── production-deployment.md  # Production promotion guide
│   ├── SCRIPT_USAGE.md          # Detailed script documentation
│   └── PROMOTION_GUIDE.md       # Legacy promotion guide
├── pyproject.toml               # Python project configuration
├── Makefile                     # Docker automation commands
└── docker-compose.yml           # Container orchestration
```

## 🛠️ Quick Start

### Installation
```bash
# Install package
pip install -e .

# Install development dependencies  
pip install -e .[dev]

# Install experimental dependencies
pip install -r experiments/requirements.txt
```

### Basic Usage
```bash
# Using Python API (production)
from src.core.standardization import standardize_html_files
standardize_html_files(6, 58)

# Using experimental scripts directly
cd experiments/html_standardization
python standardize_all.py 6 58

# Or run scripts from root directory
python experiments/clean_json_texts.py --dir ./output/content/i18n/

# Using Docker (recommended)
make build
make validate TARGET_DIR=../my-project
```

## 🐳 Docker Workflows

### Build and Setup
```bash
# Build Docker image
make build

# Create environment template
make create-env-template
```

### HTML Validation
```bash
# Validate HTML files for missing data-id attributes
make validate TARGET_DIR=../target-folder

# Verbose validation with detailed output
make validate-verbose TARGET_DIR=../target-folder

# Auto-fix missing data-id attributes
make fix-data-ids TARGET_DIR=../target-folder

# Complete validation + fix workflow
make validate-fix TARGET_DIR=../target-folder
```

### Translation Workflows
```bash
# Simple dictionary-based translation
make translate-simple TARGET_DIR=../project START=10 END=15

# AI-powered GPT translation (Spanish to English by default)
make translate-gpt5 TARGET_DIR=../project START=10 END=15

# Translate to different languages
make translate-gpt5 TARGET_DIR=../project START=10 END=15 SOURCE_LANG=es TARGET_LANG=fr

# Dry run to preview translations
make translate-gpt5-dry TARGET_DIR=../project START=10 END=15
```

## 🧪 Experimental Scripts

The `experiments/` folder contains development scripts organized by function:

### HTML Standardization (`experiments/html_standardization/`)
- **`standardize_all.py`**: Master script - runs complete standardization pipeline
- **`standardize_html.py`**: HTML structure and container classes standardization  
- **`standardize_headings.py`**: Typography, heading styles, and color standardization
- **`standardize_image_text_layouts.py`**: Intelligent responsive layout generation based on content analysis

### Text Processing (`experiments/`)
- **`restructure_text.py`**: Advanced text restructuring with span wrapping and paragraph grouping
- **`restructure_text_simple.py`**: Simplified text restructuring for basic needs
- **`clean_json_texts.py`**: Remove formatting artifacts and clean JSON text files
- **`test_single_layout.py`**: Test layout changes on individual files

### Content Generation (`experiments/content_generation/`)
- **`generate-eli5.py`**: Generate ELI5 (Explain Like I'm 5) explanations for complex content
- **`generate-image-descriptions.py`**: Create detailed alt text and image descriptions for accessibility
- **`regenerate-easy-read-v2.py`**: Transform content into easy-read format

### Translation Tools (`experiments/translation_tools/regenerate_translations/`)
- **`translate_gpt5.py`**: Advanced GPT-powered translation with context awareness
- **`translate_page_range.py`**: Simple dictionary-based translation for page ranges
- Multi-language support (Spanish, English, French, Portuguese)
- Smart matching with existing translations

### TTS Generation (`experiments/tts_generation/`)
- Multi-language text-to-speech generation
- Regional accent support (El Salvador Spanish)
- Batch processing for page ranges

## 🎨 What Gets Standardized

### HTML Structure
- **Body tag**: `bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg`
- **Container div**: `container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12`
- **Responsive layouts**: Automatic layout selection based on text-to-image ratios

### Typography  
- **H1**: `text-5xl font-bold mb-4` + smart color assignment
- **H2-H6**: Consistent sizing and color hierarchy
- **Background boxes**: Standardized colors (`bg-green-50`, `bg-amber-50`, `bg-purple-50`)

### Layout Intelligence
Automatically analyzes content and applies intelligent responsive layouts:
- **< 100 char/image**: Image top, text bottom (infographics)
- **100-500**: Image left, text right (balanced content)  
- **500-1000**: Text left, image right (text-heavy)
- **> 1000**: Text top, image bottom (documentation)

## 🔧 Configuration

### Environment Setup
```bash
# Required for translation and TTS
export OPENAI_API_KEY=your_api_key_here

# Optional: Custom target directory
export ADT_OUTPUT_DIR=/path/to/target
```

### Heading Templates  
Customize styles in `experiments/heading_templates.json`:
```json
{
  "heading_templates": {
    "h1": {
      "classes": "text-5xl font-bold mb-4",
      "color_options": ["text-amber-700", "text-red-600", "text-purple-500"]
    }
  }
}
```

## 🚦 Development Workflow

### Moving Scripts to Production
1. Develop in `experiments/` folder
2. Follow promotion guide in `docs/production-deployment.md`  
3. Move tested scripts to appropriate `src/` subfolder
4. Update `src/script_registry.py`
5. Add Makefile targets and Docker integration

### Code Quality
```bash
# Format code
black src/ experiments/
isort src/ experiments/

# Type checking
mypy src/

# Run tests  
pytest
```

## 📊 Use Cases

- **Educational Content**: Standardize HTML textbooks and learning materials
- **Accessibility**: Generate alt text and easy-read versions
- **Internationalization**: Translate content to multiple languages
- **Audio Content**: Create TTS audio for different languages and accents
- **Responsive Design**: Ensure consistent layouts across devices

## 🛡️ Safety Features

- **Data Preservation**: All `data-id` and accessibility attributes maintained
- **Non-destructive Processing**: Files can be re-processed safely  
- **Automatic Backups**: JSON files backed up before modification
- **Validation Checks**: Comprehensive validation before applying changes

## 🤝 Contributing

This is part of the UNICEF ADT (Accessible Digital Textbooks) project ecosystem. Scripts move from experimental to production through a structured promotion process documented in `docs/production-deployment.md`.

## 📄 License

MIT License - Part of the UNICEF ADT project ecosystem.

---

*For detailed script usage and examples, see `docs/SCRIPT_USAGE.md`*