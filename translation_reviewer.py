# -*- coding: utf-8 -*-
import os; os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
"""
Hulk Translation Reviewer — Improved Edition
Automated Playwright-based translator for myCBSEGuide dashboard.

Usage:
    python translation_reviewer.py            # Uses Gemini API (default)
    python translation_reviewer.py --web-ui   # Uses Gemini web UI (fallback)
    python translation_reviewer.py --dry-run  # Preview translations without saving
"""

import os, sys, time, json, re, datetime

# ── Logger ────────────────────────────────────────────────────────────────────
class Logger:
    def __init__(self, log_path):
        self.terminal = sys.__stdout__
        self.log = open(log_path, "w", encoding="utf-8")
    def _safe(self, msg):
        """Make message safe for Windows cp1252 terminal."""
        if isinstance(msg, str):
            return msg.encode('ascii', errors='replace').decode('ascii')
        return msg
    def write(self, msg):
        try: self.terminal.write(self._safe(msg))
        except: pass
        try: self.log.write(msg); self.log.flush()
        except: pass
    def flush(self):
        try: self.terminal.flush()
        except: pass

# ── Import config ─────────────────────────────────────────────────────────────
from config import (
    TARGET_URL, GEMINI_URL, USER_DATA, FIELDS, LOG_DIR,
    WAIT_AFTER_SAVE, WAIT_FOR_PAGE_LOAD, GEMINI_WEB_TIMEOUT,
)

