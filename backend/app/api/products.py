import logging
from fastapi import APIRouter, HTTPException
from typing import List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime, timedelta

from ..schemas.schemas import CompareResponse
from ..services import storage
from ..services.scraper import compare_product

router = APIRouter(tags=["products"])
logger = logging.getLogger("pricenest")

EXECUTOR = ThreadPoolExecutor(max_workers=4)
SCRAPER_TIMEOUT = 12

@router.get("/compare", response_model=CompareResponse)
def compare(q: str):
    q = q.strip().lower()
    logger.info(f"[COMPARE] {q}")

    # Cache check disabled per user request to always fetch from SerpAPI for compare tab.
    # Results will still be saved to DB for history/analytics.


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
