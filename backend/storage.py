from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from .database import SessionLocal
from .models import Product, PriceHistory, Alert, User, Wishlist


def normalize_query(q: str) -> str:
    return q.strip().lower()


# -----------------------------
# PRODUCT + PRICE HISTORY
# -----------------------------
def upsert_product(query, results):
    db: Session = SessionLocal()
    query = normalize_query(query)
    product_objects = []

    for r in results:
        # Check if product with this link already exists for this query
        existing = db.query(Product).filter(
            Product.query == query,
            Product.link == r["link"]
        ).first()

        if existing:
            product_objects.append(existing)
            continue

        product = Product(
            query=query,
            title=r["title"],
            source=r["source"],
            link=r["link"],
            image=r.get("image"),
            store_logo=r.get("store_logo"),
            price=r["price_numeric"],
            created_at=datetime.utcnow()
        )
        db.add(product)
        product_objects.append(product)

        history = PriceHistory(
            query=query,
            source=r["source"],
            price=r["price_numeric"],
            timestamp=datetime.utcnow()
        )
        db.add(history)

    db.commit()
    # Refresh to get IDs
    for p in product_objects:
        db.refresh(p)
    
    # Store return data before closing session
    output = [
        {
            "id": p.id,
            "title": p.title,
            "source": p.source,
            "link": p.link,
            "image": p.image,
            "store_logo": p.store_logo,
            "price_numeric": p.price,
            "price": f"₹{int(p.price):,}" if p.price else "₹0"
        } for p in product_objects
    ]
    
    db.close()
    return output


def get_product(query):
    db: Session = SessionLocal()
    query = normalize_query(query)
    product = db.query(Product).filter(Product.query == query).first()
    db.close()
    return product


def get_price_history(query):
    db: Session = SessionLocal()
    query = normalize_query(query)

    rows = (
        db.query(PriceHistory)
        .filter(PriceHistory.query == query)
        .order_by(PriceHistory.timestamp)
        .all()
    )

    db.close()

    return [
        {
            "timestamp": r.timestamp,
            "store": r.source,
            "price": r.price
        } for r in rows
    ]


# -----------------------------
# ALERTS
# -----------------------------
def add_alert(email, query, target_price, notify_method="email"):
    db: Session = SessionLocal()
    query = normalize_query(query)
    alert = Alert(
        email=email,
        query=query,
        target_price=target_price,
        is_active=True
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    db.close()
    return {
        "id": alert.id,
        "email": alert.email,
        "query": alert.query,
        "target_price": alert.target_price,
        "is_active": alert.is_active
    }


def list_alerts():
    db: Session = SessionLocal()
    alerts = db.query(Alert).all()
    db.close()
    return [
        {
            "id": a.id,
            "email": a.email,
            "query": a.query,
            "target_price": a.target_price,
            "is_active": a.is_active
        } for a in alerts
    ]

# -----------------------------
# USERS
# -----------------------------
def get_user_by_email(email: str):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    db.close()
    return user


def create_user(first_name, last_name, email, hashed_password):
    db: Session = SessionLocal()
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


# -----------------------------
# WISHLIST
# -----------------------------
def add_to_wishlist(email: str, product_id: int):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        return None
    
    # Check if already in wishlist
    existing = db.query(Wishlist).filter(
        Wishlist.user_id == user.id,
        Wishlist.product_id == product_id
    ).first()
    
    if existing:
        db.close()
        return existing

    wish_item = Wishlist(user_id=user.id, product_id=product_id)
    db.add(wish_item)
    db.commit()
    db.refresh(wish_item)
    db.close()
    return wish_item


def remove_from_wishlist(email: str, product_id: int):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        return False
    
    wish_item = db.query(Wishlist).filter(
        Wishlist.user_id == user.id,
        Wishlist.product_id == product_id
    ).first()
    
    if wish_item:
        db.delete(wish_item)
        db.commit()
        db.close()
        return True
    
    db.close()
    return False


def get_wishlist(email: str):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        db.close()
        return []
    
    items = (
        db.query(Product)
        .join(Wishlist, Product.id == Wishlist.product_id)
        .filter(Wishlist.user_id == user.id)
        .all()
    )
    
    result = []
    for p in items:
        result.append({
            "id": p.id,
            "query": p.query,
            "title": p.title,
            "source": p.source,
            "link": p.link,
            "image": p.image,
            "price": p.price,
            "created_at": p.created_at
        })
    
    db.close()
    return result

def deactivate_alert(alert_id: int):
    db: Session = SessionLocal()
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if alert:
        alert.is_active = False
        db.commit()
    
    db.close()
    return True

