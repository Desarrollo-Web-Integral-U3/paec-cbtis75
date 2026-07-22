import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api/client";
import PrivacyNotice from "../components/PrivacyNotice";

export default function Register() {
  const [formData, setFormData] = useState({
    nombre_completo: "",
    email: "",
    numero_control: "",
    password: "",
    confirm_password: "",
    // Consentimiento explícito del aviso de privacidad — inicia FALSE:
    // el usuario tiene que marcar el checkbox activamente (nunca pre-marcado).
    consentimiento_privacidad: false,
  });
  const [fieldErrors, setFieldErrors] = useState({});
  const [backendError, setBackendError] = useState("");
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Limpiar el error del campo al escribir
    if (fieldErrors[name]) {
      setFieldErrors((prev) => ({ ...prev, [name]: "" }));
    }
  };

  const validate = () => {
    const errors = {};
    const { nombre_completo, email, numero_control, password, confirm_password } = formData;

    if (!nombre_completo.trim()) {
      errors.nombre_completo = "El nombre es obligatorio.";
    } else if (nombre_completo.trim().length < 3) {
      errors.nombre_completo = "El nombre debe tener al menos 3 caracteres.";
    } else if (nombre_completo.trim().length > 100) {
      errors.nombre_completo = "El nombre no puede exceder 100 caracteres.";
    } else if (!/^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$/.test(nombre_completo)) {
      errors.nombre_completo = "El nombre solo puede contener letras y espacios.";
    }

    if (!email.trim()) {
      errors.email = "El correo es obligatorio.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errors.email = "Ingresa un correo electrónico válido.";
    } else if (!email.endsWith("@cbtis75.edu.mx")) {
      errors.email = "Debes ingresar un correo institucional.";
    }

    if (!numero_control.trim()) {
      errors.numero_control = "El número de control es obligatorio.";
    } else if (!/^\d+$/.test(numero_control)) {
      errors.numero_control = "El número de control solo puede contener números.";
    } else if (numero_control.length !== 8) {
      errors.numero_control = "El número de control debe tener 8 dígitos.";
    }

    if (!password) {
      errors.password = "La contraseña es obligatoria.";
    } else if (password.length < 8) {
      errors.password = "La contraseña debe tener al menos 8 caracteres.";
    } else if (!/[A-Z]/.test(password)) {
      errors.password = "Debe contener una letra mayúscula.";
    } else if (!/[a-z]/.test(password)) {
      errors.password = "Debe contener una letra minúscula.";
    } else if (!/[0-9]/.test(password)) {
      errors.password = "Debe contener un número.";
    } else if (!/[@#$%&*!]/.test(password)) {
      errors.password = "Debe contener un carácter especial.";
    }

    if (!confirm_password) {
      errors.confirm_password = "Debes confirmar la contraseña.";
    } else if (password !== confirm_password) {
      errors.confirm_password = "Las contraseñas no coinciden.";
    }

    if (!formData.consentimiento_privacidad) {
      errors.consentimiento_privacidad =
        "Debes aceptar el aviso de privacidad para continuar.";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBackendError("");

    if (!validate()) {
      return;
    }

    const {
      nombre_completo,
      email,
      numero_control,
      password,
      consentimiento_privacidad,
    } = formData;

    try {
      await api.post("/api/v1/auth/register", {
        nombre_completo,
        email,
        numero_control,
        password,
        consentimiento_privacidad,
      });
      navigate("/login");
    } catch (err) {
      const msg = err.response?.data?.detail;
      if (typeof msg === "string") {
        setBackendError(msg);
      } else {
        setBackendError("Ocurrió un error al registrar la cuenta. Verifica tus datos.");
      }
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Crea tu cuenta</h1>
          <p>Únete a PAEC para gestionar tus proyectos</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form" noValidate>
          {backendError && (
            <div className="error-message" role="alert">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              <span>{backendError}</span>
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="nombre_completo">Nombre Completo</label>
            <input
              type="text"
              id="nombre_completo"
              name="nombre_completo"
              placeholder="Juan Pérez"
              value={formData.nombre_completo}
              onChange={handleChange}
            />
            {fieldErrors.nombre_completo && <span style={{ color: 'var(--error-color)', fontSize: '0.85rem' }}>{fieldErrors.nombre_completo}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="email">Correo Institucional</label>
            <input
              type="email"
              id="email"
              name="email"
              placeholder="juan.perez@cbtis75.edu.mx"
              value={formData.email}
              onChange={handleChange}
            />
            {fieldErrors.email && <span style={{ color: 'var(--error-color)', fontSize: '0.85rem' }}>{fieldErrors.email}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="numero_control">Número de Control</label>
            <input
              type="text"
              id="numero_control"
              name="numero_control"
              placeholder="1931075..."
              value={formData.numero_control}
              onChange={handleChange}
            />
            {fieldErrors.numero_control && <span style={{ color: 'var(--error-color)', fontSize: '0.85rem' }}>{fieldErrors.numero_control}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="password">Contraseña</label>
            <input
              type="password"
              id="password"
              name="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
            />
            {fieldErrors.password && <span style={{ color: 'var(--error-color)', fontSize: '0.85rem' }}>{fieldErrors.password}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="confirm_password">Confirmar Contraseña</label>
            <input
              type="password"
              id="confirm_password"
              name="confirm_password"
              placeholder="••••••••"
              value={formData.confirm_password}
              onChange={handleChange}
            />
            {fieldErrors.confirm_password && <span style={{ color: 'var(--error-color)', fontSize: '0.85rem' }}>{fieldErrors.confirm_password}</span>}
          </div>

          <div className="form-group">
            <PrivacyNotice
              onAccept={(aceptado) => {
                setFormData((prev) => ({ ...prev, consentimiento_privacidad: aceptado }));
                if (aceptado && fieldErrors.consentimiento_privacidad) {
                  setFieldErrors((prev) => ({ ...prev, consentimiento_privacidad: "" }));
                }
              }}
            />
            {fieldErrors.consentimiento_privacidad && (
              <span style={{ color: 'var(--error-color)', fontSize: '0.85rem' }}>
                {fieldErrors.consentimiento_privacidad}
              </span>
            )}
          </div>

          <button type="submit" className="btn-primary">Registrarse</button>
        </form>
        
        <div className="auth-footer">
          <p>¿Ya tienes una cuenta? <Link to="/login">Inicia sesión</Link></p>
        </div>
      </div>
    </div>
  );
}
