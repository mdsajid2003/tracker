import os
import smtplib
from email.mime.text import MIMEText
from playwright.sync_api import sync_playwright
from datetime import datetime

# ---------- Email Settings (hardcoded for now) ----------
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "mdsajid2152@gmail.com"          # replace with your Gmail
SMTP_PASS = "ecrb ubas enen oepy"       # use Gmail App Password
ALERT_EMAIL = "mdsajid2152@gmail.com"        # where alerts are sent

# ---------- Product Search Query ----------
SEARCH_QUERY = "oppo k13x 5g"   # <-- you can change this

def send_email(subject, body):
    msg = MIMEText(body, "html")  # HTML formatting
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = ALERT_EMAIL

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print(f"📧 Email sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"❌ Email failed: {e}")

def search_flipkart(query, page, max_results=15):
    url = f"https://www.flipkart.com/search?q={query}"
    print(f"[{datetime.now()}] 🔎 Searching: {url}")
    page.goto(url, timeout=60000)

    try:
        page.wait_for_selector("div._1AtVbE", timeout=15000)
    except:
        print("⚠️ No results found or page load timeout.")
        return []

    items = []
    cards = page.locator("div._1AtVbE div._13oc-S")  # result container
    count = min(cards.count(), max_results)

    for i in range(count):
        card = cards.nth(i)
        try:
            title = card.locator("div._4rR01T").inner_text().strip()
        except:
            title = None

        try:
            price_text = card.locator("div._30jeq3").inner_text().strip()
            price = int("".join(filter(str.isdigit, price_text)))
        except:
            price = None

        try:
            link = card.locator("a").get_attribute("href")
            link_full = f"https://www.flipkart.com{link}" if link else None
        except:
            link_full = None

        if title and price and link_full:
            items.append({"title": title, "price": price, "url": link_full})

    return items

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        results = search_flipkart(SEARCH_QUERY, page, max_results=20)
        results = [r for r in results if r.get("price") is not None]

        if not results:
            print("⚠️ No valid products found.")
            browser.close()
            return

        results.sort(key=lambda r: r["price"])
        top3 = results[:3]

        # Build email content
        body_lines = [f"<h2>Top 3 lowest Flipkart prices for '{SEARCH_QUERY}'</h2><ul>"]
        for item in top3:
            body_lines.append(
                f"<li><b>{item['title']}</b> — ₹{item['price']} "
                f"<a href='{item['url']}'>View</a></li>"
            )
        body_lines.append("</ul>")

        subject = f"Top 3 lowest Flipkart prices for {SEARCH_QUERY} — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        body = "\n".join(body_lines)

        send_email(subject, body)
        browser.close()

if __name__ == "__main__":
    main()
