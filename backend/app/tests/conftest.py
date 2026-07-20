"""
Fixtures compartidas para toda la suite de tests.

- Usamos SQLite in-memory (poolclass=StaticPool para que TODAS las sesiones
  vean la misma BD dentro del mismo test) en lugar de PostgreSQL.
- Sobrescribimos la dependencia `get_db` de FastAPI para que los endpoints
  bajo prueba usen esa BD desechable.
- El fixture `client` regresa un TestClient de FastAPI listo para hacer
  requests HTTP contra la app real.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
