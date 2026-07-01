# Hulk Translation Reviewer 🤖🚀

An automated Playwright-based script designed to seamlessly translate and submit educational questions from English to Hindi.

## ✨ Features
- **Browser Automation:** Uses Playwright to drive Google Chrome automatically.
- **Dual Tab Architecture:** Operates with two tabs — one for the question review site and one for `gemini.google.com`.
- **Smart Data Extraction:** Automatically extracts English content from multiple CKEditor fields (question, options, explanation).
- **Intelligent Translation:** Bypasses table destruction by safely skipping HTML tables, and feeds exact content into the Gemini web interface.
- **Auto-Injection & Submission:** Injects the translated Hindi JSON directly back into the `_hindi` CKEditor boxes and clicks "SAVE & NEXT".
- **Rejection Recovery:** Automatically detects rejected questions, translates them, and fills out the required comment popup before resubmitting.

## 🛠️ Prerequisites
- Python 3.10+
- Google Chrome
- You must be logged into your Google Account on the `gemini.google.com` tab when the script runs.

## 🚀 Setup & Execution

1. **Install dependencies:**
   ```bash
   pip install playwright
   playwright install chromium
   ```

2. **Run the script:**
   Run the batch file `Run Translation Automation.bat` from your Desktop, or run directly via Python:
   ```bash
   python translation_reviewer.py
   ```

3. **How it works on startup:**
   - The script opens **Tab 1** (Review site) and **Tab 2** (Gemini).
   - It will pause for a few seconds. **Ensure you are logged into Gemini** in Tab 2.
   - It automatically clicks the `START` button on the review site and loops infinitely through the questions.

## ⚠️ Notes
- Do not minimize the Chrome window. The Gemini web interface requires the tab to be active/visible to process keyboard events properly.
- The script uses a persistent local Chrome profile (`my_chrome_profile/`) to remember your logins, so you only have to log in once.
