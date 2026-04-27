"""Application configuration management."""

import os
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Language
    app_language: str = os.getenv("APP_LANGUAGE", "en")
    
    # Backend Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Database Configuration
    database_url: str = os.getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./marketing_team.db"
    )
    
    # LLM Model Configuration
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Options: gpt-3.5-turbo, gpt-4o-mini, gpt-4-turbo

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

