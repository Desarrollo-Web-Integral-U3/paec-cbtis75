import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// La rúbrica exige una Progressive Web App (PWA). vite-plugin-pwa genera
// el manifest.json y el service worker automáticamente en el build.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      manifest: {
        name: "PAEC - Gestión de Proyectos Escolares",
        short_name: "PAEC",
        description: "Plataforma ABP + Scrum + Design Sprint para CBTis75",
        theme_color: "#1e293b",
        background_color: "#ffffff",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png" },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
  },
});
