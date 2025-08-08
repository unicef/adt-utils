# TTS Audio Regeneration Script

This script asynchronously regenerates TTS (Text-to-Speech) audio files for text keys using OpenAI's TTS API. It supports both English and Spanish languages, with Spanish using El Salvador accent features.

## Features

- ✅ **Asynchronous processing** for faster generation
- ✅ **Page range support** - regenerate specific sections (e.g., pages 0-5)
- ✅ **Multi-language support** - English and Spanish
- ✅ **El Salvador Spanish accent** - Custom prompting for authentic pronunciation
- ✅ **Rate limiting** - Respects API limits with concurrent request management
- ✅ **Comprehensive logging** - Detailed logs for debugging and monitoring
- ✅ **Progress tracking** - Real-time status updates and summary reports

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Or run the setup script:

```bash
python setup_tts.py
```

### 2. Set OpenAI API Key

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or provide it directly when running the script with `--api-key`.

### 3. Verify Directory Structure

Ensure you have the following structure:
```
output/
└── content/
    └── i18n/
        ├── en/
        │   ├── texts.json
        │   └── audio/
        └── es/
            ├── texts.json
            └── audio/
```

## Usage

### Basic Usage

```bash
# Regenerate English audio for pages 0-5
python regenerate_tts.py --start-page 0 --end-page 5 --language en

# Regenerate Spanish audio for pages 10-15
python regenerate_tts.py --start-page 10 --end-page 15 --language es

# Regenerate both languages for pages 0-5
python regenerate_tts.py --start-page 0 --end-page 5 --language both
```

### Advanced Usage

```bash
# Provide API key directly
python regenerate_tts.py --start-page 0 --end-page 5 --language en --api-key sk-...

# Single page
python regenerate_tts.py --start-page 5 --end-page 5 --language es
```

## Command Line Arguments

- `--start-page`: Starting page number (inclusive, required)
- `--end-page`: Ending page number (inclusive, required)
- `--language`: Language to regenerate (`en`, `es`, or `both`, default: `both`)
- `--api-key`: OpenAI API key (optional if set in environment)

## How It Works

### Text Key Filtering

The script processes text keys based on page numbers extracted from the key format:
- `text-5-2` → Page 5, processed if 5 is within the specified range
- `img-10-1` → Page 10, processed if 10 is within the specified range
- `sectioneli5-8-0` → Page 8, processed if 8 is within the specified range

### Audio File Naming

Generated audio files follow these patterns:
- `text-5-2` → `text-5-2_en.mp3` or `text-5-2_es.mp3`
- `img-10-1` → `img-10-1_en.mp3` or `img-10-1_es.mp3`
- Other keys → `easyread-{key}_{language}.mp3`

### Language-Specific Features

#### English (`en`)
- Uses `alloy` voice for clear, neutral pronunciation
- Professional tone optimized for educational content

#### Spanish (`es`)
- Uses `nova` voice for natural female Spanish pronunciation
- **El Salvador accent prompting**: Includes specific instructions to use El Salvador pronunciation features:
  - Soft pronunciation characteristics
  - Regional phonetic features typical of El Salvador
  - Authentic Central American Spanish intonation

### Rate Limiting

The script implements:
- Maximum 5 concurrent requests to respect API limits
- Proper error handling and retry logic
- Progress tracking with detailed logging

## Output and Logging

### Console Output
- Real-time progress updates
- Summary report with success/failure counts
- Error notifications

### Log File
- Detailed logs saved to `tts_regeneration.log`
- Includes timestamps, API responses, and error details
- Useful for debugging and monitoring long-running jobs

### Example Output

```
2024-01-15 10:30:15 - INFO - Starting TTS regeneration for pages 0-5, languages: ['en', 'es']
2024-01-15 10:30:15 - INFO - Loaded 156 texts for language: en
2024-01-15 10:30:15 - INFO - Filtered to 23 texts for pages 0-5
2024-01-15 10:30:16 - INFO - Generating audio for: text-0-0_en.mp3
2024-01-15 10:30:17 - INFO - Successfully generated: text-0-0_en.mp3
...

==================================================
TTS REGENERATION SUMMARY
==================================================
EN: 23 successful, 0 failed
ES: 23 successful, 0 failed

TOTAL: 46 successful, 0 failed
```

## Programmatic Usage

You can also use the `TTSRegenerator` class directly in your Python code:

```python
import asyncio
from regenerate_tts import TTSRegenerator

async def regenerate_custom():
    async with TTSRegenerator("your-api-key") as regenerator:
        results = await regenerator.regenerate(
            start_page=0, 
            end_page=5, 
            languages=['en', 'es']
        )
        print(results)

asyncio.run(regenerate_custom())
```

## Error Handling

The script handles various error conditions:
- Missing API key
- Invalid page ranges
- Missing text files
- API rate limits and errors
- Network connectivity issues
- File system permissions

Check the log file for detailed error information.

## Cost Estimation

OpenAI TTS pricing (as of 2024):
- **TTS-1**: $15.00 / 1M characters
- Average text length: ~100 characters
- Cost per audio file: ~$0.0015

Example costs:
- 50 text entries: ~$0.075
- 200 text entries: ~$0.30
- 1000 text entries: ~$1.50

## Tips for Optimal Usage

1. **Test with small ranges first**: Start with `--start-page 0 --end-page 1` to verify setup
2. **Monitor logs**: Check `tts_regeneration.log` for any issues
3. **Use appropriate page ranges**: Don't regenerate everything unless necessary
4. **Set API key in environment**: More secure than command line arguments
5. **Check output directories**: Ensure proper permissions for writing audio files

## Troubleshooting

### Common Issues

1. **"OpenAI API key must be provided"**
   - Set `OPENAI_API_KEY` environment variable or use `--api-key`

2. **"No texts found for pages X-Y"**
   - Check that texts.json contains keys for those page numbers
   - Verify page range is correct

3. **"Directory missing"**
   - Run `python setup_tts.py` to check directory structure
   - Ensure `output/content/i18n/en/` and `output/content/i18n/es/` exist

4. **API errors**
   - Check your OpenAI API key is valid and has credits
   - Verify internet connection
   - Check rate limits in OpenAI dashboard

## Requirements

- Python 3.7+
- `aiohttp>=3.8.0`
- `aiofiles>=22.1.0`
- Valid OpenAI API key with TTS access
