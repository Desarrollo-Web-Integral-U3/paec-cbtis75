import { BrowserRouter, NavLink } from "react-router-dom";
import AppRoutes from "./routes";

// Enlaces principales de la nav. Se centralizan aca para poder recorrer
// el arreglo y aplicar el mismo estilo (incluida la clase de "activo").
const NAV_LINKS = [
  { to: "/equipo", label: "Mi equipo" },
  { to: "/design-sprint", label: "Design Sprint" },
  { to: "/backlog", label: "Backlog" },
  { to: "/kanban", label: "Kanban" },
  { to: "/dailies", label: "Dailies" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/perfil", label: "Mi perfil" },
];

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="app-nav" aria-label="Navegacion principal">
          <div className="app-nav-inner">
            <NavLink to="/" className="app-brand">
              PAEC
            </NavLink>
            <div className="app-nav-links">
              {NAV_LINKS.map((link) => (
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
