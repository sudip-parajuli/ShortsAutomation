import os
import sys
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.generators import quote_gen

def test_quote_filter():
    logging.basicConfig(level=logging.INFO)
    print("Testing quote word count filter...")
    
    # We'll try to generate a few quotes and check their length
    for i in range(5):
        quote = quote_gen.generate_quote(topic="success")
        if quote:
            word_count = len(quote.split())
            print(f"Sample {i+1}: {quote} ({word_count} words)")
            if word_count < 5:
                print(f"❌ ERROR: Quote too short! ({word_count} words)")
            else:
                print(f"✅ PASS: Quote is long enough.")
        else:
            print(f"Sample {i+1}: Failed to generate.")

if __name__ == "__main__":
    test_quote_filter()
