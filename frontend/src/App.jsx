import { BrowserRouter } from "react-router-dom";
import AppRoutes from "./routes";

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{ display: "flex", gap: "1rem", padding: "1rem" }}>
        <a href="/equipo">Mi equipo</a>
        <a href="/design-sprint">Design Sprint</a>
        <a href="/backlog">Backlog</a>
        <a href="/kanban">Kanban</a>
        <a href="/dailies">Dailies</a>
        <a href="/dashboard">Dashboard</a>
      </nav>
      <main style={{ padding: "1rem" }}>
        <AppRoutes />
      </main>
    </BrowserRouter>
  );
}
