import os
import sys
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def generate_sample(name, voice, rate, pitch, text, output_dir):
    filename = f"v3_{name}_{voice}.mp3"
    filepath = os.path.join(output_dir, filename)
    
    from src.generators.audio_gen import _generate_voiceover_async, sanitize_for_tts
    
    sanitized_text = sanitize_for_tts(text)
    await _generate_voiceover_async(sanitized_text, filepath, voice, rate=rate, pitch=pitch)
    print(f"Generated {name}: {filepath} (Voice: {voice}, Rate: {rate}, Pitch: {pitch})")
    return filepath

async def test_v3():
    test_quote = "My dear child, success is not just about the destination. It is the courage to keep walking when the path gets dark. Take your time, and listen to your heart."
    output_dir = "assets/test_samples_v3"
    os.makedirs(output_dir, exist_ok=True)
    
    samples = [
        # Christopher is often "warmer/friendlier" than Guy
        ("WarmGrandpa_V1", "en-US-ChristopherNeural", "-25%", "-12Hz"),
        ("WarmGrandpa_V2", "en-US-ChristopherNeural", "-30%", "-10Hz"),
        
        # Guy is deep but needs more rate reduction for "grandpa" pace
        ("Storyteller_Guy_V1", "en-US-GuyNeural", "-25%", "-12Hz"),
        ("Storyteller_Guy_V2", "en-US-GuyNeural", "-30%", "-8Hz"),
        
        # Steffan is "Rational" but can sound mature
        ("MatureMentor_Steffan", "en-US-SteffanNeural", "-25%", "-10Hz")
    ]
    
    print(f"Generating {len(samples)} v3 variants in {output_dir}...")
    for name, voice, rate, pitch in samples:
        await generate_sample(name, voice, rate, pitch, test_quote, output_dir)

if __name__ == "__main__":
    asyncio.run(test_v3())
