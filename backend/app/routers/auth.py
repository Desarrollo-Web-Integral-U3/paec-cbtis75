from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserCreatePublic, UserOut, UserLogin, Token
from app.models.user import User, RolUsuario

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreatePublic, db: Session = Depends(get_db)):
    """
    Registro público: cualquier persona puede crear una cuenta.
    El rol SIEMPRE será ESTUDIANTE — sin importar lo que envie el cliente.
    Enviar rol=docente o rol=scrum_master es ignorado (el campo no existe
    en UserCreatePublic) y el registro queda como estudiante. Issue #6.
    """
    repo = UserRepository(db)
    if repo.get_by_email(payload.email) or repo.get_by_numero_control(payload.numero_control):
        raise HTTPException(status_code=400, detail="Usuario ya registrado.")

    user = User(
        nombre_completo=payload.nombre_completo,
        numero_control=payload.numero_control,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=RolUsuario.ESTUDIANTE,  # siempre forzado: issue #6
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
    """
    repo = UserRepository(db)
    if repo.get_by_email(payload.email) or repo.get_by_numero_control(payload.numero_control):
        raise HTTPException(status_code=400, detail="Usuario ya registrado.")

    user = User(
        nombre_completo=payload.nombre_completo,
        numero_control=payload.numero_control,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=payload.rol,  # aqui si se respeta el rol: el RBAC ya valido que quien llama es docente
    )
    return repo.create(user)


@router.post("/login", response_model=Token)
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    # NOTA: además del rate limit global de slowapi (100/min, en main.py),
    # para login se recomienda un límite más estricto, p.ej. decorar con
    # @limiter.limit("5/minute") para mitigar fuerza bruta (OWASP).
    repo = UserRepository(db)
    user = repo.get_by_email(payload.email)

    # Mensaje genérico: no revelar si fue el usuario o la contraseña
    # (evita enumeración de usuarios - buena práctica OWASP)
    credenciales_invalidas = HTTPException(status_code=401, detail="Credenciales inválidas.")

    if not user or not verify_password(payload.password, user.password_hash):
        raise credenciales_invalidas

    token = create_access_token({"sub": str(user.id), "rol": user.rol.value})
    return Token(access_token=token)
