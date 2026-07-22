import { useMemo, useState } from "react";
import api from "../api/client";
import PrivacyNotice from "../components/PrivacyNotice";

/*
 * Modulo de Inicio y Gestion de Equipos (issue #12).
 *
 * Permite al usuario autenticado registrar su equipo (2-4 integrantes) y
 * asignar el rol Scrum de cada uno. Al enviar el formulario:
 *   1. Se hace POST /api/v1/equipo/ con emails + roles.
 *   2. Si el backend responde 201, se reconsulta GET /api/v1/equipo/{id}
 *      para confirmar visualmente que el equipo quedo registrado con sus
 *      integrantes y roles (criterio de aceptacion del issue).
 *   3. Si el backend responde 422, se muestra el mensaje concreto (por
 *      ejemplo emails no encontrados, faltan reglas Scrum, etc).
 *
 * Cumple LGPDPPSO: el aviso de privacidad se muestra antes de capturar
 * datos y el checkbox de consentimiento NO viene premarcado.
 */

const ROLES_SCRUM = ["Scrum Master", "Product Owner", "Developer"];

const MIEMBRO_VACIO = { email: "", rol_scrum: "" };

function IntroABPScrum() {
  return (
    <section style={{ marginBottom: "1.5rem" }}>
      <h2>Que es ABP + Scrum?</h2>
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
  const [nombreProyecto, setNombreProyecto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [grupo, setGrupo] = useState("");
  const [miembros, setMiembros] = useState([{ ...MIEMBRO_VACIO }, { ...MIEMBRO_VACIO }]);
  const [aceptaAviso, setAceptaAviso] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [errorGeneral, setErrorGeneral] = useState("");
  const [emailsFaltantes, setEmailsFaltantes] = useState([]);
  const [equipoCreado, setEquipoCreado] = useState(null);

  // ---- Contadores en vivo para dar feedback visual --------------------
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
    if (miembros.length < 2) errores.push("El equipo debe tener al menos 2 integrantes.");
    if (miembros.length > 4) errores.push("El equipo no puede tener mas de 4 integrantes.");
    if (conteoRoles.sm === 0) errores.push("Falta asignar el rol de Scrum Master.");
    if (conteoRoles.sm > 1) errores.push("Solo puede haber un Scrum Master.");
    if (conteoRoles.po > 1) errores.push("Solo puede haber un Product Owner.");
    if (emailsDuplicados.size > 0) errores.push("Hay correos repetidos entre los integrantes.");
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

  // ---- Handlers del formulario ---------------------------------------
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
      // Reconsulta al GET para confirmar (criterio de aceptacion del issue).
      const { data: confirmado } = await api.get(`/api/v1/equipo/${creado.id}`);
      setEquipoCreado(confirmado);
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail && typeof detail === "object" && Array.isArray(detail.emails_no_encontrados)) {
        setEmailsFaltantes(detail.emails_no_encontrados);
        setErrorGeneral(
          detail.mensaje || "Hay correos que no corresponden a usuarios registrados."
        );
      } else if (typeof detail === "string") {
        setErrorGeneral(detail);
      } else if (Array.isArray(detail)) {
        setErrorGeneral(detail[0]?.msg || "Datos invalidos. Revisa los campos.");
      } else {
        setErrorGeneral("Ocurrio un error al registrar el equipo. Intenta nuevamente.");
      }
    } finally {
      setEnviando(false);
    }
  };

  // ---- Vista de exito -------------------------------------------------
  if (equipoCreado) {
    return (
      <div style={{ maxWidth: 720, margin: "2rem auto", padding: "1rem" }}>
        <h2>Equipo registrado correctamente</h2>
        <div
          style={{
            border: "1px solid #ccc",
            borderRadius: 8,
            padding: "1rem",
            marginTop: "1rem",
          }}
        >
          <p><strong>Proyecto:</strong> {equipoCreado.nombre_proyecto}</p>
          {equipoCreado.grupo && <p><strong>Grupo:</strong> {equipoCreado.grupo}</p>}
          {equipoCreado.descripcion_proyecto && (
            <p>
              <strong>Descripcion:</strong> {equipoCreado.descripcion_proyecto}
            </p>
          )}
          <h3>Integrantes</h3>
          <ul>
            {equipoCreado.members.map((m) => (
              <li key={m.user_id}>
                <strong>{m.nombre_completo}</strong> ({m.email}) &mdash; {m.rol_scrum}
              </li>
            ))}
          </ul>
        </div>
        <button
          type="button"
          onClick={() => {
            setEquipoCreado(null);
            setNombreProyecto("");
            setDescripcion("");
            setGrupo("");
            setMiembros([{ ...MIEMBRO_VACIO }, { ...MIEMBRO_VACIO }]);
            setAceptaAviso(false);
          }}
          style={{ marginTop: "1rem" }}
        >
          Registrar otro equipo
        </button>
      </div>
    );
  }

  // ---- Formulario -----------------------------------------------------
  return (
    <div style={{ maxWidth: 720, margin: "2rem auto", padding: "1rem" }}>
      <IntroABPScrum />

      <form onSubmit={handleSubmit} noValidate>
        <h2>Registrar equipo y proyecto</h2>

        <div style={{ marginBottom: "1rem" }}>
          <PrivacyNotice onAccept={setAceptaAviso} />
        </div>

        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Nombre del proyecto <span aria-hidden="true">*</span>
          <input
            type="text"
            value={nombreProyecto}
            onChange={(e) => setNombreProyecto(e.target.value)}
            required
            minLength={3}
            maxLength={150}
            placeholder="Nombre del proyecto ABP"
            style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
          />
        </label>

        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Descripcion (opcional)
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            maxLength={500}
            rows={3}
            placeholder="Que problema resuelve el proyecto"
            style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
          />
        </label>

        <label style={{ display: "block", marginBottom: "1rem" }}>
          Grupo (opcional)
          <input
            type="text"
            value={grupo}
            onChange={(e) => setGrupo(e.target.value)}
            maxLength={30}
            placeholder="p.ej. 6IDS-A"
            style={{ width: "100%", padding: "0.5rem", marginTop: "0.25rem" }}
          />
        </label>

        <h3>Integrantes ({miembros.length}/4)</h3>
        <p style={{ fontSize: "0.85rem", color: "#555" }}>
          Reglas: entre 2 y 4 integrantes. Exactamente 1 Scrum Master. Maximo 1
          Product Owner. El resto Developers. Cada correo debe pertenecer a un
          usuario ya registrado.
        </p>

        {miembros.map((m, i) => {
          const emailNormalizado = m.email.trim().toLowerCase();
          const esDuplicado = emailNormalizado && emailsDuplicados.has(emailNormalizado);
          const esFaltante =
            emailNormalizado &&
            emailsFaltantes.map((e) => e.toLowerCase()).includes(emailNormalizado);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                gap: "0.5rem",
                alignItems: "flex-start",
                marginBottom: "0.5rem",
                padding: "0.5rem",
                border: esDuplicado || esFaltante ? "1px solid #c00" : "1px solid #ddd",
                borderRadius: 6,
              }}
            >
              <div style={{ flex: 2 }}>
                <input
                  type="email"
                  value={m.email}
                  onChange={(e) => actualizarMiembro(i, "email", e.target.value)}
                  placeholder={`Correo integrante ${i + 1}`}
                  required
                  style={{ width: "100%", padding: "0.5rem" }}
                />
                {esDuplicado && (
                  <span style={{ color: "#c00", fontSize: "0.8rem" }}>
                    Este correo ya esta en el equipo.
                  </span>
                )}
                {esFaltante && (
                  <span style={{ color: "#c00", fontSize: "0.8rem" }}>
                    Este correo no esta registrado en el sistema.
                  </span>
                )}
              </div>
              <div style={{ flex: 1 }}>
                <select
                  value={m.rol_scrum}
                  onChange={(e) => actualizarMiembro(i, "rol_scrum", e.target.value)}
                  required
                  style={{ width: "100%", padding: "0.5rem" }}
                >
                  <option value="">-- Rol Scrum --</option>
                  {ROLES_SCRUM.map((rol) => (
                    <option key={rol} value={rol}>
                      {rol}
                    </option>
                  ))}
                </select>
              </div>
              <button
                type="button"
                onClick={() => eliminarMiembro(i)}
                disabled={miembros.length <= 2}
                title={miembros.length <= 2 ? "Debe haber al menos 2 integrantes" : "Eliminar"}
                aria-label={`Eliminar integrante ${i + 1}`}
              >
                Eliminar
              </button>
            </div>
          );
        })}

        <button
          type="button"
          onClick={agregarMiembro}
          disabled={miembros.length >= 4}
          style={{ marginBottom: "1rem" }}
        >
          + Agregar integrante
        </button>

        <div
          style={{
            fontSize: "0.85rem",
            color: "#555",
            marginBottom: "1rem",
          }}
        >
          <strong>Roles asignados:</strong> Scrum Master: {conteoRoles.sm} &middot;
          Product Owner: {conteoRoles.po} &middot; Developer: {conteoRoles.dev}
        </div>

        {validacionCliente.length > 0 && (
          <ul style={{ color: "#c00", marginBottom: "1rem" }}>
            {validacionCliente.map((msg) => (
              <li key={msg}>{msg}</li>
            ))}
          </ul>
        )}

        {errorGeneral && (
          <div role="alert" style={{ color: "#c00", marginBottom: "1rem" }}>
            {errorGeneral}
          </div>
        )}

        <button
          type="submit"
          disabled={!formularioValido || enviando}
          style={{ padding: "0.75rem 1.5rem" }}
        >
          {enviando ? "Registrando..." : "Guardar equipo"}
        </button>
      </form>
    </div>
  );
}
