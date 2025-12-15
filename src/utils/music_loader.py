import os
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Direct links to strictly CC0 / Public Domain music
MUSIC_URLS = [
    # Wikimedia Commons (CC0 or PD)
    "https://upload.wikimedia.org/wikipedia/commons/e/e8/Classical_music_loop_simple.ogg", 
    # Fallback: A known reliable test file from a CDN or similar
    "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3", 
    # Archive.org CC0 example
    "https://archive.org/download/Mythium/Mythium_vbr.mp3", 
]

def ensure_music_assets(music_dir):
    if not os.path.exists(music_dir):
        os.makedirs(music_dir)
        
    files = [f for f in os.listdir(music_dir) if f.endswith('.mp3') or f.endswith('.ogg')]
    if files:
        logger.info(f"Music assets found: {len(files)} files.")
        return

    logger.info("No music found. Downloading default assets...")
    
    for i, url in enumerate(MUSIC_URLS):
        try:
            logger.info(f"Attempting download from {url}...")
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # determine extension
                ext = url.split('.')[-1]
                if len(ext) > 4: ext = "mp3" 
                
                filename = os.path.join(music_dir, f"music_loop_{i+1}.{ext}")
                with open(filename, "wb") as f:
                    f.write(response.content)
                logger.info(f"Downloaded: {filename}")
                return 
            else:
                logger.warning(f"Failed to download music from {url} (Status: {response.status_code})")
        except Exception as e:
            logger.error(f"Error downloading music: {e}")

if __name__ == "__main__":
    ensure_music_assets("assets/music")
