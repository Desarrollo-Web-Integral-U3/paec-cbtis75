"""
Configuración global de la aplicación.

PATRÓN DE DISEÑO: Singleton
--------------------------------
get_settings() está decorado con @lru_cache, por lo que SOLO se construye
una instancia de Settings en toda la vida del proceso. Cualquier módulo que
llame get_settings() recibe siempre la MISMA instancia (mismo id en memoria).
Esto evita releer el .env o reconstruir el objeto de configuración en cada
request, y centraliza el acceso a variables sensibles (secret keys, URLs de
BD, credenciales de terceros).
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- General ---
    app_name: str = "PAEC - Gestión de Proyectos Escolares"
    environment: str = "development"

    # --- Base de datos ---
    database_url: str = "postgresql+psycopg2://paec_user:paec_pass@db:5432/paec_db"

    # --- Seguridad / JWT ---
    jwt_secret_key: str = "CHANGE_ME_IN_ENV"  # nunca dejar este valor en producción
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- CORS ---
    cors_origins: list[str] = ["http://localhost:5173"]

    # --- Servicio de terceros (notificaciones) ---
    notification_provider: str = "console"  # "console" | "email" | "webhook"
    email_api_key: str | None = None
    email_api_url: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
