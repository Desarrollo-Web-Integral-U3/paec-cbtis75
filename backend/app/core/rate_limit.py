"""
Instancia unica del rate limiter (slowapi) para toda la app.

Se extrae a su propio modulo para evitar import ciclico entre main.py
(que registra la app y el limiter global) y los routers que quieren
aplicar limites especificos con @limiter.limit("N/minute").
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter compartido: keyed por IP del cliente. El default global de
# 100/min sigue viviendo aqui; los endpoints sensibles pueden bajarlo
# con @limiter.limit("N/minute") en su decorador.
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
