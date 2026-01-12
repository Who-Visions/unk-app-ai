
"""
Configuration Settings
======================
Centralized configuration for environment variables and constants.
"""
import logging
import os

from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Logging Setup
# We configure basic logging here so it's available early
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unk_agent")

# Environment Configuration
ENV = os.environ.get("ENV", "development")
PORT = int(os.environ.get("PORT", 8080))
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "who-visions-tester")
os.environ["GOOGLE_CLOUD_PROJECT"] = GCP_PROJECT # Ensure set for SDKs

GCP_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_LOCATION # Ensure set for SDKs

os.environ["GOOGLE_CLOUD_LOCATION"] = GCP_LOCATION # Ensure set for SDKs

GOOGLE_GENAI_API_KEY = os.environ.get("GOOGLE_GENAI_API_KEY")

# Notion Integrations
# "Who Visions Teamspace" Integration
NOTION_WHO_VISIONS_SECRET = os.environ.get("NOTION_WHO_VISIONS_SECRET")

# "The Observatory" Integration (Agent Housing)
NOTION_OBSERVATORY_SECRET = os.environ.get("NOTION_OBSERVATORY_SECRET")


# Firebase Config
FIREBASE_SERVICE_ACCOUNT_PATH = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")

def get_env_bool(key: str, default: bool = False) -> bool:
    """Helper to get boolean env vars."""
    val = os.environ.get(key, str(default)).lower()
    return val in ["true", "1", "yes", "on"]
