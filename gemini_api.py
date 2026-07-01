"""
Gemini API translation engine.
Uses google.genai to translate English fields to Hindi.
Falls back gracefully if API is unavailable.
"""

import json
import time
import re
from config import GEMINI_API_KEY, GEMINI_MODEL, SYSTEM_PROMPT, MAX_RETRIES

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False
    print("[WARN] google-genai not installed. Run: pip install google-genai")


def init_api():
    """Initialize the Gemini API client. Returns the client or None."""
    if not HAS_GENAI:
        return None
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_key_here":
        print("[WARN] No valid GEMINI_API_KEY found in .env file.")
        print("       Get a free key at: https://aistudio.google.com/apikey")
        return None

    client = genai.Client(api_key=GEMINI_API_KEY)
    print(f"  + Gemini API initialized (model: {GEMINI_MODEL})")
    return client


def translate_with_api(client, data):
    """
    Translate English fields to Hindi using Gemini API.

    Args:
        client: The genai.Client instance.
        data: Dict of {field_name: english_html_content}

    Returns:
        Dict of {field_name: hindi_html_content} or empty dict on failure.
    """
    if client is None:
        return {}

    # Filter out table-heavy fields to avoid corruption
    to_translate = {}
    for k, v in data.items():
        low = v.lower()
        if '<table' not in low and '<tr' not in low and '<td' not in low:
            to_translate[k] = v
        else:
            print(f"  - Skipping {k} (contains HTML table)")

    if not to_translate:
        print("  All fields have tables -- skipping translation")
        return {}

    # Build the prompt
    prompt = (
        "Translate the following fields from English to Hindi.\n"
        "Return ONLY a JSON object with the same keys and Hindi translations as values.\n\n"
        + json.dumps(to_translate, ensure_ascii=False, indent=2)
    )

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )

            text = response.text.strip()

            # Parse JSON response
            result = _parse_json(text)
            if result:
                translated = len(result)
                print(f"  <- API: {translated} field(s) translated")
                return result

            print(f"  [Attempt {attempt}/{MAX_RETRIES}] Could not parse JSON: {text[:120]}...")

        except Exception as e:
            print(f"  [Attempt {attempt}/{MAX_RETRIES}] API error: {e}")

        if attempt < MAX_RETRIES:
            wait = 2 ** attempt
            print(f"  Retrying in {wait}s...")
            time.sleep(wait)

    print("  x All API attempts failed")
    return {}


def _parse_json(text):
    """Try multiple strategies to extract JSON from the response."""
    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from code fence
    m = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find first JSON object
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None
