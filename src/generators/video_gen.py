import requests
import random
import os
import logging

logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

def download_video(url, output_path):
    """Download video from URL to file."""
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download video: {e}")
        return False

def get_video_background(query, output_dir="assets/temp", duration_min=10, orientation="portrait"):
    """
    Fetches a video from Pexels API matching the query.
    Orientation: 'portrait' (9:16) or 'landscape' (16:9)
    Returns: Path to downloaded video file.
    """
    if not PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY not found. Fallback to image generation.")
        return None

    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    # Search for vertical videos
    # orientation=portrait ensures 9:16 usually, landscape ensures 16:9
    search_url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page=5&size=medium"

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        videos = data.get('videos', [])
        if not videos:
            logger.warning(f"No videos found for query: {query}")
            return None
            
        # Select a random video
        video_data = random.choice(videos)
        
        # Find best video file (closest to 1080x1920 or high quality)
        video_files = video_data.get('video_files', [])
        
        # Sort by quality (width * height) descending
        video_files.sort(key=lambda x: x['width'] * x['height'], reverse=True)
        
        best_file = None
        # Prefer HD files without watermarks (Pexels is free/clean usually)
        for vf in video_files:
            # We prefer MP4
            if vf['file_type'] == 'video/mp4':
                best_file = vf
                break
        
        if not best_file:
            best_file = video_files[0] if video_files else None
            
        if not best_file:
            return None
            
        video_url = best_file['link']
        
        os.makedirs(output_dir, exist_ok=True)
        filename = f"bg_video_{video_data['id']}.mp4"
        output_path = os.path.join(output_dir, filename)
        
        logger.info(f"Downloading background video {video_data['id']} from Pexels...")
        if download_video(video_url, output_path):
            logger.info("✅ Video background downloaded successfully.")
            return output_path
        else:
            return None

    except Exception as e:
        logger.error(f"Pexels API error: {e}")
        return None

def get_multiple_video_backgrounds(query, output_dir="assets/temp", count=3, orientation="landscape"):
    """
    Fetches multiple videos from Pexels API.
    Orientation: 'portrait' (9:16) or 'landscape' (16:9)
    Returns: List of paths to downloaded video files.
    """
    if not PEXELS_API_KEY:
        logger.warning("PEXELS_API_KEY not found. Fallback might be needed.")
        return []

    headers = {
        "Authorization": PEXELS_API_KEY
    }
    
    # per_page slightly higher to allow filtering if needed
    search_url = f"https://api.pexels.com/videos/search?query={query}&orientation={orientation}&per_page={count+5}&size=medium"

    try:
        response = requests.get(search_url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        videos = data.get('videos', [])
        if not videos:
            logger.warning(f"No videos found for query: {query}")
            return []
            
        selected_videos = random.sample(videos, min(len(videos), count))
        paths = []

        for video_data in selected_videos:
            video_files = video_data.get('video_files', [])
            video_files.sort(key=lambda x: x['width'] * x['height'], reverse=True)
            
            best_file = None
            for vf in video_files:
                if vf['file_type'] == 'video/mp4':
                    best_file = vf
                    break
            
            if not best_file and video_files:
                best_file = video_files[0]
                
            if best_file:
                os.makedirs(output_dir, exist_ok=True)
                filename = f"bg_video_{video_data['id']}.mp4"
                output_path = os.path.join(output_dir, filename)
                
                logger.info(f"Downloading background video {video_data['id']} from Pexels...")
                if download_video(best_file['link'], output_path):
                    paths.append(output_path)
        
        return paths

    except Exception as e:
        logger.error(f"Pexels API error: {e}")
        return []
