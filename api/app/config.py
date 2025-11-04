import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    api_port: int = 8000
    env: str = "dev"
    
    # Database
    postgres_user: str = "postgres"
    postgres_password: str = "sarlio41"
    postgres_db: str = "ZGR_AI"  # RAG servisi için ZGR_AI kullan
    postgres_port: int = 5432
    postgres_host: str = "db"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # LLM
    llm_provider: str = "ollama"
    ollama_host: str = "http://host.docker.internal:11434"
    generator_model: str = "llama3"
    extractor_model: str = "llama3"
    
    # SAM Integration (future)
    sam_enabled: bool = False
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
