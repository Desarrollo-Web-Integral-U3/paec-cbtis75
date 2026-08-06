import { useEffect } from "react";
import { Routes, Route, useParams } from "react-router-dom";
import { useAuthStore } from "../store/authStore";
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
import Perfil from "../pages/Perfil";

/**
 * Wrappers que leen :teamId de la URL para no seguir hardcodeando team_id=1
 * en todo el enrutador. Si la URL trae :teamId lo usa; si no, cae al
 * currentTeamId del store (o 1 como último fallback).
 *
 * Adicionalmente, cada wrapper actualiza el currentTeamId del store para
 * que el nav superior recuerde el último equipo visitado incluso después
 * de recargar la página.
 */
function useEffectiveTeamId() {
  const { teamId } = useParams();
  const currentTeamId = useAuthStore((s) => s.currentTeamId);
  const setCurrentTeamId = useAuthStore((s) => s.setCurrentTeamId);
  const effective = Number(teamId) || currentTeamId || 1;

  useEffect(() => {
    if (teamId && Number(teamId) !== currentTeamId) {
      setCurrentTeamId(teamId);
    }
  }, [teamId, currentTeamId, setCurrentTeamId]);

  return effective;
}

function DashboardRoute() {
  const teamId = useEffectiveTeamId();
  return <Dashboard teamId={teamId} />;
}
function DailiesRoute() {
  const teamId = useEffectiveTeamId();
  return <Dailies teamId={teamId} />;
}
function KanbanRoute() {
  const teamId = useEffectiveTeamId();
  return <KanbanBoard teamId={teamId} />;
}
function BacklogRoute() {
  const teamId = useEffectiveTeamId();
  return <Backlog teamId={teamId} />;
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Intro />} />
      <Route path="/aviso-de-privacidad" element={<PrivacyPolicy />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/equipo" element={<TeamSetup />} />
      <Route path="/design-sprint" element={<DesignSprint />} />

      {/* Rutas con teamId dinámico (nuevas) */}
      <Route path="/backlog/:teamId" element={<BacklogRoute />} />
      <Route path="/kanban/:teamId" element={<KanbanRoute />} />
      <Route path="/dailies/:teamId" element={<DailiesRoute />} />
      <Route
        path="/dashboard/:teamId"
        element={
          <RoleGuard allowedRoles={["docente", "scrum_master"]}>
            <DashboardRoute />
          </RoleGuard>
        }
      />

      {/* Rutas legacy sin teamId → siguen apuntando al equipo 1 */}
      <Route path="/backlog" element={<BacklogRoute />} />
      <Route path="/kanban" element={<KanbanRoute />} />
      <Route path="/dailies" element={<DailiesRoute />} />
      <Route
        path="/dashboard"
        element={
          <RoleGuard allowedRoles={["docente", "scrum_master"]}>
            <DashboardRoute />
          </RoleGuard>
        }
      />

      <Route path="/perfil" element={<Perfil />} />
    </Routes>
  );
}
