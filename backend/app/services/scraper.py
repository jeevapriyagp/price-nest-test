import json
import re
import statistics
from urllib.parse import urlparse
from serpapi import GoogleSearch
from ..core.config import SERPAPI_KEY


# --------------------------------------------------
# BUILD SMART SEARCH QUERY (USER TYPES ONLY PRODUCT)
# --------------------------------------------------
def build_search_query(q: str) -> str:
    return f"{q} buy price"

# --------------------------------------------------
# TITLE RELEVANCE CHECKER
# --------------------------------------------------
def _tokenize(text: str) -> list[str]:
    """Lowercase alphanumeric tokens from a string."""
    return re.findall(r"[a-z0-9]+", text.lower())

def is_relevant_title(title: str, user_query: str) -> bool:
    """
    Returns True only if the result title contains ALL tokens from the user query
    (case-insensitive substring match). Single-char tokens are ignored.
    """
    query_tokens = [t for t in _tokenize(user_query) if len(t) > 1]
    if not query_tokens:
        return True  # nothing to filter on
    title_text = title.lower()
    return all(tok in title_text for tok in query_tokens)

# --------------------------------------------------
# STRICT PRICE EXTRACTOR (NO EMI EVER)
# --------------------------------------------------
def extract_prices(text: str):
    if not text:
        return []

    emi_pattern = re.compile(
        r"""
        (
            (₹|Rs\.?|INR)\s?[\d,]+\s*(/mo(nth)?|per\s*month|x\s*\d+\s*(months?|EMIs?))
            |
            (no[\s-]?cost[\s-]?)?emi\s*(from|starting|at|of|:)?\s*(₹|Rs\.?|INR)?\s*[\d,]+
            |
            (₹|Rs\.?|INR)\s?[\d,]+\s*emi
        )
        """,
        re.IGNORECASE | re.VERBOSE
    )
    cleaned = emi_pattern.sub("", text)

    matches = re.findall(r"(₹|Rs\.?|INR)\s?([\d,]+)", cleaned)

    prices = []
    for _, num in matches:
        val = int(num.replace(",", ""))
        if 500 <= val <= 5_000_000:
            prices.append(val)

    return prices

# --------------------------------------------------
# EMI KEYWORD DETECTOR
# --------------------------------------------------
_EMI_KEYWORDS = re.compile(
    r"\bemi\b|no[\s-]?cost|per\s*month|/mo\b|monthly\s*instalment",
    re.IGNORECASE,
)
_URL_FIELDS = {"link", "thumbnail", "image", "source_icon", "favicon", "serpapi_link"}

def item_signals_emi(item: dict) -> bool:
    for key, val in item.items():
        if key in _URL_FIELDS or val is None:
            continue
        if _EMI_KEYWORDS.search(str(val)):
            return True
    return False

# --------------------------------------------------
# STATISTICAL EMI OUTLIER FILTER
# --------------------------------------------------
EMI_OUTLIER_RATIO = 0.40

def filter_emi_outliers(results: list) -> list:
    if len(results) < 2:
        return results

    prices = [r["price_numeric"] for r in results]
    median = statistics.median(prices)
    threshold = median * EMI_OUTLIER_RATIO

    filtered = [r for r in results if r["price_numeric"] >= threshold]
    return filtered if filtered else results

# --------------------------------------------------
# DOMAIN NORMALIZER
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
def extract_results(data: dict, user_query: str):
    results = []

    # ---------- GOOGLE SHOPPING ----------
    for item in data.get("shopping_results", []):
        link = item.get("link")
        title = item.get("title")
        price_text = item.get("price")

        if not link or not title or not price_text:
            continue
        if not is_relevant_title(title, user_query):
            continue
        if item_signals_emi(item):
            continue

        domain = get_domain(link)
        prices = extract_prices(price_text)
        if not prices:
            continue

        results.append({
            "title": title,
            "source": domain,
            "link": link,
            "price_numeric": max(prices),
            "price": f"₹{max(prices):,}",
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
        if not is_relevant_title(title, user_query):
            continue
        if item_signals_emi(item):
            continue

        domain = get_domain(link)
        prices = extract_prices(price_text)
        if not prices:
            continue

        results.append({
            "title": title,
            "source": domain,
            "link": link,
            "price_numeric": max(prices),
            "price": f"₹{max(prices):,}",
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
        if not is_relevant_title(title, user_query):
            continue

        domain = get_domain(link)
        prices = extract_prices(title + " " + snippet)
        if not prices:
            continue

        results.append({
            "title": title,
            "source": domain,
            "link": link,
            "price_numeric": max(prices),
            "price": f"₹{max(prices):,}",
            "image": item.get("thumbnail"),
            "store_logo": item.get("favicon")
        })
    
    # Sort, then drop statistical EMI outliers
    results = sorted(results, key=lambda x: x["price_numeric"])
    results = filter_emi_outliers(results)

    return results

# --------------------------------------------------
# MAIN ENTRY
# --------------------------------------------------
def compare_product(user_query: str):
    query = build_search_query(user_query)
    raw = google_search(query)

    return {
        "query": user_query,
        "results": extract_results(raw, user_query)  
    }