import { useEffect, useState } from "react";
import api from "../api/client";
import { useAuthStore } from "../store/authStore";

// Mantenemos la estructura de los días pero eliminamos la propiedad de color independiente.
// Todo usará las variables de CSS, principalmente var(--primary-color).
const DIAS = [
  { key: "mapear", label: "Mapear", dayName: "Lunes", desc: "Entender el problema y elegir un objetivo." },
  { key: "bocetar", label: "Bocetar", dayName: "Martes", desc: "Explorar posibles soluciones en papel." },
  { key: "decidir", label: "Decidir", dayName: "Miércoles", desc: "Elegir la mejor idea y armar el storyboard." },
  { key: "prototipar", label: "Prototipar", dayName: "Jueves", desc: "Construir un prototipo realista y rápido." },
  { key: "probar", label: "Probar", dayName: "Viernes", desc: "Validar el prototipo con usuarios reales." },
];

export default function DesignSprint() {
  const user = useAuthStore((s) => s.user);
  const userRole = user?.rol;

  const [teamId, setTeamId] = useState(null);
  const [dias, setDias] = useState([]);
  const [planesDraft, setPlanesDraft] = useState({});
  const [feedbackDrafts, setFeedbackDrafts] = useState({});
  const [cargandoPlan, setCargandoPlan] = useState({});
  const [cargandoFeedback, setCargandoFeedback] = useState({});
  const [cargandoEvidencia, setCargandoEvidencia] = useState({});
  const [archivosLocales, setArchivosLocales] = useState({});
  const [errorBackend, setErrorBackend] = useState("");
  const [loading, setLoading] = useState(true);

  const registroDe = (key) => dias.find((d) => d.dia === key);
  const estaCompletado = (registro) => registro?.completado === 1;
  const isUnlocked = (i) => {
    if (i === 0) return true;
    const previous = registroDe(DIAS[i - 1].key);
    return previous?.completado === 1;
  };

  const cargarDias = async (teamIdToLoad) => {
    try {
      const response = await api.get(`/api/v1/design-sprint/equipo/${teamIdToLoad}`);
      setDias(response.data);
    } catch (err) {
      if (err.response?.status === 403) {
        setErrorBackend("El backend rechazó el acceso. No tienes permiso para ver estos días.");
      } else {
        setErrorBackend("No se pudieron cargar los días del Design Sprint.");
      }
    }
  };

  const cargarEquipo = async () => {
    if (!user) {
      setLoading(false);
      return;
    }

    try {
      const { data } = await api.get("/api/v1/equipo/me");
      setTeamId(data.id);
      await cargarDias(data.id);
    } catch (err) {
      setErrorBackend("No se pudo obtener el equipo asignado al usuario.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarEquipo();
  }, [user]);

  if (userRole !== "estudiante" && userRole !== "docente") {
    return (
      <div className="ds-page">
        <header className="ds-header">
          <h2 className="ds-title">Acceso Denegado</h2>
          <p className="ds-subtitle">
            Esta vista de Design Sprint solo está disponible para estudiantes y docentes.
          </p>
        </header>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="ds-page">
        <header className="ds-header">
          <h2 className="ds-title">Cargando Design Sprint...</h2>
        </header>
      </div>
    );
  }

  if (errorBackend) {
    return (
      <div className="ds-page">
        <header className="ds-header">
          <h2 className="ds-title">Error</h2>
          <p className="ds-subtitle">{errorBackend}</p>
        </header>
      </div>
    );
  }

  const planearDia = async (diaKey) => {
    const descripcion = planesDraft[diaKey];
    if (!descripcion?.trim() || !teamId) return;

    setCargandoPlan((prev) => ({ ...prev, [diaKey]: true }));
    setErrorBackend("");

    try {
      const payload = {
        team_id: teamId,
        dia: diaKey,
        fecha_planeada: new Date().toISOString(),
        plan_descripcion: descripcion.trim(),
      };
      const { data } = await api.post("/api/v1/design-sprint/", payload);
      setDias((prev) => {
        const filtered = prev.filter((d) => d.dia !== data.dia);
        return [...filtered, data];
      });
      setPlanesDraft((prev) => ({ ...prev, [diaKey]: "" }));
    } catch (err) {
      setErrorBackend("No se pudo guardar el plan. Intenta nuevamente.");
    } finally {
      setCargandoPlan((prev) => ({ ...prev, [diaKey]: false }));
    }
  };

  const subirEvidencia = async (dayId, diaKey) => {
    const archivoSeleccionado = archivosLocales[diaKey];
    if (!archivoSeleccionado) return;

    setErrorBackend("");
    setCargandoEvidencia((prev) => ({ ...prev, [diaKey]: true }));

    const formData = new FormData();
    formData.append("archivo", archivoSeleccionado);

    try {
      const { data } = await api.post(
        `/api/v1/design-sprint/${dayId}/evidencia`,
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      setDias((prev) => prev.map((d) => (d.id === data.id ? data : d)));
      setArchivosLocales((prev) => ({ ...prev, [diaKey]: null }));
    } catch (err) {
      setErrorBackend("No se pudo subir la evidencia. Intenta con otro archivo.");
    } finally {
      setCargandoEvidencia((prev) => ({ ...prev, [diaKey]: false }));
    }
  };

  const enviarFeedback = async (dayId, diaKey) => {
    const comentario = feedbackDrafts[diaKey]?.trim();
    if (!comentario) return;

    setErrorBackend("");
    setCargandoFeedback((prev) => ({ ...prev, [diaKey]: true }));

    try {
      const { data } = await api.post(`/api/v1/design-sprint/${dayId}/feedback`, {
        comentario_docente: comentario,
      });
      setDias((prev) => prev.map((d) => (d.id === data.id ? data : d)));
      setFeedbackDrafts((prev) => ({ ...prev, [diaKey]: "" }));
    } catch (err) {
      setErrorBackend("No se pudo guardar el comentario. Intenta nuevamente.");
    } finally {
      setCargandoFeedback((prev) => ({ ...prev, [diaKey]: false }));
    }
  };

  const completadosCount = DIAS.filter((dia) => estaCompletado(registroDe(dia.key))).length;
  const progresoPct = (completadosCount / DIAS.length) * 100;
  let diaActualIndex = DIAS.findIndex((dia, i) => isUnlocked(i) && !estaCompletado(registroDe(dia.key)));
  if (diaActualIndex === -1) diaActualIndex = DIAS.length - 1;
  return (
    <div className="ds-page">
      {/* Encabezado */}
      <header className="ds-header">
        <h2 className="ds-title">Design Sprint</h2>
        <p className="ds-subtitle">
          Mapea, boceta, decide, prototipa y prueba una solución en una semana.
        </p>
      </header>
      {/* Riel de progreso */}
      <div className="ds-rail-wrap">
        <div className="ds-rail-track" />
        <div className="ds-rail-fill" style={{ width: `${progresoPct}%` }} />
        <div className="ds-rail-nodes">
          {DIAS.map((dia, i) => {
            const registro = registroDe(dia.key);
            const isPlaneado = !!registro;
            const isCompletado = estaCompletado(registro);
            const unlocked = isPlaneado || isUnlocked(i);
            const isActiveDay = i === diaActualIndex;
            // Clases calculadas dinámicamente
            let nodeClass = "ds-rail-dot";
            if (isCompletado) nodeClass += " ds-rail-dot--completed";
            else if (isPlaneado) nodeClass += " ds-rail-dot--planned";
            if (!unlocked) nodeClass += " ds-rail-dot--locked";
            if (isActiveDay) nodeClass += " ds-rail-dot--active";
            return (
              <div key={dia.key} className="ds-rail-node">
                <div className={nodeClass}>
                  {isCompletado ? (
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  ) : !unlocked ? (
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="5" y="11" width="14" height="10" rx="2" />
                      <path d="M8 11V7a4 4 0 018 0v4" />
                    </svg>
                  ) : (
                    <span className="ds-rail-dot-number">{i + 1}</span>
                  )}
                </div>
                <span className={`ds-rail-label ${!unlocked ? 'ds-rail-label--locked' : ''}`}>{dia.dayName}</span>
              </div>
            );
          })}
        </div>
      </div>
      <p className="ds-progress-text">
        {completadosCount} de {DIAS.length} días completados
      </p>
      {/* Tablero de días */}
      <div className="ds-grid">
        {DIAS.map((dia, i) => {
          const registro = registroDe(dia.key);
          const isPlaneado = !!registro;
          const isCompletado = estaCompletado(registro);
          const unlocked = isPlaneado || isUnlocked(i);
          const isFeatured = i === diaActualIndex;
          return (
            <div
              key={dia.key}
              className={`ds-card ${isFeatured ? "ds-card--featured" : ""} ${!unlocked ? "ds-card--locked" : ""}`}
            >
              <div className="ds-card-header">
                <div className="ds-card-header-left">
                  <span className="ds-day-index">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <h3 className="ds-day-label">{dia.label}</h3>
                    <span className="ds-day-name">{dia.dayName}</span>
                  </div>
                </div>
                <div className="ds-badge-col">
                  {isFeatured && (
                    <span className="ds-featured-badge">
                      {isCompletado ? "Sprint completado" : "Día actual"}
                    </span>
                  )}
                  {(isPlaneado || isCompletado) && (
                    <span className={`ds-status-pill ${isCompletado ? 'ds-status-pill--completed' : 'ds-status-pill--pending'}`}>
                      {isCompletado ? "✓ Completado" : "Pendiente"}
                    </span>
                  )}
                </div>
              </div>
              {isFeatured && <p className="ds-day-desc">{dia.desc}</p>}
              {!unlocked ? (
                <div className="ds-locked-body">
                  <div className="ds-lock-icon-wrap">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <rect x="5" y="11" width="14" height="10" rx="2" />
                      <path d="M8 11V7a4 4 0 018 0v4" />
                    </svg>
                  </div>
                  <p className="ds-locked-text">
                    Completa <strong>{DIAS[i - 1].label}</strong> ({DIAS[i - 1].dayName}) para desbloquear este día.
                  </p>
                </div>
              ) : !isPlaneado ? (
                <div className="ds-card-body">
                  <label className="ds-field-label">Plan de actividades</label>
                  <textarea
                    rows={isFeatured ? 5 : 3}
                    placeholder="¿Qué van a hacer este día?"
                    value={planesDraft[dia.key] || ""}
                    onChange={(e) => setPlanesDraft((prev) => ({ ...prev, [dia.key]: e.target.value }))}
                    className="ds-textarea"
                  />
                  <label className="ds-dropzone">
                    <input
                      type="file"
                      onChange={(e) => {
                        const file = e.target.files[0];
                        if (file) {
                          setArchivosLocales((prev) => ({ ...prev, [dia.key]: file }));
                        }
                      }}
                      className="ds-hidden-input"
                    />
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                    </svg>
                    <span className="ds-dropzone-text">
                      {archivosLocales[dia.key] ? archivosLocales[dia.key].name : "Adjuntar evidencia del día"}
                    </span>
                  </label>
                  <button
                    onClick={() => planearDia(dia.key)}
                    disabled={cargandoPlan[dia.key] || !planesDraft[dia.key]?.trim()}
                    className={`ds-save-button ${cargandoPlan[dia.key] || !planesDraft[dia.key]?.trim() ? 'ds-save-button--disabled' : ''}`}
                  >
                    {cargandoPlan[dia.key] ? "Guardando…" : "Guardar plan"}
                  </button>
                </div>
              ) : (
                <div className="ds-card-body">
                  <div className="ds-plan-box">
                    <span className="ds-plan-label">Plan de trabajo</span>
                    <p className="ds-plan-text" style={{ WebkitLineClamp: isFeatured ? "unset" : 3 }}>{registro.plan_descripcion}</p>
                  </div>
                  {registro?.evidencia_url ? (
                    <>
                      <p className="ds-done-text ds-done-text--success">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                          <polyline points="22 4 12 14.01 9 11.01" />
                        </svg>
                        Evidencia cargada
                      </p>
                      <a
                        href={registro.evidencia_url}
                        target="_blank"
                        rel="noreferrer"
                        className="ds-link"
                      >
                        Ver evidencia
                      </a>
                    </>
                  ) : (
                    <>
                      <p className="ds-done-text ds-done-text--pending">
                        Aún no hay evidencia cargada.
                      </p>
                      <label className="ds-dropzone ds-dropzone--small">
                        <input
                          type="file"
                          onChange={(e) => {
                            const file = e.target.files[0];
                            if (file) {
                              setArchivosLocales((prev) => ({ ...prev, [dia.key]: file }));
                            }
                          }}
                          className="ds-hidden-input"
                        />
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48" />
                        </svg>
                        <span className="ds-dropzone-text">
                          {archivosLocales[dia.key] ? archivosLocales[dia.key].name : "Selecciona evidencia"}
                        </span>
                      </label>
                      <button
                        onClick={() => subirEvidencia(registro.id, dia.key)}
                        disabled={!archivosLocales[dia.key] || cargandoEvidencia[dia.key]}
                        className={`ds-upload-button ${!archivosLocales[dia.key] || cargandoEvidencia[dia.key] ? 'ds-upload-button--disabled' : ''}`}
                      >
                        {cargandoEvidencia[dia.key] ? "Subiendo…" : "Subir evidencia"}
                      </button>
                    </>
                  )}
                  <div className="ds-feedback-panel">
                    <div className="ds-feedback-header">
                      <span className="ds-feedback-label">Retroalimentación del docente</span>
                    </div>
                    <hr className="ds-feedback-divider" />
                    {userRole === "docente" ? (
                      <>
                        <textarea
                          rows={3}
                          placeholder="Deja un comentario para el equipo..."
                          value={feedbackDrafts[dia.key] ?? registro.comentario_docente ?? ""}
                          onChange={(e) => setFeedbackDrafts((prev) => ({ ...prev, [dia.key]: e.target.value }))}
                          className="ds-textarea ds-textarea--feedback"
                        />
                        <button
                          onClick={() => enviarFeedback(registro.id, dia.key)}
                          disabled={cargandoFeedback[dia.key] || !(feedbackDrafts[dia.key]?.trim())}
                          className={`ds-save-button ${cargandoFeedback[dia.key] || !(feedbackDrafts[dia.key]?.trim()) ? 'ds-save-button--disabled' : ''}`}
                        >
                          {cargandoFeedback[dia.key] ? "Guardando…" : "Guardar comentario"}
                        </button>
                      </>
                    ) : (
                      <p className="ds-feedback-text">
                        {registro.comentario_docente || "Aún no hay retroalimentación para este día."}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}