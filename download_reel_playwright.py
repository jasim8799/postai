import os
import shutil
import requests
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from yt_dlp import YoutubeDL

SESSION_DIR = "ig_session"
INPUT_FOLDER = "input_movies"

def download_reel_with_ytdlp(reel_url, shortcode):
    os.makedirs(INPUT_FOLDER, exist_ok=True)
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': os.path.join(INPUT_FOLDER, f'{shortcode}.%(ext)s'),
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'cookiesfrombrowser': 'chrome',  # Use cookies from Chrome browser for authentication
    }
    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([reel_url])
        video_path = os.path.join(INPUT_FOLDER, f"{shortcode}.mp4")
        return video_path
    except Exception as e:
        print(f"❌ yt-dlp download failed for {shortcode}: {e}")
        return None

async def download_best_available_reel(username, posted_shortcodes):
    os.makedirs(INPUT_FOLDER, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            # Add proxy here if needed, e.g. proxy={"server": "http://your_proxy:port"}
        )
        page = await browser.new_page()

        try:
            print("🔐 Logging in (if not already logged in)...")
            await page.goto(f"https://www.instagram.com/{username}/", wait_until="networkidle")
            # Wait for profile avatar or home icon to confirm login
            await page.wait_for_selector("svg[aria-label='Home']", timeout=10000)

            print("🔄 Scrolling multiple times to force load posts...")
            max_scrolls = 5
            for i in range(max_scrolls):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await page.wait_for_timeout(3000)
                posts = await page.query_selector_all("article a[href^='/reel/'], article a[href^='/p/']")
                if posts:
                    print(f"✅ Found {len(posts)} posts after scroll {i + 1}")
                    break
                print(f"⏳ Scroll {i + 1}: No posts found yet.")
            else:
                await page.screenshot(path=f"{username}_reels_fail.png", full_page=True)
                print(f"🚨 Timeout waiting for posts after scrolling. Screenshot saved.")
                await browser.close()
                return None, None

            all_reels = []
            for post in posts:
                href = await post.get_attribute("href")
                shortcode = href.strip("/").split("/")[-1]
                all_reels.append((shortcode, urljoin("https://www.instagram.com", href)))

            for shortcode, reel_url in all_reels:
                if shortcode in posted_shortcodes:
                    continue

                print(f"🎯 Checking reel: {reel_url}")
                await page.goto(reel_url, wait_until="domcontentloaded")
                await page.wait_for_timeout(5000)

                video_src = None
                for _ in range(6):
                    try:
                        video_tag = await page.query_selector("video")
                        if video_tag:
                            video_src = await video_tag.get_attribute("src")
                            if video_src:
                                break
                    except:
                        pass
                    await page.wait_for_timeout(1000)

                if not video_src:
                    print(f"❌ No video src found in: {reel_url}")
                    continue

                video_path = os.path.join(INPUT_FOLDER, f"{shortcode}.mp4")
                with requests.get(video_src, stream=True) as r:
                    with open(video_path, "wb") as f:
                        shutil.copyfileobj(r.raw, f)

                print(f"✅ Downloaded reel: {video_path}")
                await browser.close()
                return video_path, shortcode

            print(f"🛑 All reels already posted for {username}.")
            await browser.close()
            return None, None

        except Exception as e:
            print(f"🚨 Error: {e}")
            await page.screenshot(path=f"{username}_error.png", full_page=True)
            await browser.close()
            return None, None
