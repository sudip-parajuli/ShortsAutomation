import re

# ---------------- CLEANING PIPELINE ---------------- #
def clean_quote(raw_text):
    """Clean the raw text from LLM to get just the quote."""
    if not raw_text:
        return None
        
    # 0. Strip leading/trailing whitespace
    raw_text = raw_text.strip()
    
    # 1. Remove "Sure", "Certainly", "Here is" conversational filler
    raw_text = re.sub(r"^(sure|certainly|okay|ok|actually|of course)[!.,]?\s*", "", raw_text, flags=re.IGNORECASE)
    
    # Remove "Here is a quote..." patterns up to a colon
    if ":" in raw_text:
        raw_text = raw_text.split(":", 1)[1].strip()
    
    # 2. Remove common preambles if they remain
    preambles = ["here is", "here's", "this quote", "consider this", "remember", "think about", "reflect on"]
    lowered = raw_text.lower()
    for p in preambles:
        if lowered.startswith(p):
            raw_text = re.sub(f"^{p}.*?[:\\-]", "", raw_text, flags=re.IGNORECASE).strip()
            
    # 2b. Remove "Quote:" label
    raw_text = re.sub(r"^quote:\s*", "", raw_text, flags=re.IGNORECASE)

    # 3. Remove quotation marks
    cleaned = raw_text.replace('"', '').replace("'", "")
    
    # 4. Remove author attributions
    cleaned = re.sub(r"\s*[-—]\s*[A-Z].*$", "", cleaned)
    cleaned = re.sub(r"\s+by\s+[A-Z].*$", "", cleaned, flags=re.IGNORECASE)

    # 5. Force single sentence (Take first sentence)
    match = re.match(r"(.*?[.!?])", cleaned)
    if match:
        cleaned = match.group(1)

    # 6. Hard word limit
    words = cleaned.split()
    cleaned = " ".join(words[:25]).strip()

    # 7. TTS-safe: remove ellipses
    cleaned = cleaned.replace("...", "")
    
    return cleaned

generated_quote_cleaner = clean_quote # Export for testing if needed
