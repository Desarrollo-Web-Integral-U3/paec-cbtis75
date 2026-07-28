"""
Tests del endpoint /api/v1/cron/evaluar-alertas.

Cubre los casos criticos:
- Sin header X-Cron-Secret debe rechazar (401 o 503 si no hay secret cfg).
- Con dependency overrideada (secret valido simulado) responde 200 y
  retorna el resumen con equipos_evaluados y alertas_nuevas.
"""
from app.core.dependencies import verify_cron_secret
from app.main import app


def test_cron_sin_header_es_rechazado(client):
    """
    Sin CRON_SECRET configurado el server responde 503. Si estuviera
    configurado responderia 401 por falta de header. Ambos son validos
    para este smoke test.
    """
    r = client.post("/api/v1/cron/evaluar-alertas")
    assert r.status_code in (401, 503)


def test_cron_con_secret_valido_responde_ok(client):
    """
    Simulamos un secret valido overrideando la dependency. El endpoint
    debe responder 200 y devolver el shape correcto aunque la BD de
    prueba este vacia (equipos_evaluados == 0).
    """
    app.dependency_overrides[verify_cron_secret] = lambda: True
    try:
        r = client.post("/api/v1/cron/evaluar-alertas")
        assert r.status_code == 200
        data = r.json()
        assert "equipos_evaluados" in data
        assert "alertas_nuevas" in data
        assert data["equipos_evaluados"] == 0
        assert data["alertas_nuevas"] == 0
    finally:
        app.dependency_overrides.pop(verify_cron_secret, None)
