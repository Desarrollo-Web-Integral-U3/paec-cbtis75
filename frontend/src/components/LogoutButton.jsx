import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

/**
 * Botón de cerrar sesión. Como el backend usa JWT sin estado (sin
 * blacklist ni tabla de sesiones), no existe ni se necesita un endpoint
 * de logout: basta con limpiar el store local y redirigir. El interceptor
 * de axios (api/client.js) deja de mandar el header Authorization en
 * cuanto el token queda en null.
 *
 * No se renderiza nada si no hay sesión activa.
 */
export default function LogoutButton() {
  const navigate = useNavigate();
  const token = useAuthStore((s) => s.token);
  const logout = useAuthStore((s) => s.logout);

  if (!token) return null;

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      className="app-nav-link btn-ghost"
      aria-label="Cerrar sesión"
    >
      Cerrar sesión
    </button>
  );
}