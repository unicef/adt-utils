import os
import json
import openai
import logging
import textstat
import difflib
import argparse
from datetime import datetime
from pathlib import Path

# Set up command line arguments
parser = argparse.ArgumentParser(description="Generate easy-to-read versions of texts.")
parser.add_argument('--start', type=str, help="Starting text ID (e.g., text-8-0)")
parser.add_argument('--end', type=str, help="Ending text ID (e.g., text-12-5)")
parser.add_argument('--lang', type=str, default='es', help="Language code (default: es)")
parser.add_argument('--source-lang', type=str, default='es', help="Source language for easy-read generation (default: es)")
parser.add_argument('--dry-run', action='store_true', help="Show what would be processed without making API calls")
parser.add_argument('--preserve-glossary', action='store_true', help="Preserve glossary terms in transformations (adds processing time)")
args = parser.parse_args()

# Set up logging
log_filename = f"easy_read_log_{args.lang}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Define file paths based on new structure
BASE_DIR = Path('content/i18n')
# For easy-read generation, always use the target language as both source and target
# This way we generate easy-read versions of the existing translations
SOURCE_FILE = BASE_DIR / args.lang / 'texts.json'
TARGET_FILE = BASE_DIR / args.lang / 'texts.json'
GLOSSARY_FILE = BASE_DIR / args.lang / 'glossary.json'

# Load glossary words
glossary_words = []
try:
    if GLOSSARY_FILE.exists():
        with open(GLOSSARY_FILE, 'r', encoding='utf-8') as file:
            glossary_json = json.load(file)
        
        # Handle different possible JSON structures
        if isinstance(glossary_json, list):
            if glossary_json and isinstance(glossary_json[0], str):
                glossary_words = glossary_json
            elif glossary_json and isinstance(glossary_json[0], dict) and 'term' in glossary_json[0]:
                glossary_words = [item['term'] for item in glossary_json]
        elif isinstance(glossary_json, dict):
            glossary_words = list(glossary_json.keys())
        
        logging.info(f"Loaded {len(glossary_words)} glossary terms from {GLOSSARY_FILE}")
    else:
        logging.warning(f"Glossary file not found at {GLOSSARY_FILE}")
        # Fallback glossary based on language
        if args.lang == 'es':
            glossary_words = ["autocuidado", "bienestar", "emociones", "términos", "específicos", "técnicos"]
        else:
            glossary_words = ["self-care", "wellbeing", "emotions", "terms", "specific", "technical"]
        logging.info("Using fallback glossary terms")
except Exception as error:
    logging.error(f"Error loading glossary file: {error}")
    glossary_words = ["términos", "específicos", "técnicos"]
    logging.info("Using fallback glossary terms")

# Updated easy-read transformation prompt with balanced approach
easy_read_prompt = """
Transform the following text into an easy-to-read version following these guidelines:

EASY-READ RULES:
1. Use SHORT, SIMPLE sentences (maximum 15 words per sentence)
2. Choose COMMON, EVERYDAY words instead of difficult ones
3. Break long ideas into bullet points with - or numbered lists ONLY when necessary
4. Use emojis thoughtfully to support understanding and highlight key concepts
5. The final text should be SHORTER than the original
6. Keep the same main ideas but remove unnecessary details
7. Use active voice: "You can do this" instead of "This can be done"
8. Explain technical terms only if absolutely necessary

CONTENT GUIDELINES:
- Focus on simplifying existing content, NOT adding new bullet points
- Avoid breaking simple sentences into multiple bullet points
- Only use bullet points for genuinely complex ideas with multiple parts
- Keep the structure similar to the original when possible
- Don't expand content - make it more concise

FORMATTING RULES:
- Use dashes (-) for bullet points only when truly needed
- Keep formatting clean and minimal
- Use clear line breaks for readability
- Group related ideas together

EXAMPLE TRANSFORMATIONS:

BEFORE:
"The incorporation of self-care behaviors enhances productivity: if there is a review of needs and a consequent establishment of boundaries, the most important ones are prioritized."

AFTER:
"💪 Self-care helps you work better. Look at what you need, set clear limits, and focus on what matters most."

BEFORE:
"Emotional regulation strategies involve recognizing physiological responses to stressors and implementing cognitive techniques to modulate affective states through mindfulness practices."

AFTER:
"🧠 Learn to handle your feelings. Notice how your body feels when stressed 😰. Use your mind 🤔 and focus on the present moment to feel calmer."

IMPORTANT: Return ONLY the simplified text. Do not add explanations or comments.
{translation_instruction}

TEXT TO TRANSFORM:
{original_text}
"""

