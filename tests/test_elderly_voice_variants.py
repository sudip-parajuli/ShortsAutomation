import os
import sys
import asyncio
import logging
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.generators import audio_gen

async def generate_sample(name, voice, rate, pitch, text, output_dir):
    filename = f"sample_{name}_{datetime.now().strftime('%H%M%S')}.mp3"
    filepath = os.path.join(output_dir, filename)
    
    # We use the internal async function to test specific params
    from src.generators.audio_gen import _generate_voiceover_async, sanitize_for_tts
    
    sanitized_text = sanitize_for_tts(text)
    await _generate_voiceover_async(sanitized_text, filepath, voice, rate=rate, pitch=pitch)
    print(f"Generated {name}: {filepath} (Voice: {voice}, Rate: {rate}, Pitch: {pitch})")
    return filepath

async def test_variants():
    test_quote = "Success is not final, failure is not fatal. It is the courage to continue that counts. Wisdom comes from experience."
    output_dir = "assets/test_samples_v2"
    os.makedirs(output_dir, exist_ok=True)
    
    samples = [
        ("deep_baritone", "en-US-GuyNeural", "-15%", "-15Hz"),
        ("weathered_calm", "en-US-GuyNeural", "-25%", "-8Hz"),
        ("wise_rational", "en-US-SteffanNeural", "-20%", "-12Hz"),
        ("balanced_charming", "en-US-GuyNeural", "-20%", "-10Hz")
    ]
    
    print(f"Generating {len(samples)} variants in {output_dir}...")
    for name, voice, rate, pitch in samples:
        await generate_sample(name, voice, rate, pitch, test_quote, output_dir)

if __name__ == "__main__":
    asyncio.run(test_variants())
