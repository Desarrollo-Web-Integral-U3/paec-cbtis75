import axios from "axios";
import { useAuthStore } from "../store/authStore";

// Todas las peticiones pasan por aquí. Ventajas:
// - Un solo lugar para la URL base (variable de entorno, no hardcodeada)
// - Inyecta automáticamente el JWT en cada request
// - Centraliza el manejo de errores 401 (token vencido -> logout)
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
    }
    return Promise.reject(error);
  }
);

export default api;
