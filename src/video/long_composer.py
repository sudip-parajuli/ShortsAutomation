import ffmpeg
import os
import logging
import random
from mutagen.mp3 import MP3

logger = logging.getLogger(__name__)

def get_audio_duration(file_path):
    try:
        audio = MP3(file_path)
        return audio.info.length
    except Exception:
        # Fallback using ffmpeg probe
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])

def create_long_video(audio_path, quote_text, explanation_text, music_dir="assets/music", output_file="assets/output/long_video.mp4", subtitle_path=None, background_video_path=None, image_path=None):
    """
    Composes a 16:9 long-form video using FFmpeg.
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 1. Determine constraints
        voice_duration = get_audio_duration(audio_path)
        # Add a bit of padding at the end
        video_duration = voice_duration + 2.0
        
        # 2. Prepare Inputs
        input_voice = ffmpeg.input(audio_path)
        
        # 3. Background Music Selection
        music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3') or f.endswith('.ogg')] if os.path.isdir(music_dir) else []
        if music_files:
            music_path = os.path.join(music_dir, random.choice(music_files))
            # Ducking: voice is primary, music is lowered
            input_music = ffmpeg.input(music_path).filter('volume', 0.15) 
            # Loop music infinitely
            input_music = ffmpeg.filter(input_music, 'aloop', loop=-1, size=2e+09)
            bg_music = input_music.filter('atrim', duration=video_duration)
            final_audio = ffmpeg.filter([input_voice, bg_music], 'amix', inputs=2, duration='first')
        else:
            final_audio = input_voice

        # 4. Background Visual
        if background_video_path and os.path.exists(background_video_path):
             logger.info(f"Using video background for long-form: {background_video_path}")
             # Loop background video to cover entire duration
             input_visual = ffmpeg.input(background_video_path, stream_loop=-1)
             
             video = (
                 input_visual
                 # Scale to 16:9 (1920x1080)
                 .filter('scale', 1920, 1080, force_original_aspect_ratio='increase')
                 .filter('crop', 1920, 1080)
                 .filter('trim', duration=video_duration)
                 .filter('vignette', angle='0.5')
             )
        elif image_path and os.path.exists(image_path):
            input_visual = ffmpeg.input(image_path, loop=1, t=video_duration)
            video = (
                input_visual
                .filter('scale', 1920, 1080, force_original_aspect_ratio='increase')
                .filter('crop', 1920, 1080)
                .filter('vignette', angle='0.5')
            )
        else:
             logger.error("No visual input provided for long-form video.")
             return None

        # 5. Add Subtitles (ASS Karaoke)
        if subtitle_path and os.path.exists(subtitle_path):
            safe_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            video = video.filter('subtitles', safe_subtitle_path)
        
        # 6. Final Output
        out = ffmpeg.output(
            video, 
            final_audio, 
            output_file, 
            vcodec='libx264', 
            acodec='aac', 
            t=video_duration,
            pix_fmt='yuv420p',
            r=30
        )
        
        out.run(overwrite_output=True, quiet=True)
        logger.info(f"Long-form video created successfully: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Failed to create long video: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"FFmpeg stderr: {e.stderr.decode('utf-8')}")
        return None
