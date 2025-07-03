import os
import json
from flask import Flask, request, jsonify
from google.oauth2.credentials import Credentials
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# This scope allows uploading video
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Initialize Flask app
app = Flask(__name__)

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

    request_upload = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request_upload.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")

    print(f"YT Uploaded: https://youtu.be/{response['id']}")
    return response["id"]

@app.route("/")
def home():
    return "✅ YouTube Upload Service is running."

@app.route("/upload", methods=["POST"])
def upload_video():
    """
    POST endpoint to trigger a YouTube upload.

    Expected JSON:
    {
        "video_file_path": "...",
        "title": "...",
        "description": "..."
    }
    """
    data = request.get_json()

    video_file_path = data.get("video_file_path")
    title = data.get("title")
    description = data.get("description")

    if not video_file_path or not title or not description:
        return jsonify({"error": "Missing required fields."}), 400

    try:
        youtube = authenticate_youtube()
        video_id = post_to_youtube(youtube, video_file_path, title, description)
        return jsonify({"status": "success", "video_id": video_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # For local development
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))


