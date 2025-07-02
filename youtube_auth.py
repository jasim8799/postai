import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

TOKEN_FILE = "token.json"
CLIENT_SECRET_FILE = "client_secrets.json"
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]

def authenticate_youtube():
    creds = None

    # Check if token file exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # If no valid credentials, prompt the user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # Refresh silently if possible
            creds.refresh(Request())
        else:
            # Prompt user once
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save credentials for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    youtube = build("youtube", "v3", credentials=creds)
    return youtube
