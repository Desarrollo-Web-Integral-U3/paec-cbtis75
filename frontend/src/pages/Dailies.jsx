import { useEffect, useMemo, useState } from "react";
import api from "../api/client";

export default function Dailies({ teamId }) {
  const [ayer, setAyer] = useState("");
  const [hoy, setHoy] = useState("");
  const [impedimentos, setImpedimentos] = useState("");
  const [acuerdos, setAcuerdos] = useState("");
  const [historial, setHistorial] = useState([]);
  const [miembros, setMiembros] = useState([]);
  const [filtroMiembro, setFiltroMiembro] = useState("todos");
  const [filtroFecha, setFiltroFecha] = useState("");

  const cargar = async () => {
    try {
      const [equipoRes, historialRes] = await Promise.all([
        api.get(`/api/v1/equipo/${teamId}`),
        api.get(`/api/v1/daily/equipo/${teamId}`),
      ]);
      setMiembros(equipoRes.data.members || []);
      setHistorial(historialRes.data || []);
    } catch (error) {
      setHistorial([]);
    }
  };

  useEffect(() => {
    if (!teamId) return;
    cargar();
  }, [teamId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.post("/api/v1/daily/", {
      team_id: teamId,
      que_hice_ayer: ayer,
      que_hare_hoy: hoy,
      impedimentos,
      acuerdos,
    });
    setAyer("");
    setHoy("");
    setImpedimentos("");
    setAcuerdos("");
    cargar();
  };

  const opcionesFecha = useMemo(() => {
    const fechas = historial
      .map((d) => d.fecha && obtenerFechaValor(d.fecha))
      .filter(Boolean);

    return [...new Set(fechas)].sort((a, b) => b.localeCompare(a));
  }, [historial]);

  const historialFiltrado = useMemo(() => {
    return historial.filter((d) => {
      const coincideMiembro = filtroMiembro === "todos" || String(d.user_id) === filtroMiembro;
      const coincideFecha = !filtroFecha || obtenerFechaValor(d.fecha) === filtroFecha;
      return coincideMiembro && coincideFecha;
    });
  }, [historial, filtroFecha, filtroMiembro]);

  const obtenerNombreUsuario = (userId) => {
    const miembro = miembros.find((m) => String(m.user_id) === String(userId));
    return miembro?.nombre_completo || "Integrante";
  };

  return (
    <div className="daily-page">
      <section className="daily-card">
        <div className="daily-header">
          <p className="ds-eyebrow">Daily Scrum</p>
          <h2 className="ds-title daily-title">Daily de hoy</h2>
          <p className="ds-subtitle">Registra avances, impedimentos y acuerdos para que el equipo consulte el historial fácilmente.</p>
        </div>

        <form className="auth-form daily-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="ayer">¿Qué hice ayer?</label>
            <textarea id="ayer" value={ayer} onChange={(e) => setAyer(e.target.value)} required />
          </div>

          <div className="form-group">
            <label htmlFor="hoy">¿Qué voy a hacer hoy?</label>
            <textarea id="hoy" value={hoy} onChange={(e) => setHoy(e.target.value)} required />
          </div>

          <div className="form-group">
            <label htmlFor="impedimentos">¿Qué me impide avanzar?</label>
            <textarea id="impedimentos" value={impedimentos} onChange={(e) => setImpedimentos(e.target.value)} />
          </div>

          <div className="form-group">
            <label htmlFor="acuerdos">Acuerdos del equipo</label>
            <textarea id="acuerdos" value={acuerdos} onChange={(e) => setAcuerdos(e.target.value)} />
          </div>

          <button className="btn-primary" type="submit">Guardar daily</button>
        </form>
      </section>

      <section className="daily-card">
        <div className="daily-history-header">
          <div>
            <p className="ds-eyebrow">Historial</p>
            <h3 className="daily-history-title">Consulta acuerdos por integrante y fecha</h3>
          </div>

          <div className="daily-filters">
            <div className="form-group daily-filter-group">
              <label htmlFor="integrante">Integrante</label>
              <select id="integrante" value={filtroMiembro} onChange={(e) => setFiltroMiembro(e.target.value)}>
                <option value="todos">Todos</option>
                {miembros.map((miembro) => (
                  <option key={miembro.user_id} value={miembro.user_id}>
                    {miembro.nombre_completo}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group daily-filter-group">
              <label htmlFor="fecha">Fecha</label>
              <select id="fecha" value={filtroFecha} onChange={(e) => setFiltroFecha(e.target.value)}>
                <option value="">Todas las fechas</option>
                {opcionesFecha.map((fecha) => (
                  <option key={fecha} value={fecha}>
                    {formatearFecha(fecha)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {historialFiltrado.length === 0 ? (
          <p className="daily-empty">No hay dailies para los filtros seleccionados.</p>
        ) : (
          historialFiltrado.map((d) => (
            <article key={d.id} className="daily-history-item">
              <div className="daily-history-meta">
                <span className="daily-pill">{obtenerNombreUsuario(d.user_id)}</span>
                <span className="daily-date">{formatearFecha(d.fecha)}</span>
              </div>

              <div className="daily-history-body">
                <p>
                  <strong>Ayer:</strong> {d.que_hice_ayer}
                </p>
                <p>
                  <strong>Hoy:</strong> {d.que_hare_hoy}
                </p>
                {d.impedimentos && (
                  <p>
                    <strong>Impedimentos:</strong> {d.impedimentos}
                  </p>
                )}
                <div className="daily-acuerdos">
                  <strong>Acuerdos</strong>
                  <p>{d.acuerdos || "No hay acuerdos registrados en este daily."}</p>
                </div>
              </div>
            </article>
          ))
        )}
      </section>
    </div>
  );
}

function obtenerFechaValor(fecha) {
  const fechaLocal = new Date(fecha);
  return `${fechaLocal.getFullYear()}-${String(fechaLocal.getMonth() + 1).padStart(2, "0")}-${String(fechaLocal.getDate()).padStart(2, "0")}`;
}

function formatearFecha(fecha) {
  const fechaLocal = new Date(fecha);
  return fechaLocal.toLocaleDateString("es-MX", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}
