from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.rate_limit import limiter
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserCreatePublic, UserOut, UserLogin, Token
from app.services.user_arco_service import anonimizar_usuario
from app.models.user import User, RolUsuario

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Mensaje único para el rechazo por falta de consentimiento — centralizado
# para que router y tests coincidan.
MSG_SIN_CONSENTIMIENTO = "Debes aceptar el aviso de privacidad para registrarte."


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreatePublic, db: Session = Depends(get_db)):
    """
    Registro público: cualquier persona puede crear una cuenta.
    El rol SIEMPRE será ESTUDIANTE — sin importar lo que envie el cliente.
    Enviar rol=docente o rol=scrum_master es ignorado (el campo no existe
    en UserCreatePublic) y el registro queda como estudiante. Issue #6.

    Se rechaza con 400 si el usuario no aceptó el aviso de privacidad
    (LFPDPPP / GDPR). Cuando sí lo acepta, se guarda la fecha exacta
    (server-side) como prueba auditable.
    """
    if not payload.consentimiento_privacidad:
        raise HTTPException(status_code=400, detail=MSG_SIN_CONSENTIMIENTO)

    repo = UserRepository(db)
    if repo.get_by_email(payload.email) or repo.get_by_numero_control(payload.numero_control):
        raise HTTPException(status_code=400, detail="Usuario ya registrado.")

    user = User(
        nombre_completo=payload.nombre_completo,
        numero_control=payload.numero_control,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=RolUsuario.ESTUDIANTE,  # siempre forzado: issue #6
        consentimiento_privacidad=True,
        fecha_consentimiento=datetime.utcnow(),
    )
    return repo.create(user)


@router.post("/register/docente", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_docente(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: None = Depends(require_role("docente")),
):
    """
    Registro protegido: solo un docente autenticado puede invocar este endpoint.
    Permite crear usuarios con cualquier rol (incluyendo docente).
    Requiere: Authorization: Bearer <token_de_docente>. Issue #6.

    También exige registrar el consentimiento del usuario que se está
    creando — el docente confirma que obtuvo la aceptación offline.
    """
    if not payload.consentimiento_privacidad:
        raise HTTPException(status_code=400, detail=MSG_SIN_CONSENTIMIENTO)

    repo = UserRepository(db)
    if repo.get_by_email(payload.email) or repo.get_by_numero_control(payload.numero_control):
        raise HTTPException(status_code=400, detail="Usuario ya registrado.")

    user = User(
        nombre_completo=payload.nombre_completo,
        numero_control=payload.numero_control,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=payload.rol,  # aqui si se respeta el rol: el RBAC ya valido que quien llama es docente
        consentimiento_privacidad=True,
        fecha_consentimiento=datetime.utcnow(),
    )
    return repo.create(user)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # OWASP A07: mitigacion de fuerza bruta — max 5 intentos/min por IP
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    """
    Autenticacion de usuario.
    Rate limit: 5 intentos por minuto por IP de origen.
    Al superar el limite el cliente recibe HTTP 429 Too Many Requests.
    """
    repo = UserRepository(db)
    user = repo.get_by_email(payload.email)

    # Mensaje generico: no revelar si fue el usuario o la contrasena
    # (evita enumeracion de usuarios - buena practica OWASP)
    credenciales_invalidas = HTTPException(status_code=401, detail="Credenciales invalidas.")

    if not user or not verify_password(payload.password, user.password_hash):
        raise credenciales_invalidas

    token = create_access_token({"sub": str(user.id), "rol": user.rol.value})
    return Token(access_token=token)


@router.post("/token", response_model=Token, include_in_schema=False)
def token(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Endpoint compatible con el flujo OAuth2 Password de Swagger UI.
    Acepta credenciales como form-encoded (username = email, password = ...).
    Uso exclusivo del boton Authorize en /docs — el frontend sigue usando
    POST /api/v1/auth/login con JSON. Ambos delegan en el mismo verificador
    de credenciales.
    """
    repo = UserRepository(db)
    user = repo.get_by_email(form.username)  # username del form == email
    credenciales_invalidas = HTTPException(
        status_code=401,
        detail="Credenciales inválidas.",
    )
    if not user or not verify_password(form.password, user.password_hash):
        raise credenciales_invalidas

    access_token = create_access_token(
        {"sub": str(user.id), "rol": user.rol.value},
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def obtener_mi_perfil(current_user: User = Depends(get_current_user)):
    """
    Devuelve el perfil del usuario autenticado.

    Requerido por el frontend para renderizar la pantalla de perfil
    (mostrar a quién se está por eliminar antes de confirmar el DELETE).
    """
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def eliminar_mi_cuenta(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ejerce el derecho ARCO de Cancelación (LFPDPPP).

    - Anonimiza IN-PLACE los campos PII del usuario (nombre, email,
      numero_control, password_hash) — la fila NO se elimina.
    - Estampa `fecha_anonimizacion` para invalidar cualquier JWT viejo
      (ver core/dependencies.get_current_user).
    - Preserva la integridad referencial: tasks, dailies y team_members
      siguen apuntando al mismo user_id (ahora anónimo).

    Idempotente: si la cuenta ya está anonimizada, `get_current_user`
    devuelve 401 antes de llegar aquí — nunca se ejecuta dos veces.

    Responde 204 No Content (sin body).
    """
    anonimizar_usuario(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
