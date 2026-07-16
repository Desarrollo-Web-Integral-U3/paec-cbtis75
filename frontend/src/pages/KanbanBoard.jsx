import { useEffect, useState } from "react";
import api from "../api/client";

const COLUMNAS = [
  { key: "por_hacer", label: "Por hacer" },
  { key: "haciendo", label: "Haciendo" },
  { key: "terminado", label: "Terminado" },
];

export default function KanbanBoard({ teamId }) {
  const [tareas, setTareas] = useState([]);

  const cargar = () =>
    api.get(`/api/v1/historia/equipo/${teamId}/kanban`).then((r) => setTareas(r.data));

  useEffect(() => {
    cargar();
  }, [teamId]);

  const moverTarea = async (tarea, nuevoEstado) => {
    // Si va a "terminado", es OBLIGATORIO pedir evidencia/comentario
    // (el backend también lo valida, esto es solo para UX).
    let comentario = tarea.comentario;
    if (nuevoEstado === "terminado" && !tarea.evidencia_url && !comentario) {
      comentario = prompt("Para marcar como Terminado, describe tu evidencia:");
      if (!comentario) return;
    }
    await api.patch(`/api/v1/historia/${tarea.id}/mover`, {
      nuevo_estado: nuevoEstado,
      comentario,
    });
    cargar();
  };

  return (
    <div style={{ display: "flex", gap: "1rem" }}>
      {COLUMNAS.map((col) => (
        <div key={col.key} style={{ flex: 1, border: "1px solid #ddd", padding: "0.5rem" }}>
          <h3>{col.label}</h3>
          {tareas
            .filter((t) => t.estado_kanban === col.key)
            .map((t) => (
              <div key={t.id} style={{ border: "1px solid #eee", padding: "0.5rem", margin: "0.5rem 0" }}>
                <strong>{t.nombre_actividad}</strong>
                <p>Prioridad: {t.prioridad} · {t.story_points} pts</p>
                {col.key !== "por_hacer" && (
                  <button onClick={() => moverTarea(t, "por_hacer")}>&larr; Por hacer</button>
                )}
                {col.key !== "haciendo" && (
                  <button onClick={() => moverTarea(t, "haciendo")}>Haciendo</button>
                )}
                {col.key !== "terminado" && (
                  <button onClick={() => moverTarea(t, "terminado")}>Terminado &rarr;</button>
                )}
              </div>
            ))}
        </div>
      ))}
    </div>
  );
}
