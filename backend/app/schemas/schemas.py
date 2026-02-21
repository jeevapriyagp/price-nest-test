from pydantic import BaseModel
from typing import List, Optional

class CompareResponse(BaseModel):
    query: str
    results: List[dict]


class AlertRequest(BaseModel):
    email: str
    query: str
    target_price: float
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


class UserProfileUpdate(BaseModel):
    email: str
    first_name: str
    last_name: str
