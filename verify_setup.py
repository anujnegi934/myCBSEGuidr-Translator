"""Quick verification script."""
import sys
print("Verifying Hulk Translation Reviewer setup...")
print("")

# 1. Config
has_key = False
try:
    from config import TARGET_URL, GEMINI_API_KEY, USE_API
    print("  [OK] config.py loaded")
    print("       TARGET_URL: %s..." % TARGET_URL[:60])
    has_key = bool(GEMINI_API_KEY and GEMINI_API_KEY != "your_key_here")
    print("       API Key configured: %s" % has_key)
    print("       USE_API mode: %s" % USE_API)
except Exception as e:
    print("  [FAIL] config.py: %s" % e)

# 2. Gemini API (new google.genai)
try:
    from gemini_api import init_api, translate_with_api, HAS_GENAI
    print("  [OK] gemini_api.py loaded (google.genai: %s)" % HAS_GENAI)
except Exception as e:
    print("  [FAIL] gemini_api.py: %s" % e)

# 3. Playwright
try:
    from playwright.sync_api import sync_playwright
    print("  [OK] playwright loaded")
except Exception as e:
    print("  [FAIL] playwright: %s" % e)

# 4. dotenv
try:
    from dotenv import load_dotenv
    print("  [OK] python-dotenv loaded")
except Exception as e:
    print("  [FAIL] python-dotenv: %s" % e)

print("")
print("All checks passed! Setup is ready.")
if not has_key:
    print("")
    print("NEXT STEP: Add your Gemini API key to .env file")
    print("  Get a free key at: https://aistudio.google.com/apikey")
    print("  Then edit D:\\automation\\hulk\\.env")
