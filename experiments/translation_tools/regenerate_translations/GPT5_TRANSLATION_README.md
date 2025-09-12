# GPT-5 Translation System for ADT Manual

Advanced translation system using OpenAI's GPT-5 model for sequential, context-aware translation of the ADT Manual from Spanish to English.

## 🚀 Quick Start

```bash
# Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'

# Translate a single page
./translate_gpt5.sh 23

# Translate a range with context building
./translate_gpt5.sh 23 30

# Preview without API calls (dry run)
./translate_gpt5.sh 23 30 --dry-run
```

## 🧠 Key Features

### **Sequential Context Building**
- Translates text strings in order (page by page, text by text)
- Each translation builds on previous ones for consistency
- Maintains context memory of recent translations
- GPT-5 learns terminology and style as it progresses

### **Professional Translation Quality**
- Uses OpenAI's GPT-5 model for state-of-the-art translation
- Specialized prompts for self-care and wellness content
- Maintains professional tone and terminology
- Context-aware translations that improve over time

### **Smart Memory Management**
- Configurable context window (default: 10 previous translations)
- Loads existing translations to seed initial context
- Prevents token limit issues while maintaining quality
- Optimized for long translation sessions

## 📊 Usage Examples

### Basic Translation
```bash
# Translate page 23 (sleep recommendations)
./translate_gpt5.sh 23
```
Output:
```
🤖 Translating page 23 using GPT-5...
📚 Loading existing translations for context...
📖 Loaded 8 existing translations for context

🚀 Starting sequential translation of 17 text strings...
📖 Building context as we translate...

[1/17] Translating: text-23-0
   Spanish: Dormir y descansar lo suficiente:
   English: Get enough sleep and rest:
   Context size: 9 previous translations

[2/17] Translating: text-23-1
   Spanish: Algunas recomendaciones para garantizar una rutina saludable del sueño son:
   English: Some recommendations to ensure a healthy sleep routine are:
   Context size: 10 previous translations
...
```

### Range Translation with Custom Context
```bash
# Translate pages 27-28 with larger context window
./translate_gpt5.sh 27 28 --context-size 15
```

### Preview Mode
```bash
# See what would be translated without using API
./translate_gpt5.sh 23 30 --dry-run
```

## ⚙️ Configuration Options

### Command Line Options
- `--dry-run` - Preview without API calls or file changes
- `--api-key KEY` - Use specific OpenAI API key
- `--context-size N` - Number of previous translations to remember (default: 10)

### Environment Variables
- `OPENAI_API_KEY` - Your OpenAI API key (required)

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
pip install openai
```

### 2. Set API Key
```bash
# Option 1: Environment variable (recommended)
export OPENAI_API_KEY='your-api-key-here'

# Option 2: Use --api-key flag
./translate_gpt5.sh 23 --api-key 'your-api-key-here'
```

### 3. Run Translation
```bash
# Test with dry run first
./translate_gpt5.sh 2 --dry-run

# Then run actual translation
./translate_gpt5.sh 2
```

## 📈 Translation Strategy

### **Recommended Order**
For best context building, translate in logical sections:

```bash
# 1. Start with foundational pages
./translate_gpt5.sh 0 2     # Cover and title

# 2. Introduction section
./translate_gpt5.sh 6       # Introduction content

# 3. Core content in logical groups
./translate_gpt5.sh 8 15    # Physical self-care basics
./translate_gpt5.sh 16 25   # Advanced physical care
./translate_gpt5.sh 26 30   # Emotional self-care
./translate_gpt5.sh 31 40   # Cognitive and social care
./translate_gpt5.sh 41 53   # Advanced topics
./translate_gpt5.sh 58      # Conclusion
```

### **Context Optimization**
- **Small batches**: 5-10 pages per session for best context
- **Sequential order**: Don't skip around - context builds naturally
- **Review translations**: GPT-5 learns from corrections in future sessions

## 🛡️ Safety Features

### **Automatic Backups**
- Creates timestamped backups before any changes
- Format: `texts.json.backup.YYYYMMDD_HHMMSS`

### **Error Handling**
- Graceful API error recovery
- Rate limiting protection (0.5s delay between calls)
- Validation of all inputs and outputs

### **Cost Control**
- Dry-run mode for testing
- Conservative token usage (max 200 tokens per translation)
- Progress tracking for long sessions

## 💡 Advanced Usage

### **Custom Context Building**
```bash
# For specialized sections, use larger context
./translate_gpt5.sh 42 45 --context-size 20
```

### **Resume Interrupted Sessions**
The system automatically loads existing translations for context, so you can safely resume:
```bash
# If translation stopped at page 35, just continue
./translate_gpt5.sh 36 40
```

### **Quality Review**
```bash
# Re-translate specific pages with improved context
./translate_gpt5.sh 23    # Will use all existing translations as context
```

## 📊 Expected Results

### **Translation Quality**
- Professional, consistent terminology
- Context-aware phrasing that improves over time
- Natural English that maintains Spanish meaning
- Specialized self-care vocabulary

### **Performance**
- ~2-3 seconds per text string (including rate limiting)
- ~20-30 strings per minute
- Scales well for large batches

### **Cost Estimation**
- Approximately $0.01-0.02 per text string with GPT-4o
- Full manual (~535 strings) ≈ $5-10 total cost
- Dry runs are completely free

## 🔍 Troubleshooting

### **Common Issues**
```bash
# API key not set
export OPENAI_API_KEY='your-key-here'

# OpenAI package not installed
pip install openai

# Permission errors
chmod +x translate_gpt5.sh

# Rate limiting
# Script already includes delays, but you can increase context-size for efficiency
```

### **Quality Issues**
- Use larger `--context-size` for better consistency
- Translate in logical order (don't skip around)
- Review and correct early translations to improve later ones

## 📚 Technical Details

### **Context Management**
- Maintains sliding window of recent translations
- Includes existing translations when starting new sessions
- Optimizes prompt structure for consistent terminology

### **API Integration**
- Uses OpenAI's chat completions API
- Professional system prompts for self-care content
- Temperature 0.3 for consistent, professional output
- Built-in retry logic and error handling

### **File Management**
- Sequential processing preserves translation order
- Safe merging with existing translations
- JSON formatting with proper Unicode support

This system provides production-quality translation with the intelligence and context awareness of GPT-5, specifically optimized for the ADT Manual's self-care content.
