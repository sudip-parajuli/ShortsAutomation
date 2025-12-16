import sys
import os
import argparse
import yaml
import random
import logging
import shutil

# Add src to path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import time
import requests

from src.generators import quote_gen, image_gen, audio_gen
from src.video import composer
from src.upload import youtube_api, drive_api
from src.utils import music_loader

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Main")

TOPICS = [
    "success", "discipline", "mindset", "hustle", "courage", 
    "fitness", "wisdom", "stoicism", "leadership", "focus",
    "ambition", "patience", "resilience", "gratitude", "strength",
    "learning", "growth", "purpose", "action", "confidence"
]

def check_service(url, name, retries=3, delay=5):
    """Simple health check for external services."""
    for i in range(retries):
        try:
            requests.get(url, timeout=5)
            logger.info(f"Service {name} is online.")
            return True
        except Exception:
            logger.warning(f"Service {name} not reachable (Attempt {i+1}/{retries}).")
            time.sleep(delay)
    return False

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def cleanup(files):
    for f in files:
        if f and os.path.exists(f):
            try:
                os.remove(f)
                logger.info(f"Deleted temp file: {f}")
            except Exception as e:
                logger.warning(f"Failed to delete {f}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Automated YouTube Shorts Generator")
    parser.add_argument("--dry-run", action="store_true", help="Generate video but do NOT upload")
    parser.add_argument("--topic", type=str, help="Specific topic for quote")
    parser.add_argument("--keep-temps", action="store_true", help="Do not delete temporary assets")
    args = parser.parse_args()

    config = load_config()
    
    # 0. Pre-flight Checks
    import subprocess
    
    services_ok = True
    
    # Check Ollama
    # Check LLM Service (Ollama or Gemini)
    ollama_ok = check_service(config['ollama']['base_url'], "Ollama", retries=2, delay=2)
    gemini_key_present = "GEMINI_API_KEY" in os.environ

    if not ollama_ok:
        if gemini_key_present:
            logger.info("Ollama not reachable, but GEMINI_API_KEY found. Using Gemini Cloud LLM.")
        else:
            logger.warning("Ollama not reachable and GEMINI_API_KEY not set. Attempting to start Ollama...")
            # Try to find executable in common paths
            ollama_paths = [
                "ollama", # PATH
                os.path.expanduser("~/AppData/Local/Programs/Ollama/ollama.exe"),
                "C:/Program Files/Ollama/ollama.exe"
            ]
            
            started = False
            for cmd in ollama_paths:
                try:
                    subprocess.Popen([cmd, "serve"], shell=True)
                    logger.info(f"Attempted start using: {cmd}")
                    time.sleep(5)
                    if check_service(config['ollama']['base_url'], "Ollama", retries=3, delay=2):
                        started = True
                        break
                except Exception:
                    continue
            
            if not started:
                 logger.error("CRITICAL: Ollama is not running and GEMINI_API_KEY is missing.")
                 logger.error("Please install Ollama OR set GEMINI_API_KEY environment variable.")
                 services_ok = False
    
    # Check SD (Optional - we have cloud alternatives now)
    sd_url = config.get('image_generation', {}).get('stable_diffusion_url', 'http://127.0.0.1:7860')
    if not check_service(sd_url, "Stable Diffusion", retries=1):
         logger.info("Local Stable Diffusion not running. Will use cloud-based image generation (Pollinations.ai).")
         # services_ok = False # Do NOT fail, we have cloud alternatives

    # Check FFmpeg
    ffmpeg_cmd = "ffmpeg"
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        logger.info("Service FFmpeg is operational.")
    except Exception:
        logger.warning("FFmpeg not found in PATH. Checking local bin/...")
        local_bin = os.path.join(os.getcwd(), "bin")
        local_ffmpeg = os.path.join(local_bin, "ffmpeg.exe")
        
        if os.path.exists(local_ffmpeg):
             logger.info(f"Found local FFmpeg at {local_ffmpeg}")
             os.environ["PATH"] += os.pathsep + local_bin
        else:
             logger.info("Attempting auto-install of FFmpeg...")
             from src.utils import ffmpeg_installer
             installed_path = ffmpeg_installer.install_ffmpeg()
             if installed_path and os.path.exists(installed_path):
                 logger.info("FFmpeg installed successfully.")
                 os.environ["PATH"] += os.pathsep + local_bin
             else:
                 logger.error("CRITICAL: FFmpeg could not be installed.")
                 services_ok = False

    if not services_ok and not args.dry_run:
        logger.error("Aborting due to missing services.")
        sys.exit(1)
        
    if not services_ok and args.dry_run:
        logger.warning("Dry run checking: Services are missing, but proceeding to check specific generators if possible or strictly aborting.")
        # Actually, we can't generate quotes without Ollama.
        # But we can perhaps mock if purely testing logic?
        # User wants "Fix all runtime errors". Using mocks is not fixing.
        # We must abort.
        logger.error("Cannot proceed even in dry-run without backend services.")
        sys.exit(1)

    # 1. Ensure Music Assets
    music_loader.ensure_music_assets(config['paths']['music'])

    # 2. Select Topic
    topic = args.topic if args.topic else random.choice(TOPICS)
    logger.info(f"Starting pipeline for topic: {topic}")

    temp_files = []

    try:
        # 2. Generate Quote
        quote = quote_gen.generate_quote(topic=topic, model=config['ollama']['model'])
        if not quote:
            logger.error("Failed to generate quote. Aborting.")
            logger.error("Please ensure Ollama is running and the model is installed.")
            logger.error(f"Try running: ollama pull {config['ollama']['model']}")
            return


        # 3. Generate Background (Video preferred, Image fallback)
        background_video = None
        image_path = None
        
        # Try Video First
        try:
            # Search query based on topic + abstract keywords
            video_query = f"{topic} nature abstract"
            background_video = video_gen.get_video_background(video_query, output_dir=config['paths']['temp'])
        except Exception as e:
            logger.warning(f"Video generation failed: {e}")
            
        if background_video:
            temp_files.append(background_video)
            logger.info(f"Using video background: {background_video}")
        else:
            # Fallback to Image
            logger.info("Fallback to Image Generation...")
            # Use generic abstract prompts WITHOUT topic name to avoid text in images
            abstract_prompts = [
                "abstract gradient background, soft colors, inspirational atmosphere",
                "minimalist background, smooth gradients, calming colors",
                "cinematic lighting, abstract shapes, inspirational mood",
                "soft bokeh background, dreamy atmosphere, elegant composition",
                "abstract waves, flowing colors, peaceful ambiance"
            ]
            image_prompt = random.choice(abstract_prompts)
            image_path = image_gen.generate_background(image_prompt, output_dir=config['paths']['temp'], config=config)
            if not image_path:
                logger.error("Failed to generate image. Aborting.")
                return
            temp_files.append(image_path)

        # 4. Generate Voiceover (NO subtitles)
        audio_path = audio_gen.generate_voiceover(
            quote,
            output_dir=config['paths']['temp'],
            specific_gender="male"
        )

        if not audio_path:
            logger.error("Failed to generate voiceover. Aborting.")
            return

        temp_files.append(audio_path)
        subtitle_path = None


        # 5. Compose Video
        music_dir = config['paths']['music']
        output_file = os.path.join(config['paths']['output'], f"short_{random.randint(1000,9999)}.mp4")
        
        final_video_path = composer.create_video(
            image_path=image_path,
            audio_path=audio_path,
            quote_text=quote,
            music_dir=music_dir,
            output_file=output_file,
            subtitle_path=subtitle_path,
            background_video_path=background_video
        )
        
        if not final_video_path:
            logger.error("Failed to create video. Aborting.")
            sys.exit(1)
        
        logger.info(f"Video generated at: {final_video_path}")

        # 6. Upload to YouTube
        if not args.dry_run:
            logger.info("Starting upload process...")
            title = f"Daily {topic.capitalize()} Quote #shorts #motivation"
            description = config['upload']['description_template'].format(quote=quote)
            tags = ["shorts", "motivation", "inspiration", topic, "quotes"]
            
            video_id = youtube_api.upload_video(
                final_video_path, 
                title, 
                description, 
                tags, 
                privacy_status=config['upload']['privacy_status']
            )
            
            if video_id:
                logger.info(f"Successfully uploaded! URL: https://youtube.com/shorts/{video_id}")
            else:
                logger.error("YouTube Upload failed.")
            # 7. Upload to Google Drive (Backup/Sharing)
            logger.info("Starting Google Drive upload...")
            drive_link = drive_api.upload_file(final_video_path)
            if drive_link:
                logger.info(f"Backup uploaded to Drive: {drive_link}")
            else:
                logger.warning("Google Drive upload failed.")

            # Final Cleanup of Video File
            if not args.keep_temps and os.path.exists(final_video_path):
                try:
                    os.remove(final_video_path)
                    logger.info(f"Deleted uploaded video file: {final_video_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete video file: {e}")
        else:
            logger.info("Dry run enabled. Skipping uploads.")

    except Exception as e:
        logger.error(f"Pipeline failed with exception: {e}")
        sys.exit(1)
    finally:
        if not args.keep_temps:
            cleanup(temp_files)

if __name__ == "__main__":
    main()
