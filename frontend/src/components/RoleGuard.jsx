import { Navigate } from "react-router-dom";
import { useAuthStore } from "../store/authStore";

/**
 * Protege rutas según el rol del usuario. IMPORTANTE: esto es solo UX
 * (evita que el estudiante vea un botón que no debería). La autorización
 * REAL vive en el BackEnd (require_role en cada endpoint) — nunca confiar
 * solo en este componente para seguridad.
 */
export default function RoleGuard({ allowedRoles, children }) {
  const user = useAuthStore((s) => s.user);

  if (!user) return <Navigate to="/login" replace />;
  if (!allowedRoles.includes(user.rol)) {
    return <p>No tienes permisos para ver esta sección.</p>;
  }
  return children;
}
