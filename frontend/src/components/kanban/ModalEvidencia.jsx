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
      style={overlayStyle}
      onClick={onCancel}
    >
      <div style={dialogStyle} onClick={(e) => e.stopPropagation()}>
        <h3 id="modal-evidencia-titulo" style={{ marginTop: 0 }}>
          Evidencia requerida
        </h3>
        <p style={{ marginTop: 0 }}>
          Para marcar <strong>{task.nombre_actividad}</strong> como
          Terminado es necesario describir la evidencia entregada.
        </p>
        <label
          htmlFor="comentario-evidencia"
          style={{ display: "block", marginBottom: "0.25rem" }}
        >
          Describa la evidencia:
        </label>
        <textarea
          id="comentario-evidencia"
          value={comentario}
          onChange={(e) => setComentario(e.target.value)}
          rows={4}
          style={{ width: "100%", padding: "0.5rem", boxSizing: "border-box" }}
          autoFocus
        />
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            justifyContent: "flex-end",
            marginTop: "0.75rem",
          }}
        >
          <button type="button" onClick={onCancel} disabled={submitting}>
            Cancelar
          </button>
          <button type="button" onClick={handleConfirm} disabled={!canSubmit}>
            {submitting ? "Guardando..." : "Confirmar"}
          </button>
        </div>
      </div>
    </div>
  );
}

const overlayStyle = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.45)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 1000,
};

const dialogStyle = {
  background: "#fff",
  padding: "1rem",
  borderRadius: "6px",
  width: "min(480px, 90vw)",
  boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
};
