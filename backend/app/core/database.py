from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

# Clean the URL - remove channel_binding param that psycopg2 doesn't support
clean_url = DATABASE_URL
if clean_url.startswith("postgres://"):
    clean_url = clean_url.replace("postgres://", "postgresql://", 1)

if "channel_binding" in clean_url:
    import re
    clean_url = re.sub(r'[&?]channel_binding=[^&]*', '', clean_url)
    clean_url = clean_url.rstrip('?')

engine = create_engine(
    clean_url,
    pool_pre_ping=True,      # Detects dead connections before reuse (critical for Neon)
    pool_size=5,             # Max persistent connections
    max_overflow=10,         # Extra connections allowed under heavy load
    pool_recycle=300,        # Recycle connections every 5 mins (Neon times out idle ones)
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()