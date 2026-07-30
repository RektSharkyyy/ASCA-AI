import os
from pathlib import Path
from typing import Dict, Any, List
import yaml
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "config"

class Settings(BaseSettings):
    APP_ENV: str = Field(default="development", env="APP_ENV")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")

    OPENROUTER_API_KEY: str = Field(default="", env="OPENROUTER_API_KEY")
    OPENAI_API_KEY: str = Field(default="", env="OPENAI_API_KEY")
    GOOGLE_API_KEY: str = Field(default="", env="GOOGLE_API_KEY")
    DEFAULT_LLM_PROVIDER: str = Field(default="openrouter", env="DEFAULT_LLM_PROVIDER")

    TELEGRAM_BOT_TOKEN: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_ADMIN_CHAT_ID: str = Field(default="", env="TELEGRAM_ADMIN_CHAT_ID")

    CHROMA_DB_DIR: str = Field(default=str(BASE_DIR / "data" / "chroma_db"), env="CHROMA_DB_DIR")
    DATABASE_URL: str = Field(default=f"sqlite+aiosqlite:///{BASE_DIR}/data/asca_ai.db", env="DATABASE_URL")

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

def load_yaml_config(filename: str) -> Dict[str, Any]:
    file_path = CONFIG_DIR / filename
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

class AppConfig:
    def __init__(self):
        self.env = Settings()
        self.params = load_yaml_config("param.yaml")
        self.models = load_yaml_config("models.yaml")

config = AppConfig()
