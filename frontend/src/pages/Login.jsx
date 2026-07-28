import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import { useAuthStore } from "../store/authStore";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const { data } = await api.post("/api/v1/auth/login", { email, password });
      // El JWT lleva el rol en el payload (backend: create_access_token con
      // {"sub": id, "rol": rol}). Se decodifica en el cliente (base64) para
      // que el zustand store tenga el rol real y RoleGuard pueda evaluar
      // las rutas protegidas. La firma del JWT sigue validandola el backend
      // en cada request; esto es solo lectura de un dato publico.
      const payload = JSON.parse(atob(data.access_token.split(".")[1]));
      login(data.access_token, {
        id: parseInt(payload.sub, 10),
        rol: payload.rol,
      });
      navigate("/dashboard");
    } catch {
      setError("Correo o contraseña incorrectos.");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h1>Iniciar sesión — PAEC</h1>
      <input
        type="email"
        placeholder="Correo institucional"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        type="password"
        placeholder="Contraseña"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <p role="alert">{error}</p>}
      <button type="submit">Entrar</button>
    </form>
  );
}
