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
      login: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: "paec-auth" }
  )
);
