import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Database
DATABASE_URL = os.environ.get("DATABASE_URL")

# API Keys
SERPAPI_KEY = os.environ.get("SERPAPI_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Email Config
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
