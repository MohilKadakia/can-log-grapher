"""Configuration settings for the API client."""

# API Base URLs
# Using placeholder URLs until Firebase is set up
API_BASE_URL = "https://api.placeholder.com/v1"
AUTH_BASE_URL = f"{API_BASE_URL}/auth"
LOGS_BASE_URL = f"{API_BASE_URL}/logs"

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