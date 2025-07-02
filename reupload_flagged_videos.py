import json
import os
import subprocess
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
import requests

# --------------- CONFIG ----------------

FB_ACCESS_TOKEN = "EAAOZCPZCxMxlMBOyyF4ivSjF8s7Tf2H5Wjkobii8LyPZAj2sqjWE2mH3fqpTwLU3STrHnceZBfaObguZACpV0jY2cFJdstKfrUdugPfkZAeOZBEiUDB2mjj0mJmEMAYdKYtAIg7JBCDnqd2dLZCwOVdavKmFmAe8mC6pgCisUMhWTKpcChdwZAhraZBxYnzsa2l40eLt6rDPfI"
FB_PAGE_ID = "628242183714993"

YOUTUBE_CREDENTIALS_FILE = "token.json"

# ---------------------------------------


def delete_facebook_video(fb_video_url):
    """Delete a video from Facebook given its URL."""
    try:
        video_id = fb_video_url.split("/")[-1]
        url = f"https://graph.facebook.com/v19.0/{video_id}"
        params = {"access_token": FB_ACCESS_TOKEN}
        # Check if video exists before deleting
        check_res = requests.get(url, params=params)
        if check_res.status_code != 200:
            print(f"⚠️ Facebook video {video_id} does not exist or inaccessible. Skipping delete.")
            return
        res = requests.delete(url, params=params)
        if res.status_code == 200:
            print(f"✅ Deleted Facebook video: {fb_video_url}")
        else:
            print(f"❌ Failed to delete Facebook video: {fb_video_url}. Response: {res.text}")
    except Exception as e:
        print(f"❌ Error deleting Facebook video: {e}")


def delete_youtube_video(video_id):
    """Delete a video from YouTube given its ID."""
    try:
        creds = Credentials.from_authorized_user_file(YOUTUBE_CREDENTIALS_FILE, ["https://www.googleapis.com/auth/youtube.force-ssl"])
        youtube = build("youtube", "v3", credentials=creds)
        youtube.videos().delete(id=video_id).execute()
        print(f"✅ Deleted YouTube video: {video_id}")
    except Exception as e:
        print(f"❌ Error deleting YouTube video {video_id}: {e}")


def add_new_audio(input_path, output_path, new_audio_path):
    """
    Replace audio track in a video using ffmpeg.
    new_audio_path should be the path to your new music file (mp3, etc.)
    """
    cmd = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-i", new_audio_path,
        "-c:v", "copy",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print(f"✅ Audio replaced successfully: {output_path}")
        return True
    else:
        print("❌ FFmpeg error:")
        print(result.stderr.decode())
        return False


from facebook_upload import post_to_facebook


from youtube_upload import authenticate_youtube, post_to_youtube

def upload_to_youtube(video_path, title, description="Reuploaded with new audio"):
    youtube = authenticate_youtube()
    return post_to_youtube(
        youtube,
        video_path,
        title=title,
        description=description,
        delete_file=False,
    )


import time
from datetime import datetime

def run_reuploads_once():
    try:
        with open("copyright_flags.json", "r") as f:
            data = json.load(f)
        print("✅ JSON loaded:")
        print(json.dumps(data, indent=4))
    except Exception as e:
        print("❌ Failed to load JSON:", e)
        return

    found_flagged = False
    updated = False

    for shortcode, info in list(data.items()):
        print(f"→ Checking video: {shortcode}, flagged={info.get('flagged')}")
        if info.get("flagged"):
            found_flagged = True
            print(f"⚠️ Processing flagged video: {shortcode}")

            fb_url = info["video_urls"].get("facebook")
            yt_id = info["video_urls"].get("youtube")
            video_path = info["video_path"]
            new_audio_path = info["new_audio_track"]

            # Delete from Facebook if needed
            if fb_url:
                try:
                    delete_facebook_video(fb_url)
                except Exception as e:
                    print(f"⚠️ Could not delete from Facebook: {e}. Proceeding anyway.")

            # Delete from YouTube if needed
            if yt_id:
                try:
                    delete_youtube_video(yt_id)
                except Exception as e:
                    print(f"⚠️ Could not delete from YouTube: {e}. Proceeding anyway.")

            # Check if video file exists before reupload
            if not os.path.exists(video_path):
                # fallback - look in archived_videos
                fallback_path = os.path.join("archived_videos", os.path.basename(video_path))
                if os.path.exists(fallback_path):
                    video_path = fallback_path
                else:
                    print(f"❌ File not found: {video_path}. Skipping reupload.")
                    # Clear flags to avoid repeated attempts
                    info["flagged"] = False
                    info["platforms_to_reupload"] = []
                    info["new_audio_track"] = ""
                    updated = True
                    continue

            # Create new video with new audio
            temp_new_path = f"temp_{shortcode}.mp4"
            success = add_new_audio(video_path, temp_new_path, new_audio_path)
            if not success:
                print(f"❌ Skipping reupload for {shortcode}")
                continue

            # Upload again
            new_fb_url = post_to_facebook(temp_new_path, "Enjoy this reel reuploaded with new audio!")
            new_yt_id = upload_to_youtube(temp_new_path, f"Reupload {shortcode}")

            # Update JSON
            info["video_urls"]["facebook"] = new_fb_url
            info["video_urls"]["youtube"] = new_yt_id
            info["flagged"] = False
            info["platforms_to_reupload"] = []
            info["new_audio_track"] = ""
            info["timestamp"] = datetime.now().isoformat()

