from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DB_URL: str = "sqlite:///./cards.db"
    OCR_CONFIDENCE: float = 0.8
    
    # OCR API 配置
    OCR_URL: str = "https://local_llm.star-bit.io/api/card"
    OCR_TIMEOUT: int = 30
    OCR_VERIFY_SSL: bool = False
    OCR_RETRY_ATTEMPTS: int = 2
    
    # OCR降級策略配置
    OCR_FALLBACK_ENABLED: bool = True
    OCR_LOG_LEVEL: str = "INFO"
    
    model_config = {"case_sensitive": True}

settings = Settings() 