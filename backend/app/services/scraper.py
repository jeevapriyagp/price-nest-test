import re
from urllib.parse import urlparse
from serpapi import GoogleSearch
from ..core.config import SERPAPI_KEY


# --------------------------------------------------
# BUILD SMART SEARCH QUERY (USER TYPES ONLY PRODUCT)
# --------------------------------------------------
def build_search_query(q: str) -> str:
    return f"{q} buy online India price"


# --------------------------------------------------
# CLEAN PRODUCT TITLE
# --------------------------------------------------
def clean_title(title: str) -> str:
    if not title:
        return ""
    title = title.lower()
    noise = [
        "price in india", "reviews", "review", "specs",
        "specifications", "offers", "deal", "buy online",
        "best price", "online"
    ]
    for n in noise:
        title = title.replace(n, "")
    title = re.sub(r"[^\w\s]", " ", title)
    return re.sub(r"\s+", " ", title).strip().title()


# --------------------------------------------------
# STRICT PRICE EXTRACTOR (NO EMI EVER)
# --------------------------------------------------
def extract_prices(text: str):
    if not text:
        return []

    # Match only ₹ / Rs / INR followed by >=4 digits
    matches = re.findall(r"(₹|Rs\.?|INR)\s?([\d,]{4,})", text)
    prices = []

    for _, num in matches:
        val = int(num.replace(",", ""))
        if val >= 7000:  # EMI never crosses this
            prices.append(val)

    return prices


# --------------------------------------------------
# DOMAIN NORMALIZER (VERY IMPORTANT)
# --------------------------------------------------
def get_domain(url: str) -> str:
    try:
        netloc = urlparse(url).netloc.lower()
        return netloc.replace("www.", "")
    except:
        return ""


# --------------------------------------------------
# GOOGLE SEARCH
# --------------------------------------------------
def google_search(query: str):
    return GoogleSearch({
        "q": query,
        "location": "India",
        "hl": "en",
        "gl": "in",
        "num": 60,
        "api_key": SERPAPI_KEY
    }).get_dict()


# --------------------------------------------------
# EXTRACT RESULTS (ALL PLATFORMS, ALL PRODUCTS)
# --------------------------------------------------
def extract_results(data: dict):
    results = []

    allowed_keywords = [
        "amazon", "flipkart", "croma",
        "reliance", "tatacliq", "snapdeal", "ajio"
    ]

    def is_allowed(domain):
        return any(k in domain for k in allowed_keywords)

    # ---------- GOOGLE SHOPPING ----------
    for item in data.get("shopping_results", []):
        link = item.get("link")
        title = item.get("title")
        price_text = item.get("price")

        if not link or not title or not price_text:
            continue

        domain = get_domain(link)
        if not is_allowed(domain):
            continue

        prices = extract_prices(price_text)
        if not prices:
            continue

        results.append({
            "title": clean_title(title),
            "source": domain,
            "link": link,
            "price_numeric": min(prices),
            "price": f"₹{min(prices):,}",
            "image": item.get("thumbnail"),
            "store_logo": item.get("source_icon")
        })

    # ---------- INLINE SHOPPING ----------
    for item in data.get("inline_shopping_results", []):
        link = item.get("link")
        title = item.get("title")
        price_text = item.get("price")

        if not link or not title or not price_text:
            continue

        domain = get_domain(link)
        if not is_allowed(domain):
            continue

        prices = extract_prices(price_text)
        if not prices:
            continue

        results.append({
            "title": clean_title(title),
            "source": domain,
            "link": link,
            "price_numeric": min(prices),
            "price": f"₹{min(prices):,}",
            "image": item.get("thumbnail"),
            "store_logo": item.get("source_icon")
        })

    # ---------- ORGANIC RESULTS ----------
    for item in data.get("organic_results", []):
        link = item.get("link")
        title = item.get("title")
        snippet = item.get("snippet", "")

        if not link or not title:
            continue

        domain = get_domain(link)
        if not is_allowed(domain):
            continue

        prices = extract_prices(title + " " + snippet)
        if not prices:
            continue

        results.append({
            "title": clean_title(title),
            "source": domain,
            "link": link,
            "price_numeric": min(prices),
            "price": f"₹{min(prices):,}",
            "image": item.get("thumbnail"),
            "store_logo": item.get("favicon")
        })

    # SORT BY REAL PRICE
    return sorted(results, key=lambda x: x["price_numeric"])


# --------------------------------------------------
# MAIN ENTRY
# --------------------------------------------------
def compare_product(user_query: str):
    query = build_search_query(user_query)
    raw = google_search(query)

    return {
        "query": user_query,
        "results": extract_results(raw)
    }
