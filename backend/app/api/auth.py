from fastapi import APIRouter, HTTPException, Depends
from ..schemas.schemas import UserSignupRequest, UserLoginRequest, UserProfileUpdate
from ..services import storage
from ..core.security import get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
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

    return {
        "status": "ok",
        "user": {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
    }


@router.post("/login")
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


@router.put("/profile")
def update_profile(req: UserProfileUpdate):
    user = storage.get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = storage.update_user(req.email, req.first_name, req.last_name)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update profile")

    return {
        "status": "ok",
        "user": {
            "first_name": updated["first_name"],
            "last_name": updated["last_name"],
            "email": updated["email"]
        }
    }
