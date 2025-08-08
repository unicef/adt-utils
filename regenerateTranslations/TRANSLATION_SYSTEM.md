# ADT Manual Translation System

Complete toolkit for generating English translations from Spanish text strings in the ADT Manual project.

## 🚀 Quick Start

```bash
# Find available pages to translate
python3 find_pages.py

# Translate a single page
./translate.sh 23

# Translate a range of pages
./translate.sh 23 30

# Preview translations (dry run)
./translate.sh 23 30 --dry-run
```

## 📁 Files Included

### Core Scripts
- **`translate_page_range.py`** - Main translation script (Python)
- **`translate.sh`** - User-friendly shell wrapper
- **`find_pages.py`** - Utility to discover available page ranges

### Documentation
- **`TRANSLATION_README.md`** - Detailed documentation
- **`TRANSLATION_SYSTEM.md`** - This overview file

## 🎯 Current Status

The Spanish JSON file contains **535 text strings** across **50 pages** (pages 0-58, with some gaps).

### Available Pages:
```
Page  0:  1 strings    Page 26: 14 strings    Page 42: 17 strings
Page  2:  1 strings    Page 27: 13 strings    Page 43: 17 strings
Page  6: 19 strings    Page 28: 14 strings    Page 44: 24 strings
Page  8: 14 strings    Page 29: 13 strings    Page 45:  9 strings
Page  9:  6 strings    Page 30:  7 strings    Page 46: 11 strings
Page 10:  7 strings    Page 31:  8 strings    Page 47:  1 strings
Page 11: 15 strings    Page 32:  8 strings    Page 48:  7 strings
Page 12:  7 strings    Page 33: 10 strings    Page 49:  5 strings
Page 13: 18 strings    Page 34: 20 strings    Page 50:  3 strings
Page 14: 18 strings    Page 35: 12 strings    Page 51:  4 strings
Page 15:  6 strings    Page 36: 12 strings    Page 52:  3 strings
Page 16: 18 strings    Page 37: 11 strings    Page 53:  4 strings
Page 17: 13 strings    Page 38:  4 strings    Page 58:  2 strings
Page 18: 12 strings    Page 39:  9 strings
Page 19: 12 strings    Page 40: 12 strings
Page 20: 14 strings    Page 41:  6 strings
```

## 🔧 Usage Examples

### Single Page Translation
```bash
# Translate page 23 (sleep recommendations)
./translate.sh 23
```

### Range Translation
```bash
# Translate the emotion expression series (pages 27-28)
./translate.sh 27 28

# Translate the full self-care section (pages 20-30)
./translate.sh 20 30
```

### Bulk Translation
```bash
# Translate everything at once
./translate.sh 0 58

# Or use the suggested ranges for better control:
./translate.sh 0      # Cover page
./translate.sh 2      # Title page
./translate.sh 6      # Introduction
./translate.sh 8 53   # Main content (45 pages)
./translate.sh 58     # Final page
```

### Preview Mode
```bash
# See what would be translated without making changes
./translate.sh 23 30 --dry-run
```

## 🎨 Features

### Smart Translation Dictionary
The system includes translations for:
- ✅ Self-care terminology
- ✅ Manual navigation terms
- ✅ Common recommendations and instructions
- ✅ Sleep and hygiene terminology
- ✅ Emotional wellness vocabulary

### Safe Operation
- 🔒 Automatic backups before translation
- 🔍 Dry-run mode for previewing
- 🔄 Merges with existing translations
- 📝 Detailed logging of all changes

### Easy Discovery
- 📊 `find_pages.py` shows all available content
- 🎯 Suggests optimal translation commands
- 📈 Displays statistics and ranges

## ⚙️ Technical Details

### Pattern Matching
The system looks for text strings matching: `text-{page}-{number}`
- Example: `text-23-0`, `text-23-1`, `text-27-5`

### File Structure
```
content/i18n/
├── es/texts.json      # Source (Spanish)
└── en/texts.json      # Target (English)
```

### Translation Process
1. Extract Spanish strings for specified page range
2. Apply translation dictionary
3. Merge with existing English translations
4. Save updated English file with proper formatting

## 🚨 Important Notes

1. **Backup First**: While the script creates automatic backups, manually backup your `en/texts.json` for safety
2. **Review Output**: The translations use a basic dictionary - review and refine as needed
3. **Incremental Updates**: The system safely merges new translations with existing ones
4. **Case Sensitivity**: Preserves capitalization from the translation dictionary

## 📊 Recommended Translation Order

For systematic translation of the entire manual:

```bash
# 1. Cover and introduction
./translate.sh 0 2

# 2. Main introduction section
./translate.sh 6

# 3. Content sections (in logical groups)
./translate.sh 8 15    # Physical self-care basics
./translate.sh 16 25   # Advanced physical care
./translate.sh 26 30   # Emotional self-care
./translate.sh 31 40   # Cognitive and social care
./translate.sh 41 53   # Advanced topics
./translate.sh 58      # Conclusion

# Or all at once:
./translate.sh 0 58
```

## 🔮 Future Enhancements

Potential improvements:
- Integration with Google Translate API for better quality
- Support for additional languages
- Automatic detection of new text strings
- Quality scoring for translations
- Batch processing with progress indicators

## 🆘 Troubleshooting

### Common Issues
- **"No texts found"**: Check page range with `python3 find_pages.py`
- **Permission errors**: Ensure write access to `content/i18n/en/`
- **File not found**: Run scripts from project root directory

### Getting Help
Run any script without arguments to see usage instructions:
```bash
./translate.sh          # Shows help
python3 find_pages.py   # Shows available pages
```
