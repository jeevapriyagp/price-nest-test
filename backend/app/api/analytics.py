import logging
from fastapi import APIRouter, HTTPException
from ..services.analytics import analyze_price

router = APIRouter(tags=["analytics"])
logger = logging.getLogger("pricenest")

@router.get("/analytics")
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
