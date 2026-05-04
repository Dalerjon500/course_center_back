import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(override=True)


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    value = value.strip()
    if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
        return int(value)

    raise ValueError(f"Invalid integer for {name}: {value!r}")


def _get_list_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = _get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = _get_int_env("REFRESH_TOKEN_EXPIRE_DAYS", 7)
    APP_LOGIN_URL: str = os.getenv("APP_LOGIN_URL", "https://course-center-front-swart.vercel.app/login")
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "").strip()
    TELEGRAM_WEBHOOK_SECRET: str = os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip()
    TELEGRAM_LINK_EXPIRE_MINUTES: int = _get_int_env("TELEGRAM_LINK_EXPIRE_MINUTES", 60)
    TELEGRAM_USE_POLLING: bool = os.getenv("TELEGRAM_USE_POLLING", "false").strip().lower() in {"1", "true", "yes"}
    CORS_ORIGINS: list[str] = _get_list_env(
        "CORS_ORIGINS",
        [
            "http://localhost:5173", "https://course-center-front-swart.vercel.app"
        ],
    )
    AUTO_CREATE_TABLES: bool = os.getenv("AUTO_CREATE_TABLES", "").strip().lower() in {"1", "true", "yes"}


settings = Settings()
