import os
import json

INPUT_FOLDER = "input_movies"
FACEBOOK_FOLDER = "facebook_clips"
YOUTUBE_FOLDER = "youtube_clips"
PROGRESS_FILE = "upload_progress.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"fb_index": 0, "yt_index": 0, "base_name": None, "fb_total": 0, "yt_total": 0}

def save_progress(data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