# Clean up temp file
            if os.path.exists(temp_new_path):
                os.remove(temp_new_path)

            print(f"✅ Finished reprocessing video {shortcode}")
            updated = True

    if not found_flagged:
        print("✅ No flagged videos found. Nothing to process.")

    if updated:
        try:
            with open("copyright_flags.json", "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"❌ Failed to save JSON: {e}")


import time
from youtube_upload import authenticate_youtube, post_to_youtube
from facebook_upload import post_to_facebook

def load_flags():
    try:
        with open("copyright_flags.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Failed to load copyright flags: {e}")
        return {}

def save_flags(flags):
    try:
        with open("copyright_flags.json", "w") as f:
            json.dump(flags, f, indent=4)
    except Exception as e:
        print(f"❌ Failed to save copyright flags: {e}")

def process_flagged_videos(flags):
    youtube_service = authenticate_youtube()
    for shortcode, info in flags.items():
        if info.get("flagged"):
            video_path = info.get("video_path")
            new_audio_path = info.get("new_audio_track")
            if not video_path or not new_audio_path:
                print(f"❌ Missing paths for flagged video {shortcode}. Skipping.")
                continue

            temp_new_path = f"temp_{shortcode}.mp4"
            success = add_new_audio(video_path, temp_new_path, new_audio_path)
            if not success:
                print(f"❌ Failed to replace audio for {shortcode}. Skipping.")
                continue

            new_yt_id = post_to_youtube(
                youtube_service,
                temp_new_path,
                title=f"Reupload {shortcode}",
                description="Enjoy this reel reuploaded with new audio!"
            )
            new_fb_url = post_to_facebook(temp_new_path, "Enjoy this reel reuploaded with new audio!")

            # Update flags
            info["video_urls"]["facebook"] = new_fb_url
            info["video_urls"]["youtube"] = new_yt_id
            info["flagged"] = False
            info["platforms_to_reupload"] = []
            info["new_audio_track"] = ""
            info["timestamp"] = datetime.now().isoformat()

            if os.path.exists(temp_new_path):
                os.remove(temp_new_path)

            print(f"✅ Finished reprocessing flagged video {shortcode}")

    save_flags(flags)

def download_next_reel():
    # Placeholder for the existing logic to download and post new Instagram videos
    print("🎥 Downloading and posting next video...")
    # You can integrate main.py's logic here or call a function from main.py if modularized
    # For now, just simulate wait
    shortcode = None
    video_path = None
    time.sleep(1)
    return shortcode, video_path

def main_loop():
    while True:
        flags = load_flags()

        flagged_videos = [sc for sc, info in flags.items() if info.get("flagged")]

        if flagged_videos:
            print("⚠️ Found flagged videos. Processing them first...")
            process_flagged_videos(flags)
        else:
            print("✅ No flagged videos found. Proceeding to download and post next video.")
            shortcode, video_path = download_next_reel()
            if not video_path:
                print("🚫 No new reels found.")
            else:
                fb_url = post_to_facebook(video_path, caption="Trending content alert! 🌟 Don’t miss it. #entertainment #viral")
                print(f"✅ FB uploaded: {fb_url}")

                youtube_service = authenticate_youtube()
                video_id = post_to_youtube(
                    youtube_service,
                    video_path,
                    title="🔥 Epic Movie Clip",
                    description="Auto uploaded"
                )
                if video_id:
                    print(f"✅ YT Uploaded: https://youtu.be/{video_id}")
                else:
                    print("🚨 Upload to YouTube failed.")

                archive_path = f"archived_videos/{shortcode}.mp4"
                os.rename(video_path, archive_path)
                print(f"📦 Archived uploaded video to: {archive_path}")

                flags[shortcode] = {"flagged": False}
                save_flags(flags)

        print("⏳ Waiting 2 minutes...")
        time.sleep(120)

if __name__ == "__main__":
    main_loop()

