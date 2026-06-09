import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Get credentials from environment variables (no defaults)
API_ID = os.environ.get("API_ID")
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Validate that all required variables are set
if not all([API_ID, API_HASH, BOT_TOKEN]):
    raise ValueError(
        "Missing required environment variables!\n"
        "Please set: API_ID, API_HASH, BOT_TOKEN"
    )

# Try to convert API_ID to integer
try:
    API_ID = int(API_ID)
except (ValueError, TypeError):
    raise ValueError("API_ID must be a valid integer")

# Configuration
WEBHOOK = os.environ.get("WEBHOOK", "False").lower() == "true"
PORT = int(os.environ.get("PORT", 8000))
