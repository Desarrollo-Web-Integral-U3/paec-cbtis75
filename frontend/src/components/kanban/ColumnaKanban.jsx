import { useDroppable } from "@dnd-kit/core";

import TarjetaHistoria from "./TarjetaHistoria";

// Columna droppable del Kanban. Cambia el fondo cuando hay una tarjeta
// encima para dar feedback visual claro durante el drag.
export default function ColumnaKanban({ columnKey, label, tasks, onMove }) {
  const { setNodeRef, isOver } = useDroppable({ id: columnKey });

  const classNames = ["kb-column", isOver ? "kb-column--over" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <div ref={setNodeRef} className={classNames}>
      <div className="kb-column-header">
        <span className="kb-column-title">{label}</span>
        <span className="kb-column-count">{tasks.length}</span>
      </div>
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
