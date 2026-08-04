import React from "react";

export default function PrivacyPolicy() {
  return (
    <div className="container" style={{ maxWidth: "800px", margin: "0 auto", padding: "2rem" }}>
      <h1>Aviso de Privacidad Integral</h1>
      <p><strong>Última actualización:</strong> {new Date().toLocaleDateString()}</p>

      <section style={{ marginTop: "2rem" }}>
        <h2>1. Identidad y domicilio del responsable</h2>
        <p>
          El Centro de Bachillerato Tecnológico Industrial y de Servicios No. 75 (CBTis 75), 
          es el responsable del tratamiento de los datos personales que nos proporcione, los cuales 
          serán protegidos conforme a lo dispuesto por la Ley General de Protección de Datos Personales 
          en Posesión de Sujetos Obligados, y demás normatividad que resulte aplicable.
        </p>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>2. Datos personales que se recaban y su finalidad</h2>
        <p>
          Los datos personales que recabamos de usted (nombre completo, correo institucional y número de control) 
          serán utilizados para las siguientes finalidades:
        </p>
        <ul>
          <li>Gestión y control de acceso a la plataforma PAEC.</li>
          <li>Organización de equipos de trabajo bajo las metodologías ABP y Scrum.</li>
          <li>Seguimiento académico y evaluación del desempeño en los proyectos escolares.</li>
        </ul>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>3. Fundamento legal para el tratamiento de datos</h2>
        <p>
          El tratamiento de sus datos personales se realiza con fundamento en la Ley General de Educación 
          y las normativas internas de gestión escolar del plantel.
        </p>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>4. Transferencia de datos</h2>
        <p>
          Se informa que no se realizarán transferencias de datos personales a terceros, salvo aquéllas que sean necesarias 
          para atender requerimientos de información de una autoridad competente, que estén debidamente fundados y motivados.
        </p>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h2>5. Derechos ARCO</h2>
        <p>
          Usted tiene derecho a conocer qué datos personales tenemos de usted, para qué los utilizamos y las condiciones del uso que les damos (Acceso). 
          Asimismo, es su derecho solicitar la corrección de su información personal en caso de que esté desactualizada, sea inexacta o incompleta (Rectificación); 
          que la eliminemos de nuestros registros o bases de datos cuando considere que la misma no está siendo utilizada adecuadamente (Cancelación); 
          así como oponerse al uso de sus datos personales para fines específicos (Oposición). Estos derechos se conocen como derechos ARCO.
        </p>
      </section>
    </div>
  );
}
