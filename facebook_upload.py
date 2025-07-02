import os
import time
import requests

from utils import load_progress, save_progress, FACEBOOK_FOLDER

FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "628242183714993")
FB_ACCESS_TOKEN = os.environ.get("FB_ACCESS_TOKEN", "EAAOZCPZCxMxlMBOyyF4ivSjF8s7Tf2H5Wjkobii8LyPZAj2sqjWE2mH3fqpTwLU3STrHnceZBfaObguZACpV0jY2cFJdstKfrUdugPfkZAeOZBEiUDB2mjj0mJmEMAYdKYtAIg7JBCDnqd2dLZCwOVdavKmFmAe8mC6pgCisUMhWTKpcChdwZAhraZBxYnzsa2l40eLt6rDPfI")

CHUNK_SIZE = 1024 * 1024 * 4

def check_facebook_video_status(video_id):
    url = f"https://graph.facebook.com/v18.0/{video_id}"
    params = {
        "fields": "published,status,permalink_url",
        "access_token": FB_ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    res_json = res.json()
    print(f"🔍 FB Video Status: {res_json}")
    return res_json

def post_to_facebook(video_path, message=""):
    print(f"📤 Starting Facebook upload: {video_path} - {message}")
    if not os.path.exists(video_path):
        print("❌ Video file not found.")
        return None

    file_size = os.path.getsize(video_path)
    file_name = os.path.basename(video_path)

    try:
        # Start session
        start_url = f"https://graph-video.facebook.com/v18.0/{FB_PAGE_ID}/videos"
        start_params = {
            "upload_phase": "start",
            "access_token": FB_ACCESS_TOKEN,
            "file_size": file_size
        }
        start_res = requests.post(start_url, data=start_params)
        print("📡 Raw Response (start_upload_session):", start_res.text)

        start_res.raise_for_status()

        start_json = start_res.json()
        session_id = start_json["upload_session_id"]
        video_id = start_json["video_id"]
        start_offset = start_json["start_offset"]
        end_offset = start_json["end_offset"]

        # Upload chunks
        with open(video_path, "rb") as f:
            while True:
                f.seek(int(start_offset))
                chunk = f.read(int(end_offset) - int(start_offset))
                upload_params = {
                    "access_token": FB_ACCESS_TOKEN,
                    "upload_phase": "transfer",
                    "upload_session_id": session_id,
                    "start_offset": start_offset
                }
                files = {
                    "video_file_chunk": chunk
                }
                transfer_res = requests.post(start_url, data=upload_params, files=files)
                transfer_res.raise_for_status()
                transfer_json = transfer_res.json()

                start_offset = transfer_json["start_offset"]
                end_offset = transfer_json["end_offset"]
                print(f"📡 Raw Response (upload_chunks): {transfer_json}")

                if start_offset == end_offset:
                    print("✅ All chunks uploaded.")
                    break

        # Finish upload
        finish_params = {
            "access_token": FB_ACCESS_TOKEN,
            "upload_phase": "finish",
            "upload_session_id": session_id,
            "description": message,
            "title": file_name,
            "published": "true"
        }
        finish_res = requests.post(start_url, data=finish_params)
        print(f"📡 Raw Response (finish_upload): {finish_res.text}")

        finish_res.raise_for_status()
        finish_json = finish_res.json()

        if finish_json.get("success") is True:
            print(f"✅ Upload finished. Video ID: {video_id}")
        else:
            print("❌ Upload failed at finish step.")
            return None

        # Poll until video is fully processed
        while True:
            status_info = check_facebook_video_status(video_id)
            video_status = status_info.get("status", {}).get("video_status")

            if video_status == "ready":
                permalink = status_info.get("permalink_url")
                fb_url = f"https://www.facebook.com{permalink}" if permalink.startswith("/") else permalink
                print(f"✅ Video is ready and public: {fb_url}")
                return fb_url
            else:
                print(f"⏳ Waiting... (status={video_status})")
                time.sleep(5)

    except Exception as e:
        print(f"❌ Upload Exception: {e}")
        return None

def schedule_facebook():
    progress = load_progress()
    print(f"🔍 FB Progress: {progress}")
    base_name = progress["base_name"]
    fb_index = progress["fb_index"]
    fb_total = progress["fb_total"]

    if fb_index >= fb_total:
        print("✅ All Facebook clips have been uploaded.")
        return

    filename = f"{base_name}_fb_{fb_index+1:02d}.mp4"
    video_path = os.path.join(FACEBOOK_FOLDER, filename)

    if os.path.exists(video_path):
        print(f"🚀 Uploading FB clip: {filename}")
        post_to_facebook(video_path, message=f"Reel from {base_name}")
        progress["fb_index"] += 1
        save_progress(progress)
    else:
        print(f"❌ FB clip not found: {filename}")

if __name__ == "__main__":
    schedule_facebook()
