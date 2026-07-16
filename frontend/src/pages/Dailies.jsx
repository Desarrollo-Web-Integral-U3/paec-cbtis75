import { useEffect, useState } from "react";
import api from "../api/client";

export default function Dailies({ teamId }) {
  const [ayer, setAyer] = useState("");
  const [hoy, setHoy] = useState("");
  const [impedimentos, setImpedimentos] = useState("");
  const [acuerdos, setAcuerdos] = useState("");
  const [historial, setHistorial] = useState([]);

  const cargar = () =>
    api.get(`/api/v1/daily/equipo/${teamId}`).then((r) => setHistorial(r.data));

  useEffect(() => {
    cargar();
  }, [teamId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    await api.post("/api/v1/daily/", {
      team_id: teamId,
      que_hice_ayer: ayer,
      que_hare_hoy: hoy,
      impedimentos,
      acuerdos,
    });
    setAyer(""); setHoy(""); setImpedimentos(""); setAcuerdos("");
    cargar();
  };

  return (
    <div>
      <h2>Daily de hoy</h2>
      <form onSubmit={handleSubmit}>
        <label>¿Qué hice ayer?
          <textarea value={ayer} onChange={(e) => setAyer(e.target.value)} required />
        </label>
        <label>¿Qué voy a hacer hoy?
          <textarea value={hoy} onChange={(e) => setHoy(e.target.value)} required />
        </label>
        <label>¿Qué me impide avanzar?
          <textarea value={impedimentos} onChange={(e) => setImpedimentos(e.target.value)} />
        </label>
        <label>Acuerdos del equipo
          <textarea value={acuerdos} onChange={(e) => setAcuerdos(e.target.value)} />
        </label>
        <button type="submit">Guardar daily</button>
      </form>

      <h3>Historial</h3>
      {historial.map((d) => (
        <div key={d.id} style={{ borderTop: "1px solid #eee", padding: "0.5rem 0" }}>
          <small>{new Date(d.fecha).toLocaleString()}</small>
          <p><strong>Ayer:</strong> {d.que_hice_ayer}</p>
          <p><strong>Hoy:</strong> {d.que_hare_hoy}</p>
          {d.impedimentos && <p><strong>Impedimentos:</strong> {d.impedimentos}</p>}
        </div>
      ))}
    </div>
  );
}
