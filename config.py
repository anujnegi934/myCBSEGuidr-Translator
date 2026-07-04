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
FIELDS = ["question", "option1", "option2", "option3", "option4", "option5", "option6", "explanation", "solution", "paragraph"]

# ── Translation Prompt ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert English-to-Hindi translator for educational content (CBSE curriculum).

CRITICAL RULES — follow every one without exception:
1. EVERY field provided MUST be translated. NEVER return an empty field. Even if the content seems short or numeric, you MUST output a Hindi translation between the delimiters.
2. Translate ALL English words to Hindi. Do NOT leave the question or option text in English — translate it fully.
3. Preserve ALL HTML tags exactly as they are (<p>, <strong>, <br>, <sup>, <sub>, <ul>, <li>, etc.).
4. Do NOT translate content inside <table>, <tr>, <td>, <th> tags — keep those in English.
5. Use proper Hindi grammar and vocabulary appropriate for school students.
6. Mathematical expressions, numbers, and symbols (like fractions, equations) remain unchanged.
7. Proper nouns (names of people, places) should be transliterated to Hindi script.
8. [[MATH_N]] placeholders must be kept exactly as-is in their original position.
9. Input format:
---BEGIN fieldname---
English content here
---END fieldname---
10. Output format — MANDATORY — for EVERY input field:
---BEGIN fieldname---
Hindi translation here
---END fieldname---
11. No JSON, no markdown, no code fences, no explanations. Only the delimited translated text.
12. If a field has only a number (e.g., 3600), just output that same number between the delimiters."""

# ── Timing ────────────────────────────────────────────────────────────────────
WAIT_AFTER_SAVE = 4        # Seconds to wait after clicking Save & Next
WAIT_FOR_PAGE_LOAD = 6     # Seconds to wait for initial page load
GEMINI_WEB_TIMEOUT = 20    # Seconds to wait for Gemini web UI response
MAX_RETRIES = 3            # Max retries for API calls
