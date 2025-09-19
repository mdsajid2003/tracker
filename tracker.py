import requests
from bs4 import BeautifulSoup
import os
import smtplib
from email.message import EmailMessage
import json

# ---------- Email Settings (from GitHub Secrets) ----------
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
ALERT_EMAIL = os.getenv("ALERT_EMAIL")

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_flipkart(url):
    """
    Scrape Flipkart product title and price from the product page.
    """
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")

    # Product title
    title_tag = soup.find("span", {"class": "B_NuCI"}) or soup.find("span", {"class": "yhB1nd"})
    title = title_tag.get_text(strip=True) if title_tag else "Unknown title"

    # Product price
    price_tag = soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "_30jeq3"})
    price_text = price_tag.get_text(strip=True) if price_tag else None
    price = int("".join(ch for ch in price_text if ch.isdigit())) if price_text else None

    return title, price

def send_email(subject, body):
    """
    Send an email alert using SMTP settings.
    """
    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.starttls()
        s.login(SMTP_USER, SMTP_PASS)
        s.send_message(msg)
    print(f"📧 Alert sent to {ALERT_EMAIL}")

if __name__ == "__main__":
    # Load products from JSON file
    with open("products.json", "r", encoding="utf-8") as f:
        products = json.load(f)

    for item in products:
        url = item["url"]
        target = item["target_price"]

        try:
            title, price = fetch_flipkart(url)
            print(f"{title} → Current Price: {price}, Target: {target}")

            if price and price <= target:
                send_email(
                    f"Price Alert: {title} now ₹{price}",
                    f"The price for {title} is now ₹{price} (target was ₹{target}).\nURL: {url}"
                )
        except Exception as e:
            print(f"⚠️ Error checking {url}: {e}")
