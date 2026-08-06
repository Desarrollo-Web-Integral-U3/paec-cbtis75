"""
Servicio de IA - Resumen semanal de dailies con Groq (LLM).

Consume el servicio de terceros Groq (API compatible con OpenAI) para
generar, en lenguaje natural, un resumen del último ciclo de dailies de
un equipo Scrum. Cubre:

- Actividad 3 · Servicios web de terceros (segunda API externa además de SMTP).
- Actividad 3 · Uso de Inteligencia Artificial y cualquiera de las
  funcionalidades (analiza dailies reales del sistema).

El endpoint que expone este servicio es POST /api/v1/ai/resumen-semanal/{team_id}
en `app/routers/ai.py`. Solo miembros del equipo y docentes pueden invocarlo.
"""
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.daily import Daily


SYSTEM_PROMPT = (
    "Eres un asistente Scrum experto en analizar dailies de equipos de "
    "desarrollo escolares (metodología ABP + Scrum + Design Sprint). "
    "Recibes los dailies de la última semana de un equipo y devuelves un "
    "resumen ejecutivo en ESPAÑOL, en formato Markdown, con exactamente "
    "estas tres secciones y en este orden:\n"
    "\n"
    "## Avances principales\n"
    "Enumera los logros concretos del equipo esta semana (3-5 puntos).\n"
    "\n"
    "## Blockers e impedimentos\n"
    "Enumera los obstáculos recurrentes o sin resolver (0-5 puntos). "
    "Si no hay, dilo explícitamente.\n"
    "\n"
    "## Sentimiento y recomendación\n"
    "Un párrafo corto (2-3 oraciones) evaluando la moral del equipo y "
    "una recomendación práctica para el Scrum Master.\n"
    "\n"
    "Reglas: sé conciso, específico, sin relleno. Nunca inventes datos "
    "que no aparezcan en los dailies. Si los dailies son escasos o "
    "vacíos, indícalo con honestidad."
)


def _formatear_dailies(dailies: list[Daily]) -> str:
    """
    Convierte los dailies en un bloque de texto plano que la IA pueda leer.
    Deliberadamente NO se incluye el user_id (evitamos PII); solo se
    mencionan integrantes de forma anónima ("Integrante A", etc.), lo que
    respeta la Actividad 1 · Trazabilidad sin PII.
    """
    if not dailies:
        return "(sin dailies registrados esta semana)"

    # Mapeo anónimo user_id -> "Integrante N"
    integrantes = {}
    for d in dailies:
        if d.user_id not in integrantes:
            integrantes[d.user_id] = f"Integrante {chr(65 + len(integrantes))}"

    lineas = []
    for d in sorted(dailies, key=lambda x: x.fecha):
        integrante = integrantes[d.user_id]
        fecha_str = d.fecha.strftime("%Y-%m-%d") if d.fecha else "s/f"
        lineas.append(f"[{fecha_str}] {integrante}")
        lineas.append(f"  · Ayer: {d.que_hice_ayer}")
        lineas.append(f"  · Hoy: {d.que_hare_hoy}")
        if d.impedimentos:
            lineas.append(f"  · Impedimentos: {d.impedimentos}")
        if d.acuerdos:
            lineas.append(f"  · Acuerdos: {d.acuerdos}")
        lineas.append("")

    return "\n".join(lineas)


def _consultar_groq(prompt_usuario: str) -> str:
    """
    Llama a la API de Groq (compatible con OpenAI). Devuelve el texto
    generado por el LLM o levanta HTTPException si algo falla.
    """
    settings = get_settings()

    if not settings.groq_api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "GROQ_API_KEY no configurada en el servidor. Añádela en "
                "backend/.env y reinicia el backend."
            ),
        )

    payload = {
        "model": settings.groq_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_usuario},
        ],
        "temperature": 0.4,
        "max_tokens": 800,
    }
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                f"{settings.groq_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"No se pudo contactar el servicio de IA (Groq): {e}",
        )

    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Groq respondió {r.status_code}: {r.text[:200]}",
        )

    try:
        return r.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, ValueError):
        raise HTTPException(
            status_code=502,
            detail="Respuesta inválida del servicio de IA.",
        )


def generar_resumen_semanal(db: Session, team_id: int) -> dict:
    """
    Punto de entrada principal del servicio.

    1. Lee dailies del equipo de los últimos 7 días.
    2. Los formatea anonimizando integrantes (sin PII).
    3. Llama a Groq para obtener un resumen ejecutivo en Markdown.
    4. Devuelve un dict con {resumen, dailies_analizados, rango, modelo}.
    """
    hace_7_dias = datetime.utcnow() - timedelta(days=7)

    dailies = (
        db.query(Daily)
        .filter(Daily.team_id == team_id, Daily.fecha >= hace_7_dias)
        .order_by(Daily.fecha.asc())
        .all()
    )

    prompt_usuario = (
        f"Dailies del equipo {team_id} en los últimos 7 días "
        f"(desde {hace_7_dias.strftime('%Y-%m-%d')} hasta hoy):\n\n"
        + _formatear_dailies(dailies)
    )

    resumen = _consultar_groq(prompt_usuario)

    return {
        "resumen": resumen,
        "dailies_analizados": len(dailies),
        "rango": {
            "desde": hace_7_dias.date().isoformat(),
            "hasta": datetime.utcnow().date().isoformat(),
        },
        "modelo": get_settings().groq_model,
        "generado_en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
