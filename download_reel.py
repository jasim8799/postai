import os
import json
import shutil
import requests
from urllib.parse import urljoin
from playwright.async_api import async_playwright
from datetime import datetime

INPUT_FOLDER = "input_movies"
SESSION_DIR = "ig_session"
PROFILES_FILE = "user_profiles.json"

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict) and "profiles" in data:
                data = data["profiles"]
            if isinstance(data, list):
                if all(isinstance(item, str) for item in data):
                    return [{"username": u, "posted_shortcodes": []} for u in data]
                elif all(isinstance(item, dict) for item in data):
                    for profile in data:
                        if "posted_shortcodes" not in profile:
                            profile["posted_shortcodes"] = []
                    return data
            return [data]
    return []

def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

async def download_reel_by_url(page, reel_url, shortcode):
    try:
        print(f"🎯 Visiting reel page: {reel_url}")
        await page.goto(reel_url, wait_until="domcontentloaded", timeout=40000)

        # Check for playback issues
        content = await page.content()
        if "we're having trouble playing this video" in content:
            print("⚠️ Instagram can't play this reel. Skipping.")
            # await page.screenshot(path=f"{shortcode}_video_blocked.png", full_page=True)
            print(f"⚠️ Screenshot skipped for {shortcode}_video_blocked.png")
            print("❌ Could not capture video.")
            return None, None

        # Slight scroll + click
        await page.mouse.move(200, 300)
        await page.mouse.click(200, 300)
        await page.wait_for_timeout(3000)

        video_urls = []

        # Try direct <video> element
        video_tag = await page.query_selector("video")
        if video_tag:
            video_src = await video_tag.get_attribute("src")
            if video_src:
                print(f"🎥 Found video directly in <video> tag: {video_src}")
                video_urls = [video_src]

        if not video_urls:
            print("⚠️ No <video> tag found or empty. Falling back to network interception...")

            def handle_response(response):
                url = response.url
                if any(ext in url for ext in [".mp4", ".m3u8", ".ts"]):
                    if "bytestart" not in url and "dash" not in url:
                        video_urls.append(url)

            page.on("response", handle_response)

            for i in range(15):
                if video_urls:
                    break
                print(f"⏳ Waiting for video via network... ({i+1}/15)")
                await page.wait_for_timeout(1500)

        if not video_urls:
            try:
                await page.screenshot(path=f"{shortcode}_video_error.png", full_page=True)
            except Exception as e:
                print(f"⚠️ Screenshot error: {e}")
            print("❌ Could not capture video.")
            return None, None

        # Deduplicate fragments
        seen = set()
        unique_urls = []
        for url in video_urls:
            base_url = url.split("&bytestart=")[0]
            if base_url not in seen:
                seen.add(base_url)
                unique_urls.append(url)

        if not unique_urls:
            print("❌ No valid video URLs found after filtering fragments.")
            return None, None

        final_video_url = sorted(unique_urls, key=len, reverse=True)[0]
        print(f"🎞️ Final video URL: {final_video_url}")

        os.makedirs(INPUT_FOLDER, exist_ok=True)

        for candidate_url in reversed(unique_urls):
            print(f"➡️ Trying candidate URL: {candidate_url}")
            video_path = os.path.join(INPUT_FOLDER, f"{shortcode}.mp4")

            try:
                with requests.get(candidate_url, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(video_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)

                size_mb = os.path.getsize(video_path) / (1024 * 1024)
                print(f"✅ Downloaded size: {size_mb:.2f} MB")

                if size_mb >= 2:
                    print(f"✅ Accepted video: {video_path}")
                    return video_path, shortcode
                else:
                    print(f"⚠️ File too small, skipping candidate.")
                    os.remove(video_path)

            except Exception as e:
                print(f"❌ Error downloading candidate: {e}")

        print("❌ All candidate video URLs were too small or failed.")
        return None, None

    except Exception as e:
        print(f"🚨 Error downloading reel: {e}")
        return None, None

async def download_best_available_reel(username, posted_shortcodes):
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=True,
        )
        page = await browser.new_page()

        try:
            print(f"🔐 Logging in for user: {username}")
            await page.goto(f"https://www.instagram.com/{username}/reels/")
            await page.wait_for_timeout(3000)

            if "accounts/onetap" in page.url:
                print("⚠️ OneTap login detected. Bypassing...")
                not_now_button = await page.query_selector("text=Not Now")
                if not_now_button:
                    await not_now_button.click()
                    print("✅ Clicked 'Not Now'.")
                    await page.wait_for_timeout(5000)
                else:
                    await page.goto(f"https://www.instagram.com/{username}/reels/")
                    await page.wait_for_timeout(5000)

            for _ in range(3):
                await page.mouse.wheel(0, 5000)
                await page.wait_for_timeout(2000)

            for _ in range(5):
                await page.mouse.wheel(0, 3000)
                await page.wait_for_timeout(2000)

            try:
                await page.screenshot(path=f"{username}_reels_debug.png", full_page=True)
            except Exception as e:
                print(f"⚠️ Screenshot error: {e}")

            print("🔗 Collecting reel links on reels tab...")
            max_retries = 5
            all_hrefs = []
            for attempt in range(max_retries):
                try:
                    await page.wait_for_selector("a[href*='/reel/']", timeout=30000)
                    reel_links = await page.query_selector_all("a[href*='/reel/']")
                    for link in reel_links:
                        href = await link.get_attribute("href")
                        if href and "/reel/" in href:
                            all_hrefs.append(href)
                    if all_hrefs:
                        break
                except Exception as e:
                    print(f"⚠️ Attempt {attempt+1} waiting for reel links failed: {e}")
                    if attempt == max_retries - 1:
                        print("🚨 Failed to find reel links after retries.")
                        try:
                            await page.screenshot(path=f"{username}_reel_error.png", full_page=True)
                        except Exception as e:
                            print(f"⚠️ Screenshot error: {e}")
                        await browser.close()
                        return None, None
                    else:
                        await page.wait_for_timeout(5000)

            if not all_hrefs:
                print(f"❌ No reel links found for {username}.")
                await browser.close()
                return None, None

            all_hrefs_sorted = sorted(all_hrefs, key=lambda href: all_hrefs.index(href))
            unposted_href = None
            shortcode = None
            for href in all_hrefs_sorted:
                sc = href.strip("/").split("/")[-1]
                if sc not in posted_shortcodes:
                    unposted_href = href
                    shortcode = sc
                    break

            if not unposted_href:
                print(f"⚠️ All reels already posted for {username}.")
                await browser.close()
                return None, None

            reel_url = urljoin("https://www.instagram.com", unposted_href)
            print(f"⏳ Downloading reel from URL: {reel_url}")
            video_path, shortcode = await download_reel_by_url(page, reel_url, shortcode)

            await browser.close()
            return video_path, shortcode

        except Exception as e:
            print(f"🚨 Error in download_best_available_reel: {e}")
            await page.screenshot(path=f"{username}_error.png", full_page=True)
            await browser.close()
            return None, None

