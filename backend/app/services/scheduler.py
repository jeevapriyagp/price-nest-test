import smtplib
from email.mime.text import MIMEText
from sqlalchemy import func

from .scraper import compare_product
from . import storage
from ..core.database import SessionLocal
from ..models.models import PriceHistory
from ..core.config import EMAIL_USER, EMAIL_PASS

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL_SENDER = EMAIL_USER
EMAIL_PASSWORD = EMAIL_PASS


from email.mime.multipart import MIMEMultipart

def send_email_alert(receiver_email, subject, body_text, body_html=None):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        print("❌ Email credentials not set in environment variables.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"PriceNest <{EMAIL_SENDER}>"
    msg["To"] = receiver_email

    msg.attach(MIMEText(body_text, "plain"))
    if body_html:
        msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"[EMAIL SENT] to {receiver_email}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


# =========================
# ALERT CHECK JOB
# =========================
def check_alerts_job():
    print("\n==============================")
    print("[Scheduler] Checking alerts...")
    print("==============================\n")

    # 1. Fetch all alerts and filter active ones
    alerts = storage.list_all_alerts()
    active_alerts = [a for a in alerts if a["is_active"]]

    if not active_alerts:
        print("No active alerts found.")
        return

    # 2. Identify unique products (queries) to scrape
    unique_queries = list(set(a["query"] for a in active_alerts))
    print(f"Tracking {len(unique_queries)} unique products for {len(active_alerts)} active alerts.")

    # 3. Scrape and update products table for unique queries
    cached_results = {}
    for query in unique_queries:
        try:
            print(f"Scraping latest price for: {query}")
            result = compare_product(query)
            results = result.get("results", [])
            
            if results:
                storage.upsert_product(query, results)
                # Find the best product (lowest price)
                best_product = min(results, key=lambda x: x["price_numeric"])
                cached_results[query] = {
                    "lowest_price": best_product["price_numeric"],
                    "best_product": best_product
                }
            else:
                print(f"⚠️ No results found for: {query}")
        except Exception as e:
            print(f"⚠️ Error scraping {query}: {e}")

    # 4. Evaluate each alert based on the scraped data
    for alert in active_alerts:
        try:
            alert_id = alert["id"]
            query = alert["query"]
            target_price = float(alert["target_price"])
            last_alerted_price = alert.get("last_alerted_price")
            receiver_email = alert["email"]

            if query not in cached_results:
                continue

            current_lowest = cached_results[query]["lowest_price"]
            best_product = cached_results[query]["best_product"]

            print(f"\nEvaluating Alert {alert_id} for {query}")
            print(f"Target: ₹{target_price:,} | Current: ₹{int(current_lowest):,}")

            if current_lowest <= target_price:
                # Intelligent Alert Logic: Only notify if price changed
                # We use abs() >= 1 to handle minor float differences
                if last_alerted_price is None or abs(current_lowest - last_alerted_price) >= 1:
                    print("✅ ALERT TRIGGERED")
                    
                    price_direction = "dropped" if (last_alerted_price is None or current_lowest < last_alerted_price) else "risen"
                    emoji = "📉" if price_direction == "dropped" else "📈"
                    
                    subject = f"{emoji} Price {price_direction.capitalize()}: {query} is now ₹{int(current_lowest):,}"
                    
                    body_text = (
                        f"Price Alert from PriceNest\n\n"
                        f"The price for '{query}' has {price_direction} to ₹{int(current_lowest):,}.\n"
                        f"Target Price: ₹{int(target_price):,}\n"
                        f"Current Store: {best_product['source']}\n"
                        f"View Deal: {best_product['link']}\n\n"
                        f"Thank you for choosing PriceNest."
                    )
                    
                    # Professional HTML Template
                    body_html = f"""
                    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: auto; border: 1px solid #e0e0e0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        <div style="background-color: #2c3e50; padding: 25px; text-align: center; color: white;">
                            <h1 style="margin: 0; font-size: 24px; letter-spacing: 1px;">PriceNest Alert</h1>
                        </div>
                        <div style="padding: 40px; background-color: #ffffff;">
                            <p style="font-size: 16px; color: #444; line-height: 1.6;">Hello,</p>
                            <p style="font-size: 16px; color: #444; line-height: 1.6;">We've detected a price change for a product you're tracking.</p>
                            
                            <div style="background-color: #f8f9fa; border-left: 5px solid {'#27ae60' if price_direction == 'dropped' else '#e74c3c'}; padding: 25px; border-radius: 8px; margin: 30px 0;">
                                <h2 style="margin-top: 0; font-size: 18px; color: #2c3e50;">{query}</h2>
                                <p style="font-size: 32px; font-weight: bold; color: {'#27ae60' if price_direction == 'dropped' else '#e74c3c'}; margin: 15px 0;">
                                    ₹{int(current_lowest):,} 
                                    <span style="font-size: 16px; font-weight: normal; color: #7f8c8d;">({price_direction})</span>
                                </p>
                                <div style="font-size: 14px; color: #34495e;">
                                    <p style="margin: 5px 0;"><strong>Target Price:</strong> ₹{int(target_price):,}</p>
                                    <p style="margin: 5px 0;"><strong>Current Store:</strong> {best_product['source']}</p>
                                </div>
                            </div>
                            
                            <div style="text-align: center; margin-top: 40px;">
                                <a href="{best_product['link']}" style="background-color: #2980b9; color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px; display: inline-block;">View Deal on {best_product['source']}</a>
                            </div>
                        </div>
                        <div style="background-color: #f1f2f6; padding: 20px; text-align: center; font-size: 12px; color: #7f8c8d; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0;">You are receiving this email because you set a price alert on PriceNest.</p>
                            <p style="margin: 5px 0;">&copy; 2026 PriceNest Inc. All rights reserved.</p>
                        </div>
                    </div>
                    """
                    
                    send_email_alert(receiver_email, subject, body_text, body_html)
                    
                    # Store current price to avoid repeated alerts for the same price
                    storage.update_alert_price(alert_id, current_lowest)
                else:
                    print("Price is same as last time. Skipping duplicate alert.")
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
