import { useEffect, useMemo, useState } from "react";
import api from "../api/client";
import { useAuthStore } from "../store/authStore";

const FORM_VACIO = {
  sprint_id: "",
  asignado_a: "",
  nombre_actividad: "",
  descripcion: "",
  criterios_aceptacion: "",
  fecha_inicio: "",
  fecha_fin: "",
  tiempo_estimado_horas: "",
  prioridad: "media",
  story_points: 1,
};

export default function Backlog({ teamId }) {
  const [form, setForm] = useState(FORM_VACIO);
  const [historias, setHistorias] = useState([]);
  const [sprints, setSprints] = useState([]);
  const [miembros, setMiembros] = useState([]);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [feedbackDrafts, setFeedbackDrafts] = useState({});
  const [aprobandoSprintId, setAprobandoSprintId] = useState(null);
  const user = useAuthStore((state) => state.user);
  const esDocente = user?.rol === "docente";

  const cargarDatos = async () => {
    try {
      const [equipoRes, sprintRes, historiasRes] = await Promise.all([
        api.get(`/api/v1/equipo/${teamId}`),
        api.get(`/api/v1/equipo/${teamId}/sprints`),
        api.get(`/api/v1/equipo/${teamId}/historias`),
      ]);

      const sprintsData = sprintRes.data || [];
      setMiembros(equipoRes.data.members || []);
      setSprints(sprintsData);
      setHistorias(historiasRes.data || []);
      setFeedbackDrafts((prev) => ({
        ...prev,
        ...Object.fromEntries(sprintsData.map((sprint) => [sprint.id, prev[sprint.id] ?? sprint.feedback_docente ?? ""])),
      }));

      if (!form.sprint_id && (sprintRes.data || []).length > 0) {
        setForm((prev) => ({ ...prev, sprint_id: String(sprintRes.data[0].id) }));
      }
    } catch (err) {
      setError("No se pudo cargar el backlog del equipo.");
    }
  };

  useEffect(() => {
    if (!teamId) return;
    cargarDatos();
  }, [teamId]);

  useEffect(() => {
    if (!modalAbierto) return;

    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        closeModal();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [modalAbierto]);

  const descripcionBoton = useMemo(
    () => (editandoId ? "Actualizar historia" : "Guardar historia"),
    [editandoId]
  );

  const handleChange = (campo, valor) => {
    setForm((prev) => ({ ...prev, [campo]: valor }));
  };

  const resetFormulario = () => {
    setForm({ ...FORM_VACIO, sprint_id: sprints[0]?.id ? String(sprints[0].id) : "" });
    setEditandoId(null);
    setError("");
  };

  const closeModal = () => {
    setModalAbierto(false);
    resetFormulario();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.nombre_actividad.trim() || !form.descripcion.trim() || !form.criterios_aceptacion.trim()) {
      setError("Completa nombre, descripción y criterios de aceptación.");
      return;
    }

    if (!form.sprint_id || !form.fecha_inicio || !form.fecha_fin || !form.tiempo_estimado_horas) {
      setError("Selecciona sprint, fechas y tiempo estimado.");
      return;
    }

    const payload = {
      sprint_id: Number(form.sprint_id),
      asignado_a: form.asignado_a ? Number(form.asignado_a) : null,
      nombre_actividad: form.nombre_actividad.trim(),
      descripcion: form.descripcion.trim(),
      criterios_aceptacion: form.criterios_aceptacion.trim(),
      fecha_inicio: `${form.fecha_inicio}T00:00:00`,
      fecha_fin: `${form.fecha_fin}T00:00:00`,
      tiempo_estimado_horas: Number(form.tiempo_estimado_horas),
      prioridad: form.prioridad,
      story_points: Number(form.story_points || 1),
    };

    setGuardando(true);
    try {
      if (editandoId) {
        await api.put(`/api/v1/historia/${editandoId}`, payload);
      } else {
        await api.post(`/api/v1/historia`, payload);
      }

      await cargarDatos();
      resetFormulario();
      setModalAbierto(false);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "No se pudo guardar la historia.");
    } finally {
      setGuardando(false);
    }
  };

  const editarHistoria = (historia) => {
    setEditandoId(historia.id);
    setForm({
      sprint_id: String(historia.sprint_id),
      asignado_a: historia.asignado_a ? String(historia.asignado_a) : "",
      nombre_actividad: historia.nombre_actividad,
      descripcion: historia.descripcion,
      criterios_aceptacion: historia.criterios_aceptacion,
      fecha_inicio: historia.fecha_inicio?.slice(0, 10) || "",
      fecha_fin: historia.fecha_fin?.slice(0, 10) || "",
      tiempo_estimado_horas: String(historia.tiempo_estimado_horas),
      prioridad: historia.prioridad || "media",
      story_points: historia.story_points || 1,
    });
    setError("");
    setModalAbierto(true);
  };

  const abrirNuevoModal = () => {
    resetFormulario();
    setModalAbierto(true);
  };

  const aprobarSprint = async (sprint) => {
    setError("");
    setAprobandoSprintId(sprint.id);

    try {
      await api.post(`/api/v1/sprint/${sprint.id}/aprobar`, {
        feedback_docente: feedbackDrafts[sprint.id] ?? "",
      });
      await cargarDatos();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "No se pudo aprobar el sprint.");
    } finally {
      setAprobandoSprintId(null);
    }
  };

  return (
    <div className="bl-page">
      <header className="bl-header">
        <div>
          <h2 className="bl-title">Backlog</h2>
          <p className="bl-subtitle">
            Gestiona las historias del proyecto, asigna responsable, fechas, prioridad y sprint.
          </p>
        </div>
        <button type="button" onClick={abrirNuevoModal} className="bl-btn-new">
          + Nueva historia
        </button>
      </header>

      {error && <div className="error-message">{error}</div>}

      <section className="bl-review-section">
        <div className="bl-section-header">
          <span className="bl-section-title">Revisión de sprints parciales</span>
          <span className="bl-count">{sprints.length}</span>
        </div>

        {sprints.length === 0 ? (
          <div className="bl-empty">Aún no hay sprints creados para este equipo.</div>
        ) : (
          <div className="bl-review-list">
            {sprints.map((sprint) => (
              <article
                key={sprint.id}
                className={`bl-review-card ${sprint.aprobado_por_docente ? "bl-review-card--approved" : ""}`}
              >
                <div className="bl-review-top">
                  <div>
                    <h3 className="bl-review-title">Sprint #{sprint.numero_parcial}</h3>
                    <p className="bl-review-meta">
                      {new Date(sprint.fecha_inicio).toLocaleDateString()} - {new Date(sprint.fecha_fin).toLocaleDateString()}
                    </p>
                  </div>
                  <span className={`bl-status-pill ${sprint.aprobado_por_docente ? "bl-status-pill--approved" : "bl-status-pill--pending"}`}>
                    {sprint.aprobado_por_docente ? "Aprobado" : "Pendiente"}
                  </span>
                </div>

                {esDocente ? (
                  <>
                    <label className="bl-review-label">Retroalimentación del docente</label>
                    <textarea
                      rows={3}
                      value={feedbackDrafts[sprint.id] ?? ""}
                      onChange={(e) =>
                        setFeedbackDrafts((prev) => ({ ...prev, [sprint.id]: e.target.value }))
                      }
                      placeholder="Escribe la retroalimentación para este sprint..."
                      className="bl-review-textarea"
                    />
                    <div className="bl-review-actions">
                      <button
                        type="button"
                        className="bl-btn-primary"
                        onClick={() => aprobarSprint(sprint)}
                        disabled={aprobandoSprintId === sprint.id}
                      >
                        {aprobandoSprintId === sprint.id ? "Guardando..." : sprint.aprobado_por_docente ? "Actualizar aprobación" : "Aprobar sprint"}
                      </button>
                    </div>
                  </>
                ) : (
                  <>
                    <p className="bl-review-feedback">
                      <strong>Retroalimentación:</strong> {sprint.feedback_docente || "Sin retroalimentación aún."}
                    </p>
                    <p className="bl-review-hint">Solo el docente puede aprobar este sprint.</p>
                  </>
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <section>
        <div className="bl-section-header">
          <span className="bl-section-title">Historias en backlog</span>
          <span className="bl-count">{historias.length}</span>
        </div>

        {historias.length === 0 ? (
          <div className="bl-empty">No hay historias aún para este equipo.</div>
        ) : (
          <div className="bl-list">
            {historias.map((historia) => (
              <article key={historia.id} className={`bl-item bl-item--${historia.prioridad}`}>
                <div className="bl-item-top">
                  <div>
                    <h3 className="bl-item-title">{historia.nombre_actividad}</h3>
                    <div className="bl-item-meta">
                      <span className="bl-chip">Sprint #{historia.sprint_id}</span>
                      <span className="bl-priority-pill">{historia.prioridad}</span>
                      <span className="bl-chip">{historia.tiempo_estimado_horas} hrs</span>
                    </div>
                  </div>
                  <button type="button" onClick={() => editarHistoria(historia)} className="bl-btn-edit">
                    Editar
                  </button>
                </div>

                <p className="bl-item-desc">{historia.descripcion}</p>
                <p className="bl-item-criteria">
                  <strong>Criterios:</strong> {historia.criterios_aceptacion}
                </p>

                <div className="bl-item-footer">
                  <span>
                    <strong>Asignado:</strong> {historia.asignado_a ?? "Sin asignar"}
                  </span>
                  <span>
                    <strong>Inicio:</strong> {historia.fecha_inicio?.slice(0, 10)}
                  </span>
                  <span>
                    <strong>Entrega:</strong> {historia.fecha_fin?.slice(0, 10)}
                  </span>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      {modalAbierto && (
        <div className="bl-modal-overlay" onClick={closeModal}>
          <div className="bl-modal-content" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleSubmit}>
              <h3 className="bl-modal-title">{editandoId ? "Editar historia" : "Nueva historia"}</h3>

              <div className="bl-form-grid">
                <div className="form-group">
                  <label>Nombre</label>
                  <input
                    value={form.nombre_actividad}
                    onChange={(e) => handleChange("nombre_actividad", e.target.value)}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Descripción</label>
                  <textarea
                    value={form.descripcion}
                    onChange={(e) => handleChange("descripcion", e.target.value)}
                    style={{ minHeight: 90 }}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Criterios de aceptación</label>
                  <textarea
                    value={form.criterios_aceptacion}
                    onChange={(e) => handleChange("criterios_aceptacion", e.target.value)}
                    style={{ minHeight: 90 }}
                    required
                  />
                </div>

                <div className="form-group">
                  <label>Persona asignada</label>
                  <select value={form.asignado_a} onChange={(e) => handleChange("asignado_a", e.target.value)}>
                    <option value="">Sin asignar</option>
                    {miembros.map((m) => (
                      <option key={m.user_id} value={m.user_id}>
                        {m.nombre_completo} ({m.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bl-form-row">
                  <div className="form-group">
                    <label>Fecha de inicio</label>
                    <input
                      type="date"
                      value={form.fecha_inicio}
                      onChange={(e) => handleChange("fecha_inicio", e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Fecha de entrega</label>
                    <input
                      type="date"
                      value={form.fecha_fin}
                      onChange={(e) => handleChange("fecha_fin", e.target.value)}
                      required
                    />
                  </div>
                </div>

                <div className="bl-form-row">
                  <div className="form-group">
                    <label>Tiempo estimado (horas)</label>
                    <input
                      type="number"
                      min="1"
                      value={form.tiempo_estimado_horas}
                      onChange={(e) => handleChange("tiempo_estimado_horas", e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label>Prioridad</label>
                    <select value={form.prioridad} onChange={(e) => handleChange("prioridad", e.target.value)}>
                      <option value="alta">Alta</option>
                      <option value="media">Media</option>
                      <option value="baja">Baja</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label>Sprint al que pertenece</label>
                  <select value={form.sprint_id} onChange={(e) => handleChange("sprint_id", e.target.value)} required>
                    <option value="">Selecciona un sprint</option>
                    {sprints.map((s) => (
                      <option key={s.id} value={s.id}>
                        Sprint #{s.numero_parcial} · {new Date(s.fecha_inicio).toLocaleDateString()} - {new Date(s.fecha_fin).toLocaleDateString()}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="bl-modal-actions">
                  <button type="submit" disabled={guardando} className="bl-btn-primary">
                    {guardando ? "Guardando..." : descripcionBoton}
                  </button>
                  <button type="button" onClick={closeModal} className="bl-btn-cancel">
                    Cancelar
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}