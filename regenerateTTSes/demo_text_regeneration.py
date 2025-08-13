#!/usr/bin/env python3
"""
Demo script showing how to use the text regeneration features.
This script demonstrates the easyread and eli5 text generation capabilities.
"""

from regenerate_text import TextRegenerator

def demo_text_regeneration():
    """Demonstrate the text regeneration prompts and configuration."""
    
    # Create a regenerator instance (dummy key for demo)
    regenerator = TextRegenerator("dummy-key")
    
    print("Text Regeneration Prompts Configuration")
    print("=" * 60)
    
    # Sample original text
    sample_text = ("El autocuidado es una práctica fundamental que implica "
                  "la adopción consciente de hábitos y comportamientos que "
                  "promueven el bienestar físico, mental y emocional.")
    
    print(f"\nOriginal Text:")
    print(f'"{sample_text}"')
    
    # Show EasyRead prompts
    print(f"\n🔍 EASYREAD CONVERSION:")
    print(f"Spanish System Prompt:")
    system_es_easy = regenerator.get_system_prompt('easyread', 'es')
    print(f'"{system_es_easy[:100]}..."')
    
    user_es_easy = regenerator.get_user_prompt(sample_text, 'easyread', 'es')
    print(f"\nSpanish User Prompt:")
    print(f'"{user_es_easy[:150]}..."')
    
    # Show ELI5 prompts
    print(f"\n👶 ELI5 CONVERSION:")
    system_es_eli5 = regenerator.get_system_prompt('eli5', 'es')
    print(f"Spanish System Prompt:")
    print(f'"{system_es_eli5[:100]}..."')
    
    user_es_eli5 = regenerator.get_user_prompt(sample_text, 'eli5', 'es')
    print(f"\nSpanish User Prompt:")
    print(f'"{user_es_eli5[:150]}..."')
    
    # Show English versions
    print(f"\n🇺🇸 ENGLISH VERSIONS:")
    system_en_easy = regenerator.get_system_prompt('easyread', 'en')
    print(f"EasyRead System Prompt:")
    print(f'"{system_en_easy[:100]}..."')
    
    system_en_eli5 = regenerator.get_system_prompt('eli5', 'en')
    print(f"\nELI5 System Prompt:")
    print(f'"{system_en_eli5[:100]}..."')
    
    print("\n" + "=" * 60)
    print("Key Generation Features:")
    print("✅ Converts text- keys to easyread-text- keys")
    print("✅ Converts text- keys to sectioneli5- keys")
    print("✅ El Salvador Spanish context for Spanish content")
    print("✅ Age-appropriate simplification for ELI5")
    print("✅ Accessibility-focused for EasyRead")
    print("✅ gpt-4o-mini model for cost-effective generation")


if __name__ == "__main__":
    demo_text_regeneration()
