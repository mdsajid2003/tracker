# tracker_playwright.py
import os
import json
import time
import smtplib
from email.message import EmailMessage
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# ---------- Config / env ----------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")  # fallback recipient if per-product not provided

# Debug option: set DEBUG_SAVE_HTML = "1" in secrets to save HTML when parsing fails
DEBUG_SAVE_HTML = os.getenv("DEBUG_SAVE_HTML", "0") == "1"

# ---------- Helpers ----------
def send_email(subject: str, body: str, to_email: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not (SMTP_USER and SMTP_PASS and to_email):
        print("⚠️ Email not sent: SMTP_USER, SMTP_PASS, or recipient missing")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print(f"📧 Email sent to {to_email} — {subject}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False

def parse_price_text(text: str):
    """Extract integer price from a text like '₹ 12,999' -> 12999"""
    if not text:
        return None
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else None

def extract_title_and_price_from_page(page):
    """
    Try several selectors and fallbacks to get title & price from Flipkart page.
    Returns (title:str, price:int|None).
    """
    selectors_title = ["span.B_NuCI", "span.yhB1nd", "h1", "title"]
    selectors_price = ["div._30jeq3._16Jk6d", "div._30jeq3", "span._30jeq3._16Jk6d", "span._30jeq3"]

    title = None
    price_text = None

    for sel in selectors_title:
        try:
            handle = page.locator(sel)
            if handle.count() > 0:
                txt = handle.first.inner_text(timeout=2000).strip()
                if txt:
                    title = txt
                    break
        except Exception:
            continue

    for sel in selectors_price:
        try:
            handle = page.locator(sel)
            if handle.count() > 0:
                txt = handle.first.inner_text(timeout=2000).strip()
                if txt:
                    price_text = txt
                    break
        except Exception:
            continue

    # fallback: search page content for '₹' and extract nearby digits
    if not price_text:
        try:
            html = page.content()
            i = html.find("₹")
            if i != -1:
                fragment = html[i:i+80]
                candidate = "".join(ch for ch in fragment if ch.isdigit())
                if candidate:
                    price_text = candidate
        except Exception:
            price_text = None

    price = parse_price_text(price_text) if price_text else None
    if not title:
        try:
            title = page.title()
        except Exception:
            title = "Unknown title"

    return title, price

# ---------- Main ----------
def main():
    # Load products.json
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load products.json: {e}")
        return

    if not isinstance(products, list) or len(products) == 0:
        print("No products found in products.json. Exiting.")
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"),
            locale="en-US"
        )
        page = context.new_page()

        for idx, item in enumerate(products, 1):
            url = item.get("url")
            target = item.get("target_price")   # kept for info in email
            to_email = item.get("alert_email") or ALERT_EMAIL

            if not url:
                print(f"Skipping invalid entry #{idx}: missing url")
                continue

            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking #{idx}: {url}")
            try:
                page.goto(url, timeout=60000)
                try:
                    page.wait_for_selector("._30jeq3", timeout=8000)
                except Exception:
                    pass  # continue to fallback parsing

                title, price = extract_title_and_price_from_page(page)
                print(f"Parsed -> title: {title!r}, price: {price}")

                if price is None and DEBUG_SAVE_HTML:
                    try:
                        fname = f"debug_product_{idx}_{int(time.time())}.html"
                        with open(fname, "w", encoding="utf-8") as fh:
                            fh.write(page.content())
                        print(f"Saved debug HTML -> {fname}")
                    except Exception as e:
                        print(f"Could not save debug HTML: {e}")

                # Always send update mail for this product
                subject = f"Flipkart Price Update: {title[:80]}"
                body_lines = [
                    f"Product: {title}",
                    f"URL: {url}",
                    f"Checked at: {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Current Price: {'₹' + str(price) if price is not None else 'Not found'}",
                    f"Target Price: {'₹' + str(target) if target is not None else 'Not set'}",
                ]
                body = "\n".join(body_lines)

                if to_email:
                    send_email(subject, body, to_email)
                else:
                    print("No recipient email configured (per-product or ALERT_EMAIL). Skipping send.")

            except PWTimeoutError as te:
                print(f"Timeout while loading {url}: {te}")
            except Exception as e:
                print(f"Error while processing {url}: {e}")

        page.close()
        context.close()
        browser.close()

if __name__ == "__main__":
    main()
