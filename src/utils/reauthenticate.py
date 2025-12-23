import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Combined scopes for YouTube and Drive
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/drive.file"
]

def main():
    """
    Force a new authentication flow to refresh token.pickle.
    Run this script LOCALLY on your machine.
    """
    token_path = "token.pickle"
    secret_path = "client_secret.json"

    if not os.path.exists(secret_path):
        logger.error(f"CRITICAL: {secret_path} not found. Please ensure your client_secret.json is in the root directory.")
        return

    logger.info("Starting new authentication flow...")
    logger.info("A browser window should open. Please log in and authorize the application.")

    try:
        # Force a new flow
        flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the valid credentials
        with open(token_path, "wb") as token:
            pickle.dump(creds, token)
        
        logger.info(f"✅ Successfully authenticated! New credentials saved to {token_path}")
        logger.info("You can now update your GitHub Secrets with this new token.pickle (base64 encoded).")
        
    except Exception as e:
        logger.error(f"❌ Authentication flow failed: {e}")

if __name__ == "__main__":
    main()
