import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api/client";
import PrivacyNotice from "../components/PrivacyNotice";
import { useAuthStore } from "../store/authStore";

/*
 * Modulo de Inicio y Gestion de Equipos (issue #12).
 *
 * Permite al usuario autenticado registrar su equipo (2-4 integrantes) y
 * asignar el rol Scrum de cada uno.
 */

const ROLES_SCRUM = ["Scrum Master", "Product Owner", "Developer"];
const MIEMBRO_VACIO = { email: "", rol_scrum: "" };

function IntroABPScrum() {
  return (
    <section className="pf-arco-text" style={{ marginBottom: "1rem" }}>
      <strong>Que es ABP + Scrum?</strong>
      <p>
        El Aprendizaje Basado en Proyectos (ABP) es una metodologia donde
        aprenden resolviendo un problema real mediante un proyecto concreto.
        Scrum es el marco de trabajo agil que usaremos para organizar ese
        proyecto en Sprints (parciales), con roles como el Scrum Master
        (facilita al equipo) y el Product Owner (representa los intereses
        del cliente/docente).
      </p>
    </section>
  );
}

export default function TeamSetup() {
  const setCurrentTeamId = useAuthStore((s) => s.setCurrentTeamId);
  const [nombreProyecto, setNombreProyecto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [grupo, setGrupo] = useState("");
  const [miembros, setMiembros] = useState([
    { ...MIEMBRO_VACIO },
    { ...MIEMBRO_VACIO },
  ]);
  const [aceptaAviso, setAceptaAviso] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorGeneral, setErrorGeneral] = useState("");
  const [emailsFaltantes, setEmailsFaltantes] = useState([]);
  const [equipoCreado, setEquipoCreado] = useState(null);

  const conteoRoles = useMemo(() => {
    return miembros.reduce(
      (acc, m) => {
        if (m.rol_scrum === "Scrum Master") acc.sm += 1;
        else if (m.rol_scrum === "Product Owner") acc.po += 1;
        else if (m.rol_scrum === "Developer") acc.dev += 1;
        return acc;
      },
      { sm: 0, po: 0, dev: 0 }
    );
  }, [miembros]);

  const emailsDuplicados = useMemo(() => {
    const vistos = new Set();
    const dup = new Set();
    for (const m of miembros) {
      const e = m.email.trim().toLowerCase();
      if (!e) continue;
      if (vistos.has(e)) dup.add(e);
      vistos.add(e);
    }
    return dup;
  }, [miembros]);

  const validacionCliente = useMemo(() => {
    const errores = [];
    if (miembros.length < 2)
      errores.push("El equipo debe tener al menos 2 integrantes.");
    if (miembros.length > 4)
      errores.push("El equipo no puede tener mas de 4 integrantes.");
    if (conteoRoles.sm === 0)
      errores.push("Falta asignar el rol de Scrum Master.");
    if (conteoRoles.sm > 1) errores.push("Solo puede haber un Scrum Master.");
    if (conteoRoles.po > 1) errores.push("Solo puede haber un Product Owner.");
    if (emailsDuplicados.size > 0)
      errores.push("Hay correos repetidos entre los integrantes.");
    return errores;
  }, [miembros, conteoRoles, emailsDuplicados]);

  const formularioValido = useMemo(() => {
    if (validacionCliente.length > 0) return false;
    if (!nombreProyecto.trim()) return false;
    if (!aceptaAviso) return false;
    for (const m of miembros) {
      if (!m.email.trim() || !m.rol_scrum) return false;
    }
    return true;
  }, [validacionCliente, nombreProyecto, aceptaAviso, miembros]);

  const actualizarMiembro = (i, campo, valor) => {
    setMiembros((prev) => {
      const copia = [...prev];
      copia[i] = { ...copia[i], [campo]: valor };
      return copia;
    });
  };

  const agregarMiembro = () => {
    if (miembros.length >= 4) return;
    setMiembros((prev) => [...prev, { ...MIEMBRO_VACIO }]);
  };

  const eliminarMiembro = (i) => {
    if (miembros.length <= 2) return;
    setMiembros((prev) => prev.filter((_, idx) => idx !== i));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorGeneral("");
    setEmailsFaltantes([]);
    setEquipoCreado(null);

    if (!formularioValido) return;

    const payload = {
      nombre_proyecto: nombreProyecto.trim(),
      descripcion_proyecto: descripcion.trim() || null,
      grupo: grupo.trim() || null,
      members: miembros.map((m) => ({
        email: m.email.trim(),
        rol_scrum: m.rol_scrum,
      })),
    };

    setEnviando(true);
    try {
      const { data: creado } = await api.post("/api/v1/equipo/", payload);
      const { data: confirmado } = await api.get(
        `/api/v1/equipo/${creado.id}`
      );
      setEquipoCreado(confirmado);
      // Marca este equipo como el activo del usuario para que el nav
      // superior arme los enlaces (Dailies, Kanban, Dashboard) con el
      // teamId correcto.
      setCurrentTeamId(confirmado.id);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (
        detail &&
        typeof detail === "object" &&
        Array.isArray(detail.emails_no_encontrados)
      ) {
        setEmailsFaltantes(detail.emails_no_encontrados);
        setErrorGeneral(
          detail.mensaje ||
            "Hay correos que no corresponden a usuarios registrados."
        );
      } else if (typeof detail === "string") {
        setErrorGeneral(detail);
      } else if (Array.isArray(detail)) {
        setErrorGeneral(detail[0]?.msg || "Datos invalidos. Revisa los campos.");
      } else {
        setErrorGeneral(
          "Ocurrio un error al registrar el equipo. Intenta nuevamente."
        );
      }
    } finally {
      setEnviando(false);
    }
  };

  if (equipoCreado) {
    return (
      <div className="ts-page">
        <header className="ts-header">
          <h1 className="ts-title">Equipo registrado</h1>
          <p className="ts-subtitle">
            Tu equipo quedo correctamente registrado en la base de datos.
          </p>
        </header>

        <section className="ts-success-card">
          <div className="ts-success-title">Registro exitoso</div>
          <p><strong>Proyecto:</strong> {equipoCreado.nombre_proyecto}</p>
          {equipoCreado.grupo && (
            <p><strong>Grupo:</strong> {equipoCreado.grupo}</p>
          )}
          {equipoCreado.descripcion_proyecto && (
            <p><strong>Descripcion:</strong> {equipoCreado.descripcion_proyecto}</p>
          )}
          <h3 className="section-title" style={{ marginTop: "1rem" }}>
            Integrantes
          </h3>
          <ul className="ts-member-list">
            {equipoCreado.members.map((m) => (
              <li key={m.user_id}>
                <strong>{m.nombre_completo}</strong> ({m.email}) &mdash;{" "}
                {m.rol_scrum}
              </li>
            ))}
          </ul>

          <div
            style={{
              marginTop: "1.5rem",
              paddingTop: "1rem",
              borderTop: "1px solid rgba(148,163,184,0.2)",
            }}
          >
            <p style={{ fontWeight: 600, marginBottom: "0.75rem" }}>
              Continúa trabajando en tu equipo (ID: {equipoCreado.id})
            </p>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <Link
                to={`/dashboard/${equipoCreado.id}`}
                className="btn-primary"
                style={{ textDecoration: "none", display: "inline-block" }}
              >
                Ir al Dashboard
              </Link>
              <Link
                to={`/dailies/${equipoCreado.id}`}
                className="btn-secondary"
                style={{ textDecoration: "none", display: "inline-block" }}
              >
                Ir a Dailies
              </Link>
              <Link
                to={`/kanban/${equipoCreado.id}`}
                className="btn-secondary"
                style={{ textDecoration: "none", display: "inline-block" }}
              >
                Ir al Kanban
              </Link>
              <Link
                to={`/backlog/${equipoCreado.id}`}
                className="btn-secondary"
                style={{ textDecoration: "none", display: "inline-block" }}
              >
                Ir al Backlog
              </Link>
            </div>
          </div>
        </section>

        <button
          type="button"
          className="btn-secondary"
          onClick={() => {
            setEquipoCreado(null);
            setNombreProyecto("");
            setDescripcion("");
            setGrupo("");
            setMiembros([{ ...MIEMBRO_VACIO }, { ...MIEMBRO_VACIO }]);
            setAceptaAviso(false);
          }}
        >
          Registrar otro equipo
        </button>
      </div>
    );
  }

  return (
    <div className="ts-page">
      <header className="ts-header">
        <h1 className="ts-title">Registrar equipo y proyecto</h1>
        <p className="ts-subtitle">
          Alta del equipo de trabajo (2-4 integrantes) con sus roles Scrum.
          Cada correo debe corresponder a un usuario ya registrado.
        </p>
      </header>

      <div className="ts-card">
        <IntroABPScrum />

        <form className="ts-form" onSubmit={handleSubmit} noValidate>
          <div style={{ marginBottom: "0.5rem" }}>
            <PrivacyNotice onAccept={setAceptaAviso} />
          </div>

          <div className="form-group">
            <label htmlFor="nombre-proyecto">
              Nombre del proyecto <span aria-hidden="true">*</span>
            </label>
            <input
              id="nombre-proyecto"
              type="text"
              value={nombreProyecto}
              onChange={(e) => setNombreProyecto(e.target.value)}
              required
              minLength={3}
              maxLength={150}
              placeholder="Nombre del proyecto ABP"
            />
          </div>

          <div className="form-group">
            <label htmlFor="descripcion">Descripcion (opcional)</label>
            <textarea
              id="descripcion"
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              maxLength={500}
              rows={3}
              placeholder="Que problema resuelve el proyecto"
            />
          </div>

          <div className="form-group">
            <label htmlFor="grupo">Grupo (opcional)</label>
            <input
              id="grupo"
              type="text"
              value={grupo}
              onChange={(e) => setGrupo(e.target.value)}
              maxLength={30}
              placeholder="p.ej. 6IDS-A"
            />
          </div>

          <div>
            <h3 className="section-title">
              Integrantes ({miembros.length}/4)
            </h3>
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--text-secondary)",
                marginBottom: "0.85rem",
              }}
            >
              Reglas: entre 2 y 4 integrantes. Exactamente 1 Scrum Master.
              Maximo 1 Product Owner. El resto Developers.
            </p>

            {miembros.map((m, i) => {
              const emailNormalizado = m.email.trim().toLowerCase();
              const esDuplicado =
                emailNormalizado && emailsDuplicados.has(emailNormalizado);
              const esFaltante =
                emailNormalizado &&
                emailsFaltantes
                  .map((e) => e.toLowerCase())
                  .includes(emailNormalizado);
              const tieneError = esDuplicado || esFaltante;
              return (
                <div
                  key={i}
                  className={
                    tieneError ? "ts-row ts-row--error" : "ts-row"
                  }
                  style={{ marginBottom: "0.5rem" }}
                >
                  <div>
                    <input
                      type="email"
                      value={m.email}
                      onChange={(e) =>
                        actualizarMiembro(i, "email", e.target.value)
                      }
                      placeholder={`Correo integrante ${i + 1}`}
                      required
                      style={{
                        width: "100%",
                        background: "rgba(15, 23, 42, 0.6)",
                        border: "1px solid var(--border-color)",
                        borderRadius: "8px",
                        padding: "0.65rem 0.85rem",
                        color: "var(--text-primary)",
                        fontFamily: "inherit",
                      }}
                    />
                    {esDuplicado && (
                      <span className="ts-row-error-msg">
                        Este correo ya esta en el equipo.
                      </span>
                    )}
                    {esFaltante && (
                      <span className="ts-row-error-msg">
                        Este correo no esta registrado en el sistema.
                      </span>
                    )}
                  </div>
                  <select
                    value={m.rol_scrum}
                    onChange={(e) =>
                      actualizarMiembro(i, "rol_scrum", e.target.value)
                    }
                    required
                    style={{
                      background: "rgba(15, 23, 42, 0.6)",
                      border: "1px solid var(--border-color)",
                      borderRadius: "8px",
                      padding: "0.65rem 0.85rem",
                      color: "var(--text-primary)",
                      fontFamily: "inherit",
                    }}
                  >
                    <option value="">-- Rol Scrum --</option>
                    {ROLES_SCRUM.map((rol) => (
                      <option key={rol} value={rol}>
                        {rol}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    className="btn-ghost"
                    onClick={() => eliminarMiembro(i)}
                    disabled={miembros.length <= 2}
                    aria-label={`Eliminar integrante ${i + 1}`}
                  >
                    Quitar
                  </button>
                </div>
              );
            })}

            <button
              type="button"
              className="btn-secondary"
              onClick={agregarMiembro}
              disabled={miembros.length >= 4}
              style={{ marginTop: "0.5rem" }}
            >
              + Agregar integrante
            </button>
          </div>

          <div className="ts-role-count">
            <strong>Roles asignados:</strong> Scrum Master: {conteoRoles.sm}{" "}
            &middot; Product Owner: {conteoRoles.po} &middot; Developer:{" "}
            {conteoRoles.dev}
          </div>

          {validacionCliente.length > 0 && (
            <ul className="ts-error-list">
              {validacionCliente.map((msg) => (
                <li key={msg}>{msg}</li>
              ))}
            </ul>
          )}

          {errorGeneral && (
            <div role="alert" className="error-message">
              <span>{errorGeneral}</span>
            </div>
          )}

          <button
            type="submit"
            className="btn-primary"
            disabled={!formularioValido || enviando}
          >
            {enviando ? "Registrando..." : "Guardar equipo"}
          </button>
        </form>
      </div>
    </div>
  );
}
