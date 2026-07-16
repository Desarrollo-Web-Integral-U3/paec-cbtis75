"""
PATRÓN DE DISEÑO: Repository
------------------------------
Aísla el acceso a datos (SQLAlchemy/Session) del resto de la aplicación.
Los routers y servicios NUNCA hacen `db.query(...)` directamente: siempre
pasan por un Repository. Esto permite, por ejemplo, cambiar de PostgreSQL
a otro motor, o mockear el acceso a datos en pruebas unitarias, sin tocar
la lógica de negocio ni los endpoints.
"""
from typing import Generic, TypeVar, Type

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, db: Session, model: Type[ModelType]):
        self.db = db
        self.model = model

    def get_by_id(self, id_: int) -> ModelType | None:
        return self.db.query(self.model).filter(self.model.id == id_).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> list[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, obj: ModelType) -> ModelType:
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.commit()
