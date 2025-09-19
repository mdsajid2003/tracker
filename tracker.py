import os
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import smtplib
from email.message import EmailMessage

# ---------- Email Settings ----------
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")


async def extract_title_and_price_from_page(page):
    """Extract product title and price using Playwright selectors."""
    try:
        title_el = await page.wait_for_selector("span.B_NuCI, span.yhB1nd", timeout=8000)
        title = (await title_el.inner_text()).strip()
    except:
        title = ""

    try:
        price_el = await page.wait_for_selector(
            "div._30jeq3._16Jk6d, div._30jeq3, div._25b18c ._30jeq3",
            timeout=8000,
        )
        raw_price = await price_el.inner_text()
        # Clean price → keep only digits
        digits = "".join(ch for ch in raw_price if ch.isdigit())
        price = int(digits) if digits else None
    except:
        price = None

    return title, price


async def fetch_flipkart(url):
    """Open product page and fetch title + price."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0")
        await page.goto(url, timeout=30000)
        title, price = await extract_title_and_price_from_page(page)
        await browser.close()
        return title, price


def send_email(subject, body, recipient=None):
    """Send email via SMTP."""
    to_email = recipient or ALERT_EMAIL
    if not all([SMTP_USER, SMTP_PASS, to_email]):
        print("⚠️ No recipient email configured (per-product or ALERT_EMAIL). Skipping send.")
        return

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
        print(f"📧 Alert sent to {to_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {e}")


async def main():
    # Load products
    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    for i, item in enumerate(products, start=1):
        url = item["url"]
        target = item.get("target_price")
        recipient = item.get("email")  # optional per-product email

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking #{i}: {url}")

        try:
            title, price = await fetch_flipkart(url)
            print(f"Parsed -> title: '{title}', price: {price}")

            # Always send current price (irrespective of target)
            if price:
                send_email(
                    f"Flipkart Price Update: {title}",
                    f"Product: {title}\nCurrent Price: ₹{price}\nTarget: ₹{target}\nURL: {url}",
                    recipient,
                )
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
