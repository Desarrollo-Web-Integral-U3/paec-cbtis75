import { useEffect, useState } from "react";
import {
  DndContext,
  DragOverlay,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
} from "@dnd-kit/core";

import api from "../api/client";
import ColumnaKanban from "../components/kanban/ColumnaKanban";
import ModalEvidencia from "../components/kanban/ModalEvidencia";
import TarjetaHistoria from "../components/kanban/TarjetaHistoria";

// Definicion estatica de columnas. La key DEBE coincidir con el enum
// EstadoKanban del backend (backend/app/models/task.py).
const COLUMNS = [
  { key: "por_hacer", label: "Por hacer" },
  { key: "haciendo", label: "Haciendo" },
  { key: "terminado", label: "Terminado" },
];

// Pesos para ordenar por prioridad de forma estable. Alta primero.
const PRIORITY_WEIGHT = { alta: 0, media: 1, baja: 2 };

function sortByPriority(a, b) {
  const wa = PRIORITY_WEIGHT[a.prioridad] ?? 99;
  const wb = PRIORITY_WEIGHT[b.prioridad] ?? 99;
  if (wa !== wb) return wa - wb;
  return a.id - b.id;
}

export default function KanbanBoard({ teamId }) {
  const [tasks, setTasks] = useState([]);
  const [activeTask, setActiveTask] = useState(null);
  // pendingMove guarda { task, targetState } cuando se necesita evidencia
  // antes de persistir el movimiento a "terminado".
  const [pendingMove, setPendingMove] = useState(null);
  const [error, setError] = useState("");

  // Sensores del DndContext:
  // - PointerSensor con activationConstraint de 5px evita disparar drag
  //   por click accidental sobre los botones fallback.
  // - KeyboardSensor da soporte para navegacion con teclado (Enter para
  //   levantar, flechas para mover, Espacio para soltar).
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor)
  );

  const loadTasks = () =>
    api
      .get(`/api/v1/historia/equipo/${teamId}/kanban`)
      .then((r) => setTasks(r.data))
      .catch(() => setError("No se pudo cargar el tablero."));

  useEffect(() => {
    loadTasks();
  }, [teamId]);

  // Entrada unica para mover una tarea. Si el destino es "terminado" y
  // la tarea no tiene evidencia previa, abre el modal en vez de disparar
  // el request. La regla tambien esta validada en el backend, aqui es UX.
  const requestMove = (task, targetState) => {
    setError("");
    if (task.estado_kanban === targetState) return;

    const needsEvidence =
      targetState === "terminado" &&
      !task.evidencia_url &&
      !task.comentario;

    if (needsEvidence) {
      setPendingMove({ task, targetState });
      return;
    }
    persistMove(task, targetState, {});
  };

  const persistMove = async (task, targetState, extra) => {
    try {
      await api.patch(`/api/v1/historia/${task.id}/mover`, {
        nuevo_estado: targetState,
        ...extra,
      });
      await loadTasks();
    } catch (err) {
      const detail =
        err?.response?.data?.detail || "No se pudo mover la tarjeta.";
      setError(detail);
    }
  };

  const handleDragStart = ({ active }) => {
    const task = tasks.find((t) => t.id === active.id);
    setActiveTask(task || null);
  };

  const handleDragEnd = ({ active, over }) => {
    setActiveTask(null);
    if (!over) return;
    const task = tasks.find((t) => t.id === active.id);
    if (!task) return;
    requestMove(task, over.id);
  };

  const confirmEvidence = async (comentario) => {
    if (!pendingMove) return;
    const { task, targetState } = pendingMove;
    setPendingMove(null);
    await persistMove(task, targetState, { comentario });
  };

  return (
    <>
      {error && (
        <div
          role="alert"
          style={{
            background: "#fdecea",
            color: "#611a15",
            padding: "0.5rem",
            marginBottom: "0.5rem",
            borderRadius: "4px",
          }}
        >
          {error}
        </div>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={() => setActiveTask(null)}
      >
        <div style={{ display: "flex", gap: "1rem", alignItems: "flex-start" }}>
          {COLUMNS.map((col) => (
            <ColumnaKanban
              key={col.key}
              columnKey={col.key}
              label={col.label}
              tasks={tasks
                .filter((t) => t.estado_kanban === col.key)
                .sort(sortByPriority)}
              onMove={requestMove}
            />
          ))}
        </div>

        {/* DragOverlay muestra un preview flotante de la tarjeta durante
            el drag, independiente del layout de la columna origen. */}
        <DragOverlay>
          {activeTask ? <TarjetaHistoria task={activeTask} isOverlay /> : null}
        </DragOverlay>
      </DndContext>

      {pendingMove && (
        <ModalEvidencia
          task={pendingMove.task}
          onConfirm={confirmEvidence}
          onCancel={() => setPendingMove(null)}
        />
      )}
    </>
  );
}
