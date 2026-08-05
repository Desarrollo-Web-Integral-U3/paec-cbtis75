import { useEffect, useState } from "react";
import api from "../../api/client";

// Ancho maximo (en px) de la barra visual. La escala se calcula sobre el
// mayor entre capacidad y asignadas, de modo que la sobrecarga siempre
// se vea desbordando la linea de capacidad, no truncada.
const BAR_WIDTH = 480;

// Paleta:
// - verde: horas asignadas dentro de la capacidad.
// - rojo:  porcion de horas asignadas que excede la capacidad.
// - marca: linea vertical negra que indica el limite de capacidad.
const COLOR_OK = "#10b981";
const COLOR_OVERLOAD = "#dc2626";
const COLOR_TRACK = "#e5e7eb";

export default function CapacidadChart({ teamId }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    api
      .get(`/api/v1/equipo/${teamId}/capacidad`)
      .then((r) => setData(r.data))
      .catch(() => setError("No se pudo cargar la capacidad del equipo."));
  }, [teamId]);

  if (error) {
    return (
      <p role="alert" style={{ color: "#611a15" }}>
        {error}
      </p>
    );
  }
  if (!data) return <p>Cargando capacidad...</p>;

  const { horas_disponibles, horas_asignadas, horas_restantes } = data;
  const overloaded = horas_asignadas > horas_disponibles;

  // Caso especial: el equipo aun no declara sus horas disponibles.
  // Sin esa referencia no hay comparacion posible.
  if (horas_disponibles <= 0) {
    return (
      <p style={{ color: "#666", fontStyle: "italic" }}>
        El equipo no ha declarado sus horas disponibles. Actualiza el equipo
        con el campo <code>horas_disponibles</code> para ver esta vista.
      </p>
    );
  }

  // Escala: la barra se dimensiona segun el mayor de los dos valores para
  // que la sobrecarga sea visible sin truncarse.
  const escala = Math.max(horas_disponibles, horas_asignadas);
  const anchoAsignadasOk =
    (Math.min(horas_asignadas, horas_disponibles) / escala) * BAR_WIDTH;
  const anchoExceso = overloaded
    ? ((horas_asignadas - horas_disponibles) / escala) * BAR_WIDTH
    : 0;
  const posicionMarca = (horas_disponibles / escala) * BAR_WIDTH;

  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: "1rem",
          alignItems: "center",
          marginBottom: "0.5rem",
          fontSize: "0.9rem",
        }}
      >
        <span>
          <strong>Capacidad:</strong> {horas_disponibles} h
        </span>
        <span>
          <strong>Asignadas:</strong> {horas_asignadas} h
        </span>
        <span
          style={{
            color: overloaded ? COLOR_OVERLOAD : COLOR_OK,
            fontWeight: "bold",
          }}
        >
          {overloaded
            ? `Sobrecarga: ${Math.abs(horas_restantes)} h por encima`
            : `Restantes: ${horas_restantes} h`}
        </span>
      </div>

      {/* Barra: track gris + fill verde + fill rojo (si hay exceso) + marca */}
      <div
        role="img"
        aria-label={
          overloaded
            ? `Equipo sobrecargado: ${horas_asignadas} horas asignadas de ${horas_disponibles} disponibles`
            : `${horas_asignadas} horas asignadas de ${horas_disponibles} disponibles`
        }
        style={{
          position: "relative",
          width: `${BAR_WIDTH}px`,
          maxWidth: "100%",
          height: "32px",
          background: COLOR_TRACK,
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${anchoAsignadasOk}px`,
            height: "100%",
            background: COLOR_OK,
            transition: "width 200ms ease",
          }}
        />
        {overloaded && (
          <div
            style={{
              position: "absolute",
              top: 0,
              left: `${posicionMarca}px`,
              width: `${anchoExceso}px`,
              height: "100%",
              background: COLOR_OVERLOAD,
              transition: "width 200ms ease",
            }}
          />
        )}
        {/* Linea vertical negra que marca el limite de capacidad. */}
        <div
          aria-hidden="true"
          style={{
            position: "absolute",
            top: 0,
            left: `${posicionMarca}px`,
            width: "2px",
            height: "100%",
            background: "#111",
          }}
        />
      </div>

      {overloaded && (
        <p
          role="alert"
          style={{
            color: COLOR_OVERLOAD,
            marginTop: "0.5rem",
            fontSize: "0.85rem",
          }}
        >
          Advertencia: el esfuerzo asignado supera la capacidad declarada
          del equipo. Considera redistribuir tareas o aumentar
          <code> horas_disponibles</code>.
        </p>
      )}
    </div>
  );
}
