import instaloader
import os
import shutil

USERNAME = "sofia9__official"
MAX_REELS = 1
DEST_FOLDER = "input_movies"

# Create the destination folder if it doesn't exist
os.makedirs(DEST_FOLDER, exist_ok=True)

# Initialize instaloader
L = instaloader.Instaloader(download_videos=True, download_video_thumbnails=False, save_metadata=False)

# ✅ Load session from file
L.load_session_from_file("jasim_as")

# Get posts from the user
profile = instaloader.Profile.from_username(L.context, USERNAME)
reels_downloaded = 0

print(f"🎯 Fetching reels from: {USERNAME}")

for post in profile.get_posts():
    if post.typename == "GraphVideo" and post.is_video and post.video_url:
        if reels_downloaded >= MAX_REELS:
            break

        print(f"🎥 Downloading reel: {post.shortcode}")

        # Download to temp folder
        temp_dir = f"temp_reel_{post.shortcode}"
        L.download_post(post, target=temp_dir)

        # Move only the .mp4 file to input_movies/
        for file in os.listdir(temp_dir):
            if file.endswith(".mp4"):
                src = os.path.join(temp_dir, file)
                dst = os.path.join(DEST_FOLDER, f"{USERNAME}_reel_{post.shortcode}.mp4")
                shutil.move(src, dst)
                print(f"✅ Saved reel to: {dst}")
                reels_downloaded += 1
                break

        # Cleanup
        shutil.rmtree(temp_dir)

if reels_downloaded == 0:
    print("❌ No reels found.")
else:
    print(f"🎉 Done! {reels_downloaded} reel(s) ready for upload.")
