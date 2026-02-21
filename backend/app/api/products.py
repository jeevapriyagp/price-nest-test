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

    try:
        cached = storage.get_products(q)
        if cached:
            last_update = cached[0].get("created_at")
            if last_update and (datetime.utcnow() - last_update.replace(tzinfo=None)) < timedelta(hours=24):
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
