import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

import api from "../api/client";
import CapacidadChart from "../components/dashboard/CapacidadChart";
import GanttChart from "../components/dashboard/GanttChart";

export default function Dashboard({ teamId }) {
  const [resumen, setResumen] = useState(null);

  useEffect(() => {
    api.get(`/api/v1/equipo/${teamId}/dashboard`).then((r) => setResumen(r.data));
  }, [teamId]);

  if (!resumen) return <p>Cargando dashboard...</p>;

  const dataStoryPoints = [
    { nombre: "Planeados", valor: resumen.story_points_planeados },
    { nombre: "Completados", valor: resumen.story_points_completados },
  ];

  // El backend ahora devuelve [{user_id, nombre_completo, horas}] para
  // que el eje X del chart muestre el nombre real en vez de "Usuario N".
  const dataEsfuerzo = (resumen.esfuerzo_por_integrante || []).map((e) => ({
    nombre: e.nombre_completo,
    horas: e.horas,
  }));

  return (
    <div>
      <h2>Panel de avance del equipo</h2>

      <h3>Story points: planeados vs. completados</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={dataStoryPoints}>
          <XAxis dataKey="nombre" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="valor" fill="#1e293b" />
        </BarChart>
      </ResponsiveContainer>

      <h3>Esfuerzo (horas) por integrante</h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={dataEsfuerzo}>
          <XAxis dataKey="nombre" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="horas" fill="#0ea5e9" />
        </BarChart>
      </ResponsiveContainer>

      <h3>Capacidad vs esfuerzo asignado</h3>
      <CapacidadChart teamId={teamId} />

      <h3>Cronograma (Gantt)</h3>
      <GanttChart rows={resumen.gantt} />
    </div>
  );
}
