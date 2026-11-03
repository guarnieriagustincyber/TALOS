import React from "react";
import type { MessageAudit } from "../../../services/auditProjection";

export interface ContradictionViewProps {
  status: "no-session" | "loading" | "unavailable" | "error" | "available";
  audit?: MessageAudit;
}

export const ContradictionView: React.FC<ContradictionViewProps> = ({ status, audit }) => {
  const messages = {
    "no-session": "No hay una sesión disponible para consultar su evidencia.",
    loading: "Consultando información de evidencia…",
    unavailable: "No hay un reporte de auditoría disponible para esta respuesta.",
    error: "No se pudo verificar la información de evidencia de esta respuesta.",
  };
  if (status !== "available" || !audit) {
    return <div role="status" className="p-4 text-white/60">{messages[status === "available" ? "error" : status]}</div>;
  }
  const report = audit.projection;
  const approved = report.emission === "authorized" && report.decision === "APPROVED";
  const rejected = report.auditor_verdict.startsWith("REJECTED_");
  return <section className="space-y-3 p-4 text-white/70" aria-label="Auditoría de la respuesta">
    <h3 className="font-semibold">Auditoría de la respuesta</h3>
    <p role="status">{approved ? "Respuesta aprobada dentro del alcance de S4.4."
      : rejected ? "La auditoría rechazó el contenido; no se autorizó su emisión."
      : "Evaluación inconclusa; no se autorizó contenido académico."}</p>
    <dl className="break-all text-xs">
      <dt>Sesión</dt><dd>{report.session_id}</dd>
      <dt>Solicitud</dt><dd>{report.request_id}</dd>
      <dt>Auditoría</dt><dd>{report.audit_id}</dd>
      <dt>Veredicto del auditor</dt><dd>{report.auditor_verdict}</dd>
      <dt>Decisión de emisión</dt><dd>{report.decision}</dd>
      <dt>Hash del contenido auditado</dt><dd>{report.content_sha256}</dd>
    </dl>
    <p>{approved ? "Contenido recibido con binding verificado."
      : "El reporte corresponde al contenido retenido, no al mensaje explicativo de abstención."}
      {" "}Stream completado y mensaje conservado localmente; sin confirmación de entrega al servidor.</p>
    {report.claims.length === 0 ? <p>Reporte disponible sin claims evaluables; no equivale a ausencia de reporte ni a una comprobación universal de contradicciones.</p>
      : <ul className="space-y-2">{report.claims.map((claim) => <li key={claim.claim_index} className="rounded border border-white/10 p-2">
        Claim {claim.claim_index + 1} · {claim.claim_type} · {claim.nli_verdict}
        <div>Citas: {claim.cited_tags.join(", ") || "Sin citas"}</div>
        {claim.nli_verdict === "CONTRADICTED" && <p>El auditor detectó una afirmación contradicha por la evidencia citada.</p>}
      </li>)}</ul>}
    <p className="text-xs text-white/40">La proyección es derivada de esta invocación, no una nueva evaluación ni una certificación de verdad universal.</p>
  </section>;
};

export default ContradictionView;
