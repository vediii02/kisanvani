import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    # Database
    PG_HOST: str = os.getenv('PG_HOST', 'localhost')
    PG_PORT: int = int(os.getenv('PG_PORT', '5432'))
    PG_USER: str = os.getenv('PG_USER', 'postgres')
    PG_PASSWORD: str = os.getenv('PG_PASSWORD', 'postgres')
    PG_DATABASE: str = os.getenv('PG_DATABASE', 'kisanvani')
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_HOST}:{self.PG_PORT}/{self.PG_DATABASE}"
    
    # Redis
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))

    @property
    def REDIS_URL(self) -> str:
        explicit_redis_url = os.getenv('REDIS_URL')
        if explicit_redis_url:
            return explicit_redis_url
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # PGVector Embeddings
    PG_VECTOR_DIM: int = int(os.getenv('PG_VECTOR_DIM', '1536'))
    
    # LLM
    EMERGENT_LLM_KEY: str = os.getenv('EMERGENT_LLM_KEY', '')
    DEFAULT_LLM_PROVIDER: str = os.getenv('DEFAULT_LLM_PROVIDER', 'openai')
    DEFAULT_LLM_MODEL: str = os.getenv('DEFAULT_LLM_MODEL', 'gpt-5.2')
    
    # Voice Providers
    DEFAULT_STT_PROVIDER: str = os.getenv('DEFAULT_STT_PROVIDER', 'mock')
    DEFAULT_TTS_PROVIDER: str = os.getenv('DEFAULT_TTS_PROVIDER', 'mock')
    
    # API Keys
    SARVAM_API_KEY: str = os.getenv('SARVAM_API_KEY', '')
    GOOGLE_TTS_API_KEY: str = os.getenv('GOOGLE_TTS_API_KEY', '')
    
    # CORS
    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS', '*')
    
    # RAG - Lower threshold to allow more direct answers
    CONFIDENCE_THRESHOLD: float = 0.60

settings = Settings()
