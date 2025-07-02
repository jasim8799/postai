import os
import time
import json
import requests

FB_PAGE_ID = "628242183714993"
FB_ACCESS_TOKEN = "EAAOZCPZCxMxlMBOyyF4ivSjF8s7Tf2H5Wjkobii8LyPZAj2sqjWE2mH3fqpTwLU3STrHnceZBfaObguZACpV0jY2cFJdstKfrUdugPfkZAeOZBEiUDB2mjj0mJmEMAYdKYtAIg7JBCDnqd2dLZCwOVdavKmFmAe8mC6pgCisUMhWTKpcChdwZAhraZBxYnzsa2l40eLt6rDPfI"  # Replace with valid token
VIDEO_PATH = "facebook_clips/90.mp4"
VIDEO_MESSAGE ="🎬 Watch this amazing clip! #movie #reel #shorts"

CHUNK_SIZE = 1024 * 1024 * 4  # 4MB


def start_upload_session(file_size):
    url = f"https://graph-video.facebook.com/v18.0/{FB_PAGE_ID}/videos"
    params = {
        "upload_phase": "start",
        "access_token": FB_ACCESS_TOKEN,
        "file_size": file_size
    }
    res = requests.post(url, data=params)
    print("📡 Raw Response (start_upload_session):", res.text)
    if res.status_code != 200:
        raise Exception(f"❌ HTTP Error {res.status_code}: {res.text}")
    try:
        res_json = res.json()
    except Exception as e:
        print(f"❌ JSON Parse Error (start_upload_session): {e}")
        raise
    if "upload_session_id" not in res_json:
        raise Exception(f"Start session failed: {res_json}")
    return res_json["upload_session_id"], res_json["video_id"]


def upload_chunks(video_path, session_id):
    url = f"https://graph-video.facebook.com/v18.0/{FB_PAGE_ID}/videos"
    start_offset = "0"
    with open(video_path, "rb") as f:
        while True:
            f.seek(int(start_offset))
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            params = {
                "upload_phase": "transfer",
                "upload_session_id": session_id,
                "start_offset": start_offset,
                "access_token": FB_ACCESS_TOKEN
            }
            files = {
                "video_file_chunk": (os.path.basename(video_path), chunk, "video/mp4")
            }
            res = requests.post(url, data=params, files=files)
            print("📡 Raw Response (upload_chunks):", res.text)
            if res.status_code != 200:
                raise Exception(f"❌ HTTP Error {res.status_code}: {res.text}")
            try:
                res_json = res.json()
            except Exception as e:
                print(f"❌ JSON Parse Error (upload_chunks): {e}")
                raise
            if "start_offset" not in res_json:
                raise Exception(f"Chunk upload failed: {res_json}")
            start_offset = res_json["start_offset"]
            if start_offset == res_json["end_offset"]:
                break


def finish_upload(session_id, title, description):
    url = f"https://graph-video.facebook.com/v18.0/{FB_PAGE_ID}/videos"
    params = {
        "upload_phase": "finish",
        "upload_session_id": session_id,
        "access_token": FB_ACCESS_TOKEN,
        "title": title,
        "description": description,
        "published": "true",
        #"privacy[value]": "EVERYONE"
    }
    res = requests.post(url, data=params)
    print("📡 Raw Response (finish_upload):", res.text)
    if res.status_code != 200:
        raise Exception(f"❌ HTTP Error {res.status_code}: {res.text}")
    try:
        res_json = res.json()
    except Exception as e:
        print(f"❌ JSON Parse Error (finish_upload): {e}")
        raise
    if not res_json.get("success"):
        raise Exception(f"Finish failed: {res_json}")
    return res_json


def wait_until_ready(video_id, timeout=300):
    url = f"https://graph.facebook.com/v18.0/{video_id}"
    params = {
        "fields": "status,privacy,published",
        "access_token": FB_ACCESS_TOKEN
    }
    for _ in range(timeout // 10):
        res = requests.get(url, params=params)
        print("📡 Raw Response (wait_until_ready):", res.text)
        if res.status_code != 200:
            print(f"❌ HTTP Error {res.status_code}: {res.text}")
            return False
        try:
            res_json = res.json()
        except Exception as e:
            print(f"❌ JSON Parse Error (wait_until_ready): {e}")
            return False
        status = res_json.get("status", {}).get("video_status")
        if status == "ready" and res_json.get("published"):
            print("✅ Video is ready and public.")
            return True
        print(f"⏳ Waiting... (status={status})")
        time.sleep(10)
    print("⚠️ Timed out waiting for video readiness.")
    return False


def upload_video(video_path, message):
    if not os.path.exists(video_path):
        print("❌ Video file not found.")
        return

    print(f"\n🚀 Uploading {video_path}")
    file_size = os.path.getsize(video_path)
    file_name = os.path.basename(video_path)

    try:
        session_id, video_id = start_upload_session(file_size)
        upload_chunks(video_path, session_id)
        finish_upload(session_id, file_name, message)
        if wait_until_ready(video_id):
            os.remove(video_path)
            print("🗑️ Deleted local file after upload.")
    except Exception as e:
        print(f"❌ Upload failed: {e}")


if __name__ == "__main__":
    upload_video(VIDEO_PATH, VIDEO_MESSAGE)
