import instaloader
import os
import shutil

USERNAME = "sofia9__official"  # Replace with any IG username
MAX_REELS = 1  # Change to 3 or 5 to fetch more
LOGIN_USER = "jasim_as"  # Your login username

def download_latest_reels(username, max_reels=1):
    L = instaloader.Instaloader(
        download_pictures=False,
        download_comments=False,
        save_metadata=False,
        post_metadata_txt_pattern=""
    )
    try:
        L.load_session_from_file(LOGIN_USER)
        print(f"✅ Logged in as {LOGIN_USER} (session loaded)")
    except FileNotFoundError:
        print("❌ Session file not found. Run `instaloader --login=your_username` first.")
        return

    profile = instaloader.Profile.from_username(L.context, username)

    os.makedirs("input_movies", exist_ok=True)
    temp_dir = f"{username}_temp"
    os.makedirs(temp_dir, exist_ok=True)

    count = 0
    for post in profile.get_posts():
        if post.typename != "GraphVideo":
            continue  # skip images
        if not post.is_video:
            continue
        if "/reel/" not in post.url:
            continue  # skip non-reels

        shortcode = post.shortcode
        dest_path = f"input_movies/{shortcode}.mp4"
        if os.path.exists(dest_path):
            continue  # skip if already downloaded

        print(f"🎬 Downloading reel {shortcode}...")

        # Download using instaloader’s native logic (handles tokens/session)
        L.download_post(post, target=temp_dir)

        # Move MP4 to input_movies folder
        for file in os.listdir(temp_dir):
            if file.endswith(".mp4") and shortcode in file:
                full_src = os.path.join(temp_dir, file)
                shutil.move(full_src, dest_path)
                print(f"✅ Saved: {dest_path}")
                break

        # Clean up temp files
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))

        count += 1
        if count >= max_reels:
            break

if __name__ == "__main__":
    download_latest_reels(USERNAME, MAX_REELS)
