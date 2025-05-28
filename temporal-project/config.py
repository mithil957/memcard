import os

QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
PB_APP_USER_EMAIL = os.getenv("PB_APP_USER_EMAIL", "tempbot@memcard.com")
PB_APP_USER_PASSWORD = os.getenv("PB_APP_USER_PASSWORD", "password2")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "add_an_api_key_from_gemini")

if GEMINI_API_KEY == "add_an_api_key_from_gemini" or not GEMINI_API_KEY:
    print("WARNING: Default or missing GEMINI_API_KEY is being used.")


