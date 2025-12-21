import os
import sys
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.generators import quote_gen

def test_quote_filter_mock():
    print("Testing quote filter with Mock LLM...")
    
    # Mock LLMManager
    mock_llm = MagicMock()
    # Configure it to return a short quote twice, then a long one
    mock_llm.generate_with_fallback.side_effect = [
        ("Too short", "mock"),
        ("Tiny", "mock"),
        ("This is a long enough quote for testing", "mock")
    ]
    
    # We need to patch LLMManager inside quote_gen
    from src.generators.quote_gen import LLMManager
    quote_gen.LLMManager = lambda settings: mock_llm
    
    quote = quote_gen.generate_quote(topic="success")
    
    if quote:
        word_count = len(quote.split())
        print(f"Final Quote: {quote} ({word_count} words)")
        if word_count >= 5:
            print("✅ Mock Test PASS: Filter worked and retried.")
        else:
            print(f"❌ Mock Test FAIL: Got short quote: {quote}")
    else:
        print("❌ Mock Test FAIL: No quote returned.")

if __name__ == "__main__":
    test_quote_filter_mock()
