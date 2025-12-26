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

def generate_karaoke_ass(word_boundaries, output_file, quote_text, keywords=None, video_duration=None, width=1080, height=1920):
    """
    Generates an .ass subtitle file with a single-event karaoke highlighting effect.
    The whole quote is shown at once, with words highlighted as they are spoken.
    If video_duration is provided, the caption stays until that time.
    """
    if keywords is None:
        keywords = []
    
    # Pre-process keywords: lowercase and strip punctuation
    clean_keywords = [re.sub(r'[^\w]', '', k.lower()) for k in keywords]
    
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,80,&H0000FFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,2,5,80,80,50,1
"""
# Swapped: Primary is now Yellow (&H0000FFFF), Secondary is White (&H00FFFFFF)
# In \k karaoke, Secondary is base color, Primary is highlight color.

    if not word_boundaries:
        logger.warning("No word boundaries provided for ASS generation.")
        return None

    # Determine timing for the whole quote (used for logging and fallback)
    quote_start_s = word_boundaries[0]['offset'] / 10**9
    quote_end_s = video_duration if video_duration else (word_boundaries[-1]['offset'] + word_boundaries[-1]['duration']) / 10**9 + 1.0

    # segmentation logic
    # For shorts, we show everything. For long-term, we show chunks.
    is_long_form = video_duration and video_duration > 60
    
    events = []
    
    if is_long_form:
        # Segment words into groups of ~10-15 words or ~2 lines
        word_segments = []
        current_segment = []
        current_chars = 0
        max_chars_per_segment = 50
        
        for boundary in word_boundaries:
            word = boundary['text']
            if current_chars + len(word) > max_chars_per_segment and current_segment:
                word_segments.append(current_segment)
                current_segment = []
                current_chars = 0
            
            current_segment.append(boundary)
            current_chars += len(word) + 1
            
        if current_segment:
            word_segments.append(current_segment)
            
        for segment in word_segments:
            seg_start_s = segment[0]['offset'] / 10**9
            seg_end_s = (segment[-1]['offset'] + segment[-1]['duration']) / 10**9
            
            # Add small buffer at end of segment unless it's the next one immediately
            seg_end_s += 0.3
            
            start_ts = format_ass_timestamp(seg_start_s)
            end_ts = format_ass_timestamp(seg_end_s)
            
            event_start_ms = int(seg_start_s * 1000)
            
            # Group segment into 2 lines if possible
            seg_lines = []
            curr_line = []
            curr_line_chars = 0
            max_line_chars = 25
            
            for b in segment:
                if curr_line_chars + len(b['text']) > max_line_chars and curr_line:
                    seg_lines.append(curr_line)
                    curr_line = []
                    curr_line_chars = 0
                curr_line.append(b)
                curr_line_chars += len(b['text']) + 1
            if curr_line:
                seg_lines.append(curr_line)
                
            ass_text_parts = []
            for line in seg_lines:
                line_parts = []
                for b in line:
                    start_ms = int(b['offset'] / 10**6)
                    dur_ms = int(b['duration'] / 10**6)
                    rel_start = start_ms - event_start_ms
                    rel_mid = rel_start + (dur_ms // 2)
                    rel_end = rel_start + dur_ms
                    k_dur = dur_ms // 10
                    zoom_tag = f"{{\\k{k_dur}}}"
                    line_parts.append(f"{zoom_tag}{b['text']}")
                ass_text_parts.append(" ".join(line_parts))
            
            final_content = "\\N".join(ass_text_parts)
            events.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{final_content}")
            
    else:
        # Shorts Logic (Original) - Show everything at once
        start_ts = format_ass_timestamp(quote_start_s)
        end_ts = format_ass_timestamp(quote_end_s)
        event_start_ms = int(quote_start_s * 1000)
        
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
            
        ass_text_parts = []
        for line in lines:
            line_parts = []
            for boundary in line:
                start_ms = int(boundary['offset'] / 10**6)
                dur_ms = int(boundary['duration'] / 10**6)
                rel_start = start_ms - event_start_ms
                rel_mid = rel_start + (dur_ms // 2)
                rel_end = rel_start + dur_ms
                k_dur = dur_ms // 10
                zoom_tag = f"{{\\k{k_dur}}}"
                line_parts.append(f"{zoom_tag}{boundary['text']}")
            ass_text_parts.append(" ".join(line_parts))
            
        final_content = "\\N".join(ass_text_parts)
        events.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{final_content}")

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write("\n[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for event in events:
            f.write(event + "\n")

            
    logger.info(f"Karaoke ASS subtitles saved to {output_file} (duration: {quote_end_s:.2f}s)")
    return output_file

