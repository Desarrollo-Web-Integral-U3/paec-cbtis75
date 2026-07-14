"""
Capa de conexión a PostgreSQL.

Aquí también aplicamos el patrón Singleton: `engine` se crea UNA sola vez
a nivel de módulo. SQLAlchemy internamente gestiona un connection pool sobre
ese engine, así que jamás debe crearse un segundo engine para la misma base
de datos dentro del proceso.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import get_settings

settings = get_settings()

# Instancia única (singleton) del engine de conexión a la BD
engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesión de BD por request y la cierra al final."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
