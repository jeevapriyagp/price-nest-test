from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from ..core.database import SessionLocal
from ..models.models import Product, Alert, User, Wishlist


def normalize_query(q: str) -> str:
    return q.strip().lower()


# -----------------------------
# PRODUCT + PRICE HISTORY
# -----------------------------
def upsert_product(query, results):
    db: Session = SessionLocal()
    query = normalize_query(query)
    product_objects = []

    try:
        for r in results:
            # Check if product with this link already exists for this query
            existing = db.query(Product).filter(
                Product.query == query,
                Product.link == r["link"]
            ).first()

            if existing:
                # Update price and timestamp
                existing.price = r["price_numeric"]
                existing.created_at = datetime.utcnow()
                db.add(existing)
                product_objects.append(existing)
            else:
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
        return output
    finally:
        db.close()


def get_products(query):
    db: Session = SessionLocal()
    query = normalize_query(query)
    try:
        products = db.query(Product).filter(Product.query == query).all()
        return [
            {
                "id": p.id,
                "title": p.title,
                "source": p.source,
                "link": p.link,
                "image": p.image,
                "store_logo": p.store_logo,
                "price_numeric": p.price,
                "price": f"₹{int(p.price):,}" if p.price else "₹0",
                "created_at": p.created_at
            } for p in products
        ]
    finally:
        db.close()


def get_product(query):
    db: Session = SessionLocal()
    query = normalize_query(query)
    try:
        return db.query(Product).filter(Product.query == query).first()
    finally:
        db.close()


# -----------------------------
# ALERTS
# -----------------------------
def add_alert(email, query, target_price, notify_method="email"):
    db: Session = SessionLocal()
    query = normalize_query(query)
    try:
        alert = Alert(
            email=email,
            query=query,
            target_price=target_price,
            is_active=True
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return {
            "id": alert.id,
            "email": alert.email,
            "query": alert.query,
            "target_price": alert.target_price,
            "last_alerted_price": alert.last_alerted_price,
            "is_active": alert.is_active,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
    finally:
        db.close()


def list_alerts(email: str):
    db: Session = SessionLocal()
    try:
        alerts = db.query(Alert).filter(Alert.email == email).all()
        return [
            {
                "id": a.id,
                "email": a.email,
                "query": a.query,
                "target_price": a.target_price,
                "last_alerted_price": a.last_alerted_price,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in alerts
        ]
    finally:
        db.close()


def list_all_alerts():
    db: Session = SessionLocal()
    try:
        alerts = db.query(Alert).all()
        return [
            {
                "id": a.id,
                "email": a.email,
                "query": a.query,
                "target_price": a.target_price,
                "last_alerted_price": a.last_alerted_price,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None
            } for a in alerts
        ]
    finally:
        db.close()


def update_alert_status(alert_id: int, is_active: bool):
    db: Session = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        alert.is_active = is_active
        db.commit()
        db.refresh(alert)
        return {
            "id": alert.id,
            "email": alert.email,
            "query": alert.query,
            "target_price": alert.target_price,
            "last_alerted_price": alert.last_alerted_price,
            "is_active": alert.is_active,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
    finally:
        db.close()


def delete_alert(alert_id: int):
    db: Session = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return False
        db.delete(alert)
        db.commit()
        return True
    finally:
        db.close()


def deactivate_alert(alert_id: int):
    db: Session = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_active = False
            db.commit()
        return True
    finally:
        db.close()


def update_alert_price(alert_id: int, last_price: float):
    db: Session = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.last_alerted_price = last_price
            db.commit()
            return True
        return False
    finally:
        db.close()


# -----------------------------
# USERS
# -----------------------------
def get_user_by_email(email: str):
    db: Session = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).first()
    finally:
        db.close()


def create_user(first_name, last_name, email, hashed_password):
    db: Session = SessionLocal()
    try:
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def update_user(email: str, first_name: str, last_name: str):
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return None
        user.first_name = first_name
        user.last_name = last_name
        db.commit()
        db.refresh(user)
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email
        }
    finally:
        db.close()


# -----------------------------
# WISHLIST
# -----------------------------
def add_to_wishlist(email: str, product_id: int):
    db: Session = SessionLocal()
    try:
        # Check if already in wishlist
        existing = db.query(Wishlist).filter(
            Wishlist.email == email,
            Wishlist.product_id == product_id
        ).first()

        if existing:
            return existing

        wish_item = Wishlist(email=email, product_id=product_id)
        db.add(wish_item)
        db.commit()
        db.refresh(wish_item)
        return wish_item
    finally:
        db.close()


def remove_from_wishlist(email: str, product_id: int):
    db: Session = SessionLocal()
    try:
        wish_item = db.query(Wishlist).filter(
            Wishlist.email == email,
            Wishlist.product_id == product_id
        ).first()

        if wish_item:
            db.delete(wish_item)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_wishlist(email: str):
    db: Session = SessionLocal()
    try:
        items = (
            db.query(Product)
            .join(Wishlist, Product.id == Wishlist.product_id)
            .filter(Wishlist.email == email)
            .all()
        )
        return [
            {
                "id": p.id,
                "query": p.query,
                "title": p.title,
                "source": p.source,
                "link": p.link,
                "image": p.image,
                "price": p.price,
                "created_at": p.created_at
            } for p in items
        ]
    finally:
        db.close()