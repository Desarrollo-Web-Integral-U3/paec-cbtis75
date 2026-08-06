import { BrowserRouter, NavLink } from "react-router-dom";
import AppRoutes from "./routes";
import { useAuthStore } from "./store/authStore";
import LogoutButton from "./components/LogoutButton";

/**
 * Enlaces principales del nav. Las 4 rutas de "equipo activo" (backlog,
 * kanban, dailies, dashboard) usan currentTeamId del store para no seguir
 * hardcodeando team_id=1. Se actualiza al crear equipo o al navegar a una
 * URL con :teamId.
 */
function buildNavLinks(currentTeamId) {
  const t = currentTeamId || 1;
  return [
    { to: "/equipo", label: "Mi equipo" },
    { to: "/design-sprint", label: "Design Sprint" },
    { to: `/backlog/${t}`, label: "Backlog" },
    { to: `/kanban/${t}`, label: "Kanban" },
    { to: `/dailies/${t}`, label: "Dailies" },
    { to: `/dashboard/${t}`, label: "Dashboard" },
    { to: "/perfil", label: "Mi perfil" },
  ];
}

export default function App() {
  const currentTeamId = useAuthStore((s) => s.currentTeamId);
  const links = buildNavLinks(currentTeamId);

  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="app-nav" aria-label="Navegacion principal">
          <div className="app-nav-inner">
            <NavLink to="/" className="app-brand">
              PAEC
            </NavLink>
            <div className="app-nav-links">
              {links.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  className={({ isActive }) =>
                    isActive
                      ? "app-nav-link app-nav-link--active"
                      : "app-nav-link"
                  }
                >
                  {link.label}
                </NavLink>
              ))}
              <LogoutButton />
            </div>
          </div>
        </nav>
        <main className="app-main">
          <AppRoutes />
        </main>
      </div>
    </BrowserRouter>
  );
}
