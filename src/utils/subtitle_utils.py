import os
import logging
import re

logger = logging.getLogger(__name__)

def format_ass_timestamp(seconds):
    """Convert seconds to ASS timestamp format H:MM:SS.cc"""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    centiseconds = int((secs - int(secs)) * 100)
    return f"{hours}:{minutes:02d}:{int(secs):02d}.{centiseconds:02d}"

def generate_karaoke_ass(word_boundaries, output_file, quote_text, keywords=None):
    """
    Generates an .ass subtitle file with a karaoke highlighting effect.
    Supports keyword highlighting.
    """
    if keywords is None:
        keywords = []
    
    # Pre-process keywords: lowercase and strip punctuation
    clean_keywords = [re.sub(r'[^\w]', '', k.lower()) for k in keywords]
    
    # ASS Header
    # PrimaryColor: White (&H00FFFFFF)
    # SecondaryColor (Highlight): Yellow/Green (&H0000FFFF or &H0000FF00)
    # ImportantColor: Bright Green (&H0000FF00)
    
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,90,&H00FFFFFF,&H0000FFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,2,5,10,10,10,1
Style: Highlight,Arial,110,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,5,3,5,10,10,10,1
Style: Important,Arial,120,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,6,4,5,10,10,10,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    events = []
    
    if not word_boundaries:
        logger.warning("No word boundaries provided for ASS generation.")
        return None

    for i, boundary in enumerate(word_boundaries):
        start_s = boundary['offset'] / 10**9
        duration_s = boundary['duration'] / 10**9
        end_s = start_s + duration_s
        
        # Extend end time slightly to bridge gaps between words
        if i < len(word_boundaries) - 1:
            next_start = word_boundaries[i+1]['offset'] / 10**9
            if next_start - end_s < 0.2:
                end_s = next_start
        else:
            end_s += 0.5

        start_ts = format_ass_timestamp(start_s)
        end_ts = format_ass_timestamp(end_s)
        
        word = boundary['text'].strip()
        clean_word = re.sub(r'[^\w]', '', word.lower())
        
        style = "Highlight"
        # Check if it's an important keyword
        if clean_word in clean_keywords or len(clean_word) > 7:
            style = "Important"
        
        # Add simple zoom animation using \t (transform)
        # From scale 80% to 100% over the duration
        animated_text = f"{{\\fscx80\\fscy80\\t(0,{int(duration_s*500)},\\fscx100\\fscy100)}}{word}"
        
        events.append(f"Dialogue: 0,{start_ts},{end_ts},{style},,0,0,0,,{animated_text}")

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        for event in events:
            f.write(event + "\n")
            
    logger.info(f"Karaoke ASS subtitles saved to {output_file}")
    return output_file

