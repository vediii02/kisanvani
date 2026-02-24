import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    # Database
    MYSQL_HOST: str = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT: int = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER: str = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD: str = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE: str = os.getenv('MYSQL_DATABASE', 'kisanvani_db')
    
    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Qdrant
    QDRANT_URL: str = os.getenv('QDRANT_URL', 'http://localhost:6333')
    QDRANT_COLLECTION: str = 'agricultural_kb'
    
    # LLM
    EMERGENT_LLM_KEY: str = os.getenv('EMERGENT_LLM_KEY', '')
    DEFAULT_LLM_PROVIDER: str = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
    DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'gpt-5.2')
    
    # Voice Providers
    DEFAULT_STT_PROVIDER: str = os.getenv('DEFAULT_STT_PROVIDER', 'mock')
    DEFAULT_TTS_PROVIDER: str = os.getenv('DEFAULT_TTS_PROVIDER', 'mock')
    
    # CORS
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')
    
    # RAG - Lower threshold to allow more direct answers
    CONFIDENCE_THRESHOLD: float = 0.60

settings = Settings()