import os
import json
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright

# Read products.json
with open("products.json", "r") as f:
    products = json.load(f)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")


def send_email(subject, body):
    if not (SMTP_USER and SMTP_PASS and ALERT_EMAIL):
        print("⚠️ Email not sent: SMTP_USER, SMTP_PASS, or ALERT_EMAIL missing")
        return

    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL

    try:
        with smtplib.SMTP(SMTP_HOST, 587) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())
        print(f"📧 Email sent: {subject}")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")


def fetch_price(page, url):
    page.goto(url, timeout=60000)
    page.wait_for_selector("._30jeq3")  # Flipkart price selector
    title = page.title()
    price_element = page.query_selector("._30jeq3")
    price_text = price_element.inner_text().replace("₹", "").replace(",", "")
    return title, int(price_text)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for product in products:
            url = product["url"]
            try:
                title, price = fetch_price(page, url)
                log = f"[Update] {title}\nCurrent Price: ₹{price}"
                print(log)

                # Always send price update
                send_email(
                    subject=f"Flipkart Price Update: {title[:40]}...",
                    body=f"{title}\nURL: {url}\nCurrent Price: ₹{price}"
                )
            except Exception as e:
                print(f"⚠️ Error fetching {url}: {e}")

        browser.close()


if __name__ == "__main__":
    main()
