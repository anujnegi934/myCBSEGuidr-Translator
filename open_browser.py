import os
from playwright.sync_api import sync_playwright

USER_DATA_DIR = os.path.join(os.getcwd(), "my_chrome_profile")

print("Launching browser...")
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        channel="chrome",
        headless=False,
        ignore_default_args=["--enable-automation"],
        args=[
            "--disable-blink-features=AutomationControlled",
            "--start-maximized"
        ]
    )
    
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://mycbseguide.com/dashboard/content-workflow/QuestionTranslationBacklogWorkflow/permissions/module/1")
    
    print("Please try to log in and solve the CAPTCHA.")
    input("Press Enter when done, or if it fails...")
