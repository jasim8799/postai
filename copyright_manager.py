import os
import json
from datetime import datetime, timedelta
from youtube_upload import authenticate_youtube, replace_audio, post_to_youtube
from facebook_upload import post_to_facebook

COPYRIGHT_FILE = "copyright_pending.json"

def add_copyright_pending_record(video_id, fb_url, yt_url, file_path, shortcode):
    data = {}
    if os.path.exists(COPYRIGHT_FILE):
        with open(COPYRIGHT_FILE, "r") as f:
            data = json.load(f)

    data[shortcode] = {
        "video_path": file_path,
        "video_urls": {
            "youtube": yt_url,
            "facebook": fb_url
        },
        "flagged": False,
        "platforms_to_reupload": [],
        "new_audio_track": None,
        "timestamp": datetime.utcnow().isoformat(),
        "reuploaded_video_id": None
    }

    with open(COPYRIGHT_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fix_copyright(video_path, new_audio, item):
    youtube = authenticate_youtube()

    # Delete videos only on platforms listed in platforms_to_reupload
    if "youtube" in item.get("platforms_to_reupload", []):
        old_yt_url = item["video_urls"].get("youtube")
        if old_yt_url:
            old_id = old_yt_url.split("/")[-1]
            try:
                youtube.videos().delete(id=old_id).execute()
                print(f"✅ Deleted old video on YouTube: {old_id}")
            except Exception as e:
                print(f"❌ Could not delete YouTube video {old_id}: {e}")

    if "facebook" in item.get("platforms_to_reupload", []):
        # Implement Facebook video deletion logic here if needed
        fb_url = item["video_urls"].get("facebook")
        if fb_url:
            try:
                import requests
                # Extract Facebook video ID from URL
                fb_video_id = fb_url.rstrip("/").split("/")[-1]
                access_token = "YOUR_FACEBOOK_ACCESS_TOKEN"  # Replace with your token or config
                delete_url = f"https://graph.facebook.com/{fb_video_id}?access_token={access_token}"
                response = requests.delete(delete_url)
                if response.status_code == 200:
                    print(f"✅ Deleted old video on Facebook: {fb_video_id}")
                else:
                    print(f"❌ Failed to delete Facebook video {fb_video_id}: {response.text}")
            except Exception as e:
                print(f"❌ Exception during Facebook video deletion: {e}")

    new_path = video_path.replace(".mp4", "_noflag.mp4")
    success = replace_audio(video_path, new_path, new_audio)
    if not success:
        print("❌ Audio replacement failed. Aborting.")
        return

    new_video_id = None
    if "youtube" in item.get("platforms_to_reupload", []):
        new_video_id = post_to_youtube(youtube, new_path, title="Re-uploaded after copyright fix")
        item["video_urls"]["youtube"] = f"https://youtu.be/{new_video_id}"

    if "facebook" in item.get("platforms_to_reupload", []):
        post_to_facebook(new_path, message="Re-uploaded with new music")

    try:
        os.remove(new_path)
        print(f"🗑️ Deleted temp file: {new_path}")
    except Exception:
        pass

    item["reuploaded_video_id"] = new_video_id
    item["flagged"] = False
    item["platforms_to_reupload"] = []
    item["new_audio_track"] = None

    print(f"✅ Re-upload complete. New YT link: https://youtu.be/{new_video_id}")

def check_copyright_file():
    if not os.path.exists(COPYRIGHT_FILE):
        return

    with open(COPYRIGHT_FILE, "r") as f:
        data = json.load(f)

    new_data = {}
    for shortcode, item in data.items():
        uploaded_at = datetime.fromisoformat(item["timestamp"])
        hours_since = (datetime.utcnow() - uploaded_at).total_seconds() / 3600

        if item.get("flagged", False):
            fix_copyright(
                item["video_path"],
                item["new_audio_track"],
                item
            )
            continue

        if hours_since >= 48:
            try:
                os.remove(item["video_path"])
                print(f"🗑️ Deleted expired local file: {item['video_path']}")
            except FileNotFoundError:
                pass
            continue

        new_data[shortcode] = item

    with open(COPYRIGHT_FILE, "w") as f:
        json.dump(new_data, f, indent=2)
