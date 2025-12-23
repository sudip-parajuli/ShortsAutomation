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

def create_long_video(audio_path, quote_text, explanation_text, music_dir="assets/music", output_file="assets/output/long_video.mp4", subtitle_path=None, background_video_paths=None, image_path=None):
    """
    Composes a 16:9 long-form video using FFmpeg.
    background_video_paths can be a string (single path) or a list of paths.
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
            # Use stream_loop on input for infinite looping without buffer size issues
            input_music = ffmpeg.input(music_path, stream_loop=-1).filter('volume', 0.15) 
            bg_music = input_music.filter('atrim', duration=video_duration)
            final_audio = ffmpeg.filter([input_voice, bg_music], 'amix', inputs=2, duration='first')
        else:
            final_audio = input_voice

        # 4. Background Visual
        if background_video_paths:
            if isinstance(background_video_paths, str):
                background_video_paths = [background_video_paths]
            
            # Filter out non-existent files
            background_video_paths = [p for p in background_video_paths if os.path.exists(p)]
            
            if not background_video_paths:
                 logger.error("No valid background videos found.")
                 return None

            logger.info(f"Using {len(background_video_paths)} video background(s) for long-form.")
            
            processed_clips = []
            for path in background_video_paths:
                clip = (
                    ffmpeg.input(path)
                    .filter('scale', 1920, 1080, force_original_aspect_ratio='increase')
                    .filter('crop', 1920, 1080)
                )
                processed_clips.append(clip)
            
            # If we have multiple clips, we cycle them or just concat
            # To cycle until duration is met, we might need a more complex filter or just loop the concat
            if len(processed_clips) > 1:
                # Simple concatenation. For the loop filter, we use a safer size limit (32767) 
                # supported by older FFmpeg builds. For video frames, this is plenty.
                video = ffmpeg.concat(*processed_clips, v=1, a=0).filter('loop', loop=-1, size=32767)
            else:
                # For single video, we can just use loop filter with safe size
                video = processed_clips[0].filter('loop', loop=-1, size=32767)
            
            video = video.filter('trim', duration=video_duration).filter('vignette', angle='0.5')
            
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
