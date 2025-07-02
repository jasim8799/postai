import argparse
import os
from youtube_upload import (
    authenticate_youtube,
    replace_audio,
    post_to_youtube
)
from facebook_upload import post_to_facebook

def fix_copyright(video_path, new_audio, delete_youtube_video_id=None):
    youtube = authenticate_youtube()

    # Replace audio
    new_video_path = video_path.replace(".mp4", "_noflag.mp4")
    success = replace_audio(video_path, new_video_path, new_audio)

    if not success:
        print("❌ Audio replacement failed. Aborting.")
        return

    # Delete original video if specified
    if delete_youtube_video_id:
        try:
            youtube.videos().delete(id=delete_youtube_video_id).execute()
            print(f"✅ Deleted original video from YouTube: {delete_youtube_video_id}")
        except Exception as e:
            print(f"❌ Failed to delete video {delete_youtube_video_id}: {e}")

    # Upload to YouTube
    new_video_id = post_to_youtube(
        youtube,
        new_video_path,
        title="🔥 Re-uploaded after audio replacement",
        description="Fixed copyright issues"
    )

    # Upload to Facebook
    post_to_facebook(new_video_path, message="Reel reposted with royalty-free music!")

    # Delete temp video
    try:
        os.remove(new_video_path)
        print(f"🗑️ Deleted temp file: {new_video_path}")
    except Exception as e:
        print(f"❌ Failed to delete temp file: {e}")

    print(f"✅ New video ID on YouTube: {new_video_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True, help="Path to original video file")
    parser.add_argument("--new_audio", required=True, help="Path to royalty-free audio file (e.g. audio_library/happy.mp3)")
    parser.add_argument("--delete_youtube_video_id", help="Optional YouTube video ID to delete before re-upload")
    args = parser.parse_args()

    fix_copyright(args.video_path, args.new_audio, args.delete_youtube_video_id)
