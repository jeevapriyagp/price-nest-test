from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from ..services.summary import get_product_summary
except ImportError:
    from services.summary import get_product_summary

router = APIRouter()


class SummaryRequest(BaseModel):
    query: str


@router.post("/summary")
def ai_summary(body: SummaryRequest):
    if not body.query or not body.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    result = get_product_summary(body.query.strip())

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result