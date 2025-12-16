import os
import requests
import logging
import time
import random
import google.generativeai as genai
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text based on the prompt. Returns None on failure."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the provider."""
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, config):
        self._config = config
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found in environment variables.")

    @property
    def name(self):
        return "gemini"

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            return None
            
        try:
            genai.configure(api_key=self.api_key)
            
            # List of models to try in order
            models_to_try = [
                self._config.get('model', 'gemini-2.0-flash'),
                'gemini-2.0-flash',
                'gemini-1.5-flash',
                'gemini-pro'
            ]
            
            # Deduplicate while preserving order
            models_to_try = list(dict.fromkeys(models_to_try))

            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    text = response.text.strip()
                    logger.info(f"Gemini ({model_name}) success.")
                    return text
                except Exception as e:
                    logger.warning(f"Gemini model {model_name} failed: {e}")
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Gemini provider failed: {e}")
            return None

class GroqProvider(LLMProvider):
    def __init__(self, config):
        self._config = config
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.base_url = config.get("base_url", "https://api.groq.com/openai/v1")
        self.model = config.get("model", "llama3-8b-8192")
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables.")

    @property
    def name(self):
        return "groq"

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 100
        }

        try:
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Groq API error {resp.status_code}: {resp.text}")
                return None
                
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq provider failed: {e}")
            return None

class HuggingFaceProvider(LLMProvider):
    def __init__(self, config):
        self._config = config
        self.api_key = os.environ.get("HUGGINGFACE_API_KEY") or config.get("huggingface_api_key")
        self.base_url = config.get("base_url", "https://api-inference.huggingface.co/models")
        self.model = config.get("model", "mistralai/Mistral-7B-Instruct-v0.2")

        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not found.")

    @property
    def name(self):
        return "huggingface"

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            return None
            
        api_url = f"{self.base_url}/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # HF Inference API expects simple inputs for text-generation
        # Depending on model, sometimes we need to format prompt as instruction
        formatted_prompt = f"[INST] {prompt} [/INST]"
        
        payload = {
            "inputs": formatted_prompt,
            "parameters": {
                "max_new_tokens": 100,
                "return_full_text": False,
                "temperature": 0.7
            }
        }

        try:
            resp = requests.post(api_url, headers=headers, json=payload, timeout=20)
            if resp.status_code != 200:
                logger.warning(f"HuggingFace API error {resp.status_code}: {resp.text}")
                return None
                
            # Response is usually a list of dicts: [{'generated_text': '...'}]
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0].get("generated_text", "").strip()
            return None
        except Exception as e:
            logger.error(f"HuggingFace provider failed: {e}")
            return None

class OllamaProvider(LLMProvider):
    def __init__(self, config):
        self._config = config
        self.base_url = config.get("base_url", "http://localhost:11434/api/generate")
        self.model = config.get("model", "phi3")

    @property
    def name(self):
        return "ollama"

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 1.0,
                "num_predict": 60,
                "stop": ["\n", "—", "-", "Author:", "Explanation:"]
            }
        }
        
        try:
            resp = requests.post(self.base_url, json=payload, timeout=120)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama provider failed: {e}")
            return None

class LLMManager:
    def __init__(self, settings):
        self.settings = settings
        self.providers = {}
        self._init_providers()

    def _init_providers(self):
        llm_conf = self.settings.get("llm_providers", {})
        
        # Instantiate available providers
        self.providers["gemini"] = GeminiProvider(llm_conf.get("gemini", {}))
        self.providers["groq"] = GroqProvider(llm_conf.get("groq", {}))
        self.providers["huggingface"] = HuggingFaceProvider(llm_conf.get("huggingface", {}))
        self.providers["ollama"] = OllamaProvider(llm_conf.get("ollama", {}))
        
        # Load order
        self.provider_order = llm_conf.get("provider_order", ["gemini", "groq", "huggingface", "ollama"])

    def generate_with_fallback(self, prompt: str) -> tuple[str, str]:
        """
        Try generating text using providers in the configured order.
        Returns (generated_text, provider_name_used) or (None, None).
        """
        for provider_name in self.provider_order:
            provider = self.providers.get(provider_name)
            if not provider:
                continue
                
            logger.info(f"Attempting generation with provider: {provider_name}")
            result = provider.generate(prompt)
            
            if result and len(result.strip()) > 5: # Basic valid check
                return result, provider_name
            else:
                logger.warning(f"Provider {provider_name} returned empty or invalid result.")
        
        return None, None
