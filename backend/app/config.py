from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


class Settings(BaseSettings):
    APP_NAME: str = "MedLens AI"
    SECRET_KEY: str = "medlens-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    DATABASE_URL: str = "sqlite:///./medlens.db"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    UPLOAD_DIR: str = os.path.join(os.path.dirname(__file__), "..", "uploads")
    GRADCAM_DIR: str = os.path.join(os.path.dirname(__file__), "..", "gradcam_outputs")

    class Config:
        env_file = ".env"


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.GRADCAM_DIR, exist_ok=True)
