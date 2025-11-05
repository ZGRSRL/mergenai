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
    postgres_host: str = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
    
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
        # Fix Docker hostname issue: if host is 'db' and we're not in Docker, use 'localhost'
        db_host = self.postgres_host
        if db_host == 'db':
            # Check if we're running in Docker
            # Method 1: Check /proc/1/cgroup (Linux)
            # Method 2: Check environment variable DOCKER_CONTAINER
            # Method 3: Check if we can resolve 'db' hostname
            import os
            import socket
            
            is_docker = False
            # Check environment variable
            if os.getenv('DOCKER_CONTAINER') == 'true' or os.getenv('DOCKER') == 'true':
                is_docker = True
            # Check Linux cgroup
            elif os.path.exists('/proc/1/cgroup'):
                try:
                    with open('/proc/1/cgroup', 'r') as f:
                        if 'docker' in f.read():
                            is_docker = True
                except:
                    pass
            
            # If not in Docker, try to resolve 'db' hostname
            if not is_docker:
                try:
                    socket.gethostbyname('db')
                    # If we can resolve 'db', we're probably in Docker network
                    is_docker = True
                except socket.gaierror:
                    # Cannot resolve 'db', use localhost
                    db_host = 'localhost'
        
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{db_host}:{self.postgres_port}/{self.postgres_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


settings = Settings()
