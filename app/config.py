import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    STEAM_API_KEY: str = os.getenv("STEAM_API_KEY", "")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "secret-key-123")

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Экспортируем готовый экземпляр
settings = Settings()