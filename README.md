# ADT Utils - HTML Standardization Suite

A comprehensive collection of Python utilities for standardizing and processing HTML files in the ADT (Adaptive Document Technology) project. These scripts ensure consistent styling, structure, and formatting across all HTML documents using Tailwind CSS.

## 🚀 Features

### Complete Standardization Pipeline
- **HTML Structure Standardization**: Consistent body and container classes
- **Heading Typography**: Standardized heading styles and colors  
- **Image & Text Layouts**: Intelligent responsive layouts based on content analysis
- **Text Restructuring**: Proper span wrapping and paragraph grouping
- **JSON Text Cleanup**: Remove formatting artifacts from JSON files

### Validation & Auto-Fixing
- **HTML Validation**: Comprehensive validation of data-id attributes
- **Auto-Fix Missing Data-IDs**: Automatically adds missing data-id attributes
- **JSON Integration**: Smart matching with existing translations

### Translation & Localization
- **Multi-language GPT Translation**: AI-powered translation with context awareness
- **Flexible Language Support**: Configurable source and target languages (es, en, fr, pt, etc.)
- **Smart Path Detection**: Automatic discovery of i18n structure in target directories
- **Simple Translation**: Dictionary-based translation for common terms
- **Sequential Processing**: Maintains context across related text elements

### TTS Audio Generation
- **Multi-language TTS**: English and Spanish audio generation
- **El Salvador Spanish Accent**: Specialized TTS for regional dialect
- **Batch Processing**: Efficient audio generation for page ranges

### Smart Content Analysis
- Automatic text-to-image ratio calculation
- Intelligent layout strategy selection
- Content-aware paragraph grouping
- Responsive design adaptation

### Preservation of Important Data
- All `data-id` attributes maintained
- Accessibility attributes preserved
- Existing content structure respected

## 📁 Current Repository Structure

```
adt-utils/
├── standardize_all.py               # Master script - runs everything
├── standardize_html.py              # HTML structure standardization
├── standardize_headings.py          # Heading typography & colors
├── standardize_image_text_layouts.py # Layout optimization
├── demo_standardization.py         # Demo/testing script
├── restructure_text.py             # Advanced text restructuring
├── restructure_text_simple.py      # Simplified text restructuring
├── clean_json_texts.py              # JSON cleanup utility
├── test_single_layout.py           # Test layout on single file
├── restore_template.py             # Restore original structure
├── validate_adt.py                 # HTML validation for data-id attributes
├── fix_missing_data_ids.py         # Auto-fix missing data-id attributes
├── config.py                       # Configuration and path management
├── heading_templates.json          # Heading style configurations
├── regenerate_translations/        # Translation utilities
│   ├── translate_gpt5.py           # GPT-5 translation with context
│   ├── translate_page_range.py     # Simple translation utility
│   └── *.md                        # Translation documentation
├── regenerate_tts_es/              # TTS audio generation
│   ├── regenerate_tts.py           # Multi-language TTS generation
│   ├── setup_tts.py                # TTS setup utilities
│   └── *.md                        # TTS documentation
├── Dockerfile                      # Docker container definition
├── docker-compose.yml              # Docker Compose configuration
├── Makefile                        # Make commands for Docker operations
├── .gitignore                      # Git ignore rules
├── IMAGE_TEXT_LAYOUTS.md           # Layout strategy documentation
└── README.md                       # This file
```

## 🛠️ Quick Start

### Prerequisites
```bash
pip install beautifulsoup4 nltk
```

### Run Complete Standardization
```bash
# Standardize all files from page 6 to 58
python standardize_all.py 6 58

# Skip JSON cleaning if not needed
python standardize_all.py 6 58 --skip-json
```

### Run Individual Components
```bash
# HTML structure only
python standardize_html.py 6 58

# Headings and colors only  
python standardize_headings.py 6 58

# Text restructuring only
python restructure_text_simple.py 6 58

# Image layouts only
python standardize_image_text_layouts.py

# JSON cleanup only
python clean_json_texts.py --dir ./output/content/i18n/
```

## 📊 What Gets Standardized

