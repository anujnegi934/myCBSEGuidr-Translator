import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── URLs ──────────────────────────────────────────────────────────────────────
TARGET_URL = "https://mycbseguide.com/dashboard/content-workflow/QuestionTranslationBacklogWorkflow/permissions/module/1"
GEMINI_URL = "https://gemini.google.com/app"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
USER_DATA = os.path.join(BASE_DIR, "my_chrome_profile")

os.makedirs(LOG_DIR, exist_ok=True)

# ── Gemini API ────────────────────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"
USE_API = bool(GEMINI_API_KEY)  # Use API if key is available, else fall back to web UI

# ── CKEditor Fields ──────────────────────────────────────────────────────────
# English fields that the script reads from
FIELDS = ["question", "option1", "option2", "option3", "option4", "explanation", "solution", "paragraph"]

# ── Translation Prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert English-to-Hindi translator for educational content (CBSE curriculum).

Rules:
1. Translate ALL given fields from English to Hindi.
2. Preserve ALL HTML tags exactly as they are (e.g., <p>, <strong>, <br>, <sup>, <sub>, <ul>, <li>, etc.).
3. Do NOT translate content inside <table>, <tr>, <td>, <th> tags — keep those in English.
4. Use proper Hindi grammar and vocabulary appropriate for school students.
5. Mathematical expressions, formulas, numbers, and symbols should remain unchanged.
6. Proper nouns (names of people, places, scientific terms) can be transliterated to Hindi.
7. Return ONLY a valid JSON object with the same field names as keys and Hindi translations as values.
8. No explanation, no markdown, no code fences — just the raw JSON object."""

# ── Timing ────────────────────────────────────────────────────────────────────
WAIT_AFTER_SAVE = 4        # Seconds to wait after clicking Save & Next
WAIT_FOR_PAGE_LOAD = 6     # Seconds to wait for initial page load
GEMINI_WEB_TIMEOUT = 20    # Seconds to wait for Gemini web UI response
MAX_RETRIES = 3            # Max retries for API calls
