from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    """DTO de respuesta al subir un archivo a almacenamiento remoto."""

    url: str
    public_id: str

    # extra='forbid' bloquea mass assignment (OWASP API3:2019)
    model_config = ConfigDict(extra="forbid")
