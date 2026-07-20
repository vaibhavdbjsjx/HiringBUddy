import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "HiringBuddy"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hiringbuddy.db")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "dummy-key")
    # AI provider selection: groq | sambanova | openai. Empty = auto-detect from key.
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    # Optional AI provider overrides (else provider-appropriate defaults are used).
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "")
    AI_MODEL: str = os.getenv("AI_MODEL", "")
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "dummy@example.com")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "dummy-password")

    # Auth / JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-insecure-secret-change-me-in-production-0000")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24 * 7))
    
    class Config:
        env_file = ".env"

settings = Settings()
