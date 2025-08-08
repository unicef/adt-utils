#!/usr/bin/env python3
"""
Demo script showing Spanish El Salvador accent prompting features.
This script demonstrates how the Spanish TTS is enhanced for El Salvador pronunciation.
"""

from regenerate_tts import TTSRegenerator

def demo_spanish_prompting():
    """Demonstrate the Spanish accent prompting."""
    
    # Create a regenerator instance (dummy key for demo)
    regenerator = TTSRegenerator("dummy-key")
    
    # Show the voice and prompt configuration
    voice_en, prompt_en = regenerator.get_voice_and_prompt('en')
    voice_es, prompt_es = regenerator.get_voice_and_prompt('es')
    
    print("TTS Voice and Prompt Configuration")
    print("=" * 50)
    
    print("\n🇺🇸 ENGLISH:")
    print(f"Voice: {voice_en}")
    print(f"Prompt: {prompt_en}")
    
    print("\n🇸🇻 SPANISH (EL SALVADOR):")
    print(f"Voice: {voice_es}")
    print(f"Prompt: {prompt_es}")
    
    print("\n" + "=" * 50)
    print("Spanish Enhancement Features:")
    print("✅ El Salvador accent specification")
    print("✅ Regional pronunciation characteristics") 
    print("✅ Soft pronunciation guidance")
    print("✅ Authentic Central American intonation")
    
    # Example of how text would be enhanced
    sample_text = "El autocuidado es fundamental para la salud mental."
    enhanced_text = f"{prompt_es}{sample_text}"
    
    print(f"\nSample Enhancement:")
    print(f"Original: {sample_text}")
    print(f"Enhanced: {enhanced_text[:100]}...")

if __name__ == "__main__":
    demo_spanish_prompting()
