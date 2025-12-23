import sys
import os
import argparse
import yaml
import random
import logging
import warnings
import subprocess

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.generators import long_form_gen, image_gen, audio_gen, video_gen
from src.video import long_composer
from src.upload import youtube_api, drive_api
from src.utils import music_loader, subtitle_utils

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("long_automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LongMain")

TOPICS = [
    "success", "discipline", "mindset", "hustle", "courage", 
    "fitness", "wisdom", "stoicism", "leadership", "focus",
    "ambition", "patience", "resilience", "gratitude", "strength",
    "learning", "growth", "purpose", "action", "confidence"
]

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
    parser = argparse.ArgumentParser(description="Automated YouTube Long-form Video Generator")
    parser.add_argument("--dry-run", action="store_true", help="Generate video but do NOT upload")
    parser.add_argument("--topic", type=str, help="Specific topic for the video")
    parser.add_argument("--keep-temps", action="store_true", help="Do not delete temporary assets")
    args = parser.parse_args()

    config = load_config()
    
    # 0. Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        logger.error("FFmpeg not found. Please ensure it is in PATH.")
        sys.exit(1)

    # 1. Ensure Music Assets
    music_loader.ensure_music_assets(config['paths']['music'])

    # 2. Select Topic
    topic = args.topic if args.topic else random.choice(TOPICS)
    logger.info(f"Starting long-form pipeline for topic: {topic}")

    temp_files = []

    try:
        # 2. Generate Long-form Script
        script = long_form_gen.generate_long_form_script(topic=topic)
        if not script:
            logger.error("Failed to generate long-form script. Aborting.")
            return

        quote = script['quote']
        explanation = script['explanation']
        full_text = script['full_text']

        # 3. Generate Background Video (Landscape 16:9)
        background_videos = []
        try:
            video_query = f"{topic} nature landscape abstract"
            background_videos = video_gen.get_multiple_video_backgrounds(
                video_query, 
                output_dir=config['paths']['temp'],
                count=5,
                orientation="landscape"
            )
        except Exception as e:
            logger.warning(f"Video background search failed: {e}")
            
        if background_videos:
            temp_files.extend(background_videos)
            image_path = None
        else:
            # Fallback to image (16:9)
            logger.info("Fallback to Image Generation...")
            abstract_prompts = [
                "cinematic landscape, abstract digital art, hyperrealistic, 8k",
                "peaceful nature scene, morning mist, 16:9 resolution, elegant",
                "outer space galaxy, nebula, vibrant colors, cinematic lighting"
            ]
            image_prompt = random.choice(abstract_prompts)
            image_path = image_gen.generate_background(image_prompt, output_dir=config['paths']['temp'], config=config)
            if not image_path:
                logger.error("Failed to generate visual background. Aborting.")
                return
            temp_files.append(image_path)


        # 4. Generate Voiceover
        logger.info("Generating long-form voiceover...")
        audio_path, word_boundaries, sanitized_text = audio_gen.generate_voiceover(
            full_text,
            output_dir=config['paths']['temp'],
            style="elderly",
            long_form=True
        )

        if not audio_path:
            logger.error("Failed to generate voiceover. Aborting.")
            return

        temp_files.append(audio_path)
        
        # Calculate approximate duration for subtitles
        voice_duration = long_composer.get_audio_duration(audio_path)
        video_duration = voice_duration + 2.0
        
        # 5. Generate Karaoke Subtitles (ASS format, 1920x1080)
        subtitle_path = None
        if word_boundaries:
            ass_filename = audio_path.replace(".mp3", ".ass")
            subtitle_path = subtitle_utils.generate_karaoke_ass(
                word_boundaries, 
                ass_filename, 
                sanitized_text,
                video_duration=video_duration, # Trigger segmentation if > 60
                width=1920,
                height=1080
            )
            if subtitle_path:
                temp_files.append(subtitle_path)

        # 6. Compose Video
        output_file = os.path.join(config['paths']['output'], f"long_{random.randint(1000,9999)}.mp4")
        
        final_video_path = long_composer.create_long_video(
            audio_path=audio_path,
            quote_text=quote,
            explanation_text=explanation,
            music_dir=config['paths']['music'],
            output_file=output_file,
            subtitle_path=subtitle_path,
            background_video_paths=background_videos,
            image_path=image_path if not background_videos else None
        )
        
        if not final_video_path:
            logger.error("Failed to create video. Aborting.")
            return
        
        logger.info(f"Long-form video generated at: {final_video_path}")

        # 7. Upload to YouTube
        if not args.dry_run:
            logger.info("Starting upload process...")
            title = f"Finding Peace in {topic.capitalize()}: A Life Lesson"
            description = f"Today we explore {topic} through a powerful quote and a detailed explanation.\n\n{full_text}\n\n#motivation #wisdom #{topic}"
            tags = ["motivation", "wisdom", "inspiration", topic, "meditation"]
            
            video_id = youtube_api.upload_video(
                final_video_path, 
                title, 
                description, 
                tags, 
                privacy_status=config['upload']['privacy_status']
            )
            
            if video_id:
                logger.info(f"Successfully uploaded! URL: https://youtube.com/watch?v={video_id}")
                # Backup to Drive
                drive_link = drive_api.upload_file(final_video_path)
                if drive_link:
                    logger.info(f"Backup uploaded to Drive: {drive_link}")
            else:
                logger.error("YouTube Upload failed.")

            if not args.keep_temps and os.path.exists(final_video_path):
                os.remove(final_video_path)
        else:
            logger.info("Dry run enabled. Skipping upload.")

    except Exception as e:
        logger.error(f"Long-form pipeline failed: {e}")
    finally:
        if not args.keep_temps:
            cleanup(temp_files)

if __name__ == "__main__":
    main()
