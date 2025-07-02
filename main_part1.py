import os
import json
import random
import shutil
from datetime import datetime
import urllib.request

from facebook_upload import post_to_facebook
from youtube_upload import post_to_youtube, authenticate_youtube
from main_startup_checks import run_startup_checks
from reupload_flagged_videos import run_reuploads_once
from copyright_manager import check_copyright_file
from copyright_flags import load_flags, save_flags, update_flag
from playwright.async_api import async_playwright

PROFILES_FILE = "user_profiles.json"

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "profiles" in data:
                data = data["profiles"]
            if isinstance(data, list):
                if all(isinstance(item, str) for item in data):
                    return [{"username": username, "posted_shortcodes": []} for username in data]
                elif all(isinstance(item, dict) for item in data):
                    for profile in data:
                        if "posted_shortcodes" not in profile:
                            profile["posted_shortcodes"] = []
                    return data
            return [data]
    return []

def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def generate_title_caption():
    titles = [
        "🔥 Must-Watch Viral clip!",
        "✨ Trending  | Don't Miss Out!",
        "🎥 Latest Trending Short Video!",
        "🚀 Instagram Viral Reel | Entertainment Shorts",
        "📸 Exclusive Insta Reel | Short Going Viral!"
    ]

    captions = [
        "Enjoy this latest trending reel! 🔥 #viral #reels #trending #shorts #instagram",
        "New viral video — watch till the end! 🤩 #InstaReels #shortvideo",
        "Trending content alert! 🌟 Don’t miss it. #entertainment #viral",
        "Another viral reel. Check it out! 💥 #trending #viralvideos",
    ]

    tags = ["viral", "reels", "instagram", "trending", "shorts", "entertainment"]

    title = random.choice(titles)
    caption = random.choice(captions)
    return title, caption, tags
