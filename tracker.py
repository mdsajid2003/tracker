import os
import smtplib
import json
import time
from email.message import EmailMessage
from playwright.sync_api import sync_playwright

# ---------- Email Settings (from GitHub Secrets / env) ----------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")


def fetch_flipkart(url):
    """
    Use Playwright (Chromium) to fetch Flipkart product page
    and extract title + price reliably.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(url, timeout=60000)  # wait up to 60 sec
        page.wait_for_timeout(5000)    # wait 5 sec for JS to load

        try:
            # Extract title
            title = page.locator("span.B_NuCI").inner_text(timeout=5000)
        except:
            try:
                title = page.locator("span.yhB1nd").inner_text(timeout=5000)
            except:
                title = "Unknown title"

        try:
            # Extract price (₹ symbol + numbers)
            price_text = page.locator("div._30jeq3._16Jk6d").inner_text(timeout=5000)
        except:
            try:
                price_text = page.locator("div._30jeq3").inner_text(timeout=5000)
            except:
                price_text = None

        browser.close()

        if price_text:
            price = int("".join(ch for ch in price_text if ch.isdigit()))
        else:
            price = None

        return title, price


def send_email(subject, body, to_email):
    """
    Send an email alert using SMTP. If creds missing, prints warning.
    """
    if not all([SMTP_USER, SMTP_PASS, to_email]):
        print("⚠️ Email not sent: SMTP_USER, SMTP_PASS, or ALERT_EMAIL missing")
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
        print(f"📧 Alert sent to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
        return False


if __name__ == "__main__":
    # Load products from JSON file
    try:
        with open("products.json", "r", encoding="utf-8") as f:
            products = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load products.json: {e}")
        products = []

    if not products:
        print("No products to track (products.json is empty or missing). Exiting.")
        exit(0)

    for item in products:
        url = item.get("url")
        target = item.get("target_price")
        to_email = item.get("alert_email") or ALERT_EMAIL

        if not url or target is None:
            print(f"Skipping invalid product entry: {item}")
            continue

        try:
            title, price = fetch_flipkart(url)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {title} → Current Price: {price}, Target: {target}")

            if price is not None and price <= int(target):
                subject = f"Price Alert: {title} now ₹{price}"
                body = f"The price for {title} is now ₹{price} (target was ₹{target}).\nURL: {url}"
                send_email(subject, body, to_email)
            else:
                print("No alert (price above target or price not found).")

        except Exception as e:
            print(f"⚠️ Unexpected error processing {url}: {e}")

    print("Run complete.")
