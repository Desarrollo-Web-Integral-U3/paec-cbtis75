import { useDroppable } from "@dnd-kit/core";

import TarjetaHistoria from "./TarjetaHistoria";

// Columna droppable del Kanban. Cambia el fondo cuando hay una tarjeta
// encima para dar feedback visual claro durante el drag.
export default function ColumnaKanban({ columnKey, label, tasks, onMove }) {
  const { setNodeRef, isOver } = useDroppable({ id: columnKey });

  return (
    <div
      ref={setNodeRef}
      style={{
        flex: 1,
        border: "1px solid #ddd",
        padding: "0.5rem",
        borderRadius: "4px",
        background: isOver ? "#eef6ff" : "transparent",
        transition: "background 120ms ease",
        minHeight: "300px",
      }}
    >
      <h3 style={{ marginTop: 0 }}>
        {label}{" "}
        <span style={{ color: "#888", fontWeight: "normal" }}>
          ({tasks.length})
        </span>
      </h3>
      {tasks.map((t) => (
        <TarjetaHistoria
          key={t.id}
          task={t}
          currentColumn={columnKey}
          onMove={onMove}
        />
      ))}
    </div>
  );
}
