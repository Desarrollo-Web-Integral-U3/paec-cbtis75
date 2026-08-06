import { create } from "zustand";
import { persist } from "zustand/middleware";

// Nota: esto es un proyecto real desplegado fuera de claude.ai (no un
// artifact embebido), así que localStorage es válido aquí para persistir
// la sesión entre recargas de página.
export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null, // { id, nombre_completo, rol, ... }
      // Equipo activo del usuario en la sesión. Se actualiza cuando:
      //  - se crea un equipo nuevo (TeamSetup)
      //  - se navega a /dashboard/:teamId, /dailies/:teamId, etc.
      // El nav superior usa este id para armar los enlaces del menú y
      // evitar que /dailies caiga al fallback team_id=1.
      currentTeamId: 1,
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null, currentTeamId: 1 }),
      setCurrentTeamId: (teamId) =>
        set({ currentTeamId: Number(teamId) || 1 }),
    }),
    { name: "paec-auth" }
  )
);
