# Integración de correo real (Resend)

Guía para configurar y verificar el envío real de correos desde el sistema
PAEC. Sustituye al `EmailNotifier` simulado que solo imprimía en consola.

## Por qué Resend

- Setup en < 5 minutos (login con GitHub, sin verificación de dominio).
- Free tier de 3,000 correos/mes (100/día) — más que suficiente para R1.
- API de una sola llamada HTTP, sin SDK obligatorio.
- Sandbox `onboarding@resend.dev` funciona out-of-the-box sin dominio propio.

## Setup paso a paso

### 1. Crear cuenta en Resend

1. Ir a https://resend.com
2. **Get Started** → login con GitHub (recomendado, es instantáneo).
3. Aceptar los términos de servicio.

### 2. Generar una API key

1. En el dashboard, panel izquierdo, ir a **API Keys**.
2. **Create API Key**:
   - **Name**: `PAEC dev` (o el que prefieras).
   - **Permission**: `Full access` (o `Sending access` si prefieres granular).
   - **Domain**: `All domains` (default).
3. Copiar la key que aparece (empieza con `re_`). **Solo se muestra una vez**
   — si la pierdes, hay que generar otra.

### 3. Configurar el `.env` del backend

Editar `backend/.env` (créalo desde `backend/.env.example` si no existe):

```env
NOTIFICATION_PROVIDER=email
EMAIL_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxx   # ← tu key de Resend
EMAIL_API_URL=https://api.resend.com/emails
EMAIL_FROM=PAEC <onboarding@resend.dev>
```

> `EMAIL_FROM` puede quedar tal cual mientras uses el sandbox de Resend.
> Si más adelante verificas un dominio propio (`paec.cbtis75.edu.mx`,
> por ejemplo), cambia el remitente a `PAEC <no-reply@paec.cbtis75.edu.mx>`.

### 4. Reiniciar el backend con la nueva configuración

```bash
docker compose down
docker compose up -d --build backend
```

## Verificación: mandar un correo de prueba

Hay un script CLI dedicado:

```bash
docker compose exec backend python -m app.scripts.probar_email TU_CORREO@ejemplo.com
```

Salida esperada:

```
Enviando correo de prueba a TU_CORREO@ejemplo.com...
Notifier activo: EmailNotifier
2026-XX-XX ... [INFO] app.factories.notification_factory:
    Correo enviado a TU_CORREO@ejemplo.com vía Resend (id=abc-123, asunto='PAEC: Correo de prueba desde el sistema PAEC').
Listo. Revisa tu bandeja de entrada (y Spam por si acaso).
```

Si el status code es 4xx/5xx verás un `ERROR` con el detalle que devuelva
Resend. Normalmente:

| Error | Causa | Solución |
|---|---|---|
| `Missing API key` | Falta `EMAIL_API_KEY` en `.env` | Poner la key y reiniciar backend |
| `The from address is not verified` | Usaste un dominio no verificado | Cambiar `EMAIL_FROM` a `onboarding@resend.dev` |
| `Invalid to field` | Mal escrito el destinatario | Revisar el argumento del script |

## Evidencia (caso real)

Screenshot de un correo recibido con la integración funcionando:

![Correo recibido en la bandeja del Scrum Master](./evidencias/email-recibido.png)

_Reemplazar con tu screenshot real después de correr el script._

**Cómo tomar la evidencia**:
1. Correr `docker compose exec backend python -m app.scripts.probar_email tu-correo@gmail.com`.
2. Abrir Gmail (o el cliente que uses).
3. Screenshot del correo abierto mostrando:
   - Remitente `PAEC <onboarding@resend.dev>`.
   - Asunto `PAEC: Correo de prueba...`.
   - Cuerpo del mensaje.
4. Guardar en `docs/evidencias/email-recibido.png`.

## Dónde se dispara en producción

Con `NOTIFICATION_PROVIDER=email` los siguientes flujos empiezan a mandar
correo real automáticamente, sin cambios en su código (patrón Factory):

| Flujo | Se dispara cuando | Servicio |
|---|---|---|
| Alerta diaria de atrasos | GitHub Actions cron llama `POST /api/v1/cron/evaluar-alertas` cada día | `services/alert_service.py` |
| Evidencia nueva sin aprobar | El estudiante hace `PATCH /api/v1/historia/{id}/mover` con `evidencia_url` | `services/evidence_notification_service.py` |
| Evaluación manual por equipo | `POST /api/v1/equipo/{id}/evaluar-alertas` (rol docente o scrum_master) | `services/alert_service.py` |

Todos usan `NotificationFactory.get_notifier()`, que resuelve a
`EmailNotifier` cuando `NOTIFICATION_PROVIDER=email`.

## Rotación de la API key

Si sospechas que la key se filtró (accidentalmente commiteada, capturada en
un log, etc.):

1. Resend dashboard → **API Keys** → tres puntitos en la key comprometida →
   **Revoke**.
2. Crear una nueva.
3. Actualizar `EMAIL_API_KEY` en `.env` local y en los secrets de GitHub
   (`Settings → Secrets and variables → Actions`).
4. `docker compose up -d --build backend` para que el backend tome la nueva.
