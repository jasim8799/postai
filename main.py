import os
import asyncio
from playwright.async_api import async_playwright

USERNAME = os.getenv("IG_USERNAME", "sofia9__official")
VIDEO_DIR = "input_movies"
SESSION_DIR = "ig_session"

async def download_latest_reel_playwright(username):
    os.makedirs(VIDEO_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(storage_state=None)
        page = await context.new_page()

        # Instagram URL
        url = f"https://www.instagram.com/{username}/"

        print(f"🌐 Visiting profile: {url}")
        await page.goto(url, wait_until="networkidle")

        # Find the first reel thumbnail
        reel_links = await page.locator("a[href*='/reel/']").all()
        if not reel_links:
            print("⚠️ No reels found on profile.")
            return

        first_reel_link = await reel_links[0].get_attribute("href")
        reel_url = f"https://www.instagram.com{first_reel_link}"
        print(f"🎯 Found reel URL: {reel_url}")

        # Go to the reel page
        await page.goto(reel_url, wait_until="networkidle")

        # Locate video tag and extract URL
        video_tag = page.locator("video")
        video_url = await video_tag.get_attribute("src")

        if not video_url:
            print("⚠️ Could not extract video URL.")
            return

        # Download the video file
        filename = os.path.join(VIDEO_DIR, f"{first_reel_link.strip('/').split('/')[-1]}.mp4")
        print(f"⬇️ Downloading video to {filename}")
        import requests
        response = requests.get(video_url, stream=True)
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print(f"✅ Download complete: {filename}")

        await browser.close()

async def main():
    await download_latest_reel_playwright(USERNAME)

if __name__ == "__main__":
    asyncio.run(main())
