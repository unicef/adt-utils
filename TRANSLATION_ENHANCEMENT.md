# GPT Translation Script Enhancement

## Summary of Changes

The `translate_gpt5.py` script has been enhanced to be more general and flexible, supporting multiple source and target languages with configurable paths.

## 🔧 Key Improvements

### 1. **Multi-Language Support**
- **Configurable source and target languages**: No longer hardcoded to Spanish→English
- **Language detection**: Automatic language name mapping for better user experience
- **Supported languages**: Spanish (es), English (en), French (fr), Portuguese (pt), and easily extensible

### 2. **Flexible Path Configuration**
- **Target directory parameter**: First positional argument specifies the root directory
- **Dynamic path resolution**: Automatically finds `content/i18n/{language}/texts.json`
- **Path validation**: Checks for directory and file existence before processing

### 3. **Enhanced Command-Line Interface**
```bash
# Old usage (hardcoded paths and languages)
python translate_gpt5.py 10 15 --api-key KEY

# New usage (flexible and configurable)
python translate_gpt5.py /path/to/target 10 15 --source-lang es --target-lang en --api-key KEY
```

### 4. **Updated Class Structure**
- **Renamed class**: `GPT5Translator` → `GPTTranslator` (more generic)
- **Language configuration**: Built-in language mapping with descriptions
- **Context-aware prompts**: Dynamic prompt generation based on source/target languages

## 🚀 New Makefile Integration

### **Language Variables**
```makefile
SOURCE_LANG ?= es  # Default source language
TARGET_LANG ?= en  # Default target language
```

### **Updated Commands**
```bash
# Default behavior (Spanish to English)
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12

# Custom language pair (Spanish to French)
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=es TARGET_LANG=fr

# English to Portuguese
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=en TARGET_LANG=pt
```

## 📋 Usage Examples

### **Basic Translation (Spanish to English)**
```bash
export OPENAI_API_KEY=your_api_key_here
make translate-gpt5 TARGET_DIR=../ADT-manual-autocuidados START=10 END=12
```

### **Multi-Language Translation**
```bash
# Translate to French
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=es TARGET_LANG=fr

# Translate from English to Spanish (reverse direction)
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=en TARGET_LANG=es

# Translate to Portuguese
make translate-gpt5 TARGET_DIR=../my-project START=10 END=12 SOURCE_LANG=es TARGET_LANG=pt
```

### **Direct Script Usage**
```bash
# Run the script directly with custom parameters
docker run --rm -v "$(pwd):/workspace" \
    -e OPENAI_API_KEY=your_key \
    adt-utils python /app/regenerate_translations/translate_gpt5.py \
    /workspace/target-folder 10 12 \
    --source-lang es --target-lang fr \
    --context-size 15
```

## 🔍 Technical Details

### **File Structure Requirements**
The script expects the following directory structure in the target directory:
```
target-directory/
├── content/
│   └── i18n/
│       ├── es/
│       │   └── texts.json    # Source language
│       └── en/
│           └── texts.json    # Target language (created/updated)
```

### **Language Configuration**
The script includes built-in configuration for common languages:
- **Spanish (es)**: "self-care manual from Spanish"
- **English (en)**: "self-care manual to English"  
- **French (fr)**: "self-care manual to French"
- **Portuguese (pt)**: "self-care manual to Portuguese"

Additional languages can be easily added to the `lang_config` dictionary.

### **Context Management**
- **Context size**: Configurable number of previous translations to maintain
- **Language-aware context**: Context descriptions adapt to source/target languages
- **Sequential processing**: Maintains translation consistency across related content

## 🔄 Backward Compatibility

The changes maintain backward compatibility with existing workflows:
- **Default languages**: Spanish to English (same as before)
- **Default paths**: Works with existing project structures
- **Make commands**: Existing commands work without modification
- **API compatibility**: Same OpenAI API usage patterns

## 🎯 Benefits

### **For Content Creators**
- **Multi-language support**: Translate to any supported target language
- **Flexible workflows**: Use the same tool for different language pairs
- **Context preservation**: Better translation quality through context awareness

### **For Developers**
- **Reusable tool**: One script handles multiple language combinations
- **Easy integration**: Simple parameter changes for different projects
- **Extensible design**: Easy to add new languages and features

### **For Project Management**
- **Standardized workflow**: Same process for all language translations
- **Cost optimization**: Efficient context management reduces API calls
- **Quality assurance**: Consistent translation approach across languages

## 🔮 Future Enhancements

The enhanced design enables future improvements:
- **Language auto-detection**: Automatically detect source language
- **Batch language processing**: Translate to multiple target languages in one run
- **Custom language models**: Support for specialized translation models
- **Translation memory**: Persistent context across translation sessions
- **Quality metrics**: Translation quality scoring and validation

---

*This enhancement makes the translation tool significantly more flexible and useful for international projects while maintaining simplicity and reliability.*
