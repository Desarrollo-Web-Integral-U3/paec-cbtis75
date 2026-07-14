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
      // TODO: pedir /api/v1/auth/me (o decodificar el JWT) para obtener
      // el perfil completo del usuario y guardarlo junto al token.
      login(data.access_token, { rol: "estudiante" });
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
