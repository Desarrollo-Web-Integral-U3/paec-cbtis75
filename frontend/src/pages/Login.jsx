import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
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
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Iniciar sesión — PAEC</h1>
          <p>Accede a tu cuenta para gestionar tus proyectos</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {error && (
            <div className="error-message" role="alert">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
              <span>{error}</span>
            </div>
          )}
          <div className="form-group">
            <label htmlFor="email">Correo institucional</label>
            <input
              type="email"
              id="email"
              placeholder="correo@cbtis75.edu.mx"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="btn-primary">Entrar</button>
        </form>
        <div className="auth-footer">
          <p>¿No tienes cuenta? <Link to="/register">Regístrate</Link></p>
        </div>
      </div>
    </div>
  );

}
