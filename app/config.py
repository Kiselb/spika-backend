import os
from dotenv import load_dotenv

load_dotenv()  # Загружает .env из текущей рабочей директории

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
BOT_SECRET_KEY = os.getenv("BOT_SECRET_KEY")
if not BOT_SECRET_KEY:
    raise RuntimeError("BOT_SECRET_KEY is not set")
