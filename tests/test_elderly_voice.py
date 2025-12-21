import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.generators import audio_gen

def test_elderly_samples():
    logging.basicConfig(level=logging.INFO)
    test_quote = "The only true wisdom is in knowing you know nothing. Take a deep breath and reflect."
    
    print("Generating elderly voice samples...")
    
    # Test with style="elderly"
    audio_path, boundaries, text = audio_gen.generate_voiceover(
        test_quote, 
        output_dir="assets/test_samples", 
        style="elderly"
    )
    
    if audio_path and os.path.exists(audio_path):
        print(f"✅ Success! Elderly sample generated at: {audio_path}")
        print(f"Sanitized text: {text}")
        print(f"Word boundaries captured: {len(boundaries)}")
    else:
        print("❌ Failed to generate elderly sample.")

if __name__ == "__main__":
    test_elderly_samples()
