"""
Instancia unica del rate limiter (slowapi) para toda la app.

Se extrae a su propio modulo para evitar import ciclico entre main.py
(que registra la app y el limiter global) y los routers que quieren
aplicar limites especificos con @limiter.limit("N/minute").
"""
import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# El rate limiter se desactiva cuando la variable de entorno
# DISABLE_RATE_LIMIT esta seteada a "1", "true" o "yes". Esto se usa
# durante la suite de pruebas para evitar falsos 429 causados por que
# el TestClient envia todas las peticiones desde 127.0.0.1 y supera
# los umbrales pensados para trafico humano real.
_ENABLED = os.getenv("DISABLE_RATE_LIMIT", "").lower() not in ("1", "true", "yes")

# Limiter compartido: keyed por IP del cliente. El default global de
# 100/min sigue viviendo aqui; los endpoints sensibles pueden bajarlo
# con @limiter.limit("N/minute") en su decorador.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
    enabled=_ENABLED,
)
