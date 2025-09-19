import requests
from bs4 import BeautifulSoup
import os
import smtplib
from email.message import EmailMessage
import json
import time

# ---------- Email Settings (from GitHub Secrets / env) ----------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = 587   # fixed to avoid empty-secret issues
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

# ---------- Request Headers (pretend to be a real Chrome browser) ----------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.flipkart.com/",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

# ---------- Retry Settings ----------
MAX_RETRIES = 3
INITIAL_BACKOFF = 2  # seconds (doubles each retry)


def fetch_flipkart(url):
    """
    Try to fetch the Flipkart product page and parse title & price.
    Retries on failures with exponential backoff.
    Returns (title, price) where price is int or None.
    """
    session = requests.Session()
    backoff = INITIAL_BACKOFF

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()  # will raise HTTPError for 4xx/5xx
            soup = BeautifulSoup(resp.text, "lxml")

            # Title selectors (common Flipkart classes)
            title_tag = soup.find("span", {"class": "B_NuCI"}) or soup.find("span", {"class": "yhB1nd"})
            title = title_tag.get_text(strip=True) if title_tag else "Unknown title"

            # Price selectors
            price_tag = soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "_30jeq3"})
            if not price_tag:
                # fallback: any span containing ₹
                price_tag = soup.find("span", string=lambda s: s and '₹' in s)

            price_text = price_tag.get_text(strip=True) if price_tag else None
            price = int("".join(ch for ch in price_text if ch.isdigit())) if price_text else None

            return title, price

        except requests.exceptions.HTTPError as he:
            status = getattr(he.response, "status_code", None)
            print(f"HTTPError (attempt {attempt}/{MAX_RETRIES}) for {url}: {he} (status={status})")
        except requests.exceptions.RequestException as re:
            print(f"RequestException (attempt {attempt}/{MAX_RETRIES}) for {url}: {re}")
        except Exception as e:
            print(f"Parsing/Error (attempt {attempt}/{MAX_RETRIES}) for {url}: {e}")

        if attempt < MAX_RETRIES:
            print(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)
            backoff *= 2
        else:
            print(f"All {MAX_RETRIES} attempts failed for {url}. Giving up.")
    return "Unknown title", None


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
        print(f"📧 Email sent to {to_email}")
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

        if not url:
            print(f"Skipping invalid product entry: {item}")
            continue

        try:
            title, price = fetch_flipkart(url)
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {title} → Current Price: {price}, Target: {target}")

            # ✅ Always send an update, no matter the price
            subject = f"Price Update: {title} → ₹{price if price else 'N/A'}"
            body = (
                f"Here is the latest update for {title}:\n\n"
                f"💰 Current Price: ₹{price if price else 'Not Found'}\n"
                f"🎯 Target Price: ₹{target}\n\n"
                f"🔗 Product Link: {url}\n"
                f"⏰ Checked at: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            send_email(subject, body, to_email)

        except Exception as e:
            print(f"⚠️ Unexpected error processing {url}: {e}")

    print("Run complete.")
