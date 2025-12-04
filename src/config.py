import os
from dotenv import load_dotenv

load_dotenv()

# Server Config
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8001"))

# Backend Config
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")
SERVER_AUTH_KEY = os.getenv("SERVER_AUTH_KEY")
