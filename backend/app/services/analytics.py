import pandas as pd
from datetime import datetime
import logging

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
        df["price"] = df["price_numeric"]
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

    # --- Group into 1-hour windows (Search Events) ---
    df["event_id"] = df["timestamp"].dt.floor("1h")

    # Get min price per event (the "Best Deal" at that point in time)
    event_mins = df.groupby("event_id")["price"].min().sort_index()

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

    price_trend = df.drop(columns=["event_id"]).to_dict(orient="records")

    # Volatility logic based on overall variance
    volatility_score = round(df["price"].std(), 2) if len(df) > 1 else 0
    if volatility_score < 500:
        stability = "🟢 Stable"
    elif volatility_score < 1500:
        stability = "🟡 Moderate"
    else:
        stability = "🔴 Highly Volatile"

    # --- Refined Best Time-to-Buy Logic ---
    insight = "Only one search event found — search again later to see price movement"

    if len(event_mins) >= 2:
        latest_best = int(event_mins.iloc[-1])
        earliest_best = int(event_mins.iloc[0])
        diff = latest_best - earliest_best

        if diff < 0:
            insight = f"Prices have dropped by ₹{abs(diff)} since your first search! Good time to buy."
        elif diff > 0:
            insight = f"Prices have increased by ₹{diff} since your first search."
        else:
            insight = "Prices are currently equal to the earliest recorded price."

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