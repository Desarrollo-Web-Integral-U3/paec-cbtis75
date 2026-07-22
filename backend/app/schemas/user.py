from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, field_validator

from app.models.user import RolUsuario


class UserBase(BaseModel):
    nombre_completo: str
    numero_control: str
    email: EmailStr
    rol: RolUsuario = RolUsuario.ESTUDIANTE


class UserCreate(UserBase):
    # Pydantic valida el tipo/longitud automáticamente -> cumple
    # "Validación de Datos en Cliente/BackEnd" y "principio de minimización":
    # el front solo debe enviar estos campos, ni uno más.
    password: str
    # Consentimiento explícito del aviso de privacidad. Sin default -> el
    # cliente OBLIGATORIAMENTE tiene que mandarlo. Si viene False, el router
    # responde 400. NO exponemos fecha_consentimiento aquí: el servidor la
    # fija con datetime.utcnow() al registrar (nunca confiar en timestamps
    # que vengan del cliente).
    consentimiento_privacidad: bool


class UserCreatePublic(BaseModel):
    """
    Schema exclusivo para el endpoint público POST /api/v1/auth/register.

    El campo `rol` NO existe aquí: el handler siempre asignará RolUsuario.ESTUDIANTE,
    independientemente de cualquier valor que el cliente intente enviar en el JSON.
    Esto cierra la vulnerabilidad del issue #6 a nivel de validación de schema,
    antes de que el dato llegue siquiera al handler.
    """
    nombre_completo: str
    numero_control: str
    email: EmailStr
    password: str
    # Consentimiento explícito del aviso de privacidad — mismo criterio que en UserCreate.
    consentimiento_privacidad: bool

    @field_validator("nombre_completo")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("El nombre completo no puede estar vacío.")
        return v.strip()


class UserOut(UserBase):
    id: int
    # Incluidos para transparencia y auditoría: el usuario recibe la
    # confirmación de que su consentimiento quedó registrado y cuándo.
    consentimiento_privacidad: bool
    fecha_consentimiento: datetime | None = None
    model_config = ConfigDict(from_attributes=True)
    # OJO: password_hash NUNCA se incluye aquí -> evita
    # "Fuga de Datos Masiva / Excessive Data Exposure" (OWASP, Actividad 2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
