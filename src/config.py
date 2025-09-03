import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Telegram bot token
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Authorized users (comma-separated IDs in .env)
AUTHORIZED_USERS = [
    int(x) for x in os.getenv("AUTHORIZED_USERS", "").split(",") if x.strip().isdigit()
]