# Function to determine the processing strategy for text
def get_processing_strategy(text):
    """
    Determines how to process text for easy-read.
    Returns: (strategy, reason)
    - 'copy': Copy as-is (table of contents, simple labels)
    - 'simple': Light enhancement with emojis but keep simple
    - 'transform': Full easy-read transformation
    """
    text_stripped = text.strip()
    word_count = len(text_stripped.split())
    
    # Single words or very short text - copy as-is
    if word_count <= 1 or len(text_stripped) <= 3:
        return 'copy', "Single word/very short"
    
    # Pure numbers - copy as-is 
    if text_stripped.replace(' ', '').replace('.', '').replace(',', '').isdigit():
        return 'copy', "Number only"
    
    # Simple labels and status words - copy as-is
    simple_labels = ['true', 'false', 'myth:', 'myth', 'fact:', 'fact', 'yes', 'no', 'correct', 'incorrect']
    if text_stripped.lower() in simple_labels:
        return 'copy', "Simple label"
    
    # Table of contents items (short titles/headings) - add emoji enhancement
    if word_count <= 4 and len(text_stripped) <= 30:
        if (text_stripped[0].isupper() and 
            not text_stripped.endswith('.') and 
            not text_stripped.endswith('!') and 
            not text_stripped.endswith('?')):
            return 'simple', "Short title/heading"
    
    # Short numbered list items - add emoji enhancement  
    if text_stripped.startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
        if word_count <= 8:
            return 'simple', "Numbered list item"
    
    # Questions or short phrases - add emoji enhancement
    if word_count <= 6:
        return 'simple', "Short phrase"
    
    # Everything else gets full transformation
    return 'transform', "Complex text"


# Function to process text based on strategy
def process_text_by_strategy(text, strategy):
    """Process text according to the determined strategy"""
    
    if strategy == 'copy':
        # Just return the original text unchanged
        return text
    
    elif strategy == 'simple':
        # Add contextual emoji but keep text simple
        text_lower = text.lower().strip()
        
        # Enhanced emoji mapping for different contexts
        emoji_map = {
            # Content structure
            'contents': '📚',
            'index': '📑', 
            'introduction': '👋',
            'bibliography': '📖',
            'references': '📄',
            
            # Self-care topics
            'self-care': '💆‍♀️',
            'physical': '💪',
            'emotional': '❤️',
            'mental': '🧠',
            'cognitive': '🤔',
            'social': '👥',
            'spiritual': '✨',
            'wellbeing': '😊',
            'health': '🌿',
            
            # Activities and practices
            'exercise': '🏃‍♀️',
            'nutrition': '🥗',
            'sleep': '😴',
            'meditation': '🧘‍♀️',
            'breathing': '🌬️',
            'mindfulness': '🎯',
            
            # Relationships and communication
            'relationship': '💕',
            'communication': '💬',
            'support': '🤝',
            'family': '👨‍👩‍👧‍👦',
            'friends': '👫',
            
            # Learning and growth
            'learning': '📚',
            'growth': '🌱',
            'development': '📈',
            'skills': '🛠️',
            'practice': '🎯',
            'exercise': '📝',
            
            # Emotions and feelings
            'stress': '😰',
            'anxiety': '😟',
            'depression': '😔',
            'joy': '😄',
            'peace': '☮️',
            'calm': '😌',
            
            # Goals and planning
            'goal': '🎯',
            'plan': '📋',
            'routine': '🔄',
            'habit': '✅',
            'step': '👣',
            
            # Time and scheduling
            'daily': '📅',
            'weekly': '🗓️',
            'morning': '🌅',
            'evening': '🌆',
            'time': '⏰',
        }
        
        # Find appropriate emoji
        emoji = ''
        for keyword, emoji_char in emoji_map.items():
            if keyword in text_lower:
                emoji = emoji_char + ' '
                break
        
        # If no specific emoji found, use generic ones based on context
        if not emoji:
            if text.endswith('?'):
                emoji = '❓ '
            elif any(num in text for num in ['1.', '2.', '3.', '4.', '5.']):
                emoji = '📌 '
            elif text[0].isupper() and len(text.split()) <= 4:
                emoji = '📋 '
        
        return emoji + text
    
    elif strategy == 'transform':
        # Use the full OpenAI transformation
        return transform_to_easy_read(text)
    
    return text

# Function to identify glossary words in a text
def find_glossary_words_in_text(text):
    return [word for word in glossary_words if word.lower() in text.lower()]

