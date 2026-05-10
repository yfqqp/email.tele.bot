import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]
EMAIL_API_URL = os.getenv("EMAIL_API_URL", "https://www.1secmail.com/api/v1")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Email domains available
EMAIL_DOMAINS = [
    "1secmail.com", "1secmail.net", "1secmail.org",
    "ezztt.com", "guerillamail.com", "guerrillamail.net",
    "mailnator.com", "temp-mail.org"
]

# Max messages to show per page
MESSAGES_PER_PAGE = 8

# Cache time for messages (seconds)
CACHE_TIME = 30
