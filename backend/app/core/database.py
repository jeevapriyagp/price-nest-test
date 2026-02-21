import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

engine = None
SessionLocal = None

if DATABASE_URL:
    # Clean Neon URL safely
    clean_url = DATABASE_URL.replace("channel_binding=require", "")

    engine = create_engine(
        clean_url,
        pool_pre_ping=True
    )

    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
else:
    print("⚠️ DATABASE_URL not set")