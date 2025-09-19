import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from playwright.sync_api import sync_playwright

# -------------------------------
# Hardcoded SMTP Config
# -------------------------------
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "mdsajid2152@gmail.com"      # <-- your Gmail
SMTP_PASS = "ecrb ubas enen oepy"         # <-- App Password from Google

# -------------------------------
# Email sender
# -------------------------------
def send_email(recipient, subject, body):
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = recipient

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [recipient], msg.as_string())
        print(f"✅ Email sent to {recipient}")
    except Exception as e:
        print(f"❌ Email error: {e}")

# -------------------------------
# Flipkart scraper
# -------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def fetch_flipkart(url):
    """Scrape title and clean price from Flipkart product page."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS["User-Agent"])
            page.goto(url, timeout=60000)

            # Title
            title = page.locator("span.B_NuCI, span.yhB1nd").first.inner_text(timeout=5000)

            # Price
            price_text = page.locator(
                "div._30jeq3._16Jk6d, div._30jeq3, span:has-text('₹')"
            ).first.inner_text(timeout=5000)
            digits = "".join(ch for ch in price_text if ch.isdigit())
            price = int(digits) if digits else None

            browser.close()
            return title.strip(), price
    except Exception as e:
        print(f"⚠️ Error scraping {url}: {e}")
        return "Unknown title", None

# -------------------------------
# Main
# -------------------------------
def main():
    ts = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{ts} 🔎 Starting Flipkart tracker...")

    # HARD-CODED products
    products = [
        {
            "url": "https://www.flipkart.com/oppo-k13x-5g-6000mah-45w-supervooc-charger-ai-midnight-violet-128-gb/p/itm62b2e62fbb43e?pid=MOBHDY9PPU2NRCZH",
            "target_price": 7000,
            "email": "your-email@gmail.com"
        },
        {
            "url": "https://www.flipkart.com/oppo-k13-5g-7000mah-80w-supervooc-charger-in-the-box-icy-purple-128-gb/p/itm6f2ebf6d205cf?pid=MOBHB392H7TZ4ZKJ",
            "target_price": 10000,
            "email": "your-email@gmail.com"
        }
    ]

    for i, product in enumerate(products, start=1):
        url = product["url"]
        target_price = product["target_price"]
        recipient = product["email"]

        title, price = fetch_flipkart(url)

        print(f"\n{ts} Checking #{i}: {url}")
        print(f"Parsed -> title: '{title}', price: {price}")

        if recipient and price:
            subject = f"Flipkart Price Update: {title}"
            body = (
                f"Product: {title}\n"
                f"URL: {url}\n"
                f"Current Price: ₹{price}\n"
                f"Target Price: ₹{target_price}\n"
                f"Checked at: {ts}"
            )
            send_email(recipient, subject, body)
        else:
            print("⚠️ No email recipient or price missing. Skipping send.")

if __name__ == "__main__":
    main()
