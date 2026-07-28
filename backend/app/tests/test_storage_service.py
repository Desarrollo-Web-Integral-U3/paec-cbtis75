"""
Tests unitarios del StorageService.

Se hace monkeypatch a cloudinary.uploader.upload y .destroy para no
golpear la API real; los tests validan la logica pura del contrato:
validaciones de tipo/tamano y forma del UploadResult.
"""
import pytest

from app.services.storage_service import (
    CloudinaryStorageStrategy,
    MAX_FILE_SIZE_BYTES,
    UploadResult,
    validate_file,
)


# --- validate_file: casos validos ---

def test_valida_imagen_png_dentro_del_limite():
    validate_file(filename="foto.png", content_type="image/png", size_bytes=1024)


def test_valida_pdf():
    validate_file(
        filename="reporte.pdf",
        content_type="application/pdf",
        size_bytes=1024,
    )


def test_valida_docx():
    validate_file(
        filename="acta.docx",
        content_type=(
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        size_bytes=1024,
    )


# --- validate_file: casos invalidos ---

def test_rechaza_archivo_sin_extension():
    with pytest.raises(ValueError, match="no tiene extension"):
        validate_file(
            filename="archivo",
            content_type="image/png",
            size_bytes=1024,
        )


def test_rechaza_extension_no_permitida():
    with pytest.raises(ValueError, match="Extension 'exe' no permitida"):
        validate_file(
            filename="virus.exe",
            content_type="application/x-msdownload",
            size_bytes=1024,
        )


def test_rechaza_mime_no_permitido():
    with pytest.raises(ValueError, match="Tipo MIME"):
        validate_file(
            filename="script.png",
            content_type="text/html",
            size_bytes=1024,
        )


def test_rechaza_archivo_muy_grande():
    with pytest.raises(ValueError, match="tamano maximo"):
        validate_file(
            filename="foto.png",
            content_type="image/png",
            size_bytes=MAX_FILE_SIZE_BYTES + 1,
        )


# --- CloudinaryStorageStrategy: upload monkeypatcheado ---

def test_upload_regresa_url_y_public_id(monkeypatch):
    fake_response = {
        "secure_url": (
            "https://res.cloudinary.com/demo/image/upload/v1/paec/foo.png"
        ),
        "public_id": "paec/evidencias/foo_abc123",
    }
    monkeypatch.setattr(
        "app.services.storage_service.cloudinary.uploader.upload",
        lambda *a, **kw: fake_response,
    )
    # Evita que __init__ intente cargar credenciales reales
    monkeypatch.setattr(
        "app.services.storage_service.cloudinary.config",
        lambda **kw: None,
    )

    backend = CloudinaryStorageStrategy()
    result = backend.upload(
        file_bytes=b"data",
        filename="foo.png",
        folder="paec/test",
    )

    assert isinstance(result, UploadResult)
    assert result.url == fake_response["secure_url"]
    assert result.public_id == fake_response["public_id"]


def test_delete_llama_destroy_con_public_id(monkeypatch):
    llamadas = []
    monkeypatch.setattr(
        "app.services.storage_service.cloudinary.uploader.destroy",
        lambda public_id, **kw: llamadas.append((public_id, kw)),
    )
    monkeypatch.setattr(
        "app.services.storage_service.cloudinary.config",
        lambda **kw: None,
    )

    backend = CloudinaryStorageStrategy()
    backend.delete("paec/evidencias/foo_abc123")

    assert llamadas == [
        ("paec/evidencias/foo_abc123", {"resource_type": "auto"}),
    ]
