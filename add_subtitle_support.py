# Subtitle Integration Helper

import os
import sys

def add_subtitle_support_to_composer():
    """
    This script adds subtitle filter support to composer.py
    Run this once to enable synchronized subtitles
    """
    
    composer_path = "src/video/composer.py"
    
    if not os.path.exists(composer_path):
        print("Error: composer.py not found!")
        return False
    
    with open(composer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if subtitle support already exists
    if 'subtitle_path' in content and 'subtitles' in content:
        print("Subtitle support already integrated!")
        return True
    
    # Find the drawtext section and add subtitle logic before it
    subtitle_code = '''
        # 5. Add Subtitles (synchronized with audio)
        if subtitle_path and os.path.exists(subtitle_path):
            # Use subtitles filter for word-by-word sync
            safe_subtitle_path = subtitle_path.replace('\\\\', '/').replace(':', '\\\\:')
            
            video = video.filter(
                'subtitles',
                safe_subtitle_path,
                force_style='FontName=Arial,FontSize=90,Bold=1,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=3,Shadow=2,Alignment=10,MarginV=50'
            )
        else:
            # Fallback to static text (existing code below)
            pass

        # Draw Text (Fallback)'''
    
    # Replace the "# Draw Text" comment
    content = content.replace('        # Draw Text', subtitle_code)
    
    # Write back
    with open(composer_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ Subtitle support added to composer.py")
    return True

if __name__ == "__main__":
    add_subtitle_support_to_composer()
