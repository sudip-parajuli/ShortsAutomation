import os
import requests
import logging
import re
import random
import google.generativeai as genai

logger = logging.getLogger(__name__)

def generate_quote_gemini(topic, api_key):
    """Generate quote using Google Gemini API."""
    try:
        genai.configure(api_key=api_key)
        
        logger.info("Starting Gemini generation (v2 - Flash/Pro/1.0)")
        
        # DEBUG: List available models
        try:
            logger.info("Available Gemini Models:")
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    logger.info(f" - {m.name}")
        except Exception as e:
            logger.warning(f"Could not list models: {e}")
        
        # Try models in order of preference (newer/faster first)
        # Updated based on available models in environment (Dec 2025)
        models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-1.5-flash', # Keep as fallback just in case
        ]
        
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(model_name)
                
                prompt = (
                    f"Generate a concise, inspiring quote about {topic}. "
                    "Rules: 1) Max 25 words. 2) No author names. "
                    "3) No quotation marks. 4) No extra explanation. "
                    "5) Return only the quote text."
                )
                
                response = model.generate_content(prompt)
                text = response.text.strip()
                logger.info(f"Gemini ({model_name}) response: {text}")
                return text
            except Exception as e:
                logger.warning(f"Gemini model {model_name} failed: {e}")
                continue
                
        return None
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        return None

def generate_quote(topic="inspiration", api_url="http://localhost:11434/api/generate", model="mistral"):
    """
    Generate a single inspiring quote:
    - Single sentence
    - Max 25 words
    - No author, preamble, or explanation
    """
    
    # Check for Gemini API Key first
    gemini_key = os.environ.get("GEMINI_API_KEY")
    raw_text = None
    
    if gemini_key:
        logger.info(f"Using Gemini API for quote generation (Topic: {topic})")
        raw_text = generate_quote_gemini(topic, gemini_key)
    
    # Fallback to Ollama if no Gemini key or Gemini failed
    if not raw_text:
        salt = random.randint(1, 100000)
        prompt = (
            f"Generate a concise, inspiring quote about {topic}. "
            "Rules: 1) Max 25 words. 2) No author names. "
            "3) No quotation marks. 4) No extra explanation. "
            "5) Return only the quote."
        )

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 1.0,
                "num_predict": 60,
                "seed": salt,
                "stop": ["\n", "—", "-", "Author:", "Explanation:"]
            }
        }

        try:
            logger.info(f"Requesting quote from Ollama (Topic: {topic})")
            response = requests.post(api_url, json=payload, timeout=120)
            response.raise_for_status()
            raw_text = response.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return None

    if not raw_text:
        logger.error("Empty response from primary and backup generators")
        return None

    # ---------------- CLEANING PIPELINE ---------------- #
    # 0. Strip leading/trailing whitespace
    raw_text = raw_text.strip()
    
    # 1. Remove "Sure", "Certainly", "Here is" conversational filler
    # Regex explains:
    # ^(sure|certainly|okay|ok|here is|here's|this quote|consider this).*?[:\-]
    # Matches start of string, common filler words, optional content, until a colon or hyphen
    
    # Remove "Sure, ..." or "Certainly!" patterns at start
    raw_text = re.sub(r"^(sure|certainly|okay|ok|actually|of course)[!.,]?\s*", "", raw_text, flags=re.IGNORECASE)
    
    # Remove "Here is a quote..." patterns up to a colon
    if ":" in raw_text:
        raw_text = raw_text.split(":", 1)[1].strip()
    
    # 2. Remove common preambles if they remain (e.g. "Think about this")
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

    # 5. Force single sentence
    # Split by . ! ? but keep the punctuation? No, remove it for TTS usually, or keep first.
    # If we split by [.!?], we lose the punctuation.
    # Let's simple take the first sentence.
    match = re.match(r"(.*?[.!?])", cleaned)
    if match:
        cleaned = match.group(1)
    else:
        # No punctuation found, just take it all (it was likely short)
        pass

    # 6. Hard word limit
    words = cleaned.split()
    cleaned = " ".join(words[:25]).strip()

    # 7. TTS-safe: remove ellipses and add natural pauses
    cleaned = cleaned.replace("...", "")  # remove any literal ellipses

    logger.info(f"Generated quote: {cleaned}")
    return cleaned

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(generate_quote("resilience"))
