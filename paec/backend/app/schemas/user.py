from pydantic import BaseModel, EmailStr, ConfigDict

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


class UserOut(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
    # OJO: password_hash NUNCA se incluye aquí -> evita
    # "Fuga de Datos Masiva / Excessive Data Exposure" (OWASP, Actividad 2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
