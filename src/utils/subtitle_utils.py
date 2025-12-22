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
    Generates an .ass subtitle file with a single-event karaoke highlighting effect.
    The whole quote is shown at once, with words highlighted as they are spoken.
    """
    if keywords is None:
        keywords = []
    
    # Pre-process keywords: lowercase and strip punctuation
    clean_keywords = [re.sub(r'[^\w]', '', k.lower()) for k in keywords]
    
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,80,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,2,5,80,80,10,1
"""
# Swapped: Primary is now Yellow (&H0000FFFF), Secondary is White (&H00FFFFFF)
# In \k karaoke, Secondary is base color, Primary is highlight color.

    if not word_boundaries:
        logger.warning("No word boundaries provided for ASS generation.")
        return None

    # Determine timing for the whole quote
    quote_start_s = word_boundaries[0]['offset'] / 10**9
    quote_end_s = (word_boundaries[-1]['offset'] + word_boundaries[-1]['duration']) / 10**9 + 0.5
    
    start_ts = format_ass_timestamp(quote_start_s)
    end_ts = format_ass_timestamp(quote_end_s)
    
    event_start_ms = int(quote_start_s * 1000)

    # Build the karaoke text with \k tags
    max_chars_per_line = 25
    lines = []
    current_line_words = []
    current_line_length = 0
    
    for boundary in word_boundaries:
        word = boundary['text'].strip()
        word_len = len(word)
        
        if current_line_length + word_len + (1 if current_line_words else 0) > max_chars_per_line and current_line_words:
            lines.append(current_line_words)
            current_line_words = []
            current_line_length = 0
            
        current_line_words.append(boundary)
        current_line_length += word_len + 1

    if current_line_words:
        lines.append(current_line_words)

    # Construct the final ASS Dialogue text
    ass_text_parts = []
    
    for line in lines:
        line_parts = []
        for boundary in line:
            start_ms = int(boundary['offset'] / 10**6)
            duration_ms = int(boundary['duration'] / 10**6)
            
            # Times relative to event start for \t
            rel_start = start_ms - event_start_ms
            rel_mid = rel_start + (duration_ms // 2)
            rel_end = rel_start + duration_ms
            
            # Karaoke duration in centiseconds
            k_duration = duration_ms // 10
            
            word = boundary['text']
            
            # Add zoom animation: 100% -> 115% -> 100%
            # \fscx100\fscy100 is the base scale
            zoom_tag = f"{{\\t({rel_start},{rel_mid},\\fscx115\\fscy115)\\t({rel_mid},{rel_end},\\fscx100\\fscy100)\\k{k_duration}}}"
            
            line_parts.append(f"{zoom_tag}{word}")
            
        ass_text_parts.append(" ".join(line_parts))

    final_content = "\\N".join(ass_text_parts) # \N is hard line break in ASS

    event_line = f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{final_content}"

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write("\n[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        f.write(event_line + "\n")
            
    logger.info(f"Karaoke ASS subtitles saved to {output_file}")
    return output_file

