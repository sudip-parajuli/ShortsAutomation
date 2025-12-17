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

def create_video(image_path=None, audio_path=None, quote_text="", music_dir="assets/music", output_file="assets/output/final_video.mp4", subtitle_path=None, background_video_path=None):
    """
    Composes the video using FFmpeg.
    """
    try:
        # Ensure output directory exists (Critical for GitHub runners)
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        # 1. Determine constraints
        voice_duration = get_audio_duration(audio_path)
        # Min duration 8 seconds, Max 40 seconds (clamp)
        # Add 3 seconds padding for "slower" feel/silence at end
        base_duration = max(voice_duration + 3.0, 8.0)
        video_duration = min(base_duration, 40.0)
        
        # 2. Prepare Inputs
        input_voice = ffmpeg.input(audio_path)
        
        # 3. Background Music Selection
        music_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3') or f.endswith('.ogg')] if os.path.isdir(music_dir) else []
        if music_files:
            music_path = os.path.join(music_dir, random.choice(music_files))
            input_music = ffmpeg.input(music_path).filter('volume', 0.1) # Ducking background
            # Loop music if shorter than video
            input_music = ffmpeg.filter(input_music, 'aloop', loop=-1, size=2e+09) 
        else:
            logger.warning("No music found in assets/music. Proceeding without background music.")
            input_music = None
        
        # Determine background input
        if image_path and os.path.exists(image_path):
             # ORIGINAL IMAGE LOGIC (Fallback)
            input_visual = ffmpeg.input(image_path)
            video = (
                input_visual
                .filter('scale', -1, 1920)
                .filter('crop', 1080, 1920)
                .filter('zoompan', z='min(zoom+0.0005,1.1)', d=int(video_duration*30), x='iw/2-(iw/zoom/2)', y='ih/2-(ih/zoom/2)', s='1080x1920')
            )
        elif background_video_path and os.path.exists(background_video_path):
             # NEW VIDEO LOGIC
             logger.info(f"Using video background: {background_video_path}")
             input_visual = ffmpeg.input(background_video_path)
             # Loop video to ensure it covers full duration
             # 1. Scale to cover 1080x1920
             # 2. Crop to 1080x1920
             # 3. Trim to exact duration (looping handled by stream_loop or aloop? stream_loop input option is best)
             
             # Better approach for looping video input:
             # Re-define input with stream_loop
             input_visual = ffmpeg.input(background_video_path, stream_loop=-1)
             
             video = (
                 input_visual
                 # Scale to cover 1080x1920 while preserving aspect ratio
                 .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')
                 .filter('crop', 1080, 1920) # Center crop
                 .filter('trim', duration=video_duration) # Cut to length
                 # No zoompan for video usually, it's already moving
             )
        else:
             logger.error("No visual input provided (image or video).")
             return None


        # 5. Add Subtitles (synchronized with audio)
        if subtitle_path and os.path.exists(subtitle_path):
            # Use subtitles filter for word-by-word sync
            safe_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\:')
            
            video = video.filter(
                'subtitles',
                safe_subtitle_path,
                force_style='FontName=Arial,FontSize=90,Bold=1,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=3,Shadow=2,Alignment=10,MarginV=50'
            )
        else:
            # Fallback to static text (existing code below)
            pass

        # Draw Text (Fallback)
        # Robust escaping for FFmpeg drawtext
        # FFmpeg drawtext escaping is tricky. 
        # 1. Escape \ to \\
        # 2. Escape ' to \' (if using single quotes for the string)
        # 3. Escape : to \:
        # 4. Escape % to \%
        
        # We will use single quotes to wrap the text in the command typically, 
        # but ffmpeg-python handles the argument passing. 
        # The main issue usually is the internal string interpretation of drawtext.
        
        # Preserve newlines but escape other special characters for FFmpeg drawtext
        safe_text = quote_text.replace('\\', '\\\\').replace(':', '\\:').replace("'", "\u2019").replace('%', '\\%')
        # Replaced ' with right single quote to avoid syntax errors and look better.
        # Note: We preserve \n characters as they will be used for line breaks
        
        # Smart line wrapping based on character count (max ~25 chars per line for font size 90)
        # This ensures text fits within 1080px width
        # First check if the quote already has manual line breaks (\n)
        if '\n' in safe_text:
            # Use the existing line breaks from the quote
            lines = safe_text.split('\n')
            # Still apply character limit per line and truncate if needed
            max_chars_per_line = 30
            wrapped_lines = []
            for line in lines:
                if len(line) <= max_chars_per_line:
                    wrapped_lines.append(line)
                else:
                    # Wrap long lines
                    words = line.split()
                    current_line = []
                    current_length = 0
                    for word in words:
                        word_length = len(word)
                        test_length = current_length + word_length + (1 if current_line else 0)
                        if test_length <= max_chars_per_line:
                            current_line.append(word)
                            current_length = test_length
                        else:
                            if current_line:
                                wrapped_lines.append(" ".join(current_line))
                            current_line = [word]
                            current_length = word_length
                    if current_line:
                        wrapped_lines.append(" ".join(current_line))
            lines = wrapped_lines
        else:
            # Auto-wrap based on character count
            max_chars_per_line = 25
            words = safe_text.split()
            lines = []
            current_line = []
            current_length = 0
            
            for word in words:
                word_length = len(word)
                # Account for space between words
                test_length = current_length + word_length + (1 if current_line else 0)
                
                if test_length <= max_chars_per_line:
                    current_line.append(word)
                    current_length = test_length
                else:
                    # Start new line
                    if current_line:
                        lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
            
            # Add remaining words
            if current_line:
                lines.append(" ".join(current_line))
        
        # Limit to 5 lines max for readability (increased from 3 for longer quotes)
        if len(lines) > 5:
            lines = lines[:5]
            lines[-1] += "..."  # Indicate truncation
        
        # Use \n for FFmpeg drawtext line breaks (NOT \\n)
        final_text = "\n".join(lines)
        
        # Font Selection Strategy (Cross-Platform)
        font_path = None
        possible_fonts = [
            "assets/fonts/Roboto-Bold.ttf", # Bundled font (if present)
            "font.ttf", # Root fallback
            "C:/Windows/Fonts/arial.ttf",   # Windows Default
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", # Linux Default (Ubuntu/Debian)
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", # Linux Alternative
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" # Linux Alternative 2
        ]
        
        for f in possible_fonts:
            if os.path.exists(f):
                font_path = f
                break
                
        if not font_path:
             logger.warning("No suitable font found. FFmpeg might fail if it can't find default font.")
             # On Linux, sometimes "Sans" works as a generic alias if fontconfig is set up
             # But best to rely on explicit path.
             # We will try a generic name and hope ffmpeg finds it in system path
             font_path = "Sans"

        video = video.drawtext(
            text=final_text,
            fontfile=font_path,
            fontsize=70,  # Reduced from 90 for better multi-line readability
            fontcolor='white',
            shadowcolor='black',
            shadowx=5,
            shadowy=5,
            x='(w-text_w)/2',
            y='(h-text_h)/2',
            fix_bounds=True, 
            line_spacing=15  # Reduced from 20 for tighter line spacing
        )

        # 5. Audio Mixing
        if input_music:
            # Fix: Ensure music plays for entire video duration
            # 1. Loop music infinitely first
            # 2. Trim to exact video_duration
            # 3. Mix with voice. Voice is shorter.
            # We want voice to start maybe 1 second in, not 0. But for now 0 is fine.
            # Crucially, 'amix' with duration='first' (voice) was cutting off the music.
            # We need duration='duration' of the longest input, OR trim the music explicitly and rely on that.
            
            # Prepare music: Loop -> Vol -> Trim to Video Length
            # stream_music = ffmpeg.input(music_path).filter('aloop', loop=-1, size=2e+09)
            # input_music variable already has aloop and volume from block above.
            
            # Explicitly trim music to video duration so it doesn't run forever
            bg_music = input_music.filter('atrim', duration=video_duration)
            
            # Pad voice with silence at the end to match video duration? 
            # Or just use amix duration='longest'.
            # If we use 'longest', and bg_music is trimmed to video_duration, the output will be video_duration.
            # Voice is shorter, so it will stop contributing, which is fine.
            
            final_audio = ffmpeg.filter([input_voice, bg_music], 'amix', inputs=2, duration='longest')
            
            # Ensure the final audio stream is exactly video_duration just in case amix is weird
            final_audio = final_audio.filter('atrim', duration=video_duration)
        else:
            final_audio = input_voice

        # 6. Output
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
        logger.info(f"Video created successfully: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Failed to create video: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            logger.error(f"FFmpeg stderr: {e.stderr.decode('utf-8')}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # create_video(...)
    pass
