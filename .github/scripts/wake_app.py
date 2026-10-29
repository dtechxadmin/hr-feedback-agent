"""Wake a Streamlit Community Cloud app and keep it awake.

1. Opens the app in headless Chromium.
2. If the "gone to sleep" page shows, clicks "Yes, get this app back up!".
3. Waits until the real app UI has rendered (positive check, not just
   "no button found"), then stays connected for a while so the visit
   registers as traffic.
4. Fails the run (red X + GitHub email) if it can't confirm the app is up.

Results are written as GitHub annotations (::notice / ::error) so they show
on the run summary page.
"""
import os
import re
import sys
import time

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL", "https://hr-feedback-agent.streamlit.app/")
SLEEP_TEXT = re.compile(r"gone to sleep|get this app back up", re.I)
WAKE_BUTTON = re.compile(r"get this app back up", re.I)
BOOT_TEXT = re.compile(r"in the oven|waking up|spinning up|starting up", re.I)
APP_SELECTOR = '[data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stMain"]'

FIRST_LOAD_S = 60      # time to decide which page we're on
WAKE_TIMEOUT_S = 420   # cold boots can take several minutes
STAY_CONNECTED_S = 60  # keep the session open so it counts as traffic


def note(msg):
    print(f"::notice title=Wake Streamlit::{msg}", flush=True)


def fail(msg):
    print(f"::error title=Wake Streamlit::{msg}", flush=True)


def frame_text(frame):
    try:
        return frame.locator("body").inner_text(timeout=2_000)
    except Exception:
        return ""


def state(page):
    """Return 'asleep', 'app', 'booting' or 'unknown'."""
    texts = [frame_text(f) for f in page.frames]
    if any(SLEEP_TEXT.search(t) for t in texts):
        return "asleep"
    for f in page.frames:
        try:
            if f.locator(APP_SELECTOR).count() > 0:
                return "app"
        except Exception:
            pass
    if any(BOOT_TEXT.search(t) for t in texts):
        return "booting"
    return "unknown"


def click_wake(page):
    for f in page.frames:
        for loc in (f.get_by_role("button", name=WAKE_BUTTON), f.get_by_text(WAKE_BUTTON)):
            try:
                if loc.count() > 0:
                    loc.first.click(timeout=10_000)
                    return True
            except Exception:
                continue
    return False


def diagnostics(page):
    frames = ", ".join(f.url[:80] for f in page.frames)
    snippet = " | ".join(t.strip().replace("\n", " ")[:150] for t in (frame_text(f) for f in page.frames) if t.strip())
    return f"title={page.title()!r}; frames=[{frames}]; text={snippet[:400]!r}"


def wait_for(page, wanted, timeout_s, label):
    deadline = time.time() + timeout_s
    s = state(page)
    while time.time() < deadline:
        s = state(page)
        if s in wanted:
            return s
        print(f"{label}: state={s}", flush=True)
        page.wait_for_timeout(10_000)
    return s


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1280, "height": 900},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"),
        )
        try:
            page.goto(APP_URL, wait_until="domcontentloaded", timeout=90_000)
            initial = wait_for(page, {"asleep", "app"}, FIRST_LOAD_S, "Initial load")

            if initial == "asleep":
                if not click_wake(page):
                    page.screenshot(path="result.png", full_page=True)
                    fail(f"App is asleep but the wake-up button could not be clicked. {diagnostics(page)}")
                    return 1
                print("Clicked wake-up button; waiting for app to boot...", flush=True)
                page.wait_for_timeout(5_000)
                final = wait_for(page, {"app"}, WAKE_TIMEOUT_S, "Waking")
                if final != "app":
                    # Sometimes the wrapper needs a reload once the container is up.
                    page.reload(wait_until="domcontentloaded", timeout=90_000)
                    final = wait_for(page, {"app"}, 90, "After reload")
                if final != "app":
                    page.screenshot(path="result.png", full_page=True)
                    fail(f"Clicked wake-up but app did not come up within {WAKE_TIMEOUT_S}s (state={final}). {diagnostics(page)}")
                    return 1
                outcome = "App WAS ASLEEP -> clicked wake-up -> app is now up"
            elif initial == "app":
                outcome = "App was already awake"
            else:
                page.screenshot(path="result.png", full_page=True)
                fail(f"Could not recognise the page (state={initial}). {diagnostics(page)}")
                return 1

            page.wait_for_timeout(STAY_CONNECTED_S * 1000)
            page.screenshot(path="result.png", full_page=True)
            note(f"{outcome}; stayed connected {STAY_CONNECTED_S}s.")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
