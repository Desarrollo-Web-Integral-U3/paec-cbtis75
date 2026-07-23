"""
Endpoint generico de subida de evidencias.

Reutilizable por Kanban, Dailies y cualquier feature que necesite
persistir un archivo del usuario en Cloudinary. Aplica validaciones
OWASP:
- Whitelist de MIME + extension.
- Limite de tamano (4 MB).
- Rate limit por IP (10/min).
- Autenticacion obligatoria (JWT via get_current_user).
"""
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.core.dependencies import get_current_user
from app.core.rate_limit import limiter
from app.schemas.upload import UploadResponse
from app.services.storage_service import (
    get_storage_backend,
    validate_file,
)

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


@router.post("/evidencia", response_model=UploadResponse, status_code=201)
@limiter.limit("10/minute")
async def subir_archivo_evidencia(
    request: Request,
    archivo: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """
    Sube un archivo de evidencia a Cloudinary y regresa la URL publica.

    Uso desde el frontend: se llama primero a este endpoint, se obtiene la
    URL, y luego se envia esa URL al endpoint de negocio correspondiente
    (kanban /mover, dailies, etc). Asi la logica de storage vive en un
    solo lugar y los endpoints de negocio no tocan Cloudinary.
    """
    contenido = await archivo.read()
    try:
        validate_file(
            filename=archivo.filename or "",
            content_type=archivo.content_type or "",
            size_bytes=len(contenido),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    backend = get_storage_backend()
    resultado = backend.upload(
        file_bytes=contenido,
        filename=archivo.filename or "archivo",
        folder="paec/evidencias",
    )
    return UploadResponse(url=resultado.url, public_id=resultado.public_id)