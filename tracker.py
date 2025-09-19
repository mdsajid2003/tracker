import time
from playwright.sync_api import sync_playwright
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- Gmail SMTP (⚠️ use app password if 2FA is on) ---
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "mdsajid2152@gmail.com"
SMTP_PASS = "ecrb ubas enen oepy"

# --- Products to track ---
PRODUCTS = [
    {
        "url": "https://www.flipkart.com/oppo-k13x-5g-6000mah-45w-supervooc-charger-ai-midnight-violet-128-gb/p/itm62b2e62fbb43e?pid=MOBHDY9PPU2NRCZH",
        "email": "your@gmail.com",
    },
    {
        "url": "https://www.flipkart.com/oppo-k13-5g-7000mah-80w-supervooc-charger-in-the-box-icy-purple-128-gb/p/itm6f2ebf6d205cf?pid=MOBHB392H7TZ4ZKJ",
        "email": "your@gmail.com",
    },
]

def send_email(subject, body, to_email):
    try:
        msg = EmailMessage()
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(body)

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print(f"[{datetime.now()}] 📧 Sent email to {to_email}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def fetch_with_playwright(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        # Get product title
        try:
            title = page.locator("span.B_NuCI, span.yhB1nd").first.inner_text(timeout=20000)
        except:
            title = "Unknown title"

        # Get product price
        price = None
        try:
            price_tags = page.locator("div._30jeq3._16Jk6d, div._30jeq3").all_inner_texts()
            for txt in price_tags:
                clean = "".join(ch for ch in txt if ch.isdigit())
                if clean.isdigit():
                    val = int(clean)
                    if 1000 <= val <= 200000:  # sensible filter
                        price = val
                        break
        except Exception as e:
            print(f"⚠️ Failed to parse price: {e}")

        browser.close()
        return title, price

if __name__ == "__main__":
    print(f"[{datetime.now()}] 🔎 Checking current Flipkart prices...")

    for idx, product in enumerate(PRODUCTS, 1):
        url = product["url"]
        print(f"[{datetime.now()}] Checking #{idx}: {url}")

        try:
            title, price = fetch_with_playwright(url)
            print(f"Parsed -> title: '{title}', price: {price}")
        except Exception as e:
            print(f"⚠️ Error scraping {url}: {e}")
            title, price = "Unknown", None

        if product.get("email") and price:
            subject = f"[Price Update] {title} → ₹{price}"
            body = f"Product: {title}\nCurrent Price: ₹{price}\nURL: {url}\nChecked at {datetime.now()}"
            send_email(subject, body, product["email"])
        else:
            print("⚠️ No email recipient or price missing. Skipping send.")
