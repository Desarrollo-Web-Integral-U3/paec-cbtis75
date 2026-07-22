import { useNavigate } from "react-router-dom";

export default function Intro() {
  const navigate = useNavigate();

  return (
    <div className="intro-page">
      <div className="intro-content">
        <h1 className="intro-title">
          Antes de armar tu equipo,<br />alineemos el método
        </h1>

        <p className="intro-lede">
          Este proyecto se desarrolla combinando dos formas de trabajo: una define <em>qué</em> construyes y <em>por qué</em>; la otra organiza <em>cómo</em> lo construyes y <em>cuándo</em>. Conócelas antes de registrar a tu equipo.
        </p>

        <div className="intro-thread">
          <div className="intro-node abp">
            <svg className="intro-node-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <circle cx="12" cy="12" r="9" />
              <circle cx="12" cy="12" r="4" />
              <circle cx="12" cy="12" r="0.5" fill="currentColor" />
            </svg>
            <h2>ABP - Aprendizaje Basado en Proyectos</h2>
            <p>
              Adquieren conocimientos y habilidades resolviendo un problema real, no un ejercicio hipotético. El proyecto completo, con sus decisiones y resultados, es la evaluación. Exige investigación, pensamiento crítico y trabajo colaborativo sostenido.
            </p>
            <span className="intro-node-tag">Define el rumbo del proyecto: qué se construye y para quién.</span>
          </div>

          <div className="intro-node scrum">
            <svg className="intro-node-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <path d="M4 12a8 8 0 0 1 14-5.2M20 12a8 8 0 0 1-14 5.2" />
              <path d="M18 4v3h-3M6 20v-3h3" />
            </svg>
            <h2>Scrum</h2>
            <p>
              El equipo divide el proyecto en Sprints: ciclos cortos con una meta clara, revisión al final y ajustes antes de continuar. Reuniones breves y frecuentes mantienen visible el avance y detectan bloqueos a tiempo.
            </p>
            <span className="intro-node-tag">Organiza el trabajo del ABP en ciclos medibles y revisables.</span>
          </div>
        </div>

        <div className="intro-cta-wrap">
          <button onClick={() => navigate('/login')} className="btn-primary intro-cta">
            Continuar al registro
          </button>
        </div>
      </div>
    </div>
  );
}