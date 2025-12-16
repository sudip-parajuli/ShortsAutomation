import os
import logging
import re
import yaml
from pathlib import Path
from src.generators.llm_providers import LLMManager
from src.generators.quote_cleaning import clean_quote

logger = logging.getLogger(__name__)

def load_settings():
    """Load settings from yaml file."""
    try:
        # Assuming run from root
        config_path = Path("config/settings.yaml")
        if not config_path.exists():
            # Try looking up one level if run from src/something
            config_path = Path("../config/settings.yaml")
        
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load settings: {e}")
    return {}

def generate_quote(topic="inspiration"):
    """
    Generate a single inspiring quote using the configured LLM provider fallback chain.
    """
    settings = load_settings()
    llm_manager = LLMManager(settings)
    
    prompt = (
        f"Generate a concise, inspiring quote about {topic}. "
        "Rules: 1) Max 25 words. 2) No author names. "
        "3) No quotation marks. 4) No extra explanation. "
        "5) Return only the quote text."
    )
    
    raw_text, provider_used = llm_manager.generate_with_fallback(prompt)
    
    if not raw_text:
        logger.error("All LLM providers failed to generate a quote.")
        return None
        
    logger.info(f"Quote generated using provider: {provider_used}")
    
    cleaned = clean_quote(raw_text)
    logger.info(f"Final processed quote: {cleaned}")
    return cleaned

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(generate_quote("resilience"))
