#!/usr/bin/env python3
"""
Setup script for TTS regeneration environment.
"""

import os
import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Successfully installed requirements")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def check_api_key():
    """Check if OpenAI API key is set."""
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("✅ OpenAI API key found in environment")
        return True
    else:
        print("⚠️  OpenAI API key not found in environment")
        print("   Set it with: export OPENAI_API_KEY='your-api-key-here'")
        print("   Or provide it with the --api-key argument when running the script")
        return False

def check_directories():
    """Check if required directories exist."""
    output_dir = Path("output/content/i18n")
    
    required_dirs = [
        output_dir / "en",
        output_dir / "es",
        output_dir / "en" / "audio",
        output_dir / "es" / "audio"
    ]
    
    required_files = [
        output_dir / "en" / "texts.json",
        output_dir / "es" / "texts.json"
    ]
    
    all_good = True
    
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            all_good = False
    
    for file_path in required_files:
        if file_path.exists():
            print(f"✅ File exists: {file_path}")
        else:
            print(f"❌ File missing: {file_path}")
            all_good = False
    
    return all_good

def main():
    """Main setup function."""
    print("TTS Regeneration Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        return 1
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install requirements
    if not install_requirements():
        return 1
    
    # Check API key
    check_api_key()
    
    # Check directories
    if not check_directories():
        print("\n⚠️  Some required directories or files are missing.")
        print("   Make sure you're running this from the correct directory")
        print("   and that the output structure exists.")
    
    print("\n" + "=" * 50)
    print("Setup complete! You can now run:")
    print("python regenerate_tts.py --start-page 0 --end-page 5 --language en")
    print("python regenerate_tts.py --start-page 0 --end-page 5 --language es")
    print("python regenerate_tts.py --start-page 0 --end-page 5 --language both")

if __name__ == "__main__":
    sys.exit(main())
