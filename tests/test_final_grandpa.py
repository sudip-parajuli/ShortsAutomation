import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def generate_final_sample_sync(name, text, output_dir):
    filename = f"final_grandpa_{name}.mp3"
    filepath = os.path.join(output_dir, filename)
    
    from src.generators.audio_gen import generate_voiceover
    
    # generate_voiceover is a sync wrapper that uses asyncio.run() internally
    path, boundaries, text_out = generate_voiceover(text, output_dir=output_dir, style="elderly")
    if path:
        # Rename to the descriptive name
        new_path = os.path.join(output_dir, filename)
        if os.path.exists(path):
            if os.path.exists(new_path):
                os.remove(new_path)
            os.rename(path, new_path)
            print(f"Generated {name}: {new_path}")
    return path

def test_final_grandpa_sync():
    quotes = [
        ("LifeLessons", "Life, my dear, is not measured by the number of breaths we take, but by the moments that take our breath away."),
        ("QuietStrength", "True strength is not found in the roar of a lion, but in the quiet whisper of a heart that refuses to give up."),
        ("Patience", "Nature does not hurry, yet everything is accomplished. Remember that when you feel the world is moving too fast.")
    ]
    
    output_dir = "assets/final_grandpa_samples"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating {len(quotes)} final samples in {output_dir}...")
    for name, text in quotes:
        generate_final_sample_sync(name, text, output_dir)

if __name__ == "__main__":
    test_final_grandpa_sync()
