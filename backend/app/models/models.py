from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


# -----------------------------
# PRODUCT
# -----------------------------
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    title = Column(String)
    source = Column(String)
    link = Column(String, unique=False)
    image = Column(String, nullable=True)
    store_logo = Column(String, nullable=True)
    price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# PRICE HISTORY
# -----------------------------
class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    source = Column(String)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# ALERTS
# -----------------------------
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    query = Column(String, index=True)
    target_price = Column(Float)
    last_alerted_price = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# -----------------------------
# USERS
# -----------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


# -----------------------------
# WISHLIST
# -----------------------------
class Wishlist(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))

    product = relationship("Product")
