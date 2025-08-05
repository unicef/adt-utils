# ADT Utils - HTML Standardization Suite

A comprehensive collection of Python utilities for standardizing and processing HTML files in the ADT (Adaptive Document Technology) project. These scripts ensure consistent styling, structure, and formatting across all HTML documents using Tailwind CSS.

## 🚀 Features

### Complete Standardization Pipeline
- **HTML Structure Standardization**: Consistent body and container classes
- **Heading Typography**: Standardized heading styles and colors  
- **Image & Text Layouts**: Intelligent responsive layouts based on content analysis
- **Text Restructuring**: Proper span wrapping and paragraph grouping
- **JSON Text Cleanup**: Remove formatting artifacts from JSON files

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
├── heading_templates.json          # Heading style configurations
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

## 🧪 Testing & Validation

### Demo Mode
```bash
# Run demo on small file range
python demo_standardization.py 6 10
```

### Single File Testing
```bash
# Test layout changes on specific file
python test_single_layout.py path/to/file.html
```

### Restore Templates
```bash
# Restore original template structure if needed
python restore_template.py
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
| `demo_standardization.py` | Demo script for testing | `python demo_standardization.py 6 10` |
| `test_single_layout.py` | Test layout on single file | `python test_single_layout.py file.html` |
| `restore_template.py` | Restore original structure | `python restore_template.py` |

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
