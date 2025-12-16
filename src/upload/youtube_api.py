import logging
import os
from src.utils import google_auth

logger = logging.getLogger(__name__)

def get_authenticated_service():
    service = google_auth.get_service("youtube", "v3")
    if not service:
        return None

    # Verify and log connected channel
    try:
        channels_response = service.channels().list(mine=True, part="snippet").execute()
        if 'items' in channels_response:
             channel_name = channels_response['items'][0]['snippet']['title']
             logger.info(f"✅ Authenticated as YouTube Channel: '{channel_name}'")
    except Exception as e:
        logger.warning(f"Could not verify channel name: {e}")

    return service

def upload_video(file_path, title, description, tags, privacy_status="private"):
    try:
        youtube = get_authenticated_service()
        if not youtube:
            return None

        body = {
            "snippet": {
                "title": title[:100],
                "description": description,
                "tags": tags,
                "categoryId": "22", # People & Blogs
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        
        logger.info(f"Uploading {file_path}...")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"Uploaded {int(status.progress() * 100)}%")
        
        logger.info(f"Upload Complete! Video ID: {response['id']}")
        return response['id']

    except Exception as e:
        logger.error(f"An error occurred during upload: {e}")
        return None
