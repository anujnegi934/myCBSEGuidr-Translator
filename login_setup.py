"""
One-time login setup for Hulk Translation Reviewer.
Opens a browser for you to log in manually. Your session is saved in the Chrome profile.

Usage:
    python login_setup.py
"""

import os
from playwright.sync_api import sync_playwright
from config import USER_DATA, TARGET_URL, GEMINI_URL

def setup_login():
    print("""
╔══════════════════════════════════════════════════════╗
║  🔑 Hulk Translation Reviewer — Login Setup         ║
╚══════════════════════════════════════════════════════╝
    """)
    print("Launching browser with persistent profile...")
    print(f"Profile location: {USER_DATA}\n")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA,
            channel="chrome",
            headless=False,
            ignore_default_args=["--enable-automation"],
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ],
            no_viewport=True,
        )

        # Tab 1: myCBSEGuide
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(TARGET_URL)
        print("Tab 1: myCBSEGuide — Please log in here")

        # Tab 2: Gemini (for web UI fallback)
        gemini_page = ctx.new_page()
        gemini_page.goto(GEMINI_URL)
        print("Tab 2: Gemini — Please log in here too (for web UI fallback)")

        page.bring_to_front()

        print("\n" + "─" * 55)
        print("  Instructions:")
        print("  1. Log in to myCBSEGuide in Tab 1")
        print("  2. Log in to Google/Gemini in Tab 2")
        print("  3. Make sure both are fully loaded")
        print("  4. Come back here and press Enter")
        print("─" * 55)

        input("\n  Press Enter when you're logged in to BOTH sites... ")

        print("\n  ✓ Session saved to Chrome profile!")
        print(f"  ✓ Profile: {USER_DATA}")
        print("\n  You can now run: python translation_reviewer.py\n")

        ctx.close()

if __name__ == "__main__":
    setup_login()
