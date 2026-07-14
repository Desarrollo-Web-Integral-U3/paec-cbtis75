"""
Prueba unitaria mínima de ejemplo. Con esto GitHub Actions ya tiene algo
que ejecutar en cada PR (requisito de CI/CD). Amplíen esta suite conforme
avancen: registro, login, RBAC por rol, kanban, alertas, etc.
"""
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hash_roundtrip():
    plano = "MiClaveSegura123"
    hashed = hash_password(plano)
    assert hashed != plano
    assert verify_password(plano, hashed) is True
    assert verify_password("otra_clave", hashed) is False


def test_jwt_roundtrip():
    token = create_access_token({"sub": "1", "rol": "estudiante"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["rol"] == "estudiante"


def test_jwt_invalido():
    assert decode_access_token("token.invalido.xyz") is None