### HTML Structure (`standardize_html.py`)
- **Body tag**: `bg-white lg:p-5 md:p-5 sm:p-0 mb-12 font-sans text-lg`
- **Container div**: `container mx-auto max-w-5xl bg-white rounded-lg lg:px-24 md:px-12 sm:px-6 pt-12 pb-12`
- **Section tags**: All classes removed for clean structure

### Typography (`standardize_headings.py`)
- **H1**: `text-5xl font-bold mb-4` + color
- **H2**: `text-2xl font-bold mb-4` + color  
- **H3-H6**: Scaled appropriately with consistent colors
- **Background boxes**: Standardized to `bg-green-50`, `bg-amber-50`, `bg-purple-50`

### Layout Intelligence (`standardize_image_text_layouts.py`)

The layout engine automatically analyzes content and applies intelligent responsive layouts based on text-to-image ratios:

#### Layout Strategy Matrix

| Text-to-Image Ratio | Layout Strategy | Description | Use Case |
|---------------------|----------------|-------------|----------|
| **< 100** | Image Top, Text Bottom | Minimal text, image-focused | Infographics, diagrams |
| **100-500** | Image Left, Text Right | Balanced content | Tutorials, explanations |
| **500-1000** | Text Left, Image Right | Text-heavy with supporting image | Articles, detailed content |
| **> 1000** | Text Top, Image Bottom | Text-dominant content | Documentation, essays |

#### Technical Implementation

**Content Analysis Process:**
1. **Text Extraction**: Counts characters in all text elements (excluding alt text)
2. **Image Detection**: Identifies `<img>` tags and calculates count
3. **Ratio Calculation**: `text_char_count / image_count`
4. **Layout Application**: Applies corresponding Tailwind CSS classes

**Generated CSS Classes:**
```html
<!-- Image Top (ratio < 100) -->
<div class="flex flex-col space-y-4">
  <div class="flex justify-center"><!-- images --></div>
  <div><!-- text content --></div>
</div>

<!-- Image Left (100-500) -->
<div class="flex flex-col lg:flex-row lg:space-x-6 space-y-4 lg:space-y-0">
  <div class="lg:w-1/2"><!-- images --></div>
  <div class="lg:w-1/2"><!-- text --></div>
</div>

<!-- Text Left (500-1000) -->
<div class="flex flex-col lg:flex-row lg:space-x-6 space-y-4 lg:space-y-0">
  <div class="lg:w-2/3"><!-- text --></div>
  <div class="lg:w-1/3"><!-- images --></div>
</div>

<!-- Text Top (ratio > 1000) -->
<div class="flex flex-col space-y-4">
  <div><!-- text content --></div>
  <div class="flex justify-center"><!-- images --></div>
</div>
```

#### Responsive Behavior
- **Mobile**: All layouts stack vertically (`flex-col`)
- **Desktop**: Applies side-by-side layouts (`lg:flex-row`)
- **Tablet**: Inherits mobile behavior for consistency

#### Smart Features
- **Automatic Detection**: No manual configuration needed
- **Content Preservation**: All `data-id` attributes maintained
- **Accessibility**: Proper semantic structure preserved
- **Fallback Handling**: Defaults to text-top layout if analysis fails

For detailed examples and edge cases, see [`IMAGE_TEXT_LAYOUTS.md`](IMAGE_TEXT_LAYOUTS.md).

### Text Structure (`restructure_text_simple.py`)
- Wraps text in `<span>` tags with `data-id` attributes
- Groups related content into proper paragraphs
- Preserves accessibility attributes

## 🔧 Configuration

### Heading Templates
Customize styles in `heading_templates.json`:

```json
{
  "heading_templates": {
    "h1": {
      "classes": "text-5xl font-bold mb-4",
      "color_options": ["text-amber-700", "text-red-600", "text-purple-500"]
    }
  },
  "color_mapping": {
    "blue": "text-amber-700",
    "green": "text-amber-700"
  }
}
```

## 📖 Usage Examples

### Standardize Specific Page Range
```bash
# Process pages 10-15
python standardize_all.py 10 15
```

### Test Single File Layout
```bash
# Test layout changes on one file
python test_single_layout.py output/25_0_adt.html
```

