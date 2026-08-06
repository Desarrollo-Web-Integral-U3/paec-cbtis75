import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuthStore } from "../store/authStore";

/**
 * Pagina de perfil del usuario autenticado.
 *
 * Cumple el ejercicio del derecho ARCO de Cancelacion (LFPDPPP):
 * permite al titular solicitar la anonimizacion de sus datos personales
 * llamando a DELETE /api/v1/auth/me.
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
    const confirmado = window.confirm(
      "¿Seguro que deseas eliminar tu cuenta?\n\n" +
        "Se anonimizaran tus datos personales (nombre, correo, numero de control).\n" +
        "Tus aportaciones historicas (tareas, dailies) se conservaran sin tu nombre.\n\n" +
        "Esta accion NO se puede deshacer.",
    );
    if (!confirmado) return;

    setEnviando(true);
    setError("");
    try {
      await api.delete("/api/v1/auth/me");
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
          : "No se pudo eliminar la cuenta. Intenta de nuevo mas tarde.",
      );
      setEnviando(false);
    }
  };

  if (cargando) {
    return (
      <div className="pf-page">
        <p className="loading-state">Cargando perfil...</p>
      </div>
    );
  }

  return (
    <div className="pf-page">
      <header className="pf-header">
        <h1 className="pf-title">Mi perfil</h1>
      </header>

      <section className="pf-card">
        <h2>Datos personales</h2>
        {perfil ? (
          <dl className="pf-dl">
            <dt>Nombre</dt>
            <dd>{perfil.nombre_completo}</dd>
            <dt>Correo</dt>
            <dd>{perfil.email}</dd>
            <dt>Numero de control</dt>
            <dd>{perfil.numero_control}</dd>
            <dt>Rol</dt>
            <dd>{perfil.rol}</dd>
          </dl>
        ) : (
          <p role="alert" className="cap-alert">
            {error}
          </p>
        )}
      </section>

      <section className="pf-card pf-card--danger">
        <h2>Eliminar mi cuenta (derecho ARCO)</h2>
        <p className="pf-arco-text">
          En cumplimiento de la <strong>LFPDPPP</strong>, puedes solicitar
          en cualquier momento la cancelacion de tus datos personales. Se
          anonimizaran tu nombre, correo y numero de control. Las tareas y
          dailies que hayas capturado <em>se conservaran</em> (para no
          romper el historial del equipo) pero ya no podran vincularse a ti.
        </p>
        <p className="pf-arco-text">
          Esta accion es <strong>irreversible</strong>: despues no podras
          iniciar sesion con esta cuenta.
        </p>

        {error && (
          <p role="alert" className="cap-alert">
            {error}
          </p>
        )}

        <button
          type="button"
          className="btn-danger"
          onClick={handleEliminar}
          disabled={enviando}
          style={{ marginTop: "0.75rem" }}
        >
          {enviando ? "Eliminando..." : "Eliminar mi cuenta"}
        </button>
      </section>
    </div>
  );
}
