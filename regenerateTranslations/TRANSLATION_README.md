# Translation Script for ADT Manual

This script extracts text strings from a specified page range in the Spanish JSON file (`content/i18n/es/texts.json`) and generates English translations in the English JSON file (`content/i18n/en/texts.json`).

## Usage

```bash
# Translate a single page
python3 translate_page_range.py 23

# Translate a page range
python3 translate_page_range.py 23 30

# Dry run (preview translations without saving)
python3 translate_page_range.py 23 30 --dry-run
```

## Features

- **Page Range Support**: Translate single pages or page ranges
- **Dry Run Mode**: Preview translations before applying them
- **Smart Merging**: Preserves existing English translations while adding new ones
- **Pattern Matching**: Automatically finds all text strings matching `text-{page}-{number}` pattern
- **Comprehensive Dictionary**: Includes common terms and phrases for better translations

## Examples

### Single Page Translation
```bash
python3 translate_page_range.py 2
```
Output:
```
Loading Spanish texts from content/i18n/es/texts.json...
Extracting texts for pages 2 to 2...
Found 1 text strings to translate.

Generating English translations...
Translated: text-2-0
  ES: Manual de Autocuidado
  EN: Self-Care Manual

✅ Successfully generated 1 English translations!
📝 Total English translations: 150
```

### Page Range Translation with Preview
```bash
python3 translate_page_range.py 23 25 --dry-run
```
This will show all translations that would be generated without actually saving them.

### Large Page Range
```bash
python3 translate_page_range.py 20 30
```
This will translate all text strings from pages 20 through 30.

## Translation Dictionary

The script includes a comprehensive translation dictionary for common terms:

- **Manual terms**: "Manual de Autocuidado" → "Self-Care Manual"
- **Self-care types**: "Autocuidado físico" → "Physical self-care"
- **Common phrases**: "Se recomienda" → "It is recommended"
- **Navigation**: "Contenido" → "Contents"
- **And many more...**

## File Structure

The script expects the following file structure:
```
content/
├── i18n/
│   ├── es/
│   │   └── texts.json    # Source Spanish translations
│   └── en/
│       └── texts.json    # Target English translations
```

## Script Options

- `page_start`: Starting page number (required)
- `page_end`: Ending page number (optional, defaults to page_start)
- `--dry-run`: Show translations without saving to files

## Notes

1. **Backup Recommended**: The script merges with existing translations, but it's always good to backup your `en/texts.json` file first
2. **Case Sensitivity**: The script preserves case from the translation dictionary
3. **Pattern Matching**: Only matches exact pattern `text-{page}-{number}` (e.g., `text-23-0`, `text-23-1`)
4. **Extensible**: Easy to add more translation pairs to the dictionary

## Advanced Usage

### Adding Custom Translations
Edit the `translations` dictionary in the script to add more Spanish-English pairs:

```python
translations = {
    # Add your custom translations here
    "Tu término español": "Your English term",
    # ...existing translations
}
```

### Running for All Pages
To translate all pages at once, you can find the range by checking your JSON file:

```bash
# See all available text strings
grep -o '"text-[0-9]\+-[0-9]\+"' content/i18n/es/texts.json | sort -u

# Then run for the full range
python3 translate_page_range.py 1 50
```

## Troubleshooting

- **"File not found"**: Make sure you're running the script from the project root directory
- **"No texts found"**: Check that the page range contains text strings in the Spanish JSON
- **Permission errors**: Ensure you have write permissions for the `content/i18n/en/` directory
