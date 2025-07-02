import os
import pickle
import google.auth.transport.requests
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
VIDEO_PATH = "youtube_clips/56_fb_01.mp4"
VIDEO_TITLE = "🔥 Sample Clip Upload"
VIDEO_DESCRIPTION = "🎬 Uploaded automatically via Python script. #shorts #movieclip"

def authenticate_youtube():
    """
    Authenticates and returns a YouTube API client.
    """
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_console()
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)

def upload_video(youtube, file_path, title, description):
    """
    Uploads a video file to YouTube with the given title and description.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    request_body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": "24"  # Entertainment
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(file_path, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=request_body, media_body=media)

    print(f"📤 Uploading to YouTube: {file_path}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"📈 Upload Progress: {int(status.progress() * 100)}%")

    print(f"✅ Uploaded Successfully: https://youtu.be/{response['id']}")

if __name__ == "__main__":
    youtube = authenticate_youtube()
    upload_video(youtube, VIDEO_PATH, VIDEO_TITLE, VIDEO_DESCRIPTION)