# Function to verify glossary terms are preserved
def verify_glossary_terms(original_text, simplified_text, glossary_terms):
    missing_terms = []
    for term in glossary_terms:
        if term.lower() in original_text.lower() and term.lower() not in simplified_text.lower():
            missing_terms.append(term)
    
    if missing_terms:
        logging.warning(f"Missing glossary terms in simplified text: {', '.join(missing_terms)}")
        return False, missing_terms
    return True, []

# Function to calculate readability scores
def calculate_readability(original_text, simplified_text):
    # Calculate Flesch-Kincaid Grade Level for both texts
    original_fk = textstat.flesch_kincaid_grade(original_text)
    simplified_fk = textstat.flesch_kincaid_grade(simplified_text)
    
    # Calculate text statistics
    original_stats = {
        "flesch_kincaid_grade": original_fk,
        "flesch_reading_ease": textstat.flesch_reading_ease(original_text),
        "syllable_count": textstat.syllable_count(original_text),
        "lexicon_count": textstat.lexicon_count(original_text),
        "sentence_count": textstat.sentence_count(original_text)
    }
    
    simplified_stats = {
        "flesch_kincaid_grade": simplified_fk,
        "flesch_reading_ease": textstat.flesch_reading_ease(simplified_text),
        "syllable_count": textstat.syllable_count(simplified_text),
        "lexicon_count": textstat.lexicon_count(simplified_text),
        "sentence_count": textstat.sentence_count(simplified_text)
    }
    
    improvement = original_fk - simplified_fk
    
    return original_stats, simplified_stats, improvement

def transform_to_easy_read(text):
    try:
        # Get API key from environment variable
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError('OPENAI_API_KEY environment variable is not set')
        
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        # Prepare the prompt with original text (no translation needed since same language)
        prompt = easy_read_prompt.format(
            original_text=text,
            translation_instruction=""
        )
        
        logging.info("Transforming text using OpenAI API...")
        
        # Choose system message based on target language
        if args.lang == 'es':
            system_msg = "Eres un experto en lectura fácil. Crea versiones MÁS CORTAS y sencillas usando palabras comunes y frases cortas. Usa emojis de manera inteligente para apoyar la comprensión. No agregues contenido extra. El texto final debe ser más fácil de entender que el original."
        else:
            system_msg = "You are an expert in easy-read text. Create SHORTER and simpler versions using common words and short sentences. Use emojis thoughtfully to support understanding. Don't add extra content. The final text should be easier to understand than the original."
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o",  # Updated to available model
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        
        # Extract and return the simplified text
        simplified_text = response.choices[0].message.content.strip()
        
        # Calculate readability scores
        original_stats, simplified_stats, improvement = calculate_readability(text, simplified_text)
        
        # Log the differences and readability scores
        logging.info(f"Original text: {text}")
        logging.info(f"Simplified text: {simplified_text}")
        logging.info(f"Original readability: Grade {original_stats['flesch_kincaid_grade']:.1f}, Ease {original_stats['flesch_reading_ease']:.1f}")
        logging.info(f"Simplified readability: Grade {simplified_stats['flesch_kincaid_grade']:.1f}, Ease {simplified_stats['flesch_reading_ease']:.1f}")
        logging.info(f"Readability improvement: {improvement:.1f} grade levels")
        
        return simplified_text
    
    except Exception as error:
        logging.error(f'Error calling OpenAI API: {error}')
        # Return original text if API call fails
        return f'Failed to simplify: {text}'

# Function to parse text ID into components for numerical comparison
def parse_text_id(text_id):
    """Parse text-X-Y format into (X, Y) tuple for numerical comparison"""
    parts = text_id.split('-')
    if len(parts) >= 3:
        try:
            return int(parts[1]), int(parts[2])
        except ValueError:
            return 0, 0
    return 0, 0


# Function to check if text_id is within the specified range
def is_in_range(text_id, start_id, end_id):
    """Check if text_id falls within the numerical range from start_id to end_id"""
    if not start_id and not end_id:
        return True
    
    # Parse the current text ID into numerical components
    current_page, current_section = parse_text_id(text_id)
    
    # Parse start and end IDs if provided
    start_page, start_section = parse_text_id(start_id) if start_id else (0, 0)
    end_page, end_section = parse_text_id(end_id) if end_id else (999, 999)
    
    # Create comparable tuples (page, section)
    current = (current_page, current_section)
    start = (start_page, start_section) if start_id else (0, 0)
    end = (end_page, end_section) if end_id else (999, 999)
    
    # Check if current falls within the range
    if start_id and not end_id:
        return current >= start
    elif not start_id and end_id:
        return current <= end
    else:
        return start <= current <= end

