import os
import json
import asyncio

from download_reel import download_reel_by_user, save_profiles, load_profiles
from youtube_upload import authenticate_youtube, post_to_youtube
from facebook_upload import post_to_facebook

# Title/caption/tag rotation state
title_caption_index = 0

def get_next_title_caption_tags():
    """
    Returns next title, caption, and tags from rotating lists.
    """
    global title_caption_index

    titles = [
        "🔥 Must-Watch Viral clip!",
        "✨ Trending | Don't Miss Out!",
        "🎥 Latest Trending Short Video!",
        "🚀 Instagram Viral Reel | Entertainment Shorts",
        "📸 Exclusive Insta Reel | Short Going Viral!"
    ]

    captions = [
        "Enjoy this latest trending reel! 🔥 #viral #reels #trending #shorts #instagram",
        "New viral video — watch till the end! 🤩 #InstaReels #shortvideo",
        "Trending content alert! 🌟 Don’t miss it. #entertainment #viral",
        "Another viral reel. Check it out! 💥 #trending #viralvideos",
        "Watch and share! 🙌 #insta #viralcontent #trending"
    ]

    tags = [
        ["viral", "reels", "instagram", "trending", "shorts", "entertainment"],
        ["instareels", "shortvideo", "viralvideo", "trend", "viralcontent"],
        ["entertainment", "viral", "videooftheday", "mustwatch"],
        ["trending", "viralvideos", "hot", "explorepage"],
        ["insta", "viralcontent", "trending", "explore", "foryou"]
    ]

    idx = title_caption_index % len(titles)
    title_caption_index += 1

    return titles[idx], captions[idx], tags[idx]

def load_user_profiles(path="user_profiles.json"):
    if not os.path.exists(path):
        print(f"❌ {path} not found!")
        return []
    with open(path, "r") as f:
        return json.load(f)

async def handle_user(user_obj, youtube):
    username = user_obj["username"]
    posted_shortcodes = user_obj.get("posted_shortcodes", [])

    print(f"\n🔁 Processing user: {username}")
    try:
        video_path, shortcode = await download_reel_by_user(username, posted_shortcodes)

        if not video_path:
            print(f"⚠️ No video found for {username}")
            return False

        # Get rotating title, caption, tags
        title, caption, tags = get_next_title_caption_tags()

        # Upload to YouTube
        yt_id = post_to_youtube(
            youtube,
            video_path,
            title=title,
            description=caption
        )
        if not yt_id:
            print(f"❌ YouTube upload failed for {username}")
            return False

        # Upload to Facebook
        fb_url = post_to_facebook(
            video_path,
            message=caption
        )
        if not fb_url:
            print(f"❌ Facebook upload failed for {username}")
            return False

        # Mark this shortcode as posted
        posted_shortcodes.append(shortcode)
        user_obj["posted_shortcodes"] = posted_shortcodes

        # Save updated profiles
        try:
            profiles = load_profiles()
            save_profiles(profiles=profiles)
        except Exception as e:
            print(f"⚠️ Failed to save user profiles: {e}")

        # Clean up file
        os.remove(video_path)
        print(f"✅ Successfully posted for {username}")
        return True

    except Exception as e:
        print(f"❌ Exception for {username}: {e}")
        return False

async def main_loop():
    youtube = authenticate_youtube()
    user_list = load_user_profiles()
    if not user_list:
        print("❌ No users found in user_profiles.json")
        return

    user_index = 0
    while True:
        user_obj = user_list[user_index % len(user_list)]

        success = await handle_user(user_obj, youtube)

        if success:
            user_index += 1
            print("⏳ Sleeping 2 minutes...\n")
            await asyncio.sleep(120)
        else:
            print(f"🔁 Retrying user: {user_obj['username']} (no sleep because upload or download failed)")

if __name__ == "__main__":
    asyncio.run(main_loop())
