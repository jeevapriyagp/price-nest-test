import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timedelta

from .backend_scrapper import compare_product
from .analytics_engine import analyze_price
from . import storage
from .auth_utils import get_password_hash, verify_password


# -----------------------
# Logging
# -----------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pricenest")


# -----------------------
# FastAPI App
# -----------------------
app = FastAPI(
    title="PriceNest API",
    version="1.0.0"
)


# -----------------------
# CORS
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------
# Models
# -----------------------
class CompareResponse(BaseModel):
    query: str
    results: List[dict]


class AlertRequest(BaseModel):
    email: str
    query: str
    target_price: int
    notify_method: Optional[str] = "email"


class AlertStatusUpdate(BaseModel):
    is_active: bool


class UserSignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class WishlistRequest(BaseModel):
    email: str
    product_id: int


# -----------------------
# Thread Pool
# -----------------------
EXECUTOR = ThreadPoolExecutor(max_workers=4)
SCRAPER_TIMEOUT = 12


# ===========================================================
# PRODUCT COMPARE
# ===========================================================
@app.get("/compare", response_model=CompareResponse)
def compare(q: str):
    q = q.strip().lower()
    logger.info(f"[COMPARE] {q}")

    try:
        cached = storage.get_products(q)
        if cached:
            last_update = cached[0].get("created_at")
            if last_update and (datetime.utcnow() - last_update) < timedelta(hours=24):
                logger.info(f"[CACHE HIT] {q}")
                return {"query": q, "results": cached}
    except Exception as e:
        logger.error(f"Cache check failed: {e}")

    future = EXECUTOR.submit(compare_product, q)

    try:
        data = future.result(timeout=SCRAPER_TIMEOUT)
    except FuturesTimeout:
        raise HTTPException(status_code=504, detail="Scraper timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        results = storage.upsert_product(q, data.get("results", []))
        return {"query": q, "results": results}
    except Exception:
        return data


# ===========================================================
# ALERTS (FINAL FIX)
# ===========================================================

@app.post("/alerts")
def create_alert(req: AlertRequest):
    try:
        query = req.query.strip().lower()
        logger.info(f"[ALERT CREATE] {query} for {req.email}")

        # Ensure product exists
        if not storage.get_product(query):
            try:
                # 🔍 DEBUG: Log that we are scraping
                logger.info(f"[ALERT CREATE] Product not found, scraping: {query}")
                fresh = compare_product(query)
                if not fresh or "results" not in fresh:
                    logger.error(f"[ALERT CREATE] Scraper returned invalid data for {query}: {fresh}")
                    raise HTTPException(status_code=500, detail="Failed to fetch product data")
                
                storage.upsert_product(query, fresh.get("results", []))
            except Exception as e:
                logger.error(f"[ALERT CREATE] Scraper failed for {query}: {e}")
                # We can allow the alert to be created even if scraping fails, 
                # but for now let's fail to let user know product is invalid.
                raise HTTPException(status_code=500, detail=f"Failed to verify product: {str(e)}")

        alert = storage.add_alert(
            email=req.email,
            query=query,
            target_price=req.target_price,
            notify_method=req.notify_method  # This is safe even if DB ignores it? Yes, function arg.
        )
        
        logger.info(f"[ALERT CREATE] Success: {alert}")
        return {"status": "ok", "alert": alert}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[ALERT CREATE] Database/System error: {e}")
        raise HTTPException(status_code=500, detail=f"System error: {str(e)}")


# ✅ FIXED: email optional + safe + always returns list
@app.get("/alerts")
def get_alerts(email: Optional[str] = Query(None)):
    """
    Usage:
    /alerts?email=user@gmail.com
    """

    try:
        if email:
            logger.info(f"[ALERT LIST] {email}")
            alerts = storage.list_alerts(email)
        else:
            # fallback (for debugging)
            logger.info("[ALERT LIST] all alerts")
            alerts = storage.list_all_alerts()

        # Ensure list format
        if not alerts:
            return []

        return alerts

    except Exception as e:
        logger.error(f"Fetch alerts failed: {e}")
        raise HTTPException(status_code=503, detail="Database error")


@app.put("/alerts/{alert_id}")
def update_alert_status(alert_id: int, req: AlertStatusUpdate):
    logger.info(f"[ALERT UPDATE] {alert_id} -> {req.is_active}")
    updated = storage.update_alert_status(alert_id, req.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok", "alert": updated}


@app.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int):
    logger.info(f"[ALERT DELETE] {alert_id}")
    success = storage.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok"}


# ===========================================================
# ANALYTICS
# ===========================================================
@app.get("/analytics")
def analytics(q: str):
    q = q.strip().lower()
    logger.info(f"[ANALYTICS] {q}")

    try:
        result = analyze_price(q)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analytics failure for {q}: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Analytics service temporarily unavailable (database connection issue)"
        )


# ===========================================================
# AUTH
# ===========================================================
@app.post("/auth/signup")
def signup(req: UserSignupRequest):
    existing_user = storage.get_user_by_email(req.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(req.password)

    user = storage.create_user(
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        hashed_password=hashed_password
    )

    return {"status": "ok", "user": user.email}


@app.post("/auth/login")
def login(req: UserLoginRequest):
    user = storage.get_user_by_email(req.email)

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "status": "ok",
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
    }


# ===========================================================
# WISHLIST
# ===========================================================
@app.post("/wishlist")
def add_to_wishlist(req: WishlistRequest):
    item = storage.add_to_wishlist(req.email, req.product_id)
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@app.delete("/wishlist")
def remove_from_wishlist(req: WishlistRequest):
    success = storage.remove_from_wishlist(req.email, req.product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "ok"}


@app.get("/wishlist")
def get_wishlist(email: str):
    items = storage.get_wishlist(email)
    return {"status": "ok", "wishlist": items}
