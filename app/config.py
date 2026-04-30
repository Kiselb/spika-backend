import os
from dotenv import load_dotenv

load_dotenv()  # Загружает .env из текущей рабочей директории

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
