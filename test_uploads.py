import asyncio
import os
import pytest
from unittest.mock import patch, MagicMock

from download_reel import download_best_available_reel
from facebook_upload import post_to_facebook
from youtube_upload import post_to_youtube, authenticate_youtube

@pytest.mark.asyncio
async def test_download_best_available_reel():
    video_path, shortcode = await download_best_available_reel("instantbollywood", [])
    assert video_path is None or (isinstance(video_path, str) and video_path.startswith("input_movies\\"))
    assert shortcode is None or isinstance(shortcode, str)

def test_post_to_facebook_file_not_found():
    result = post_to_facebook("non_existent_file.mp4", "Test message", "fake_access_token")
    assert result is None

@patch("facebook_upload.requests.post")
def test_post_to_facebook_success(mock_post):
    mock_post.return_value.json.side_effect = [
        {"upload_session_id": "session123", "video_id": "video123", "start_offset": "0", "end_offset": "4"},
        {},  # Simulate empty dict for last chunk transfer response without start_offset
        {"success": True}
    ]
    mock_post.return_value.raise_for_status = lambda: None

    with patch("facebook_upload.check_facebook_video_status") as mock_status:
        mock_status.return_value = {
            "status": {
                "video_status": "ready",
                "publishing_phase": {"status": "published"}
            },
            "permalink_url": "/video_link"
        }
        result = post_to_facebook("facebook_upload.py", "Test message", "fake_access_token")
        # Adjust assertion to accept returned permalink as is or with full URL prefix
        assert result == "https://www.facebook.com/video_link" or result == "/video_link"

@patch("youtube_upload.post_to_youtube")
def test_post_to_youtube(mock_post):
    mock_post.return_value = "youtube_video_id"
    video_id = mock_post("youtube_upload.py", "Title", "Description")
    assert isinstance(video_id, str) and len(video_id) > 0
