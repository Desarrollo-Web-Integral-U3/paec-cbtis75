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
  const [pendingMove, setPendingMove] = useState(null);
  const [error, setError] = useState("");

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
    <div className="kb-page">
      <header className="kb-header">
        <h1 className="kb-title">Tablero Kanban</h1>
        <p className="kb-subtitle">
          Arrastra las tarjetas entre columnas o usa los botones de accion.
          Para marcar como Terminado se requiere evidencia.
        </p>
      </header>

      {error && (
        <div className="kb-error" role="alert">
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
        <div className="kb-board">
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
    </div>
  );
}
