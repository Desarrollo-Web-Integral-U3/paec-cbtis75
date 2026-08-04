import { Routes, Route } from "react-router-dom";
import Login from "../pages/Login";
import Register from "../pages/Register";
import TeamSetup from "../pages/TeamSetup";
import DesignSprint from "../pages/DesignSprint";
import KanbanBoard from "../pages/KanbanBoard";
import Dailies from "../pages/Dailies";
import Dashboard from "../pages/Dashboard";
import Backlog from "../pages/Backlog";
import RoleGuard from "../components/RoleGuard";
import Intro from "../pages/Intro";
import PrivacyPolicy from "../pages/PrivacyPolicy";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Intro />} />
      <Route path="/aviso-de-privacidad" element={<PrivacyPolicy />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/equipo" element={<TeamSetup />} />
      <Route path="/design-sprint" element={<DesignSprint />} />
      <Route path="/backlog" element={<Backlog teamId={1} />} />
      <Route path="/kanban" element={<KanbanBoard teamId={1} />} />
      <Route path="/dailies" element={<Dailies teamId={1} />} />
      <Route
        path="/dashboard"
        element={
          <RoleGuard allowedRoles={["docente", "scrum_master"]}>
            <Dashboard teamId={1} />
          </RoleGuard>
        }
      />
    </Routes>
  );
}
