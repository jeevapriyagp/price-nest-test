import smtplib
import os
from email.mime.text import MIMEText
from sqlalchemy import func

from backend.backend_scrapper import compare_product
from backend import storage
from backend.database import SessionLocal
from backend.models import PriceHistory


# =========================
# EMAIL CONFIG (GMAIL)
# =========================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_SENDER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS")


# =========================
# SEND EMAIL FUNCTION
# =========================
def send_email_alert(receiver_email, subject, body):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("❌ Email credentials not set in environment variables.")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = receiver_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL SENT] to {receiver_email}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


# =========================
# GET LOWEST PRICE FROM DB
# =========================
def get_lowest_price_from_db(query: str):
    db = SessionLocal()

    lowest_price = (
        db.query(func.min(PriceHistory.price))
        .filter(PriceHistory.query == query)
        .scalar()
    )

    db.close()
    return lowest_price


# =========================
# ALERT CHECK JOB
# =========================
def check_alerts_job():
    print("\n==============================")
    print("[Scheduler] Checking alerts...")
    print("==============================\n")

    alerts = storage.list_alerts()

    if not alerts:
        print("No alerts found.")
        return

    for alert in alerts:
        try:
            if not alert.get("is_active", True):
                continue

            alert_id = alert["id"]
            query = alert["query"]
            target_price = int(alert["target_price"])
            receiver_email = alert["email"]

            print(f"\nChecking Alert ID {alert_id}")
            print(f"Product: {query}")
            print(f"Target Price: ₹{target_price:,}")

            # =========================
            # STEP 1: Scrape latest prices
            # =========================
            result = compare_product(query)

            results = result.get("results", [])
            if not results:
                print("No prices found from scraper.")
                continue

            # =========================
            # STEP 2: Store updated prices in DB
            # =========================
            storage.upsert_product(query, results)

            # =========================
            # STEP 3: Get lowest price from DB
            # =========================
            lowest_price = get_lowest_price_from_db(query)

            if lowest_price is None:
                print("No price history found.")
                continue

            print(f"Lowest Price Found: ₹{int(lowest_price):,}")

            # =========================
            # STEP 4: Compare & Trigger Alert
            # =========================
            if int(lowest_price) <= target_price:
                print("✅ ALERT TRIGGERED")

                # Find store with lowest price
                best_product = min(results, key=lambda x: x["price_numeric"])

                subject = f"🎉 Price Drop Alert: {query}"

                body = (
                    f"Price Alert Triggered!\n\n"
                    f"Product: {query}\n"
                    f"Target Price: ₹{target_price:,}\n"
                    f"Current Lowest Price: ₹{int(lowest_price):,}\n"
                    f"Store: {best_product['source']}\n"
                    f"Link: {best_product['link']}\n\n"
                    f"Alert ID: {alert_id}\n"
                    f"\n- PriceNest"
                )

                send_email_alert(receiver_email, subject, body)

                storage.deactivate_alert(alert_id)
                print(f"Alert {alert_id} deactivated.\n")

            else:
                print("Price still above target.")

        except Exception as e:
            print(f"[ERROR] Failed processing alert {alert.get('id')}: {e}")


# =========================
# MAIN RUNNER (GitHub Actions Mode)
# =========================
if __name__ == "__main__":
    print("Running alert check (GitHub Actions mode)...")
    check_alerts_job()
    print("\nFinished alert check.")
