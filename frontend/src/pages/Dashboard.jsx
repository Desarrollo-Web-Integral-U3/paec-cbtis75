import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

import api from "../api/client";
import CapacidadChart from "../components/dashboard/CapacidadChart";
import GanttChart from "../components/dashboard/GanttChart";
import ResumenIA from "../components/dashboard/ResumenIA";

export default function Dashboard({ teamId }) {
  const [resumen, setResumen] = useState(null);

  useEffect(() => {
    api.get(`/api/v1/equipo/${teamId}/dashboard`).then((r) => setResumen(r.data));
  }, [teamId]);

  if (!resumen) {
    return (
      <div className="dash-page">
        <p className="dash-loading">Cargando dashboard...</p>
      </div>
    );
  }

  const dataStoryPoints = [
    { nombre: "Planeados", valor: resumen.story_points_planeados },
    { nombre: "Completados", valor: resumen.story_points_completados },
  ];

  // El backend devuelve [{user_id, nombre_completo, horas}] para que el
  // eje X muestre el nombre real en vez de "Usuario N".
  const dataEsfuerzo = (resumen.esfuerzo_por_integrante || []).map((e) => ({
    nombre: e.nombre_completo,
    horas: e.horas,
  }));

  return (
    <div className="dash-page">
      <header className="dash-header">
        <h1 className="dash-title">Panel de avance del equipo</h1>
        <p className="dash-subtitle">
          Metricas en vivo del progreso, esfuerzo asignado y cronograma.
        </p>
      </header>

      <section className="dash-grid">
        <article className="dash-card">
          <h3 className="dash-card-title">Story points: planeados vs. completados</h3>
          <div className="dash-chart">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={dataStoryPoints}>
                <XAxis dataKey="nombre" stroke="#cbd5e1" />
                <YAxis stroke="#cbd5e1" />
                <Tooltip cursor={{ fill: "rgba(59,130,246,0.08)" }} />
                <Bar dataKey="valor" fill="#3b82f6" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="dash-card">
          <h3 className="dash-card-title">Esfuerzo (horas) por integrante</h3>
          {dataEsfuerzo.length === 0 ? (
            <p className="dash-loading">No hay tareas asignadas todavia.</p>
          ) : (
            <div className="dash-chart">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={dataEsfuerzo}>
                  <XAxis dataKey="nombre" stroke="#cbd5e1" />
                  <YAxis stroke="#cbd5e1" />
                  <Tooltip cursor={{ fill: "rgba(59,130,246,0.08)" }} />
                  <Bar dataKey="horas" fill="#a78bfa" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </article>
      </section>

      <article className="dash-card">
        <h3 className="dash-card-title">Capacidad vs esfuerzo asignado</h3>
        <CapacidadChart teamId={teamId} />
      </article>

      <article className="dash-card">
        <h3 className="dash-card-title">Cronograma (Gantt)</h3>
        <GanttChart rows={resumen.gantt} />
      </article>

      <ResumenIA teamId={teamId} />
    </div>
  );
}
