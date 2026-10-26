"""Wake a Streamlit Community Cloud app if it has gone to sleep.

Opens the app in headless Chromium, clicks "Yes, get this app back up!" if the
sleep page is showing, and waits for the app to come back. Exits non-zero on
failure so GitHub Actions marks the run red and emails you.
"""
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL", "https://hr-feedback-agent.streamlit.app/")
WAKE_TEXT = re.compile(r"get this app back up", re.I)
WAKE_TIMEOUT_S = 240


def find_wake_button(page):
    """Look for the wake-up button in the page and any iframes."""
    for frame in page.frames:
        try:
            btn = frame.get_by_role("button", name=WAKE_TEXT)
            if btn.count() > 0 and btn.first.is_visible():
                return btn.first
        except Exception:
            continue
    return None


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        print(f"Opening {APP_URL}")
        page.goto(APP_URL, wait_until="domcontentloaded", timeout=90_000)
        page.wait_for_timeout(10_000)  # let the sleep page / app shell render

        btn = find_wake_button(page)
        if btn is None:
            print("App is awake (no wake-up button). Visit counted as traffic.")
            page.screenshot(path="result.png", full_page=True)
            browser.close()
            return 0

        print("App is asleep. Clicking the wake-up button...")
        btn.click()

        deadline = time.time() + WAKE_TIMEOUT_S
        while time.time() < deadline:
            page.wait_for_timeout(15_000)
            if find_wake_button(page) is None:
                page.wait_for_timeout(15_000)  # give the app a moment to boot
                print("Wake-up button gone; app is starting/awake.")
                page.screenshot(path="result.png", full_page=True)
                browser.close()
                return 0
            print("Still waking...")

        print(f"App did not wake within {WAKE_TIMEOUT_S}s.", file=sys.stderr)
        page.screenshot(path="result.png", full_page=True)
        browser.close()
        return 1


if __name__ == "__main__":
    sys.exit(main())
