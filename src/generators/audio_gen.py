# import asyncio
# import edge_tts
# import logging
# import os
# import random
# from datetime import datetime

# logger = logging.getLogger(__name__)

# # Mature, natural-sounding voices (podcast/audiobook style)
# NATURAL_VOICES = [
#     "en-US-GuyNeural",           # Deep, mature male
#     "en-GB-RyanNeural",          # British male, authoritative
#     "en-US-ChristopherNeural",   # Warm male narrator
#     "en-US-DavisNeural",         # Calm, professional male
#     "en-US-JennyNeural",         # Mature female, clear
#     "en-GB-LibbyNeural",         # British female, elegant
#     "en-US-AriaNeural",          # Warm female narrator
#     "en-US-SaraNeural"           # Professional female
# ]

# def build_ssml(text):
#     """
#     Build SSML for natural-sounding speech:
#     - Slower pace for contemplation
#     - Lower pitch for maturity
#     - Pauses for emphasis and breathing
#     """
#     return f"""
# <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
#   <prosody rate="slow" pitch="-4%">
#     <p>
#       <break time="500ms"/>
#       {text}
#       <break time="700ms"/>
#     </p>
#   </prosody>
# </speak>
# """

# async def _generate_voiceover_async(text, output_file, voice, subtitle_file=None):
#     """
#     Generate natural-sounding voiceover using SSML.
#     """
#     # Build SSML for natural speech
#     ssml = build_ssml(text)
    
#     # Create communicate object with SSML and natural settings
#     communicate = edge_tts.Communicate(
#         text=ssml,
#         voice=voice,
#         rate="-10%",      # Slightly slower for clarity
#         volume="+5%"      # Slightly louder for presence
#     )
    
#     # Save audio
#     await communicate.save(output_file)
    
#     # Generate subtitle file if requested
#     if subtitle_file:
#         subtitles = []
#         # Re-create communicate for subtitle generation (without SSML for timing)
#         async for chunk in edge_tts.Communicate(text, voice, rate="-10%").stream():
#             if chunk["type"] == "WordBoundary":
#                 subtitles.append(chunk)
        
#         # Write VTT format
#         with open(subtitle_file, 'w', encoding='utf-8') as f:
#             f.write("WEBVTT\n\n")
#             for i, sub in enumerate(subtitles):
#                 start_time = sub['offset'] / 10000000  # Convert to seconds
#                 duration = sub.get('duration', 500000000) / 10000000
#                 end_time = start_time + duration
                
#                 f.write(f"{i+1}\n")
#                 f.write(f"{format_timestamp(start_time)} --> {format_timestamp(end_time)}\n")
#                 f.write(f"{sub['text']}\n\n")

# def format_timestamp(seconds):
#     """Convert seconds to VTT timestamp format HH:MM:SS.mmm"""
#     hours = int(seconds // 3600)
#     minutes = int((seconds % 3600) // 60)
#     secs = seconds % 60
#     return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

# def generate_voiceover(text, output_dir="assets/temp", specific_gender=None, rate="-15%", generate_subtitles=True):
#     """
#     Generates natural-sounding voiceover using Edge TTS with SSML.
    
#     Voice characteristics:
#     - Podcast narrator style
#     - Audiobook wisdom tone
#     - Calm mentor voice
    
#     Returns tuple: (audio_path, subtitle_path) or (audio_path, None)
#     """
#     # Select random natural voice
#     if specific_gender == 'male':
#         male_voices = [v for v in NATURAL_VOICES if any(m in v for m in ["Guy", "Ryan", "Christopher", "Davis"])]
#         voice = random.choice(male_voices)
#     elif specific_gender == 'female':
#         female_voices = [v for v in NATURAL_VOICES if any(f in v for f in ["Jenny", "Libby", "Aria", "Sara"])]
#         voice = random.choice(female_voices)
#     else:
#         voice = random.choice(NATURAL_VOICES)
        
