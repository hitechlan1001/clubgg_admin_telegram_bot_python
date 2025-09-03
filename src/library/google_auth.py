# src/gmail/google_auth.py
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def gmail_auth_from_env():
    """
    Build a Gmail API client using env vars:
    - GMAIL_CLIENT_ID
    - GMAIL_CLIENT_SECRET
    - GMAIL_REFRESH_TOKEN
    """
    creds_info = {
        "client_id": os.getenv("GMAIL_CLIENT_ID"),
        "client_secret": os.getenv("GMAIL_CLIENT_SECRET"),
        "refresh_token": os.getenv("GMAIL_REFRESH_TOKEN"),
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    creds = Credentials.from_authorized_user_info(creds_info)
    return build("gmail", "v1", credentials=creds)
