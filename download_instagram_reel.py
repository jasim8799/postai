import instaloader
import os
import shutil
import requests

# Load session
L = instaloader.Instaloader()
L.load_session_from_file("jasim_as")  # <- Your IG login

REEL_URL = "https://www.instagram.com/reel/DKpNXOMt-TD/"

def download_reel(url):
    shortcode = url.strip("/").split("/")[-1]
    post = instaloader.Post.from_shortcode(L.context, shortcode)
    video_url = post.video_url
    print("🎬 Found video:", video_url)

    # Ensure input_movies directory exists
    os.makedirs("input_movies", exist_ok=True)

    # Download via requests
    res = requests.get(video_url, stream=True)
    file_path = f"input_movies/{shortcode}.mp4"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(res.raw, f)
    print(f"✅ Downloaded to {file_path}")

if __name__ == "__main__":
    download_reel(REEL_URL)
