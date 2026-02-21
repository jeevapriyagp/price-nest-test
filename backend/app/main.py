import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from .api import auth, products, alerts, wishlist, analytics

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

# If running on Vercel, the /api prefix is already handled by vercel.json routing
# When running locally, we keep the /api prefix for convenience
API_PREFIX = "" if os.environ.get("VERCEL") == "1" else "/api"

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(alerts.router, prefix=API_PREFIX)
app.include_router(wishlist.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)


@app.get("/")
def read_root():
    return {"message": "Welcome to PriceNest API", "status": "online"}


handler = Mangum(app)