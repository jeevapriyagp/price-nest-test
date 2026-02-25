import pandas as pd
import logging

from . import storage

logger = logging.getLogger("pricenest")


# ---------------------------------------------------------
# Fetch ALL historical product rows from the products table
# Each scrape inserts new rows, so this grows over time.
# ---------------------------------------------------------
def fetch_all_price_data(query: str) -> pd.DataFrame:
    try:
        rows = storage.get_products(query)
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["created_at"])
        df["store"] = df["source"]
        df["price"] = df["price_numeric"].astype(float)
        return df[["timestamp", "store", "price"]]
    except Exception as e:
        logger.error(f"Error fetching price data for analytics ({query}): {e}")
        return pd.DataFrame()


# ---------------------------------------------------------
# Main Analytics Engine
# All 4 metrics are calculated across ALL rows ever stored
# for this query — including every past and current scrape.
# ---------------------------------------------------------
def analyze_price(query: str):
    df = fetch_all_price_data(query)

    if df.empty:
        return {"error": "No price data available yet"}

    df = df.sort_values("timestamp")

    # -------------------------------------------------------
    # LOWEST PRICE
    # The single lowest price ever seen for this query
    # across all stores and all scrapes in the products table.
    # -------------------------------------------------------
    lowest_price = int(df["price"].min())

    # -------------------------------------------------------
    # HIGHEST PRICE
    # The single highest price ever seen for this query
    # across all stores and all scrapes in the products table.
    # -------------------------------------------------------
    highest_price = int(df["price"].max())

    # -------------------------------------------------------
    # AVERAGE PRICE
    # Mean of every price row ever stored for this query.
    # Reflects the true average across all stores + all time.
    # -------------------------------------------------------
    avg_price = int(df["price"].mean())

    cheapest_store = df.loc[df["price"].idxmin()]["store"]

    # Latest price per store (for store comparison card)
    latest_per_store = (
        df.sort_values("timestamp")
        .groupby("store")
        .last()
        .reset_index()
    )
    store_prices = {
        row["store"]: int(row["price"])
        for _, row in latest_per_store.iterrows()
    }

    # Price trend — all data points across all scrapes, ordered by time
    price_trend = df.to_dict(orient="records")

    # -------------------------------------------------------
    # STABILITY
    # Standard deviation across all prices ever stored.
    # Higher std dev = more volatile pricing over time.
    # Thresholds are in rupees:
    #   < 500  → Stable
    #   < 1500 → Moderate
    #   >= 1500 → Highly Volatile
    # -------------------------------------------------------
    volatility_score = round(df["price"].std(), 2) if len(df) > 1 else 0.0
    if volatility_score < 500:
        stability = "🟢 Stable"
    elif volatility_score < 1500:
        stability = "🟡 Moderate"
    else:
        stability = "🔴 Highly Volatile"

    # -------------------------------------------------------
    # BEST TIME TO BUY INSIGHT
    # Compares best price from the earliest scrape event
    # vs the most recent scrape event.
    # Groups into 1-hour windows to avoid noise from
    # stores within the same scrape having slightly
    # different timestamps.
    # -------------------------------------------------------
    df["event_id"] = df["timestamp"].dt.floor("1h")
    event_mins = df.groupby("event_id")["price"].min().sort_index()

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