def process_translations():
    try:
        # Check if source file exists
        if not SOURCE_FILE.exists():
            logging.error(f"Source file not found: {SOURCE_FILE}")
            logging.info(f"Expected structure: content/i18n/{args.lang}/texts.json")
            return
        
        # Read the source translations file
        with open(SOURCE_FILE, 'r', encoding='utf-8') as file:
            source_translations = json.load(file)
        
        logging.info(f"Loaded source translations from {SOURCE_FILE}")
        
        # Load existing target translations if they exist
        target_translations = {}
        if TARGET_FILE.exists():
            with open(TARGET_FILE, 'r', encoding='utf-8') as file:
                target_translations = json.load(file)
            logging.info(f"Loaded existing target translations from {TARGET_FILE}")
        else:
            logging.info(f"Target file doesn't exist, will create new: {TARGET_FILE}")

        # Determine start and end IDs for filtering
        start_id = args.start
        end_id = args.end
        
        if start_id or end_id:
            logging.info(f"Processing range: {start_id or 'start'} to {end_id or 'end'}")
        
        # Copy all existing target translations to result
        result = target_translations.copy()
                
        # Now process and add easy-read versions
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        # Process each entry in the source translations
        for key, value in source_translations.items():
            # Process only original text entries (not already easy-read)
            if key.startswith('text-') and not key.startswith('easyread-'):
                # Check if this key is in the requested range
                if start_id or end_id:
                    if not is_in_range(key, start_id, end_id):
                        skipped_count += 1
                        continue
                
                original_text = value
                easy_read_key = f'easyread-{key}'
                
                # Always regenerate easy-read version (no skipping existing versions)
                logging.info(f"Processing {key} (regenerating if exists)")
                
                # Check if this text should be processed using strategy approach
                strategy, reason = get_processing_strategy(original_text)
                logging.info(f"Strategy for {key}: {strategy} - {reason}")
                
                # Always generate easy-read version (1:1 mapping requirement)
                if args.dry_run:
                    easy_read_text = f"[DRY RUN] Would process {key} with {strategy} strategy: {original_text[:50]}..."
                    logging.info(f"DRY RUN: Would process {key} with {strategy}")
                else:
                    # Find glossary words in this text (only if preserve-glossary flag is set)
                    if args.preserve_glossary:
                        found_glossary_words = find_glossary_words_in_text(original_text)
                    else:
                        found_glossary_words = []
                    
                    # Process according to strategy
                    easy_read_text = process_text_by_strategy(original_text, strategy)
                
                # For dry run, still count as success
                if args.dry_run:
                    success_count += 1
                    logging.info(f"DRY RUN: Processed {key} with {strategy} strategy")
                else:
                    # Verify all glossary terms are preserved (only if preserve-glossary flag is set and strategy is transform)
                    if args.preserve_glossary and strategy == 'transform' and found_glossary_words:
                        terms_preserved, missing_terms = verify_glossary_terms(original_text, easy_read_text, found_glossary_words)
                        if terms_preserved:
                            success_count += 1
                            logging.info(f"Successfully processed {key} - All glossary terms preserved")
                        else:
                            failure_count += 1
                            logging.warning(f"Issue with {key} - Missing terms: {', '.join(missing_terms)}")
                    else:
                        success_count += 1
                        logging.info(f"Successfully processed {key} with {strategy} strategy")
                
                # Add the easy-read version to results (always overwrite)
                result[easy_read_key] = easy_read_text
        
        # Create target directory if it doesn't exist
        TARGET_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the updated translations to the target file
        with open(TARGET_FILE, 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=2, sort_keys=True)
            
        logging.info(f"Processed {success_count + failure_count} entries. Success: {success_count}, Issues: {failure_count}, Skipped: {skipped_count}")
        logging.info(f"Results saved to {TARGET_FILE}")
        logging.info(f"Log file saved to {log_filename}")
        
    except Exception as error:
        logging.error(f'Error processing translations: {error}')

# Run the script
if __name__ == "__main__":
    logging.info(f"Starting Easy-Read generation process for language: {args.lang}")
    logging.info(f"Source file: {SOURCE_FILE}")
    logging.info(f"Target file: {TARGET_FILE}")
    process_translations()
    logging.info("Easy-Read generation process complete")