#     logger.info(f"Selected natural voice: {voice}")
    
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = f"voice_{timestamp}.mp3"
#     subtitle_filename = f"voice_{timestamp}.vtt" if generate_subtitles else None
    
#     os.makedirs(output_dir, exist_ok=True)
#     filepath = os.path.join(output_dir, filename)
#     subtitle_path = os.path.join(output_dir, subtitle_filename) if subtitle_filename else None
    
#     try:
#         # Run async function in sync wrapper
#         asyncio.run(_generate_voiceover_async(text, filepath, voice, subtitle_file=subtitle_path))
#         logger.info(f"✅ Natural voiceover saved to {filepath}")
#         if subtitle_path:
#             logger.info(f"Subtitles saved to {subtitle_path}")
#         return (filepath, subtitle_path)
#     except Exception as e:
#         logger.error(f"Failed to generate voiceover: {e}")
#         return (None, None)

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     print(generate_voiceover("Success is not final, failure is not fatal. It is the courage to continue that counts"))


import asyncio
import edge_tts
import logging
import os
import random
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# Mature, raconteur/anecdotist voices
NATURAL_VOICES = [
    "en-US-GuyNeural",         # Deep, mature male
    "en-GB-RyanNeural",        # British male, authoritative
    "en-US-ChristopherNeural", # Warm, calm male
    "en-US-DavisNeural",       # Calm, professional male
    "en-GB-LibbyNeural",       # British female, elegant
    "en-US-AriaNeural",        # Warm female narrator
]

# ---------------- SANITIZATION ---------------- #
def sanitize_for_tts(text: str) -> str:
    """Clean quote text to ensure single sentence, max words, no preambles or extra commentary."""
    if not text:
        raise ValueError("Empty text passed to TTS")

    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    # Block common non-quote content
    forbidden = [
        "here is",
        "here's",
        "this quote",
        "remember",
        "this means",
        "because",
        "which shows",
        "this reminds",
        "consider this",
        "think about",
        "reflect on",
    ]
    lowered = text.lower()
    if any(f in lowered for f in forbidden):
        # Remove everything before first meaningful part
        text = re.split(r"[:\-]", text, 1)[-1].strip()

    # Single sentence only
    text = re.split(r"[.!?]", text)[0]

    # Max 25 words
    text = " ".join(text.split()[:25])
    return text

# ---------------- ASYNC CORE ---------------- #
async def _generate_voiceover_async(text: str, output_file: str, voice: str):
    """Generate TTS audio (plain text, no SSML wrapper for v7.2.7)."""
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_file)

# ---------------- PUBLIC API ---------------- #
def generate_voiceover(
    text: str,
    output_dir="assets/temp",
    specific_gender=None
):
    """
    Generates natural, mature/anecdotist-style voiceover using Edge TTS v7.2.7.
    Returns: filepath of generated audio.
    """
    try:
        text = sanitize_for_tts(text)
    except ValueError as e:
        logger.error(f"TTS sanitization failed: {e}")
        return None

    # Voice selection
    if specific_gender == "male":
        pool = [v for v in NATURAL_VOICES if "Guy" in v or "Ryan" in v or "Christopher" in v or "Davis" in v]
    elif specific_gender == "female":
        pool = [v for v in NATURAL_VOICES if "Libby" in v or "Aria" in v]
    else:
        pool = NATURAL_VOICES

    voice = random.choice(pool)
    logger.info(f"Selected voice: {voice}")

    # Output path
    os.makedirs(output_dir, exist_ok=True)
    filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
    filepath = os.path.join(output_dir, filename)

    try:
        asyncio.run(_generate_voiceover_async(text, filepath, voice))
        logger.info(f"Voiceover saved: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Voice generation failed: {e}")
        return None

# ---------------- MAIN TEST ---------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_quote = "Success is not final, failure is not fatal. It is the courage to continue that counts"
    generate_voiceover(test_quote)
