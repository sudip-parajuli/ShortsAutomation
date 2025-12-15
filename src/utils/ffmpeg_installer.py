import os
import zipfile
import requests
import shutil
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FFmpegInstaller")

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
INSTALL_DIR = os.path.join(os.getcwd(), "bin")

def install_ffmpeg():
    if os.path.exists(os.path.join(INSTALL_DIR, "ffmpeg.exe")):
        logger.info("FFmpeg already exists in bin/")
        return os.path.join(INSTALL_DIR, "ffmpeg.exe")

    logger.info("Downloading FFmpeg...")
    try:
        r = requests.get(FFMPEG_URL, stream=True)
        r.raise_for_status()
        
        zip_path = "ffmpeg.zip"
        with open(zip_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Info: the zip contains a root folder like 'ffmpeg-6.0-essentials_build/bin/ffmpeg.exe'
            # We want to extract just the bin contents to our bin/
            for file in zip_ref.namelist():
                if file.endswith("ffmpeg.exe"):
                    # Extract to temp
                    zip_ref.extract(file, ".")
                    # Move to bin
                    os.makedirs(INSTALL_DIR, exist_ok=True)
                    shutil.move(file, os.path.join(INSTALL_DIR, "ffmpeg.exe"))
                    logger.info("FFmpeg moved to bin/")
                    break
                    
        # Cleanup
        os.remove(zip_path)
        # Cleanup extracted folder (the root one left behind if any)
        # simplistic cleanup
        
        return os.path.join(INSTALL_DIR, "ffmpeg.exe")

    except Exception as e:
        logger.error(f"Failed to install FFmpeg: {e}")
        return None

if __name__ == "__main__":
    install_ffmpeg()
