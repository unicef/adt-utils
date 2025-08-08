#!/usr/bin/env python3
"""
Example usage of the TTS regeneration script.
This script demonstrates different usage patterns.
"""

import asyncio
import os
from regenerate_tts import TTSRegenerator

async def example_usage():
    """Example of how to use TTSRegenerator programmatically."""
    
    # Get API key (you should set this in your environment)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create regenerator instance
    async with TTSRegenerator(api_key) as regenerator:
        
        # Example 1: Regenerate English pages 0-2
        print("Example 1: Regenerating English pages 0-2")
        results = await regenerator.regenerate(
            start_page=0, 
            end_page=2, 
            languages=['en']
        )
        print(f"Results: {results}")
        
        # Example 2: Regenerate Spanish pages 0-2  
        print("\nExample 2: Regenerating Spanish pages 0-2")
        results = await regenerator.regenerate(
            start_page=0, 
            end_page=2, 
            languages=['es']
        )
        print(f"Results: {results}")
        
        # Example 3: Regenerate both languages for pages 0-1
        print("\nExample 3: Regenerating both languages for pages 0-1")
        results = await regenerator.regenerate(
            start_page=0, 
            end_page=1, 
            languages=['en', 'es']
        )
        print(f"Results: {results}")

if __name__ == "__main__":
    asyncio.run(example_usage())
