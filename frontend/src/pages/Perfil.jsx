import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuthStore } from "../store/authStore";

/**
 * Página de perfil del usuario autenticado.
 *
 * Cumple el ejercicio del derecho ARCO de Cancelación (LFPDPPP):
 * permite al titular solicitar la anonimización de sus datos personales
 * llamando a DELETE /api/v1/auth/me.
 *
 * Flujo:
 *  1. GET /me al montar la página para mostrar a quién se va a eliminar.
 *  2. Al pulsar "Eliminar mi cuenta" se pide confirmación explícita
 *     (destructivo, irreversible).
 *  3. DELETE /me → 204 → logout local + redirect a /login.
 */
export default function Perfil() {
  const navigate = useNavigate();
  const logout = useAuthStore((s) => s.logout);

  const [perfil, setPerfil] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    let cancelado = false;
    api
      .get("/api/v1/auth/me")
      .then((r) => {
        if (!cancelado) setPerfil(r.data);
      })
      .catch(() => {
        if (!cancelado) setError("No se pudo cargar tu perfil.");
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  const handleEliminar = async () => {
    // Confirmación destructiva. window.confirm es KISS y suficiente para R1;
    // se puede reemplazar más adelante por un modal más pulido.
    const confirmado = window.confirm(
      "¿Seguro que deseas eliminar tu cuenta?\n\n" +
        "Se anonimizarán tus datos personales (nombre, correo, número de control).\n" +
        "Tus aportaciones históricas (tareas, dailies) se conservarán sin tu nombre.\n\n" +
        "Esta acción NO se puede deshacer.",
    );
    if (!confirmado) return;

    setEnviando(true);
    setError("");
    try {
      await api.delete("/api/v1/auth/me");
      // Éxito (204): limpiamos la sesión local y regresamos al login.
      logout();
      navigate("/login", {
        replace: true,
        state: { mensaje: "Tu cuenta fue eliminada. Gracias por usar PAEC." },
      });
    } catch (err) {
      const detalle = err?.response?.data?.detail;
      setError(
        typeof detalle === "string"
          ? detalle
          : "No se pudo eliminar la cuenta. Intenta de nuevo más tarde.",
      );
      setEnviando(false);
    }
  };

  if (cargando) return <p>Cargando perfil…</p>;

  return (
    <div style={{ maxWidth: 600 }}>
      <h1>Mi perfil</h1>

      {perfil ? (
        <dl>
          <dt>Nombre</dt>
          <dd>{perfil.nombre_completo}</dd>
          <dt>Correo</dt>
          <dd>{perfil.email}</dd>
          <dt>Número de control</dt>
          <dd>{perfil.numero_control}</dd>
          <dt>Rol</dt>
          <dd>{perfil.rol}</dd>
        </dl>
      ) : (
        <p style={{ color: "var(--error-color)" }}>{error}</p>
      )}

      <hr style={{ margin: "2rem 0" }} />

      <section>
        <h2>Eliminar mi cuenta (derecho ARCO)</h2>
        <p>
          En cumplimiento de la <strong>LFPDPPP</strong>, puedes solicitar
          en cualquier momento la cancelación de tus datos personales. Se
          anonimizarán tu nombre, correo y número de control. Las tareas y
          dailies que hayas capturado <em>se conservarán</em> (para no
          romper el historial del equipo) pero ya no podrán vincularse a ti.
        </p>
        <p>
          Esta acción es <strong>irreversible</strong>: después no podrás
          iniciar sesión con esta cuenta.
        </p>

        {error && (
          <p role="alert" style={{ color: "var(--error-color)" }}>
            {error}
          </p>
        )}

        <button
          type="button"
          onClick={handleEliminar}
          disabled={enviando}
          style={{
            background: "var(--error-color, #b91c1c)",
            color: "white",
            padding: "0.6rem 1rem",
            border: "none",
            borderRadius: 4,
            cursor: enviando ? "not-allowed" : "pointer",
          }}
        >
          {enviando ? "Eliminando…" : "Eliminar mi cuenta"}
        </button>
      </section>
    </div>
  );
}
