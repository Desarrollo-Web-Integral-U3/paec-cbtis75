import { useEffect, useState } from "react";
import api from "../../api/client";

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
      <p role="alert" className="cap-alert">
        {error}
      </p>
    );
  }
  if (!data) return <p className="loading-state">Cargando capacidad...</p>;

  const { horas_disponibles, horas_asignadas, horas_restantes } = data;
  const overloaded = horas_asignadas > horas_disponibles;

  // Sin capacidad declarada no hay barra que dibujar.
  if (horas_disponibles <= 0) {
    return (
      <p className="cap-empty">
        El equipo no ha declarado sus horas disponibles. Actualiza el equipo
        con el campo <code>horas_disponibles</code> para ver esta vista.
      </p>
    );
  }

  // Escala relativa al mayor valor para que la sobrecarga NO se trunque.
  const escala = Math.max(horas_disponibles, horas_asignadas);
  const pctAsignadasOk =
    (Math.min(horas_asignadas, horas_disponibles) / escala) * 100;
  const pctExceso = overloaded
    ? ((horas_asignadas - horas_disponibles) / escala) * 100
    : 0;
  const pctMarca = (horas_disponibles / escala) * 100;

  const ariaLabel = overloaded
    ? `Equipo sobrecargado: ${horas_asignadas} horas asignadas de ${horas_disponibles} disponibles`
    : `${horas_asignadas} horas asignadas de ${horas_disponibles} disponibles`;

  return (
    <div>
      <div className="cap-header">
        <span>
          <strong>Capacidad:</strong> {horas_disponibles} h
        </span>
        <span>
          <strong>Asignadas:</strong> {horas_asignadas} h
        </span>
        <span
          className={
            overloaded
              ? "cap-status cap-status--overload"
              : "cap-status cap-status--ok"
          }
        >
          {overloaded
            ? `Sobrecarga: ${Math.abs(horas_restantes)} h por encima`
            : `Restantes: ${horas_restantes} h`}
        </span>
      </div>

      <div role="img" aria-label={ariaLabel} className="cap-bar">
        <div
          className="cap-bar-fill"
          style={{ width: `${pctAsignadasOk}%` }}
        />
        {overloaded && (
          <div
            className="cap-bar-overflow"
            style={{ left: `${pctMarca}%`, width: `${pctExceso}%` }}
          />
        )}
        <div
          aria-hidden="true"
          className="cap-bar-marker"
          style={{ left: `${pctMarca}%` }}
        />
      </div>

      {overloaded && (
        <p role="alert" className="cap-alert">
          Advertencia: el esfuerzo asignado supera la capacidad declarada del
          equipo. Considera redistribuir tareas o aumentar
          <code> horas_disponibles</code>.
        </p>
      )}
    </div>
  );
}
