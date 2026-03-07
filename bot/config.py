import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE_URL = "http://127.0.0.1:8000/api/v1"