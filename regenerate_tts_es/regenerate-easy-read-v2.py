import os
import json
import openai
import logging
import textstat
import difflib
import argparse
from datetime import datetime

# Set up command line arguments
parser = argparse.ArgumentParser(description="Generate easy-to-read versions of Spanish texts.")
parser.add_argument('--start', type=str, help="Starting text ID (e.g., text-8-0)")
parser.add_argument('--end', type=str, help="Ending text ID (e.g., text-12-5)")
args = parser.parse_args()

# Set up logging
log_filename = f"easy_read_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Load glossary words from glossary_es.json file
glossary_words = []
try:
    with open('glossary_es.json', 'r', encoding='utf-8') as file:
        glossary_json = json.load(file)
    
    # Handle different possible JSON structures
    if isinstance(glossary_json, list):
        if isinstance(glossary_json[0], str):
            glossary_words = glossary_json
        elif glossary_json[0] and 'term' in glossary_json[0]:
            glossary_words = [item['term'] for item in glossary_json]
    elif isinstance(glossary_json, dict):
        glossary_words = list(glossary_json.keys())
    
    logging.info(f"Loaded {len(glossary_words)} glossary terms from glossary_es.json")
except Exception as error:
    logging.error(f"Error loading glossary file: {error}")
    glossary_words = ["términos", "específicos", "técnicos"]
    logging.info("Using fallback glossary terms")

# Updated easy-read transformation prompt in Spanish
easy_read_prompt = """
Convertir el siguiente texto a formato de lectura fácil siguiendo estas instrucciones:

INSTRUCCIONES PARA CREAR TEXTOS DE LECTURA FÁCIL:
1. Usar frases cortas y sencillas con estructura: sujeto + verbo + complementos.
2. Simplificar el vocabulario usando palabras comunes y cotidianas.
3. Explicar SOLO términos técnicos esenciales, de forma muy breve.
4. Usar listas con viñetas para ideas múltiples.
5. Reducir la longitud total - el texto simplificado debe ser más corto que el original.
6. Añadir emojis relevantes con moderación (máximo 1 por párrafo o punto de lista).
7. Eliminar información secundaria o redundante.
8. Mantener el mismo orden de las ideas del texto original.
9. No añadir información o explicaciones que no estén en el texto original.
10. No repetir conceptos que ya se han explicado.

IMPORTANTE: El texto simplificado debe ser MÁS CORTO que el original.

FORMATO DE RESPUESTA:
Devolver solo el texto simplificado con emojis apropiados. No incluir preguntas, explicaciones ni indicar que es lectura fácil.

EJEMPLO:

INPUT:
La deforestación excesiva, la caza indiscriminada de algunas especies, la pesca intensiva (merluza, por ejemplo), la perforación de terrenos para la explotación minera (petróleo, carbón y otros minerales) son algunos ejemplos de actividades que pueden provocar daños en el planeta.

OUTPUT:
🌎 Algunas actividades humanas dañan el planeta:

- Cortar demasiados árboles (deforestación)
- Cazar animales sin control 
- Pescar en exceso, como la merluza
- Hacer agujeros para sacar minerales como petróleo y carbón

Estas acciones dañan la naturaleza y hacen que algunos seres vivos desaparezcan.

TEXTO A CONVERTIR:
{original_text}

Provide me the text in easy-read format. Please think carefully before responding.
"""

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
        
        # Prepare the prompt with original text
        prompt = easy_read_prompt.format(original_text=text)
        
        logging.info("Transforming text using OpenAI API...")
        
        # Call OpenAI API with explicit Spanish output requirement
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "Eres un asistente que simplifica textos en español uruguayo. Debes crear versiones CONCISAS y fáciles de leer, usando lenguaje sencillo y añadiendo algunos emojis relevantes. El texto simplificado debe ser más corto que el original."},
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
        
        # Log differences between texts
        diff = list(difflib.ndiff(text.splitlines(), simplified_text.splitlines()))
        logging.info("Text differences:")
        for line in diff:
            if line.startswith('+ ') or line.startswith('- ') or line.startswith('? '):
                logging.info(line)
        
        return simplified_text
    
    except Exception as error:
        logging.error(f'Error calling OpenAI API: {error}')
        # Return original text if API call fails
        return f'Failed to simplify: {text}'

