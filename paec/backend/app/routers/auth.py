from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserOut, UserLogin, Token
from app.models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    if repo.get_by_email(payload.email) or repo.get_by_numero_control(payload.numero_control):
        raise HTTPException(status_code=400, detail="Usuario ya registrado.")

    user = User(
        nombre_completo=payload.nombre_completo,
        numero_control=payload.numero_control,
        email=payload.email,
        password_hash=hash_password(payload.password),
        rol=payload.rol,
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
