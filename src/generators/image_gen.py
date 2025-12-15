import requests
import base64
import os
import logging
from datetime import datetime
import urllib.parse

logger = logging.getLogger(__name__)

def generate_pollinations(prompt, output_dir="assets/temp", width=768, height=1024):
    """
    Generates image using Pollinations.ai (Free, no API key required).
    """
    try:
        logger.info(f"Generating image with Pollinations.ai: {prompt}")
        
        # Enhanced prompt with STRONG anti-text instructions
        enhanced_prompt = (
            f"{prompt}, abstract background, cinematic lighting, high quality, 8k, "
            "inspirational atmosphere, vertical composition, clean image, "
            "NO TEXT, NO LETTERS, NO WORDS, NO WRITING, NO TYPOGRAPHY, "
            "NO WATERMARK, NO LOGO, plain background"
        )
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        
        # Pollinations.ai API - nologo=true, removed enhance to prevent text addition
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bg_pollinations_{timestamp}.png"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        logger.info(f"✅ Pollinations.ai image saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.warning(f"Pollinations.ai failed: {e}")
        return None

def generate_huggingface(prompt, output_dir="assets/temp", api_key=None, width=768, height=1024):
    """
    Generates image using Hugging Face Inference API (requires API key).
    """
    if not api_key:
        logger.debug("Hugging Face API key not provided, skipping")
        return None
    
    try:
        logger.info(f"Generating image with Hugging Face: {prompt}")
        
        API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
        headers = {"Authorization": f"Bearer {api_key}"}
        
        # Enhanced prompt with strong anti-text instructions
        enhanced_prompt = (
            f"{prompt}, abstract background, high quality, detailed, "
            "inspirational atmosphere, vertical 9:16, clean image, "
            "NO TEXT, NO LETTERS, NO WORDS, NO WRITING, NO TYPOGRAPHY, plain background"
        )
        
        # Strong negative prompt to prevent text
        negative_prompt = (
            "text, letters, words, writing, typography, watermark, logo, signature, "
            "caption, title, subtitle, label, sign, banner, poster, advertisement, "
            "numbers, symbols, characters, font, calligraphy"
        )
        
        payload = {
            "inputs": enhanced_prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": 25,  # Increased for better quality
                "guidance_scale": 8.5  # Higher guidance for better prompt following
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bg_huggingface_{timestamp}.png"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        logger.info(f"✅ Hugging Face image saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.warning(f"Hugging Face failed: {e}")
        return None

def generate_stable_diffusion(prompt, output_dir="assets/temp", api_url="http://127.0.0.1:7860", width=768, height=1024):
    """
    Generates image using local Stable Diffusion WebUI API (requires GPU).
    """
    try:
        logger.info(f"Generating image with local Stable Diffusion: {prompt}")
        
        payload = {
            "prompt": f"{prompt}, (masterpiece, best quality:1.2), minimal, centered composition, soft lighting, inspirational background, vertical, 9:16 aspect ratio, no text, no people",
            "negative_prompt": "(text:1.3), watermark, ugly, low quality, pixelated, blurry, human, face, people, complex, busy",
            "steps": 20,
            "width": width,
            "height": height,
            "cfg_scale": 7,
            "sampler_name": "Euler a",
            "batch_size": 1
        }
        
        response = requests.post(f"{api_url}/sdapi/v1/txt2img", json=payload, timeout=60)
        response.raise_for_status()
        
        r = response.json()
        if 'images' in r:
            image_data = base64.b64decode(r['images'][0])
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bg_sd_{timestamp}.png"
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(image_data)
                
            logger.info(f"✅ Stable Diffusion image saved to {filepath}")
            return filepath
        else:
            logger.error("No images returned from SD API")
            return None
            
    except Exception as e:
        logger.warning(f"Local Stable Diffusion failed: {e}")
        return None

def generate_background(prompt, output_dir="assets/temp", config=None, width=768, height=1024):
    """
    Generates a background image using cascading fallback system:
    1. Pollinations.ai (Free, no API key) - PRIMARY
    2. Hugging Face (Optional API key) - SECONDARY
    3. Local Stable Diffusion (Requires GPU) - TERTIARY
    4. Gradient fallback - LAST RESORT
    """
    logger.info(f"Starting image generation for prompt: {prompt}")
    
    # Extract config if provided
    huggingface_api_key = None
    sd_url = "http://127.0.0.1:7860"
    use_pollinations = True
    
    if config:
        image_config = config.get('image_generation', {})
        use_pollinations = image_config.get('use_pollinations', True)
        huggingface_api_key = image_config.get('huggingface_api_key', '')
        sd_url = image_config.get('stable_diffusion_url', sd_url)
        width = image_config.get('width', width)
        height = image_config.get('height', height)
    
    # Try methods in order
    result = None
    
    # 1. Try Pollinations.ai (Primary - Free, no API key)
    if use_pollinations:
        result = generate_pollinations(prompt, output_dir, width, height)
        if result:
            return result
    
    # 2. Try Hugging Face (Secondary - Optional API key)
    if huggingface_api_key:
        result = generate_huggingface(prompt, output_dir, huggingface_api_key, width, height)
        if result:
            return result
    
    # 3. Try Local Stable Diffusion (Tertiary - Requires GPU)
    result = generate_stable_diffusion(prompt, output_dir, sd_url, width, height)
    if result:
        return result
    
    # 4. Final fallback - Gradient
    logger.warning("All AI image generation methods failed. Using gradient fallback.")
    return generate_placeholder(prompt, output_dir=output_dir, width=width, height=height)

def generate_placeholder(prompt, output_dir="assets/temp", width=768, height=1024):
    """Generates a simple gradient background using Pillow."""
    try:
        from PIL import Image, ImageDraw
        import colorsys
        import random
        
        logger.info("Generating fallback gradient image...")
        
        # Random hue
        h1 = random.random()
        h2 = (h1 + 0.5) % 1.0
        c1 = tuple(int(c*255) for c in colorsys.hsv_to_rgb(h1, 0.6, 0.4)) # Darker
        c2 = tuple(int(c*255) for c in colorsys.hsv_to_rgb(h2, 0.6, 0.6))
        
        base = Image.new('RGB', (width, height), c1)
        top = Image.new('RGB', (width, height), c2)
        mask = Image.new('L', (width, height))
        mask_data = []
        for y in range(height):
            mask_data.extend([int(255 * (y / height))] * width)
        mask.putdata(mask_data)
        
        final_img = Image.composite(top, base, mask)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bg_fallback_{timestamp}.png"
        filepath = os.path.join(output_dir, filename)
        
        final_img.save(filepath)
        logger.info(f"Fallback image saved to {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to generate fallback image: {e}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test
    generate_background("serene mountain landscape at sunset")
