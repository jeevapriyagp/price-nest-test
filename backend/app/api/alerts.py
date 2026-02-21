import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..schemas.schemas import AlertRequest, AlertStatusUpdate
from ..services import storage
from ..services.scraper import compare_product

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger("pricenest")

@router.post("")
def create_alert(req: AlertRequest):
    try:
        query = req.query.strip().lower()
        logger.info(f"[ALERT CREATE] {query} for {req.email}")

        # Ensure product exists
        if not storage.get_product(query):
            try:
                logger.info(f"[ALERT CREATE] Product not found, scraping: {query}")
                fresh = compare_product(query)
                if not fresh or "results" not in fresh:
                    logger.error(f"[ALERT CREATE] Scraper returned invalid data for {query}: {fresh}")
                    raise HTTPException(status_code=500, detail="Failed to fetch product data")
                
                storage.upsert_product(query, fresh.get("results", []))
            except Exception as e:
                logger.error(f"[ALERT CREATE] Scraper failed for {query}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to verify product: {str(e)}")

        alert = storage.add_alert(
            email=req.email,
            query=query,
            target_price=req.target_price,
            notify_method=req.notify_method
        )
        
        logger.info(f"[ALERT CREATE] Success: {alert}")
        return {"status": "ok", "alert": alert}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"[ALERT CREATE] Database/System error: {e}")
        raise HTTPException(status_code=500, detail=f"System error: {str(e)}")


@router.get("")
def get_alerts(email: Optional[str] = Query(None)):
    try:
        if email:
            logger.info(f"[ALERT LIST] {email}")
            alerts = storage.list_alerts(email)
        else:
            logger.info("[ALERT LIST] all alerts")
            alerts = storage.list_all_alerts()

        if not alerts:
            return []

        return alerts

    except Exception as e:
        logger.error(f"Fetch alerts failed: {e}")
        raise HTTPException(status_code=503, detail="Database error")


@router.put("/{alert_id}")
def update_alert_status(alert_id: int, req: AlertStatusUpdate):
    logger.info(f"[ALERT UPDATE] {alert_id} -> {req.is_active}")
    updated = storage.update_alert_status(alert_id, req.is_active)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok", "alert": updated}


@router.delete("/{alert_id}")
def delete_alert(alert_id: int):
    logger.info(f"[ALERT DELETE] {alert_id}")
    success = storage.delete_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "ok"}
