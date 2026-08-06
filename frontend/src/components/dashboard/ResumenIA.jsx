import { useState } from "react";
import api from "../../api/client";

/**
 * Tarjeta de "Resumen semanal con IA".
 *
 * Consume el endpoint POST /api/v1/ai/resumen-semanal/{teamId}, que a su
 * vez llama al servicio de terceros Groq (LLM) para generar un resumen
 * ejecutivo de los dailies de la última semana del equipo.
 *
 * Cubre Actividad 3 · Uso de Inteligencia Artificial y refuerza el
 * criterio de consumo de servicios web de terceros.
 */
export default function ResumenIA({ teamId }) {
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [resultado, setResultado] = useState(null);

  const generar = async () => {
    setCargando(true);
    setError("");
    setResultado(null);
    try {
      const r = await api.post(`/api/v1/ai/resumen-semanal/${teamId}`);
      setResultado(r.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "No se pudo generar el resumen. Revisa que GROQ_API_KEY esté configurada."
      );
    } finally {
      setCargando(false);
    }
  };

  return (
    <article className="dash-card">
      <h3 className="dash-card-title">🤖 Resumen semanal con IA</h3>
      <p style={{ color: "#94a3b8", fontSize: "0.9rem", marginTop: "-0.5rem" }}>
        Analiza los dailies de los últimos 7 días con un modelo de lenguaje
        (Groq · Llama 3.3) y genera un reporte ejecutivo.
      </p>

      <button
        onClick={generar}
        disabled={cargando}
        className="btn-primary"
        style={{ maxWidth: "260px", marginTop: "0.5rem" }}
      >
        {cargando ? "Analizando dailies..." : "Generar resumen"}
      </button>

      {error && (
        <div
          role="alert"
          style={{
            marginTop: "1rem",
            padding: "0.75rem 1rem",
            background: "rgba(239,68,68,0.1)",
            border: "1px solid rgba(239,68,68,0.3)",
            borderRadius: 6,
            color: "#fca5a5",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      )}

      {resultado && (
        <div style={{ marginTop: "1rem" }}>
          <div
            style={{
              fontSize: "0.8rem",
              color: "#94a3b8",
              marginBottom: "0.5rem",
            }}
          >
            Analizados <strong>{resultado.dailies_analizados}</strong> daily(s) ·
            Rango {resultado.rango.desde} a {resultado.rango.hasta} · Modelo{" "}
            <code>{resultado.modelo}</code>
          </div>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              fontFamily: "system-ui, -apple-system, sans-serif",
              fontSize: "0.95rem",
              lineHeight: 1.55,
              background: "rgba(15,23,42,0.5)",
              padding: "1rem 1.25rem",
              borderRadius: 8,
              border: "1px solid rgba(148,163,184,0.15)",
              color: "#e2e8f0",
              margin: 0,
            }}
          >
            {resultado.resumen}
          </pre>
        </div>
      )}
    </article>
  );
}
