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
    
    # Show the voice and instructions configuration
    voice_en, instructions_en = regenerator.get_voice_and_instructions('en')
    voice_es, instructions_es = regenerator.get_voice_and_instructions('es')
    
    print("TTS Voice and Instructions Configuration")
    print("=" * 50)
    
    print("\n🇺🇸 ENGLISH:")
    print(f"Voice: {voice_en}")
    print(f"Instructions: {instructions_en}")
    
    print("\n🇸🇻 SPANISH (EL SALVADOR):")
    print(f"Voice: {voice_es}")
    print(f"Instructions: {instructions_es}")
    
    print("\n" + "=" * 50)
    print("Spanish Enhancement Features:")
    print("✅ El Salvador accent specification")
    print("✅ Regional pronunciation characteristics") 
    print("✅ Soft pronunciation guidance")
    print("✅ Authentic Central American intonation")
    print("✅ gpt-4o-mini-tts model for better quality")
    
    # Example of how text would be enhanced
    sample_text = "El autocuidado es fundamental para la salud mental."
    
    print(f"\nSample Text:")
    print(f"Text: {sample_text}")
    print(f"Voice: {voice_es}")
    print(f"Instructions: {instructions_es[:100]}...")

if __name__ == "__main__":
    demo_spanish_prompting()
