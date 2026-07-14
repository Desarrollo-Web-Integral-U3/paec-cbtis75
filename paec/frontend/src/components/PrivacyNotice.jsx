/**
 * Debe mostrarse ANTES de que el usuario capture cualquier dato personal
 * (registro, formularios de equipo, etc.), con enlace directo al aviso
 * completo. Cumple el criterio "Aviso de Privacidad Integral y Simplificado".
 */
export default function PrivacyNotice({ onAccept }) {
  return (
    <div style={{ border: "1px solid #ccc", padding: "1rem", borderRadius: 8 }}>
      <p>
        Este sistema recopila tus datos (nombre, número de control, correo) únicamente
        para la gestión académica del proyecto ABP/Scrum. Consulta el{" "}
        <a href="/aviso-de-privacidad" target="_blank" rel="noreferrer">
          Aviso de Privacidad completo
        </a>{" "}
        antes de continuar.
      </p>
      <label>
        {/* Checkbox NO pre-marcado: consentimiento explícito obligatorio */}
        <input type="checkbox" required onChange={(e) => onAccept?.(e.target.checked)} />
        {" "}He leído y acepto el Aviso de Privacidad.
      </label>
    </div>
  );
}