### Clean JSON Files
```bash
# Remove unwanted \n characters from JSON
python clean_json_texts.py --dir ./output/content/i18n/

# Clean specific file
python clean_json_texts.py --file ./output/content/i18n/es/texts.json

# Clean with custom pattern
python clean_json_texts.py --dir ./output/ --pattern "*.json"
```

## 🐳 Docker Usage

### Quick Start with Docker
```bash
# Build the image
make build

# Run complete standardization
make run-all START=6 END=58

# Run with custom target folder
make run-all TARGET_DIR=../my-project START=10 END=20
```

### Docker Compose
```bash
# Edit docker-compose.yml to set your target folder, then:
docker-compose run adt-utils python standardize_all.py 6 58

# Run specific scripts
docker-compose run adt-utils python clean_json_texts.py --dir /workspace/target-folder/content/i18n/
```

## 🔄 Complete Workflow: Standardization + Validation + Translation + TTS

### Prerequisites for Extended Workflow
```bash
# Set your OpenAI API key for translation and TTS
export OPENAI_API_KEY=your_api_key_here
```

### Full Pipeline in One Command
```bash
# Complete workflow: validate → fix → translate → TTS
make complete-workflow TARGET_DIR=../my-project START=10 END=15
```

### Step-by-Step Workflow

#### 1. Standardization (Original Pipeline)
```bash
# Run the original standardization pipeline
make run-all TARGET_DIR=../my-project START=10 END=15
```

#### 2. Validation & Auto-Fixing
```bash
# Check for missing data-id attributes
make validate TARGET_DIR=../my-project

# See detailed violations
make validate-verbose TARGET_DIR=../my-project

# Auto-fix missing data-id attributes
make fix-data-ids TARGET_DIR=../my-project

# Complete validation and fix workflow
make validate-fix TARGET_DIR=../my-project
```

#### 3. Translation
```bash
# Simple dictionary-based translation
make translate-simple TARGET_DIR=../my-project START=10 END=12

# AI-powered translation with context (default: Spanish to English)
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12

# Translate to different languages (e.g., Spanish to French)
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=es TARGET_LANG=fr

# Translate from English to Portuguese
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=en TARGET_LANG=pt

# Dry run to preview translations
make translate-gpt5-dry TARGET_DIR=../my-project START=10 END=12
```

#### 4. TTS Audio Generation
```bash
# Generate English TTS
make regenerate-tts-en TARGET_DIR=../my-project START=10 END=12

# Generate Spanish TTS (with El Salvador accent)
make regenerate-tts-es TARGET_DIR=../my-project START=10 END=12

# Generate both languages
make regenerate-tts-both TARGET_DIR=../my-project START=10 END=12
```

### Workflow Benefits
- **Automated validation** ensures all text elements have proper data-id attributes
- **Smart matching** reuses existing translations when possible
- **Context-aware translation** improves translation quality
- **Batch processing** handles page ranges efficiently
- **Multi-language support** for English and Spanish
- **Regional accent support** for Spanish TTS (El Salvador)

### Manual Docker Commands
```bash
# Build image
docker build -t adt-utils .

# Run standardization (replace 'target-folder' with your folder name)
docker run --rm -v "$(pwd)/../:/workspace" \
  -e ADT_OUTPUT_DIR=/workspace/target-folder \
  adt-utils python standardize_all.py 6 58

# Clean JSON files in external folder
docker run --rm -v "$(pwd)/../:/workspace" \
  adt-utils python clean_json_texts.py --dir /workspace/target-folder/content/i18n/
```

### Available Make Commands
```bash
make help                        # Show all available commands
make run-demo                    # Run demo on pages 6-10
make clean-json                  # Clean JSON files
make test-layout FILE=path.html  # Test single file
make shell                       # Open container shell for debugging
```

## 🧪 Testing & Validation

### Demo Mode
```bash
# Local
python demo_standardization.py 6 10

# Docker
make run-demo
```

### Single File Testing
```bash
# Local
python test_single_layout.py path/to/file.html

# Docker
make test-layout FILE=target-folder/file.html
```