async def download_reel_by_user(username, posted_shortcodes=[]):
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
        )
        page = await browser.new_page()

        try:
            print(f"🔐 Logging in for user: {username}")
            await page.goto(f"https://www.instagram.com/{username}/reels/")
            await page.wait_for_timeout(3000)

            if "accounts/onetap" in page.url:
                print("⚠️ OneTap login detected. Bypassing...")
                not_now_button = await page.query_selector("text=Not Now")
                if not_now_button:
                    await not_now_button.click()
                    print("✅ Clicked 'Not Now'.")
                    await page.wait_for_timeout(5000)
                else:
                    await page.goto(f"https://www.instagram.com/{username}/reels/")
                    await page.wait_for_timeout(5000)

            for _ in range(3):
                await page.mouse.wheel(0, 5000)
                await page.wait_for_timeout(2000)

            for _ in range(5):
                await page.mouse.wheel(0, 3000)
                await page.wait_for_timeout(2000)

            try:
                await page.screenshot(path=f"{username}_reels_debug.png", full_page=True)
            except Exception as e:
                print(f"⚠️ Screenshot error: {e}")

            print("🔗 Collecting reel links on reels tab...")
            max_retries = 5
            all_hrefs = []
            for attempt in range(max_retries):
                try:
                    await page.wait_for_selector("a[href*='/reel/']", timeout=30000)
                    reel_links = await page.query_selector_all("a[href*='/reel/']")
                    for link in reel_links:
                        href = await link.get_attribute("href")
                        if href and "/reel/" in href:
                            all_hrefs.append(href)
                    if all_hrefs:
                        break
                except Exception as e:
                    print(f"⚠️ Attempt {attempt+1} waiting for reel links failed: {e}")
                    if attempt == max_retries - 1:
                        print("🚨 Failed to find reel links after retries.")
                        try:
                            await page.screenshot(path=f"{username}_reel_error.png", full_page=True)
                        except Exception as e:
                            print(f"⚠️ Screenshot error: {e}")
                        await browser.close()
                        return None, None
                    else:
                        await page.wait_for_timeout(5000)

            if not all_hrefs:
                print(f"❌ No reel links found for {username}.")
                await browser.close()
                return None, None

            all_hrefs_sorted = sorted(all_hrefs, key=lambda href: all_hrefs.index(href))
            for href in all_hrefs_sorted:
                sc = href.strip("/").split("/")[-1]
                if sc in posted_shortcodes:
                    print(f"⏭️ Already posted reel {sc}. Skipping.")
                    continue

                reel_url = urljoin("https://www.instagram.com", href)
                print(f"⏳ Downloading reel from URL: {reel_url}")
                video_path, shortcode = await download_reel_by_url(page, reel_url, sc)
                if video_path:
                    await browser.close()
                    return video_path, shortcode

            print(f"⚠️ No new reels downloaded for {username}")
            await browser.close()
            return None, None

        except Exception as e:
            print(f"🚨 Error in download_reel_by_user: {e}")
            await browser.close()
            return None, None

def save_user_profiles(path="user_profiles.json", profiles=None):
    if profiles is None:
        profiles = load_profiles()
    with open(path, "w") as f:
        json.dump(profiles, f, indent=2)
