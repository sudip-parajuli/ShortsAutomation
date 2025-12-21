import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils import subtitle_utils

def test_subtitle_style():
    print("Testing subtitle style generation...")
    
    word_boundaries = [
        {'text': 'Success', 'offset': 0, 'duration': 500000000},
        {'text': 'is', 'offset': 600000000, 'duration': 200000000},
        {'text': 'journey', 'offset': 900000000, 'duration': 600000000}
    ]
    
    test_file = "assets/test_styles.ass"
    os.makedirs("assets", exist_ok=True)
    
    subtitle_utils.generate_karaoke_ass(word_boundaries, test_file, "Success is journey")
    
    if os.path.exists(test_file):
        with open(test_file, 'r') as f:
            content = f.read()
            print("--- ASS File Content ---")
            print(content)
            print("--- End Content ---")
            
            # Check for Yellow color &H0000FFFF
            if "&H0000FFFF" in content:
                print("✅ Style Check: Yellow color found.")
            else:
                print("❌ Style Check: Yellow color NOT found.")
                
            # Check for Alignment 5 (Center)
            if ",5," in content or ",5\n" in content:
                 print("✅ Style Check: Centered alignment found.")
            else:
                 print("❌ Style Check: Centered alignment NOT found.")
    else:
        print("❌ Style Check: File not generated.")

if __name__ == "__main__":
    test_subtitle_style()
