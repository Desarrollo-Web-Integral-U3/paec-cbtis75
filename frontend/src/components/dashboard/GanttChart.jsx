import { useMemo, useState } from "react";
import { Gantt, ViewMode } from "gantt-task-react";
import "gantt-task-react/dist/index.css";

// Mapeo entre el estado del Kanban del backend y el porcentaje visual
// que dibuja gantt-task-react dentro de cada barra. No tenemos un campo
// de avance real (0-100), asi que aproximamos: por_hacer=0, haciendo=50,
// terminado=100. Si en el futuro se agrega un campo porcentaje_avance al
// modelo Task, solo hay que cambiar esta funcion.
const PROGRESS_BY_STATUS = {
  por_hacer: 0,
  haciendo: 50,
  terminado: 100,
};

// Paleta por estado. backgroundColor pinta el "hueco" de la barra;
// progressColor pinta el fill de avance. Los "selected" son la version
// mas saturada que se usa al hacer hover/click en la libreria.
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

// Opciones del selector de vista. La libreria acepta Day, Week, Month
// (entre otros); dejamos las 3 mas usadas en gestion de sprints.
const VIEW_MODES = [
  { key: ViewMode.Day, label: "Dia" },
  { key: ViewMode.Week, label: "Semana" },
  { key: ViewMode.Month, label: "Mes" },
];

// Transforma una fila del backend { id, nombre, inicio, fin, estado } al
// shape que espera gantt-task-react: id string, start/end como Date,
// progress numerico y styles por estado.
function toGanttTask(row) {
  const status = row.estado || "por_hacer";
  return {
    id: String(row.id),
    name: row.nombre,
    start: new Date(row.inicio),
    end: new Date(row.fin),
    type: "task",
    progress: PROGRESS_BY_STATUS[status] ?? 0,
    isDisabled: true, // solo lectura; drag para editar fechas queda fuera de scope
    styles: STYLES_BY_STATUS[status] ?? STYLES_BY_STATUS.por_hacer,
  };
}

export default function GanttChart({ rows }) {
  const [viewMode, setViewMode] = useState(ViewMode.Week);

  // useMemo evita reconvertir el array en cada render; solo se recalcula
  // cuando cambia la data de entrada.
  const tasks = useMemo(() => (rows || []).map(toGanttTask), [rows]);

  if (tasks.length === 0) {
    return (
      <p style={{ color: "#666", fontStyle: "italic" }}>
        No hay tareas registradas todavia para este equipo.
      </p>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: "0.5rem",
          marginBottom: "0.5rem",
          alignItems: "center",
        }}
      >
        <label htmlFor="gantt-view-mode" style={{ fontSize: "0.9rem" }}>
          Vista:
        </label>
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
        <span style={{ marginLeft: "auto", fontSize: "0.85rem", color: "#666" }}>
          {tasks.length} tarea{tasks.length === 1 ? "" : "s"}
        </span>
      </div>

      <Gantt
        tasks={tasks}
        viewMode={viewMode}
        locale="es"
        listCellWidth="200px"
        columnWidth={viewMode === ViewMode.Month ? 300 : 65}
      />
    </div>
  );
}
