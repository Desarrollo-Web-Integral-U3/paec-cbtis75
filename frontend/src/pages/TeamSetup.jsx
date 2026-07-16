import { useState } from "react";
import api from "../api/client";

/**
 * Módulo de Inicio y Gestión de Equipos.
 * Debe mostrar primero una breve introducción de qué es ABP y Scrum
 * (ver <IntroABPScrum /> más abajo), y luego permitir registrar el
 * proyecto y los roles del equipo.
 */
function IntroABPScrum() {
  return (
    <section>
      <h2>¿Qué es ABP + Scrum?</h2>
      <p>
        El Aprendizaje Basado en Proyectos (ABP) es una metodología donde
        aprenden resolviendo un problema real mediante un proyecto concreto.
        Scrum es el marco de trabajo ágil que usaremos para organizar ese
        proyecto en Sprints (parciales), con roles como el Scrum Master
        (facilita al equipo y da seguimiento) y el equipo de desarrollo.
      </p>
    </section>
  );
}

export default function TeamSetup() {
  const [nombreProyecto, setNombreProyecto] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [miembros, setMiembros] = useState([{ user_id: "", rol_scrum: "" }]);

  const agregarMiembro = () =>
    setMiembros([...miembros, { user_id: "", rol_scrum: "" }]);

  const actualizarMiembro = (i, campo, valor) => {
    const copia = [...miembros];
    copia[i][campo] = valor;
    setMiembros(copia);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.post("/api/v1/equipo/", {
      nombre_proyecto: nombreProyecto,
      descripcion_proyecto: descripcion,
      members: miembros.map((m) => ({ ...m, user_id: Number(m.user_id) })),
    });
    alert("Equipo registrado correctamente.");
  };

  return (
    <div>
      <IntroABPScrum />
      <form onSubmit={handleSubmit}>
        <h2>Registrar mi equipo y proyecto</h2>
        <input
          placeholder="Nombre del proyecto"
          value={nombreProyecto}
          onChange={(e) => setNombreProyecto(e.target.value)}
          required
        />
        <textarea
          placeholder="Descripción breve del proyecto"
          value={descripcion}
          onChange={(e) => setDescripcion(e.target.value)}
        />

        <h3>Integrantes y roles Scrum</h3>
        {miembros.map((m, i) => (
          <div key={i}>
            <input
              placeholder="ID de usuario"
              value={m.user_id}
              onChange={(e) => actualizarMiembro(i, "user_id", e.target.value)}
              required
            />
            <select
              value={m.rol_scrum}
              onChange={(e) => actualizarMiembro(i, "rol_scrum", e.target.value)}
              required
            >
              <option value="">-- Rol --</option>
              <option value="Scrum Master">Scrum Master</option>
              <option value="Dev FrontEnd">Dev FrontEnd</option>
              <option value="Dev BackEnd">Dev BackEnd</option>
            </select>
          </div>
        ))}
        <button type="button" onClick={agregarMiembro}>
          + Agregar integrante
        </button>
        <br />
        <button type="submit">Guardar equipo</button>
      </form>
    </div>
  );
}
