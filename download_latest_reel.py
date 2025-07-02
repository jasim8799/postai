import asyncio
from playwright.async_api import async_playwright
import urllib.request

USERNAME = "jasim_as"
PASSWORD = "movieforyou"
TARGET_USERNAME = "sofia9__official"

async def download_latest_video():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔐 Logging in...")
        await page.goto("https://www.instagram.com/accounts/login/")
        await page.fill("input[name='username']", USERNAME)
        await page.fill("input[name='password']", PASSWORD)
        await page.press("input[name='password']", "Enter")

        # ✅ Wait until Instagram navbar appears (instead of 'networkidle')
        try:
            await page.wait_for_selector("nav", timeout=20000)
        except:
            print("⚠️ Login may have succeeded but navbar not found — continuing anyway.")
        print("✅ Login successful.")

        print(f"🌐 Visiting Reels tab: https://www.instagram.com/{TARGET_USERNAME}/reels/")
        await page.goto(f"https://www.instagram.com/{TARGET_USERNAME}/reels/")
        await page.wait_for_timeout(5000)

        print("⬇️ Scrolling to load reels...")
        await page.mouse.wheel(0, 5000)
        await page.wait_for_timeout(3000)

        print("🖼️ Finding reel links...")
        reels = await page.query_selector_all("a[href*='/reel/']")
        if not reels:
            print("❌ No reels found.")
            return

        latest_reel_href = await reels[0].get_attribute("href")
        latest_reel_url = f"https://www.instagram.com{latest_reel_href}"
        print(f"✅ Clicking latest reel: {latest_reel_url}")

        video_url = None

        async def handle_route(route, request):
            nonlocal video_url
            if ".mp4" in request.url:
                video_url = request.url
            await route.continue_()

        await context.route("**/*", handle_route)

        await page.goto(latest_reel_url, wait_until="load")
        await page.wait_for_timeout(5000)

        if video_url:
            print(f"🎬 Found video: {video_url}")
            file_name = "downloaded_reel.mp4"
            urllib.request.urlretrieve(video_url, file_name)
            print(f"✅ Video downloaded: {file_name}")
        else:
            print("❌ Failed to find video.")

        await browser.close()

asyncio.run(download_latest_video())
