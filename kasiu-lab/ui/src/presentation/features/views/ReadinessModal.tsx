import React, { useEffect, useState } from "react";
import { AlertCircle, AlertTriangle, CheckCircle2, HelpCircle, Loader2, Shield, X } from "lucide-react";
import { ReadinessReportDto } from "./types";

export interface ReadinessModalProps {
  isOpen: boolean;
  onClose: () => void;
  topicId: string;
  topicTitle?: string;
  onStartTopic?: (topicId: string) => void;
}

export const ReadinessModal: React.FC<ReadinessModalProps> = ({
  isOpen,
  onClose,
  topicId,
  topicTitle,
  onStartTopic,
}) => {
  const [report, setReport] = useState<ReadinessReportDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !topicId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);
    setReport(null);

    fetch("/api/student/readiness/assess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic_id: topicId,
        plan_only: true,
      }),
    })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`Error ${res.status}: ${res.statusText}`);
        }
        return res.json();
      })
      .then((data: ReadinessReportDto) => {
        if (isMounted) {
          setReport(data);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err?.message || "Fallo al evaluar prerrequisitos de readiness");
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [isOpen, topicId]);

  if (!isOpen) return null;

  const recBadge = {
    START: {
      color: "text-emerald-400 bg-emerald-500/10 border-emerald-500/30",
      label: "LISTO PARA INICIAR (START)",
      desc: "Todos los prerrequisitos están dominados probabilísticamente. Progresión habilitada.",
      icon: CheckCircle2,
    },
    START_WITH_SCAFFOLD: {
      color: "text-amber-400 bg-amber-500/10 border-amber-500/30",
      label: "INICIAR CON ANDAMIAJE (START_WITH_SCAFFOLD)",
      desc: "Se detectaron nociones previas pero no dominio pleno. Se inyectará andamiaje continuo.",
      icon: AlertTriangle,
    },
    REMEDIATE_FIRST: {
      color: "text-rose-400 bg-rose-500/10 border-rose-500/30",
      label: "REMEDIACIÓN PREVIA RECOMENDADA (REMEDIATE_FIRST)",
      desc: "Existen prerrequisitos esenciales ausentes. Se aconseja subsanar lagunas antes de avanzar.",
      icon: AlertCircle,
    },
  }[report?.recommendation || "START"] || {
    color: "text-white/60 bg-white/[0.05] border-white/10",
    label: report?.recommendation || "EVALUANDO",
    desc: "Calculando estado probabilístico BKT...",
    icon: HelpCircle,
  };

  const RecIcon = recBadge.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm font-mono">
      <div className="w-full max-w-xl rounded-[24px] bg-[#121214] border border-white/[0.12] p-6 shadow-2xl space-y-5">
        {/* CABECERA */}
        <div className="flex items-start justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[14px] bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <Shield className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] uppercase tracking-wider text-white/40 block">
                Sonda de Disponibilidad Cognitiva (Readiness Probe)
              </span>
              <h3 className="text-base font-bold text-white mt-0.5">
                {topicTitle || topicId}
              </h3>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-[10px] bg-white/[0.05] hover:bg-white/10 flex items-center justify-center text-white/50 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* CONTENIDO PRINCIPAL */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-10 space-y-3">
            <Loader2 className="w-7 h-7 text-amber-400 animate-spin" />
            <span className="text-xs text-white/60">
              Evaluando grafo de dependencias y vector BKT P(L)...
            </span>
          </div>
        ) : error ? (
          <div className="rounded-[16px] bg-rose-500/10 border border-rose-500/20 p-4 space-y-2">
            <div className="flex items-center gap-2 text-rose-300 font-bold text-xs">
              <AlertTriangle className="w-4 h-4" />
              <span>Fallo de Telemetría Cognitiva (Fail-Closed)</span>
            </div>
            <p className="text-xs text-rose-200/70">{error}</p>
          </div>
        ) : report ? (
          <div className="space-y-4">
            {/* DICTAMEN DE RECOMENDACIÓN */}
            <div className={`rounded-[18px] border p-4 space-y-2 ${recBadge.color}`}>
              <div className="flex items-center gap-2">
                <RecIcon className="w-5 h-5 shrink-0" />
                <span className="text-xs font-bold">{recBadge.label}</span>
              </div>
              <p className="text-[11px] text-white/80 leading-relaxed">
                {recBadge.desc}
              </p>
            </div>

            {/* TABLA DE PRERREQUISITOS */}
            <div className="space-y-2">
              <span className="text-[10px] uppercase tracking-wider text-white/40 font-semibold block">
                Vector de Prerrequisitos Evaluados ({report.prerequisites.length})
              </span>

              {report.prerequisites.length === 0 ? (
                <div className="rounded-[14px] bg-black/30 border border-white/[0.06] p-3 text-xs text-white/50 text-center">
                  Este nodo es raíz o no posee prerrequisitos inmediatos configurados.
                </div>
              ) : (
                <div className="rounded-[16px] bg-black/40 border border-white/[0.08] overflow-hidden">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-wider text-white/30">
                        <th className="py-2.5 px-3">Prerrequisito</th>
                        <th className="py-2.5 px-3">P(L) BKT</th>
                        <th className="py-2.5 px-3 text-right">Diagnóstico</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04]">
                      {report.prerequisites.map((p) => {
                        const statusPill =
                          p.status === "DOMINADO"
                            ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                            : p.status === "NOCIÓN"
                            ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
                            : "text-rose-400 bg-rose-500/10 border-rose-500/20";

                        return (
                          <tr key={p.prereq_id}>
                            <td className="py-2.5 px-3 font-semibold text-white">
                              {p.prereq_id}
                            </td>
                            <td className="py-2.5 px-3 font-mono text-white/80">
                              {(p.p_L * 100).toFixed(1)}%
                            </td>
                            <td className="py-2.5 px-3 text-right">
                              <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold border ${statusPill}`}>
                                {p.status}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* NOTAS */}
            {report.notes && report.notes.length > 0 && (
              <div className="space-y-1">
                <span className="text-[10px] uppercase tracking-wider text-white/30 block">
                  Observaciones Pedagógicas:
                </span>
                <ul className="list-disc list-inside text-[11px] text-white/60 space-y-0.5 pl-1">
                  {report.notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : null}

        {/* ACCIONES */}
        <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-[12px] bg-white/[0.05] hover:bg-white/10 text-xs text-white/70 hover:text-white transition"
          >
            Cerrar
          </button>

          {onStartTopic && report && (
            <button
              onClick={() => {
                onStartTopic(topicId);
                onClose();
              }}
              className="px-4 py-2 rounded-[12px] bg-amber-400 text-black text-xs font-bold hover:bg-amber-300 transition"
            >
              Comenzar Sesión &rarr;
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ReadinessModal;
