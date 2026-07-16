import { useEffect, useState } from "react";
import api from "../api/client";

const DIAS = [
  { key: "mapear", label: "Lunes - Mapear" },
  { key: "bocetar", label: "Martes - Bocetar" },
  { key: "decidir", label: "Miércoles - Decidir" },
  { key: "prototipar", label: "Jueves - Prototipar" },
  { key: "probar", label: "Viernes - Probar con usuarios reales" },
];

export default function DesignSprint({ teamId }) {
  const [dias, setDias] = useState([]);

  useEffect(() => {
    api.get(`/api/v1/design-sprint/equipo/${teamId}`).then((r) => setDias(r.data));
  }, [teamId]);

  const subirEvidencia = async (dayId, file) => {
    const formData = new FormData();
    formData.append("archivo", file);
    await api.post(`/api/v1/design-sprint/${dayId}/evidencia`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  };

  return (
    <div>
      <h2>Design Sprint — semana de planeación</h2>
      {DIAS.map((dia) => {
        const registro = dias.find((d) => d.dia === dia.key);
        return (
          <div key={dia.key} style={{ border: "1px solid #ddd", margin: "0.5rem 0", padding: "0.5rem" }}>
            <h3>{dia.label}</h3>
            <p>Plan: {registro?.plan_descripcion || "Aún no planeado"}</p>
            <p>Evidencia: {registro?.evidencia_url || "Sin subir"}</p>
            {registro?.comentario_docente && (
              <p><strong>Comentario del docente:</strong> {registro.comentario_docente}</p>
            )}
            {registro && (
              <input
                type="file"
                onChange={(e) => subirEvidencia(registro.id, e.target.files[0])}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
