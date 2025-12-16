import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Combined scopes for YouTube and Drive
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.file"
]

def get_authenticated_creds():
    """
    Retrieves or generates OAuth 2.0 credentials.
    Handles token file loading, refreshing, and initial OOB flow.
    """
    creds = None
    token_path = "token.pickle"
    secret_path = "client_secret.json"

    # 1. Load existing token
    if os.path.exists(token_path):
        try:
            with open(token_path, "rb") as token:
                creds = pickle.load(token)
        except Exception as e:
            logger.warning(f"Failed to load token.pickle: {e}")
            creds = None

    # 2. Check validity and refresh if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired token...")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing token: {e}")
                creds = None

        # 3. If still no valid creds, perform login flow
        if not creds:
            if not os.path.exists(secret_path):
                logger.error(f"CRITICAL: {secret_path} not found. Cannot authenticate.")
                return None
            
            logger.info("Initiating new login flow...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Authentication flow failed: {e}")
                return None

        # 4. Save the valid credentials
        try:
            with open(token_path, "wb") as token:
                pickle.dump(creds, token)
            logger.info(f"Saved new credentials to {token_path}")
        except Exception as e:
            logger.warning(f"Failed to save token.pickle: {e}")

    return creds

def get_service(api_name, api_version, creds=None):
    """
    Builds a Google API service resource.
    """
    if not creds:
        creds = get_authenticated_creds()
    
    if not creds:
        return None

    try:
        service = build(api_name, api_version, credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build service {api_name} {api_version}: {e}")
        return None
