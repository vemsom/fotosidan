import os
from pathlib import Path

class Settings:
    """Application settings from environment variables."""

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///storage/fotosidan.db")
        self.storage_path = Path(os.getenv("STORAGE_PATH", "storage"))
        self.site_title = os.getenv("SITE_TITLE", "Fotosidan")
        self.admin_enabled = os.getenv("ADMIN_ENABLED", "true").lower() == "true"
        self.admin_secret = os.getenv("ADMIN_SECRET", "")
        self.host = os.getenv("HOST", "127.0.0.1")
        self.port = int(os.getenv("PORT", "8000"))
        self.admin_port = int(os.getenv("ADMIN_PORT", "8001"))
        self.max_upload_size = int(os.getenv("MAX_UPLOAD_SIZE", "52428800"))  # 50MB in bytes

        # Ensure storage directories exist
        self.photos_path = self.storage_path / "photos"
        self.thumb_path = self.photos_path / "thumb"
        self.display_path = self.photos_path / "display"

        self.photos_path.mkdir(parents=True, exist_ok=True)
        self.thumb_path.mkdir(parents=True, exist_ok=True)
        self.display_path.mkdir(parents=True, exist_ok=True)

settings = Settings()
