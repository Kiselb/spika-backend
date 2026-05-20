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
MODEL_NAME = os.getenv("MODEL_NAME")
if not MODEL_NAME:
    raise RuntimeError("MODEL_NAME is not set")
PROXY_API_API_KEY = os.getenv("PROXY_API_API_KEY")
if not PROXY_API_API_KEY:
    raise RuntimeError("PROXY_API_API_KEY is not set")
PROXY_API_OPENAI_BASE_URL = os.getenv("PROXY_API_OPENAI_BASE_URL")
if not PROXY_API_OPENAI_BASE_URL:
    raise RuntimeError("PROXY_API_OPENAI_BASE_URL is not set")