### Restore Templates
```bash
# Local
python restore_template.py

# Docker
docker-compose run adt-utils python restore_template.py
```

## 📋 Output

After running `standardize_all.py`, your files will have:

✅ **Consistent HTML structure and styling**  
✅ **Standardized heading typography and colors**  
✅ **Unified background colors for content boxes**  
✅ **Text wrapped in spans with proper data-id attributes**  
✅ **Intelligently grouped paragraphs**  
✅ **Responsive image and text layouts**  
✅ **Clean JSON text files without formatting artifacts**  
✅ **Preserved accessibility attributes and data IDs**

## 🔄 Integration Workflow

1. **Prepare**: Ensure HTML files are in `./output/` directory
2. **Configure**: Adjust `heading_templates.json` if needed
3. **Run**: Execute `standardize_all.py` with your page range
4. **Verify**: Check output files for consistency
5. **Deploy**: Use standardized files in your project

## 🛡️ Safety Features

- **Automatic backups** created for JSON files
- **Preservation** of all `data-id` and accessibility attributes  
- **Non-destructive** processing (files can be re-processed)
- **Validation** checks before writing changes

## 📝 Script Descriptions

| Script | Purpose | Usage |
|--------|---------|-------|
| `standardize_all.py` | Master script that runs all standardization | `python standardize_all.py 6 58` |
| `standardize_html.py` | HTML structure and container classes | `python standardize_html.py 6 58` |
| `standardize_headings.py` | Heading typography and colors | `python standardize_headings.py 6 58` |
| `standardize_image_text_layouts.py` | Image and text layout optimization | `python standardize_image_text_layouts.py` |
| `restructure_text.py` | Advanced text restructuring | `python restructure_text.py 6 58` |
| `restructure_text_simple.py` | Simplified text restructuring | `python restructure_text_simple.py 6 58` |
| `clean_json_texts.py` | Clean JSON text formatting | `python clean_json_texts.py --dir ./output/` |
| `validate_adt.py` | Validate HTML files for data-id attributes | `python validate_adt.py ./target-folder --verbose` |
| `fix_missing_data_ids.py` | Auto-fix missing data-id attributes | `python fix_missing_data_ids.py ./target-folder` |
| `demo_standardization.py` | Demo script for testing | `python demo_standardization.py 6 10` |
| `test_single_layout.py` | Test layout on single file | `python test_single_layout.py file.html` |
| `restore_template.py` | Restore original structure | `python restore_template.py` |

### Translation & TTS Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `regenerate_translations/translate_gpt5.py` | AI-powered translation with context (multi-language) | `python translate_gpt5.py /path/to/target 10 15 --source-lang es --target-lang en` |
| `regenerate_translations/translate_page_range.py` | Simple dictionary-based translation | `python translate_page_range.py 10 15` |
| `regenerate_tts_es/regenerate_tts.py` | Generate TTS audio for multiple languages | `python regenerate_tts.py --start-page 10 --end-page 15 --language both` |

## 🚀 Suggested Future Structure

For better organization as the project grows, consider this structure:

```
adt-utils/
├── scripts/
│   ├── standardization/          # Move standardization scripts here
│   ├── text_processing/          # Move text processing scripts here
│   ├── validation/               # Future validation scripts
│   └── utilities/                # Move utility scripts here
├── config/
│   └── heading_templates.json    # Move config files here
├── docs/
│   ├── IMAGE_TEXT_LAYOUTS.md     # Move documentation here
│   └── api_reference.md          # Future API docs
├── tests/
│   └── test_*.py                 # Future test files
├── examples/
│   └── sample_files/             # Example input/output files
└── README.md
```

## 🤝 Contributing

This utility suite is designed to be modular and extensible. Future enhancements could include:

- **Validation scripts** to verify standardization compliance
- **Report generation** for standardization coverage
- **Custom template support** for different project variants
- **Integration with CI/CD** pipelines
- **Performance optimization** for large file sets
- **Unit tests** for each script component

## 📄 License

MIT License - See LICENSE file for details

---

*Part of the ADT (Accessible Digital Textbooks) project ecosystem*  
*Maintained by UNICEF*
