import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.generators.quote_gen import generate_quote

def test_generation():
    print("Testing LLM generation resilience...")
    quote = generate_quote("resilient future")
    if quote:
        print(f"\nSUCCESS: Generated Quote: \n{quote}")
    else:
        print("\nFAILURE: Could not generate quote from any provider.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_generation()
