"""
PATRÓN DE DISEÑO: Strategy
-----------------------------
Cada proveedor de almacenamiento de objetos (Cloudinary, S3, Supabase,
disco local) es una estrategia intercambiable. Hoy usamos Cloudinary por
su tier gratuito generoso, pero migrar a otro proveedor solo requiere
agregar una clase nueva que implemente StorageStrategy y cambiar la
instancia devuelta por get_storage_backend() — sin tocar routers ni
services de negocio. Cumple OCP (Open/Closed) del SOLID.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import cloudinary
import cloudinary.uploader

from app.core.config import get_settings


# --- Validaciones (compartidas por todas las estrategias) ---
MAX_FILE_SIZE_BYTES: int = 4 * 1024 * 1024  # 4 MB (issue #7)

ALLOWED_MIME_TYPES: set[str] = {
    # Imagenes
    "image/jpeg",
    "image/png",
    "image/webp",
    # PDF
    "application/pdf",
    # Office (docx / xlsx / pptx)
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}

ALLOWED_EXTENSIONS: set[str] = {
    "jpg", "jpeg", "png", "webp",
    "pdf",
    "docx", "xlsx", "pptx",
}


@dataclass
class UploadResult:
    """Resultado de una subida: URL publica y ID interno del proveedor."""
    url: str
    public_id: str


class StorageStrategy(ABC):
    """Contrato abstracto para cualquier proveedor de almacenamiento."""

    @abstractmethod
    def upload(self, file_bytes: bytes, filename: str, folder: str) -> UploadResult:
        """Sube el archivo y regresa URL publica + public_id."""
        ...

    @abstractmethod
    def delete(self, public_id: str) -> None:
        """Elimina el archivo remoto por public_id."""
        ...


class CloudinaryStorageStrategy(StorageStrategy):
    """
    Estrategia concreta que sube a Cloudinary usando el SDK oficial.
    resource_type='auto' permite imagenes, PDFs y documentos Office con la
    misma llamada; Cloudinary detecta el tipo por magic bytes.
    """

    def __init__(self) -> None:
        settings = get_settings()
        cloudinary.config(
            cloud_name=settings.cloudinary_cloud_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            secure=True,
        )

    def upload(self, file_bytes: bytes, filename: str, folder: str) -> UploadResult:
        response = cloudinary.uploader.upload(
            file_bytes,
            folder=folder,
            filename_override=filename,
            resource_type="auto",
            use_filename=True,
            unique_filename=True,
            overwrite=False,
        )
        return UploadResult(
            url=response["secure_url"],
            public_id=response["public_id"],
        )

    def delete(self, public_id: str) -> None:
        cloudinary.uploader.destroy(public_id, resource_type="auto")


# --- Selector de backend (permite cambiar proveedor sin tocar consumidores) ---
def get_storage_backend() -> StorageStrategy:
    """
    Fabrica del backend de almacenamiento activo.
    Preparada para leer un settings.storage_provider en el futuro.
    """
    return CloudinaryStorageStrategy()


# --- Validador puro (independiente del backend) ---
def validate_file(filename: str, content_type: str, size_bytes: int) -> None:
    """
    Valida extension, MIME type y tamano contra listas blancas.
    Lanza ValueError con mensaje en espanol si algo falla.
    """
    if size_bytes > MAX_FILE_SIZE_BYTES:
        mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise ValueError(
            f"El archivo excede el tamano maximo permitido ({mb} MB)."
        )

    if "." not in filename:
        raise ValueError("El archivo no tiene extension.")

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Extension '{extension}' no permitida. "
            f"Permitidas: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
        )

    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Tipo MIME '{content_type}' no permitido."
        )