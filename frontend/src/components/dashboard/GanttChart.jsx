import { useMemo, useState } from "react";
import { Gantt, ViewMode } from "gantt-task-react";
import "gantt-task-react/dist/index.css";

// Mapeo estado Kanban -> porcentaje visual dentro de la barra del Gantt.
// El modelo Task no tiene un campo de avance real (0-100), aproximamos.
const PROGRESS_BY_STATUS = {
  por_hacer: 0,
  haciendo: 50,
  terminado: 100,
};

// Paleta por estado. backgroundColor pinta el "hueco" de la barra;
// progressColor pinta el fill de avance.
const STYLES_BY_STATUS = {
  por_hacer: {
    backgroundColor: "#e5e7eb",
    backgroundSelectedColor: "#d1d5db",
    progressColor: "#9ca3af",
    progressSelectedColor: "#6b7280",
  },
  haciendo: {
    backgroundColor: "#fef3c7",
    backgroundSelectedColor: "#fde68a",
    progressColor: "#f59e0b",
    progressSelectedColor: "#d97706",
  },
  terminado: {
    backgroundColor: "#d1fae5",
    backgroundSelectedColor: "#a7f3d0",
    progressColor: "#10b981",
    progressSelectedColor: "#059669",
  },
};

const VIEW_MODES = [
  { key: ViewMode.Day, label: "Dia" },
  { key: ViewMode.Week, label: "Semana" },
  { key: ViewMode.Month, label: "Mes" },
];

function toGanttTask(row) {
  const status = row.estado || "por_hacer";
  return {
    id: String(row.id),
    name: row.nombre,
    start: new Date(row.inicio),
    end: new Date(row.fin),
    type: "task",
    progress: PROGRESS_BY_STATUS[status] ?? 0,
    isDisabled: true,
    styles: STYLES_BY_STATUS[status] ?? STYLES_BY_STATUS.por_hacer,
  };
}

export default function GanttChart({ rows }) {
  const [viewMode, setViewMode] = useState(ViewMode.Week);

  const tasks = useMemo(() => (rows || []).map(toGanttTask), [rows]);

  if (tasks.length === 0) {
    return (
      <p className="gantt-empty">
        No hay tareas registradas todavia para este equipo.
      </p>
    );
  }

  return (
    <div>
      <div className="gantt-toolbar">
        <label htmlFor="gantt-view-mode">Vista:</label>
        <select
          id="gantt-view-mode"
          value={viewMode}
          onChange={(e) => setViewMode(e.target.value)}
        >
          {VIEW_MODES.map((v) => (
            <option key={v.key} value={v.key}>
              {v.label}
            </option>
          ))}
        </select>
        <span className="gantt-count">
          {tasks.length} tarea{tasks.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="gantt-frame">
        <Gantt
          tasks={tasks}
          viewMode={viewMode}
          locale="es"
          listCellWidth="200px"
          columnWidth={viewMode === ViewMode.Month ? 300 : 65}
        />
      </div>
    </div>
  );
}
