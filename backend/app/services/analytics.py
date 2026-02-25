import pandas as pd
import logging
from datetime import timedelta

from . import storage

logger = logging.getLogger("pricenest")


# ---------------------------------------------------------
# Fetch Products from PostgreSQL and reshape for analytics
# ---------------------------------------------------------
def fetch_price_history(query: str) -> pd.DataFrame:
    try:
        rows = storage.get_products(query)
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        # Map products columns to the shape analytics expects
        df["timestamp"] = pd.to_datetime(df["created_at"])
        df["store"] = df["source"]
        # Explicitly cast to numeric — prevents min/max running lexicographically
        # on mixed-type columns, which causes wrong price range values
        df["price"] = pd.to_numeric(df["price_numeric"], errors="coerce")
        df = df.dropna(subset=["price"])  # drop any rows where price failed to parse
        return df[["timestamp", "store", "price"]]
    except Exception as e:
        logger.error(f"Error fetching products for analytics ({query}): {e}")
        return pd.DataFrame()


# ---------------------------------------------------------
# Main Analytics Engine
# ---------------------------------------------------------
def analyze_price(query: str):
    df = fetch_price_history(query)

    if df.empty:
        return {"error": "No price data available yet"}

    df = df.sort_values("timestamp")

    lowest_price = int(df["price"].min())
    highest_price = int(df["price"].max())
    avg_price = int(df["price"].mean())

    cheapest_store = df.loc[df["price"].idxmin()]["store"]

    latest_prices = (
        df.sort_values("timestamp")
        .groupby("store")
        .last()
        .reset_index()
    )

    store_prices = {
        row["store"]: int(row["price"])
        for _, row in latest_prices.iterrows()
    }

    price_trend = df.to_dict(orient="records")

    # Volatility logic based on overall variance
    volatility_score = round(df["price"].std(), 2) if len(df) > 1 else 0
    if volatility_score < 500:
        stability = "🟢 Stable"
    elif volatility_score < 1500:
        stability = "🟡 Moderate"
    else:
        stability = "🔴 Highly Volatile"

    # --- Best Time-to-Buy Logic ---
    # "Current price" = lowest price from the most recent scrape batch.
    # We define the latest scrape batch as all rows within 10 minutes
    # of the most recent timestamp in the DB for this query.
    insight = "Not enough data yet — search again later to track price movement."

    if len(df) > 1:
        latest_timestamp = df["timestamp"].max()
        cutoff = latest_timestamp - timedelta(minutes=10)
        current_scrape_df = df[df["timestamp"] >= cutoff]
        current_lowest = int(current_scrape_df["price"].min())

        diff = current_lowest - avg_price
        pct = round((diff / avg_price) * 100, 1)

        if current_lowest <= lowest_price:
            insight = f"This is the lowest price ever recorded! Great time to buy."
        elif diff < 0:
            insight = f"Current best price (₹{current_lowest:,}) is {abs(pct)}% below the historical average. Good time to buy."
        elif diff == 0:
            insight = f"Current price is right at the historical average (₹{avg_price:,})."
        else:
            insight = f"Current best price (₹{current_lowest:,}) is {pct}% above the historical average. Consider waiting."

    return {
        "summary": {
            "lowest_price": lowest_price,
            "highest_price": highest_price,
            "average_price": avg_price,
            "price_range": f"₹{lowest_price} – ₹{highest_price}",
            "cheapest_store": cheapest_store
        },
        "store_prices": store_prices,
        "price_trend": price_trend,
        "volatility": {
            "score": volatility_score,
            "stability": stability
        },
        "best_time_to_buy": insight
    }