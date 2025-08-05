import os
from pathlib import Path

def get_base_paths():
    """
    Determine base paths based on environment or relative location
    
    Returns:
        dict: Dictionary containing base_dir, json_dir, and config_file paths
    """
    # Check if running in Docker
    if os.getenv('DOCKER_ENV'):
        # Docker environment - use environment variables
        base_dir = os.getenv('ADT_OUTPUT_DIR', '/workspace/target-folder')
        json_dir = os.getenv('ADT_JSON_DIR', '/workspace/target-folder/content/i18n/')
        config_file = os.getenv('ADT_CONFIG_FILE', '/app/heading_templates.json')
    else:
        # Local development - relative paths
        current_dir = Path(__file__).parent
        
        # Default paths (current behavior)
        base_dir = str(current_dir / 'output')  # ./output
        json_dir = str(current_dir / 'output' / 'content' / 'i18n')  # ./output/content/i18n/
        
        # Allow override via environment variables even in local mode
        base_dir = os.getenv('ADT_OUTPUT_DIR', base_dir)
        json_dir = os.getenv('ADT_JSON_DIR', json_dir)
        
        # Config file always in script directory
        config_file = str(current_dir / "heading_templates.json")
    
    return {
        'base_dir': base_dir,
        'json_dir': json_dir,
        'config_file': config_file
    }

def get_output_dir():
    """Get the output directory path"""
    return PATHS['base_dir']

def get_json_dir():
    """Get the JSON directory path"""
    return PATHS['json_dir']

def get_config_file():
    """Get the config file path"""
    return PATHS['config_file']

def set_custom_paths(base_dir=None, json_dir=None):
    """
    Override default paths with custom ones
    
    Args:
        base_dir (str): Custom base directory
        json_dir (str): Custom JSON directory
    """
    if base_dir:
        PATHS['base_dir'] = base_dir
    if json_dir:
        PATHS['json_dir'] = json_dir
    elif base_dir:
        # If only base_dir is provided, update json_dir accordingly
        PATHS['json_dir'] = os.path.join(base_dir, 'content', 'i18n')

# Initialize global configuration
PATHS = get_base_paths()

# Convenience exports
BASE_DIR = PATHS['base_dir']
JSON_DIR = PATHS['json_dir']
CONFIG_FILE = PATHS['config_file']
