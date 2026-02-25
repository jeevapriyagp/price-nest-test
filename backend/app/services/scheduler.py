import smtplib
from email.mime.text import MIMEText

from .scraper import compare_product
from . import storage
from ..core.database import SessionLocal
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
                    
                    subject = f"Price {price_direction.capitalize()}: {query} is now ₹{int(current_lowest):,}"
                    
                    body_text = (
                        f"Price Alert from PriceNest\n\n"
                        f"The price for '{query}' has {price_direction} to ₹{int(current_lowest):,}.\n"
                        f"Target Price: ₹{int(target_price):,}\n"
                        f"Current Store: {best_product['source']}\n"
                        f"View Deal: {best_product['link']}\n\n"
                        f"Thank you for choosing PriceNest."
                    )
                    
                    # Minimal Website-Inspired HTML Template
                    # Using website colors: Primary #667eea, Background #0a0e27, Success #10b981
                    body_html = f"""
                    <div style="font-family: 'Inter', -apple-system, sans-serif; max-width: 550px; margin: auto; background-color: #0a0e27; color: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1);">
                        <div style="padding: 30px; text-align: left;">
                            <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #667eea;">PriceNest</h1>
                            
                            <div style="margin-top: 30px;">
                                <p style="font-size: 14px; color: #b8c1ec; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 1px;">Price Update</p>
                                <h2 style="margin: 0; font-size: 24px; font-weight: 600; line-height: 1.3;">{query}</h2>
                                
                                <div style="margin-top: 24px; padding: 20px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                                    <p style="margin: 0; font-size: 36px; font-weight: 700; color: {'#10b981' if price_direction == 'dropped' else '#ef4444'};">
                                        ₹{int(current_lowest):,}
                                    </p>
                                    <p style="margin: 4px 0 0 0; font-size: 14px; color: #b8c1ec;">
                                        {price_direction.capitalize()} from your target of ₹{int(target_price):,}
                                    </p>
                                </div>
                            </div>

                            <div style="margin-top: 32px; text-align: center;">
                                <a href="{best_product['link']}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 12px; font-weight: 600; font-size: 16px; display: inline-block;">View Deal on {best_product['source']}</a>
                            </div>
                        </div>
                        
                        <div style="padding: 20px 30px; background-color: rgba(255,255,255,0.02); border-top: 1px solid rgba(255,255,255,0.05); text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #6b7280;">
                                You're receiving this because you set an alert for "{query}".
                            </p>
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