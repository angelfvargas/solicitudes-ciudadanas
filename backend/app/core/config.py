"""Configuración leída de variables de entorno (o del archivo .env).

Ningún secreto vive en el código: si falta JWT_SECRET la aplicación no arranca.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/vennex"

    jwt_secret: str = Field(min_length=32)  # un secreto corto se puede adivinar por fuerza bruta
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # IA (opcional). Sin llave, la funcionalidad de IA responde 503 y el resto del sistema sigue igual.
    gemini_api_key: str | None = None
    # Varios modelos separados por coma, en orden de preferencia (respaldo si uno está saturado).
    gemini_model: str = "gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite"
    ai_timeout_seconds: float = 12.0

    cors_origins: list[str] = ["http://localhost:5173"]
    # Carpeta con el build de React. Si existe, el backend la sirve (despliegue monolítico).
    frontend_dist: str = "../frontend/dist"


@lru_cache
def get_settings() -> Settings:
    return Settings()
