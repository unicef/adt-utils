#!/usr/bin/env python3
"""
Example usage script for text regeneration.
Shows how to use the regenerate_text.py script with different options.
"""

import os

def show_usage_examples():
    """Show example commands for text regeneration."""
    
    print("Text Regeneration Script - Usage Examples")
    print("=" * 50)
    
    print("\n📚 EASYREAD GENERATION:")
    print("# Generate easyread text for pages 0-5 in Spanish")
    print("python regenerate_text.py --start-page 0 --end-page 5 --language es --type easyread")
    
    print("\n# Generate easyread text for pages 10-15 in English")
    print("python regenerate_text.py --start-page 10 --end-page 15 --language en --type easyread")
    
    print("\n👶 ELI5 GENERATION:")
    print("# Generate ELI5 text for pages 0-5 in Spanish")
    print("python regenerate_text.py --start-page 0 --end-page 5 --language es --type eli5")
    
    print("\n# Generate ELI5 text for pages 10-15 in English")
    print("python regenerate_text.py --start-page 10 --end-page 15 --language en --type eli5")
    
    print("\n🌐 MULTIPLE OPTIONS:")
    print("# Generate both types for pages 0-10 in both languages")
    print("python regenerate_text.py --start-page 0 --end-page 10 --language both --type both")
    
    print("\n# Generate only Spanish content for pages 5-8")
    print("python regenerate_text.py --start-page 5 --end-page 8 --language es --type both")
    
    print("\n🔑 API KEY SETUP:")
    print("# Option 1: Set environment variable")
    print("export OPENAI_API_KEY='your-api-key-here'")
    
    print("\n# Option 2: Pass as argument")
    print("python regenerate_text.py --start-page 0 --end-page 5 --language es --type easyread --api-key 'your-key'")
    
    print("\n📁 INPUT/OUTPUT:")
    print("Input:  content/i18n/{language}/texts.json")
    print("Output: content/i18n/{language}/texts.json (updated)")
    print("Log:    text_regeneration.log")
    
    print("\n🔍 GENERATED KEY FORMATS:")
    print("Original:  text-6-1")
    print("EasyRead:  easyread-text-6-1")
    print("ELI5:      sectioneli5-6-1")
    
    print("\n⚡ PERFORMANCE:")
    print("- Uses gpt-4o-mini for cost-effective generation")
    print("- Concurrent processing (10 requests at a time)")
    print("- Automatic retry on failures")
    print("- Progress logging and summary reports")


if __name__ == "__main__":
    show_usage_examples()
