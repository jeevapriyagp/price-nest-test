import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env from backend/ root
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback to local env vars if not set (useful for CI or different envs)
    DATABASE_URL = os.environ.get("DATABASE_URL")

# API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Email Config
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def validate_config():
    missing = []
    if not DATABASE_URL: missing.append("DATABASE_URL")
    if not SERPAPI_KEY: missing.append("SERPAPI_KEY")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

# Validate on import for critical keys
validate_config()
