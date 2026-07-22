"""
Seed de base de datos para demostración del sistema PAEC.

Uso:
    docker compose exec backend python -m app.scripts.seed

Es IDEMPOTENTE: si los usuarios/equipo/sprint ya existen, no los duplica.
Se puede correr las veces que quieras sin ensuciar la BD.

Deja el entorno listo para una demo completa:
- 4 usuarios (1 docente, 1 scrum_master, 2 estudiantes)  -> cubre los 3 roles
- 1 equipo "PAEC Demo" con los 3 miembros no-docentes
- 1 sprint activo (parcial 1) aprobado por el docente
- 7 tareas distribuidas entre los 3 integrantes con estados y prioridades variados
- 1 día del Design Sprint completado
- 1 daily de ejemplo
"""
from datetime import datetime, timedelta

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.models import (
    User,
    RolUsuario,
    Team,
    TeamMember,
    Sprint,
    Task,
    EstadoKanban,
    Prioridad,
    DesignSprintDay,
    DiaDesignSprint,
    Daily,
)

# Cumple la validación del frontend: >=8 chars, mayúscula, minúscula, número, especial.
PASSWORD_DEMO = "Demo1234!"


def _get_or_create_user(db, email: str, defaults: dict) -> User:
    """Devuelve el usuario si ya existe, lo crea si no. Nunca duplica."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, **defaults)
    db.add(user)
    db.flush()
    return user


def run() -> None:
    # Por si el seed se corre contra una BD recién levantada sin que la app
    # haya arrancado primero (sin este create_all las tablas no existirían).
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        hashed = hash_password(PASSWORD_DEMO)
        ahora = datetime.utcnow()

        # Defaults comunes de consentimiento del aviso de privacidad
        # (todos los usuarios del seed se consideran ya "aceptados" para
        # que la BD quede consistente con la nueva regla de NOT NULL).
        consent_defaults = {
            "consentimiento_privacidad": True,
            "fecha_consentimiento": ahora,
        }

        # --- Usuarios (1 por rol como mínimo; ponemos 4 para hacer la demo rica) --
        docente = _get_or_create_user(db, "docente@cbtis75.edu.mx", {
            "nombre_completo": "Prof. Luis Hernandez",
            "numero_control": "DOC00001",
            "password_hash": hashed,
            "rol": RolUsuario.DOCENTE,
            **consent_defaults,
        })
        scrum_master = _get_or_create_user(db, "scrummaster@cbtis75.edu.mx", {
            "nombre_completo": "Ana Torres",
            "numero_control": "21380100",
            "password_hash": hashed,
            "rol": RolUsuario.SCRUM_MASTER,
            **consent_defaults,
        })
        estudiante_1 = _get_or_create_user(db, "estudiante1@cbtis75.edu.mx", {
            "nombre_completo": "Carlos Rivera",
            "numero_control": "21380101",
            "password_hash": hashed,
            "rol": RolUsuario.ESTUDIANTE,
            **consent_defaults,
        })
        estudiante_2 = _get_or_create_user(db, "estudiante2@cbtis75.edu.mx", {
            "nombre_completo": "Mariana Ochoa",
            "numero_control": "21380102",
            "password_hash": hashed,
            "rol": RolUsuario.ESTUDIANTE,
            **consent_defaults,
        })

        # --- Equipo (el docente NO es miembro, es supervisor) --------------------
        team = db.query(Team).filter(Team.nombre_proyecto == "PAEC Demo").first()
        if not team:
            team = Team(
                nombre_proyecto="PAEC Demo",
                descripcion_proyecto="Proyecto de demostración: gestión de proyectos escolares.",
                grupo="GIDS6O81-E",
            )
            db.add(team)
            db.flush()
            db.add_all([
                TeamMember(team_id=team.id, user_id=scrum_master.id, rol_scrum="Scrum Master"),
                TeamMember(team_id=team.id, user_id=estudiante_1.id, rol_scrum="Dev FrontEnd"),
                TeamMember(team_id=team.id, user_id=estudiante_2.id, rol_scrum="Dev BackEnd"),
            ])
            db.flush()

        # --- Sprint activo (parcial 1) aprobado -----------------------------------
        sprint = (
            db.query(Sprint)
            .filter(Sprint.team_id == team.id, Sprint.numero_parcial == 1)
            .first()
        )
        if not sprint:
            hoy = datetime.utcnow()
            sprint = Sprint(
                team_id=team.id,
                numero_parcial=1,
                fecha_inicio=hoy - timedelta(days=7),
                fecha_fin=hoy + timedelta(days=14),
                aprobado_por_docente=True,
                feedback_docente="Buena planeación. Revisen la estimación de puntos de historia.",
            )
            db.add(sprint)
            db.flush()

        # --- Tareas (7, distribuidas entre los 3 integrantes) --------------------
        if db.query(Task).filter(Task.sprint_id == sprint.id).count() == 0:
            hoy = datetime.utcnow()
            # (nombre, desc, asignado, dias_fin, estado, prioridad, story_points, horas)
            plantillas = [
                ("Diseñar pantalla de login",
                 "Wireframe y conexión con /auth/login.",
                 estudiante_1.id, 3, EstadoKanban.TERMINADO, Prioridad.ALTA, 5, 6),
                ("Modelar base de datos de usuarios",
                 "Definir tablas User, Team y TeamMember con SQLAlchemy.",
                 estudiante_2.id, 5, EstadoKanban.TERMINADO, Prioridad.ALTA, 8, 10),
                ("Implementar endpoint /auth/register",
                 "Validación con Pydantic + hash bcrypt + tests.",
                 estudiante_2.id, 7, EstadoKanban.HACIENDO, Prioridad.ALTA, 5, 8),
                ("Tablero Kanban básico",
                 "Vista de tres columnas por hacer / haciendo / terminado.",
                 estudiante_1.id, 10, EstadoKanban.HACIENDO, Prioridad.MEDIA, 8, 12),
                ("Configurar CI de GitHub Actions",
                 "Workflow con lint + pytest para PRs a develop.",
                 scrum_master.id, 12, EstadoKanban.POR_HACER, Prioridad.MEDIA, 3, 4),
                ("Documentar API en Swagger",
                 "Añadir descripciones y ejemplos a cada endpoint.",
                 estudiante_1.id, 14, EstadoKanban.POR_HACER, Prioridad.BAJA, 3, 3),
                ("Diseñar dashboard del docente",
                 "Mockup del panel con métricas de avance.",
                 estudiante_2.id, 14, EstadoKanban.POR_HACER, Prioridad.MEDIA, 5, 6),
            ]
            for nombre, desc, asignado, dias_fin, estado, prio, sp, horas in plantillas:
                terminada = estado == EstadoKanban.TERMINADO
                db.add(Task(
                    sprint_id=sprint.id,
                    asignado_a=asignado,
                    nombre_actividad=nombre,
                    descripcion=desc,
                    criterios_aceptacion=f"Se considera terminada cuando: {desc}",
                    fecha_inicio=hoy - timedelta(days=3),
                    fecha_fin=hoy + timedelta(days=dias_fin),
                    tiempo_estimado_horas=horas,
                    prioridad=prio,
                    story_points=sp,
                    estado_kanban=estado,
                    evidencia_url="/uploads/demo/evidencia.pdf" if terminada else None,
                    aprobado_por_scrum_master=terminada,
                ))

        # --- Design Sprint: día "Mapear" completado -------------------------------
        tiene_dia_mapear = (
            db.query(DesignSprintDay)
            .filter(
                DesignSprintDay.team_id == team.id,
                DesignSprintDay.dia == DiaDesignSprint.MAPEAR,
            )
            .first()
        )
        if not tiene_dia_mapear:
            db.add(DesignSprintDay(
                team_id=team.id,
                dia=DiaDesignSprint.MAPEAR,
                fecha_planeada=datetime.utcnow() - timedelta(days=6),
                plan_descripcion="Definir el problema y mapear el user journey.",
                evidencia_url="/uploads/demo/mapa-experiencia.png",
                comentario_docente="Buen inicio, considerar más edge cases.",
                completado=1,
            ))

        # --- Daily de ejemplo ------------------------------------------------------
        if not db.query(Daily).filter(Daily.team_id == team.id).first():
            db.add(Daily(
                team_id=team.id,
                user_id=estudiante_1.id,
                que_hice_ayer="Terminé el wireframe de login.",
                que_hare_hoy="Integrar el form con el endpoint /auth/login.",
                impedimentos="Ninguno.",
                acuerdos="Revisar el flujo con el Scrum Master a las 6 pm.",
            ))

        db.commit()

        # --- Resumen imprimible ---------------------------------------------------
        print("=" * 62)
        print("SEED COMPLETADO")
        print("=" * 62)
        print(f"Contraseña común para TODOS los usuarios: {PASSWORD_DEMO}")
        print()
        print(f"  Docente       -> {docente.email}")
        print(f"  Scrum Master  -> {scrum_master.email}")
        print(f"  Estudiante 1  -> {estudiante_1.email}")
        print(f"  Estudiante 2  -> {estudiante_2.email}")
        print()
        print(f"Equipo:        PAEC Demo (id={team.id})")
        print(f"Sprint activo: parcial #{sprint.numero_parcial} (id={sprint.id})")
        num_tareas = db.query(Task).filter(Task.sprint_id == sprint.id).count()
        print(f"Tareas:        {num_tareas}")
        print("=" * 62)
    finally:
        db.close()


if __name__ == "__main__":
    run()
