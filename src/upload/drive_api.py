import logging
import os
from googleapiclient.http import MediaFileUpload
from src.utils import google_auth

logger = logging.getLogger(__name__)

def get_folder_id(service, folder_name):
    """
    Search for a folder by name. If not found, create it.
    """
    try:
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if files:
            return files[0]['id']
        
        # Create folder if it doesn't exist
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        file = service.files().create(body=file_metadata, fields='id').execute()
        logger.info(f"Created new Drive folder: {folder_name}")
        return file.get('id')

    except Exception as e:
        logger.error(f"Error finding/creating folder: {e}")
        return None

def upload_file(file_path, folder_name="ShortsAutomation_Uploads"):
    """
    Uploads a file to a specific Google Drive folder.
    """
    service = google_auth.get_service("drive", "v3")
    if not service:
        logger.error("Failed to connect to Google Drive.")
        return None

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    try:
        folder_id = get_folder_id(service, folder_name)
        
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)

        logger.info(f"Uploading to Drive folder '{folder_name}'...")
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        logger.info(f"✅ Drive Upload Complete! File ID: {file.get('id')}")
        return file.get('webViewLink')

    except Exception as e:
        logger.error(f"Drive upload failed: {e}")
        return None
