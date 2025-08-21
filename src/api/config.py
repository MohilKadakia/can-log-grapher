"""Configuration settings for the API client."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Base URLs
API_BASE_URL = os.getenv("API_BASE_URL")
AUTH_BASE_URL = os.getenv("AUTH_BASE_URL")
LOGS_BASE_URL = os.getenv("LOGS_BASE_URL")  

# Firebase configuration
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID")
FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID")
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")


# Request settings
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5  # exponential backoff multiplier

# Upload settings
MAX_UPLOAD_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks for large uploads
ALLOWED_EXTENSIONS = ['.csv', '.txt']

# Network settings
REQUIRE_WIFI = True  # Only allow uploads on WiFi
CHECK_NETWORK_INTERVAL = 5  # seconds

# Mock API settings (for development)
USE_MOCK_API = True  # Set to False when connecting to real API
MOCK_DELAY = 0.5  # seconds to simulate network latency