"""Authentication configuration for the application."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Team credentials
TEAM_USERNAME = os.getenv("TEAM_USERNAME", "teamuser")
TEAM_PASSWORD = os.getenv("TEAM_PASSWORD", "teampass")