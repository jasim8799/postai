import os
import json
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# This scope allows uploading video
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def authenticate_youtube():
    """
    Authenticate YouTube API using pre-generated token from environment variable.
    """
    youtube_token_json = os.environ.get("YOUTUBE_TOKEN_JSON")

    if youtube_token_json is None:
        raise RuntimeError("YOUTUBE_TOKEN_JSON environment variable not set!")

    creds_info = json.loads(youtube_token_json)

    credentials = Credentials.from_authorized_user_info(
        creds_info,
        scopes=SCOPES
    )

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials
    )

    return youtube

def post_to_youtube(youtube, video_file_path, title, description):
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": ["instagram", "reels"],
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": "public"
        }
    }

    media = MediaFileUpload(video_file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print(f"YT Uploaded: https://youtu.be/{response['id']}")
    return response["id"]

