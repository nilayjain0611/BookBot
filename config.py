import os
from dotenv import load_dotenv

load_dotenv()

# Fetch the Telegram token from .env file
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
