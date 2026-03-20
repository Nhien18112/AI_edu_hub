# Code để load các biến môi trường từ file .env
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    GROQ_API_KEY: str
    COLLECTION_NAME: str = "ai_edu_docs"
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50

    class Config:
        env_file = ".env"

settings = Settings()