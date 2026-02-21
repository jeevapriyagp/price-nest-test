from fastapi import APIRouter, HTTPException
from ..schemas.schemas import WishlistRequest
from ..services import storage

router = APIRouter(prefix="/wishlist", tags=["wishlist"])

@router.post("")
def add_to_wishlist(req: WishlistRequest):
    item = storage.add_to_wishlist(req.email, req.product_id)
    if not item:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "ok"}


@router.delete("")
def remove_from_wishlist(req: WishlistRequest):
    success = storage.remove_from_wishlist(req.email, req.product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "ok"}


@router.get("")
def get_wishlist(email: str):
    items = storage.get_wishlist(email)
    return {"status": "ok", "wishlist": items}
