import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    database_url: str
    jwt_secret: str
    imagekit_private_key: str | None
    imagekit_public_key: str | None
    imagekit_url: str | None

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
        self.jwt_secret = self._required("JWT_SECRET")
        self.imagekit_private_key = os.getenv("IMAGEKIT_PRIVATE_KEY")
        self.imagekit_public_key = os.getenv("IMAGEKIT_PUBLIC_KEY")
        self.imagekit_url = os.getenv("IMAGEKIT_URL")

    @staticmethod
    def _required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            raise RuntimeError(f"{name} environment variable is required")
        return value

    @property
    def imagekit_configured(self) -> bool:
        return all(
            [
                self.imagekit_private_key,
                self.imagekit_public_key,
                self.imagekit_url,
            ]
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
