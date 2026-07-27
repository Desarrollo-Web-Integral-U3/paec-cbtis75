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

  const style = {
    border: "1px solid #eee",
    padding: "0.5rem",
    margin: "0.5rem 0",
    background: "#fff",
    borderRadius: "4px",
    boxShadow: isOverlay ? "0 4px 12px rgba(0,0,0,0.15)" : "none",
    opacity: isDragging && !isOverlay ? 0.4 : 1,
    cursor: isOverlay ? "grabbing" : "grab",
    transform: transform
      ? `translate3d(${transform.x}px, ${transform.y}px, 0)`
      : undefined,
  };

  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <strong>{task.nombre_actividad}</strong>
      <p style={{ margin: "0.25rem 0", fontSize: "0.85rem", color: "#555" }}>
        Prioridad: {task.prioridad} &middot; {task.story_points} pts
      </p>

      {/* Botones fallback: mismo comportamiento que el drag pero accesibles
          via teclado/tap. onPointerDown detiene la propagacion para que
          hacer click en el boton no dispare el sensor de drag del padre. */}
      {!isOverlay && onMove && (
        <div
          style={{ display: "flex", gap: "0.25rem", flexWrap: "wrap" }}
          onPointerDown={(e) => e.stopPropagation()}
        >
          {currentColumn !== "por_hacer" && (
            <button type="button" onClick={() => onMove(task, "por_hacer")}>
              &larr; Por hacer
            </button>
          )}
          {currentColumn !== "haciendo" && (
            <button type="button" onClick={() => onMove(task, "haciendo")}>
              Haciendo
            </button>
          )}
          {currentColumn !== "terminado" && (
            <button type="button" onClick={() => onMove(task, "terminado")}>
              Terminado &rarr;
            </button>
          )}
        </div>
      )}
    </div>
  );
}
