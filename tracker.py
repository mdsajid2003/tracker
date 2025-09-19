import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from playwright.sync_api import sync_playwright

# 🔧 Hardcoded Gmail credentials (or use GitHub Secrets instead)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "mdsajid2152@gmail.com"       # 🔹 change to your Gmail
SMTP_PASS = "ecrb ubas enen oepy"          # 🔹 use Gmail App Password
ALERT_EMAIL = "mdsajid84388@gmail.com"     # 🔹 recipient (can be same as SMTP_USER)

# 🔗 Flipkart product links
PRODUCTS = [
    {
        "url": "https://www.flipkart.com/oppo-k13x-5g-6000mah-45w-supervooc-charger-ai-midnight-violet-128-gb/p/itm62b2e62fbb43e?pid=MOBHDY9PPU2NRCZH",
    },
    {
        "url": "https://www.flipkart.com/oppo-k13-5g-7000mah-80w-supervooc-charger-in-the-box-icy-purple-128-gb/p/itm6f2ebf6d205cf?pid=MOBHB392H7TZ4ZKJ",
    },
]


def send_email(subject, body, recipient=ALERT_EMAIL):
    """Send email notification via Gmail SMTP"""
    try:
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = recipient

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, recipient, msg.as_string())

        print(f"📧 Email sent to {recipient}: {subject}")
    except Exception as e:
        print(f"⚠️ Email not sent: {e}")


def get_product_info(page, url):
    """Extract product title and price using multiple selectors"""
    try:
        page.goto(url, timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        # Try multiple selectors for Title
        title_selectors = [
            "span.B_NuCI",  # old
            "span.yhB1nd",  # new mobile layout
            "h1",           # fallback
        ]
        title = "Unknown title"
        for sel in title_selectors:
            try:
                title = page.locator(sel).first.inner_text(timeout=3000)
                if title:
                    break
            except:
                continue

        # Try multiple selectors for Price
        price_selectors = [
            "div._30jeq3._16Jk6d",  # old
            "div.Nx9bqj.CxhGGd",    # new
            "div._25b18c",          # fallback
        ]
        price = None
        for sel in price_selectors:
            try:
                price_text = page.locator(sel).first.inner_text(timeout=3000)
                if price_text:
                    price = int("".join(filter(str.isdigit, price_text)))
                    break
            except:
                continue

        return title, price
    except Exception as e:
        print(f"[⚠️ Error scraping {url}] {e}")
        return "Unknown title", None


def main():
    print(f"[{datetime.now()}] 🔎 Checking current Flipkart prices...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for i, product in enumerate(PRODUCTS, start=1):
            url = product["url"]
            print(f"[{datetime.now()}] Checking #{i}: {url}")

            title, price = get_product_info(page, url)
            print(f"Parsed -> title: '{title}', price: {price}")

            # Always send email update every run
            if price is not None:
                subject = f"[Flipkart] {title[:50]}..."
                body = f"📌 Product: {title}\n💰 Current Price: ₹{price}\n🔗 Link: {url}"
                send_email(subject, body)
            else:
                print("⚠️ No email sent because price was not found.")

        browser.close()


if __name__ == "__main__":
    main()
