import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Telegram bot token
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_TABLE = os.getenv("DB_TABLE", "chat_to_club")

# ClubGG login configuration
UNION_LOGIN_ID = os.getenv("UNION_LOGIN_ID", "")
UNION_LOGIN_PWD = os.getenv("UNION_LOGIN_PWD", "")
CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY", "")