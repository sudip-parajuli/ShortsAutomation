import logging
import yaml
from pathlib import Path
from src.generators.llm_providers import LLMManager

logger = logging.getLogger(__name__)

def load_settings():
    """Load settings from yaml file."""
    try:
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            config_path = Path("../config/settings.yaml")
        
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
    return {}

def generate_long_form_script(topic="success"):
    """
    Generates a long-form motivational script:
    1. A powerful quote.
    2. A detailed explanation (approx 300-400 words).
    """
    settings = load_settings()
    llm_manager = LLMManager(settings)
    
    prompt = f"""
Generate a motivational video script about {topic}.
The script must have two parts:
1. QUOTE: A powerful, concise motivational quote (max 25 words).
2. EXPLANATION: A deep, meaningful explanation of the quote and how to apply it in life. 
   Pacing should be calm and wise, like an elderly mentor.
   Length: Approximately 300-400 words.
   Format:
   [QUOTE]
   (The quote text here)
   
   [EXPLANATION]
   (The detailed explanation paragraphs here)
   
Rules:
- Do not include any other text, labels, or metadata except [QUOTE] and [EXPLANATION].
- Ensure the tone is inspiring and consistent.
- No quotation marks around the quote.
"""

    max_retries = 3
    attempt = 0
    
    while attempt < max_retries:
        raw_text, provider_used = llm_manager.generate_with_fallback(prompt)
        
        if not raw_text:
            logger.error(f"LLM failed on attempt {attempt+1}")
            attempt += 1
            continue
            
        # Parse the response
        try:
            quote_part = ""
            explanation_part = ""
            
            if "[QUOTE]" in raw_text and "[EXPLANATION]" in raw_text:
                parts = raw_text.split("[EXPLANATION]")
                quote_part = parts[0].replace("[QUOTE]", "").strip()
                explanation_part = parts[1].strip()
            
            if quote_part and explanation_part:
                logger.info(f"Long-form script generated using {provider_used}")
                return {
                    "quote": quote_part,
                    "explanation": explanation_part,
                    "full_text": f"{quote_part}\n\n{explanation_part}"
                }
            else:
                logger.warning(f"Failed to parse LLM response correctly. Attempt {attempt+1}")
                attempt += 1
        except Exception as e:
            logger.error(f"Error parsing long-form script: {e}")
            attempt += 1

    return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    script = generate_long_form_script("discipline")
    if script:
        print("--- QUOTE ---")
        print(script['quote'])
        print("\n--- EXPLANATION ---")
        print(script['explanation'])
