import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from backend/ root IF IT EXISTS (local dev only)
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = os.getenv("DATABASE_URL")

# API Keys
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
if not SERPAPI_KEY:
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Email Config
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")

# Note: We don't call validate_config() at root level to prevent 
# Vercel from crashing before we can see logs or handle errors.
