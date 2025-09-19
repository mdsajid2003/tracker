import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
from datetime import datetime

# ----------------------------
# 🔧 Hardcoded Email Settings
# ----------------------------
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "mdsajid2152gmail@gmail.com"       # replace with your Gmail
SMTP_PASS = "ecrb ubas enen oepy"         # replace with Gmail App Password
ALERT_EMAIL = "mdsajid84388@gmail.com"     # where to send alerts (can be same as user)

# ----------------------------
# 📦 Products to Track
# ----------------------------
PRODUCTS = [
    {
        "url": "https://www.flipkart.com/oppo-k13x-5g-6000mah-45w-supervooc-charger-ai-midnight-violet-128-gb/p/itm62b2e62fbb43e?pid=MOBHDY9PPU2NRCZH",
    },
    {
        "url": "https://www.flipkart.com/oppo-k13-5g-7000mah-80w-supervooc-charger-in-the-box-icy-purple-128-gb/p/itm6f2ebf6d205cf?pid=MOBHB392H7TZ4ZKJ",
    }
]

# ----------------------------
# ✉️ Email Sending
# ----------------------------
def send_email(subject, body, recipient):
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = recipient

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipient, msg.as_string())

        print(f"[📧 Email sent to {recipient}]")
    except Exception as e:
        print(f"[⚠️ Email failed] {e}")

# ----------------------------
# 🔎 Scrape Flipkart Product
# ----------------------------
def get_product_info(page, url):
    try:
        page.goto(url, timeout=60000)
        page.wait_for_selector("span.B_NuCI, span.yhB1nd", timeout=10000)

        # Title
        try:
            title = page.locator("span.B_NuCI, span.yhB1nd").first.inner_text(timeout=5000)
        except:
            title = "Unknown title"

        # Price
        try:
            price_text = page.locator("div._30jeq3._16Jk6d, div.Nx9bqj.CxhGGd").first.inner_text(timeout=5000)
            price = int("".join(filter(str.isdigit, price_text)))
        except:
            price = None

        return title, price
    except Exception as e:
        print(f"[⚠️ Error scraping {url}] {e}")
        return "Unknown title", None

# ----------------------------
# 🚀 Main Tracker
# ----------------------------
def main():
    print(f"\n[{datetime.now()}] 🔎 Checking current Flipkart prices...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, product in enumerate(PRODUCTS, start=1):
            print(f"[{datetime.now()}] Checking #{i}: {product['url']}")

            title, price = get_product_info(page, product["url"])
            print(f"Parsed -> title: '{title}', price: {price}")

            if price is not None:
                subject = f"Flipkart Price Update: {title}"
                body = f"[{datetime.now()}]\n\nProduct: {title}\nURL: {product['url']}\nCurrent Price: ₹{price}"
                send_email(subject, body, ALERT_EMAIL)
            else:
                print("⚠️ Price not found. Skipping send.")

        browser.close()

if __name__ == "__main__":
    main()
