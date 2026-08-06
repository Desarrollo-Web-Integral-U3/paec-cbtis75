import { useState } from "react";

// Modal accesible para capturar la evidencia/comentario obligatorio
// cuando una tarjeta se mueve a "Terminado". Reemplaza el prompt()
// nativo anterior (UX pobre y no accesible) sin cambiar la regla dura
// del backend, que sigue validando en el servidor.
export default function ModalEvidencia({ task, onConfirm, onCancel }) {
  const [comentario, setComentario] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const canSubmit = comentario.trim().length > 0 && !submitting;

  const handleConfirm = async () => {
    if (!canSubmit) return;
    setSubmitting(true);
    try {
      await onConfirm(comentario.trim());
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-evidencia-titulo"
      className="kb-modal-overlay"
      onClick={onCancel}
    >
      <div className="kb-modal" onClick={(e) => e.stopPropagation()}>
        <h3 id="modal-evidencia-titulo">Evidencia requerida</h3>
        <p>
          Para marcar <strong>{task.nombre_actividad}</strong> como Terminado
          es necesario describir la evidencia entregada.
        </p>
        <label htmlFor="comentario-evidencia" className="kb-modal-label">
          Describa la evidencia:
        </label>
        <textarea
          id="comentario-evidencia"
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
          rows={4}
          autoFocus
        />
        <div className="kb-modal-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancelar
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={handleConfirm}
            disabled={!canSubmit}
          >
            {submitting ? "Guardando..." : "Confirmar"}
          </button>
        </div>
      </div>
    </div>
  );
}
