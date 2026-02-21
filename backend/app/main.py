import os
import sys
import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# -----------------------
# Path Fix for Vercel
# -----------------------
# Ensure the current directory is in sys.path for robust imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

try:
    from .api import auth, products, alerts, wishlist, analytics
except (ImportError, ValueError):
    try:
        from api import auth, products, alerts, wishlist, analytics
    except ImportError as e:
        print(f"Import Error: {e}")
        # We will handle missing routers below to avoid crashing

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
# Routes
# -----------------------
# We keep the /api prefix as it matches both local dev and Vercel routing
API_PREFIX = "/api"

try:
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(products.router, prefix=API_PREFIX)
    app.include_router(alerts.router, prefix=API_PREFIX)
    app.include_router(wishlist.router, prefix=API_PREFIX)
    app.include_router(analytics.router, prefix=API_PREFIX)
except NameError:
    logger.error("One or more routers failed to import")


@app.get("/")
def read_root():
    return {"message": "Welcome to PriceNest API", "status": "online"}

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "environment": "vercel" if os.environ.get("VERCEL") == "1" else "local",
        "database": "configured" if os.environ.get("DATABASE_URL") else "missing"
    }

