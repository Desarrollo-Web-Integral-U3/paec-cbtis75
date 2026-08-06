import { useDraggable } from "@dnd-kit/core";

// Tarjeta arrastrable de una historia de usuario dentro del Kanban.
// Ademas del drag, expone botones fallback para accesibilidad (teclado)
// y para dispositivos moviles donde arrastrar puede ser incomodo.
export default function TarjetaHistoria({
  task,
  currentColumn,
  onMove,
  isOverlay = false,
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } =
    useDraggable({ id: task.id, disabled: isOverlay });

  const classNames = [
    "kb-card",
    isDragging && !isOverlay ? "kb-card--dragging" : "",
    isOverlay ? "kb-card--overlay" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const dragStyle = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      className={classNames}
      style={dragStyle}
      {...attributes}
      {...listeners}
    >
      <div className="kb-card-title">{task.nombre_actividad}</div>
      <div className="kb-card-meta">
        Prioridad: {task.prioridad} &middot; {task.story_points} pts
      </div>

      {/* Botones fallback (accesibilidad + mobile). stopPropagation en
          onPointerDown para que el click no dispare el sensor de drag. */}
      {!isOverlay && onMove && (
        <div
          className="kb-card-actions"
          onPointerDown={(e) => e.stopPropagation()}
        >
          {currentColumn !== "por_hacer" && (
            <button
              type="button"
              className="kb-btn"
              onClick={() => onMove(task, "por_hacer")}
            >
              &larr; Por hacer
            </button>
          )}
          {currentColumn !== "haciendo" && (
            <button
              type="button"
              className="kb-btn"
              onClick={() => onMove(task, "haciendo")}
            >
              Haciendo
            </button>
          )}
          {currentColumn !== "terminado" && (
            <button
              type="button"
              className="kb-btn"
              onClick={() => onMove(task, "terminado")}
            >
              Terminado &rarr;
            </button>
          )}
        </div>
      )}
    </div>
  );
}