# Function to parse text ID into components for comparison
def parse_text_id(text_id):
    parts = text_id.split('-')
    if len(parts) >= 3:
        try:
            return int(parts[1]), int(parts[2])
        except ValueError:
            return 0, 0
    return 0, 0

# Function to check if text_id is within the specified range
def is_in_range(text_id, start_id, end_id):
    if not start_id and not end_id:
        return True
    
    if start_id and not end_id:
        return text_id >= start_id
        
    if not start_id and end_id:
        return text_id <= end_id
        
    return start_id <= text_id <= end_id

# Main function to process the translations
def process_translations():
    try:
        # Read the translations file
        with open('translations2_es.json', 'r', encoding='utf-8') as file:
            translations = json.load(file)

        # Determine start and end IDs for filtering
        start_id = args.start
        end_id = args.end
        
        if start_id or end_id:
            logging.info(f"Processing range: {start_id or 'start'} to {end_id or 'end'}")
        
        # Check if translations has a "texts" key structure
        if "texts" in translations:
            logging.info("Found nested 'texts' structure in translations file")
            texts_data = translations["texts"]
            is_nested = True
        else:
            logging.info("Found flat structure in translations file")
            texts_data = translations
            is_nested = False
        
        # Setup result structure to match input
        if is_nested:
            result = {"texts": {}}
        else:
            result = {}
        
        # First, copy all original entries
        if is_nested:
            for key, value in texts_data.items():
                result["texts"][key] = value
        else:
            for key, value in texts_data.items():
                result[key] = value
                
        # Now process and add easy-read versions
        success_count = 0
        failure_count = 0
        skipped_count = 0
        
        # Process each entry in the translations that needs simplification
        for key, value in texts_data.items():
            # Process only original text entries (not already easy-read)
            if key.startswith('text-') and not key.startswith('easyread-'):
                # Check if this key is in the requested range
                if start_id or end_id:
                    if not is_in_range(key, start_id, end_id):
                        skipped_count += 1
                        continue
                
                original_text = value
                easy_read_key = f'easyread-{key}'
                
                logging.info(f"Processing {key}")
                
                # Find glossary words in this text
                found_glossary_words = find_glossary_words_in_text(original_text)
                
                # Transform the text, preserving glossary words
                easy_read_text = transform_to_easy_read(original_text)
                
                # Verify all glossary terms are preserved
                terms_preserved, missing_terms = verify_glossary_terms(original_text, easy_read_text, found_glossary_words)
                if terms_preserved:
                    success_count += 1
                    logging.info(f"Successfully processed {key} - All glossary terms preserved")
                else:
                    failure_count += 1
                    logging.warning(f"Issue with {key} - Missing terms: {', '.join(missing_terms)}")
                
                # Add the easy-read version to results
                if is_nested:
                    result["texts"][easy_read_key] = easy_read_text
                else:
                    result[easy_read_key] = easy_read_text
        
        # Write the updated translations to a new file (clean JSON only)
        with open('new_translations2_es.json', 'w', encoding='utf-8') as file:
            json.dump(result, file, ensure_ascii=False, indent=2)
            
        logging.info(f"Processed {success_count + failure_count} entries. Success: {success_count}, Issues: {failure_count}, Skipped: {skipped_count}")
        logging.info("Results saved to updated_translations_es.json")
        logging.info(f"Log file saved to {log_filename}")
        
    except Exception as error:
        logging.error(f'Error processing translations: {error}')

# Run the script
if __name__ == "__main__":
    logging.info("Starting Easy-Read generation process")
    process_translations()
    logging.info("Easy-Read generation process complete")