# Set up logging
log_file = os.path.join(LOG_DIR, f"run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
sys.stdout = Logger(log_file)
sys.stderr = Logger(log_file)

from playwright.sync_api import sync_playwright

# ── Parse CLI flags ───────────────────────────────────────────────────────────
USE_WEB_UI = "--web-ui" in sys.argv
DRY_RUN = "--dry-run" in sys.argv

# ── Extract English text from all CKEditor fields ────────────────────────────
def extract_data(page):
    """Read English content from all CKEditor instances on the page."""
    return page.evaluate("""
        (() => {
            if (typeof CKEDITOR === 'undefined') return null;
            const fields = ['question','option1','option2','option3','option4','option5','option6',
                           'explanation','solution','paragraph'];
            const out = {};
            fields.forEach(f => {
                try {
                    const inst = CKEDITOR.instances[f];
                    if (inst) {
                        const text = inst.getData().trim();
                        if (text) out[f] = text;
                    }
                } catch(_) {}
            });
            return Object.keys(out).length ? out : null;
        })()
    """)

# ── Send to Gemini Web UI and get Hindi translations ─────────────────────────
def translate_with_gemini_web(gemini_page, data):
    """Translate using gemini.google.com web interface (fallback method)."""
    to_translate = {}
    math_store = {}
    for k, v in data.items():
        low = v.lower()
        if '<table' not in low and '<tr' not in low and '<td' not in low:
            # Extract math formulas and replace with placeholders
            formulas = []
            def replace_math(m):
                idx = len(formulas)
                formulas.append(m.group(0))
                return f'[[MATH_{idx}]]'
            text = re.sub(r'<span\s+class=["\']math-tex["\']>\s*(\{tex\}.*?\{/tex\})\s*</span>', replace_math, v)
            text = re.sub(r'\{tex\}.*?\{/tex\}', replace_math, text)
            math_store[k] = formulas
            to_translate[k] = text

    if not to_translate:
        print("  All fields have tables — skipping Gemini")
        return {}

    fields_str = "\n".join(f"[FIELD: {k}]\n{v}\n[END: {k}]" for k, v in to_translate.items())
    prompt = (
        'Translate to Hindi. Return the translations wrapped in exactly the same text delimiters. Do NOT use JSON.\n'
        'Keep all [[MATH_N]] placeholders exactly where they are — do NOT translate, remove, or change them.\n\n'
        + fields_str
    )

    try:
        box = gemini_page.locator('div[contenteditable="true"]').first
        box.wait_for(state="visible", timeout=10000)

        safe = prompt.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        gemini_page.evaluate(f"""
            const b = document.querySelector('div[contenteditable="true"]');
            b.innerText = `{safe}`;
            b.dispatchEvent(new Event('input', {{bubbles:true}}));
        """)
        time.sleep(0.3)
        gemini_page.keyboard.press("Enter")
        print("  → Gemini Web: sent")

        time.sleep(3)
        last_msg = gemini_page.locator('message-content').last
        last_msg.wait_for(state="visible", timeout=GEMINI_WEB_TIMEOUT * 1000)

        # Wait for response to stabilize
        prev, stable = "", 0
        for _ in range(60):
            time.sleep(0.5)
            try:
                cur = last_msg.inner_html() if hasattr(last_msg, 'inner_html') else last_msg.inner_text()
                if not cur: continue
                # We need to extract the actual text, inner_html preserves br tags
                cur = last_msg.inner_text().strip()
                if cur and cur == prev:
                    stable += 1
                    if stable >= 3: break
                else:
                    stable, prev = 0, cur
            except: pass

        text = prev.strip()
        print(f"  ← Gemini Web: {len(text)} chars")

        # Parse delimited text from response
        result = {}
        for match in re.finditer(r'\[FIELD:\s*([a-zA-Z0-9_ ]+)\](.*?)\[END:\s*\1\]', text, flags=re.DOTALL | re.IGNORECASE):
            key = match.group(1).strip().lower().replace(' ', '')
            val = match.group(2).strip()

            # Replace [[MATH_N]] placeholders back with original math HTML
            if key in math_store:
                for idx, original in enumerate(math_store[key]):
                    if not original.startswith('<span'):
                        original = f'<span class="math-tex">{original}</span>'
                    val = val.replace(f'[[MATH_{idx}]]', original)

            # Wrap in <p> tags if not already present
            if not val.strip().startswith('<p>') and not val.strip().startswith('<ol'):
                val = f'<p>{val}</p>'
            result[key] = val

        if result:
            return result

        print(f"  Could not parse tags: {text[:100]}")
        return {}
    except Exception as e:
        print(f"  Gemini Web error: {e}")
        return {}

# ── Inject Hindi into CKEditor hindi fields ──────────────────────────────────
def inject_hindi(page, field, hindi):
    """Write Hindi translation into the corresponding _hindi CKEditor instance."""
    if not hindi: return False
    safe = hindi.replace('\\', '\\\\').replace('`', '\\`')
    try:
        page.evaluate(f"CKEDITOR.instances['{field}_hindi'].setData(`{safe}`)")
        print(f"  [OK] {field}_hindi")
        return True
    except Exception as e:
        print(f"  [FAIL] {field}_hindi: {e}")
        return False

# ── Click button by text ─────────────────────────────────────────────────────
def click_btn(page, label):
    """Click a button/link by its visible text label."""
    page.evaluate(f"""
        Array.from(document.querySelectorAll('button,ion-button,a,span'))
          .filter(e => e.offsetParent !== null && (e.innerText||'').trim().toUpperCase() === {json.dumps(label.upper())})
          .forEach(e => e.click());
    """)

# ── Fill comment box ─────────────────────────────────────────────────────────
def fill_comment(page, text):
    """Fill the comment/rejection popup text field."""
    page.evaluate(f"""
        (() => {{
            const all = Array.from(document.querySelectorAll('input,textarea,ion-input,ion-textarea'));
            const vis = all.filter(e => {{ const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; }});
            const box = vis.find(e => (e.placeholder||e.getAttribute('data-placeholder')||'').toLowerCase().includes('comment'))
                        || vis[vis.length-1];
            if (!box) return;
            box.value = {json.dumps(text)};
            ['input','change','ionInput','ionChange'].forEach(ev => box.dispatchEvent(new Event(ev, {{bubbles:true}})));
        }})()
    """)
    print(f"  comment filled")

# ── Wait for YES/OK popup ────────────────────────────────────────────────────
def wait_popup(page):
    """Wait for and click a YES/OK confirmation popup."""
    for _ in range(12):
        time.sleep(0.5)
        r = page.evaluate("""
            (() => {
                for (let el of document.querySelectorAll('button,ion-button,span,a')) {
                    const t = (el.innerText||'').trim();
                    const r = el.getBoundingClientRect();
                    if (r.width > 0 && r.height > 0) {
                        if (t === 'YES') { el.click(); return 'YES'; }
                        if (t === 'OK')  { el.click(); return 'OK'; }
                    }
                }
                return 'NONE';
            })()
        """)
        if r in ('YES', 'OK'):
            print(f"  popup: {r}")
            return r
    return 'TIMEOUT'

# ── Print banner ─────────────────────────────────────────────────────────────
def print_banner():
    mode = "WEB UI" if USE_WEB_UI else "API"
    dry = " [DRY RUN]" if DRY_RUN else ""
    print(f"""
========================================================
  Hulk Translation Reviewer -- Improved Edition
  Mode: {mode:<8s}  {dry}
  Press Ctrl+C to stop gracefully
========================================================
    """)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global USE_WEB_UI
    print_banner()
    start_time = time.time()

    # Initialize Gemini API if not using web UI
    gemini_model = None
    if not USE_WEB_UI:
        from gemini_api import init_api, translate_with_api
        gemini_model = init_api()
        if gemini_model is None:
            print("\n[!] Gemini API not available. Falling back to web UI mode.")
            print("    To use API: add your key to .env file")
            print("    Get a free key at: https://aistudio.google.com/apikey\n")
            # Fall back to web UI
            USE_WEB_UI = True

    print("Launching browser...")
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA, channel="chrome", headless=False,
            ignore_default_args=["--enable-automation"],
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
            no_viewport=True,
        )

        # Tab 1: Review site
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(TARGET_URL)
        print("Tab 1: myCBSEGuide loaded")

        # Tab 2: Gemini (only if using web UI mode)
        gemini_page = None
        if USE_WEB_UI:
            gemini_page = ctx.new_page()
            gemini_page.goto(GEMINI_URL)
            print("Tab 2: Gemini loaded — make sure you are logged in!")
            time.sleep(2)

        # Click START button if present
        review_page = page
        page.bring_to_front()
        print(f"Waiting {WAIT_FOR_PAGE_LOAD}s for page to load...")
        time.sleep(WAIT_FOR_PAGE_LOAD)

        url_before = page.url
        try:
            clicked = page.evaluate("""
                (() => {
                    const el = Array.from(document.querySelectorAll('button,ion-button,a'))
                        .find(b => (b.innerText||'').trim().toUpperCase() === 'START');
                    if (el) { el.click(); return true; }
                    return false;
                })()
            """)
            if clicked:
                print("START clicked, waiting for navigation...")
                for _ in range(20):
                    time.sleep(0.5)
                    if len(ctx.pages) > (2 if USE_WEB_UI else 1):
                        review_page = ctx.pages[-1]
                        review_page.wait_for_load_state("domcontentloaded", timeout=15000)
                        print(f"New tab opened: {review_page.url}")
                        break
                    if page.url != url_before:
                        review_page = page
                        page.wait_for_load_state("domcontentloaded", timeout=10000)
                        print(f"Navigated: {page.url}")
                        break
                else:
                    print("No navigation — staying on current page")
            else:
                print("No START button — already on questions page")
        except Exception as e:
            print(f"START error: {e}")

        last_q = None
        count = 0
        injected_count = 0
        stop_requested = False
        print("\nRunning. Press Ctrl+C to stop after current question.\n")

        while not stop_requested:
            # Wait for a NEW question to load
            data = None
            for _ in range(100):
                try:
                    d = extract_data(review_page)
                    if d:
                        q = d.get("question", "")
                        if not last_q or q != last_q:
                            data = d
                            break
                except: pass
                time.sleep(0.1)

            if not data:
                print("[WARN] No new data. Reloading...")
                try:
                    review_page.reload(timeout=15000)
                    time.sleep(4)
                    # After reload, might be back on START page
                    clicked = review_page.evaluate("""
                        (() => {
                            const el = Array.from(document.querySelectorAll('button,ion-button,a'))
                                .find(b => (b.innerText||'').trim().toUpperCase() === 'START');
                            if (el) { el.click(); return true; }
                            return false;
                        })()
                    """)
                    if clicked:
                        print("  Re-clicked START after reload")
                        time.sleep(4)
                except Exception as e:
                    print(f"  Reload error: {e}")
                last_q = None
                continue

            last_q = data.get("question", "")
            count += 1
            elapsed = time.time() - start_time
            elapsed_str = str(datetime.timedelta(seconds=int(elapsed)))
            print(f"\n{'=' * 60}")
            print(f"  Question #{count}  |  Elapsed: {elapsed_str}  |  Fields: {len(data)}")
            print(f"{'=' * 60}")

            # Show what we found
            for field, content in data.items():
                preview = content[:80].replace('\n', ' ')
                print(f"  >> {field}: {preview}...")

            # Translate
            translations = {}
            if USE_WEB_UI:
                translations = translate_with_gemini_web(gemini_page, data)
            else:
                translations = translate_with_api(gemini_model, data)

            # Inject Hindi translations
            if translations:
                print("  Injecting translations...")
                for field in data.keys():
                    if field in translations:
                        if DRY_RUN:
                            preview = translations[field][:60].replace('\n', ' ')
                            print(f"  [PREVIEW] {field}_hindi -> {preview}...")
                        else:
                            if inject_hindi(review_page, field, translations[field]):
                                injected_count += 1
            else:
                print("  [!] No translations received -- submitting as-is")

            # Save & Next (skip in dry run)
            if DRY_RUN:
                print("  [DRY RUN] Skipping Save & Next")
                print(f"\n  Would you like to continue? (Press Ctrl+C to stop)")
                try:
                    time.sleep(3)
                except KeyboardInterrupt:
                    stop_requested = True
                    continue
            else:
                # Add comment for rejected questions
                try:
                    is_rejected = review_page.evaluate("() => document.body.innerText.includes('Rejected by:')")
                    if is_rejected:
                        print("  [!] Rejected question detected. Adding 'done' comment.")
                        fill_comment(review_page, "done")
                except Exception as e:
                    print(f"  [WARN] Failed to check for rejection or fill comment: {e}")

                click_btn(review_page, "SAVE & NEXT")
                wait_popup(review_page)
                print(f"  Waiting {WAIT_AFTER_SAVE}s for next question...")
                time.sleep(WAIT_AFTER_SAVE)

        # Summary
        elapsed = time.time() - start_time
        elapsed_str = str(datetime.timedelta(seconds=int(elapsed)))
        print(f"\n{'=' * 60}")
        print(f"  Session Complete!")
        print(f"  Questions processed: {count}")
        print(f"  Fields injected:     {injected_count}")
        print(f"  Total time:          {elapsed_str}")
        print(f"  Log saved to:        {log_file}")
        print(f"{'=' * 60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  [STOP] Stopped by user. Finishing up...")
    except Exception as e:
        print(f"\n  [FATAL] {e}")
        import traceback; traceback.print_exc()
