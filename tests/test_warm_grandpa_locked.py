import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

def generate_warm_grandpa_samples():
    from src.generators.audio_gen import generate_voiceover
    
    quotes = [
        "A house is made of bricks and beams, but a home is made of love and dreams.",
        "The best time to plant a tree was twenty years ago. The second best time is now.",
        "Listen to the wind, it speaks. Listen to the silence, it whispers. Listen to your heart, it knows."
    ]
    
    output_dir = "assets/warm_grandpa_final_batch"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating samples for WarmGrandpa (Christopher) in {output_dir}...")
    for i, quote in enumerate(quotes):
        filename = f"warm_grandpa_{i+1}.mp3"
        path, boundaries, text = generate_voiceover(quote, output_dir=output_dir, style="elderly")
        if path:
            final_path = os.path.join(output_dir, filename)
            if os.path.exists(final_path): os.remove(final_path)
            os.rename(path, final_path)
            print(f"Generated: {final_path}")

if __name__ == "__main__":
    generate_warm_grandpa_samples()
