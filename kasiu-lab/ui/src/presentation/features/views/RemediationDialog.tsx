import React, { useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, Shield, X } from "lucide-react";
import { StudentActiveAlertDto, RemediationRespondResponse } from "./types";

export interface RemediationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  alert: StudentActiveAlertDto | null;
  onSuccess?: (choice: string) => void;
}

export const RemediationDialog: React.FC<RemediationDialogProps> = ({
  isOpen,
  onClose,
  alert,
  onSuccess,
}) => {
  const [selectedChoice, setSelectedChoice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RemediationRespondResponse | null>(null);

  if (!isOpen || !alert) return null;

  const handleChoose = async (choice: "PAUSE_AND_REMEDIATE" | "NOTE_AND_CONTINUE" | "DUAL_TRACK") => {
    setSelectedChoice(choice);
    setLoading(true);
    setError(null);

    try {
      const res = await fetch("/api/student/remediation/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interrupt_id: alert.kc_id,
          choice,
        }),
      });

      if (!res.ok) {
        throw new Error(`Error ${res.status}: ${res.statusText}`);
      }

      const data: RemediationRespondResponse = await res.json();
      setResult(data);
      onSuccess?.(choice);
    } catch (err: any) {
      setError(err?.message || "Error al registrar la decisión de remediación");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedChoice(null);
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm font-mono">
      <div className="w-full max-w-xl rounded-[24px] bg-[#121214] border border-white/[0.12] p-6 shadow-2xl space-y-5">
        {/* CABECERA */}
        <div className="flex items-start justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-[14px] bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider text-white/40">
                  Interrupción Pedagógica TALOS E3
                </span>
                <span
                  className={`text-[9px] px-2 py-0.5 rounded font-bold uppercase border ${
                    alert.severity === "CRITICAL"
                      ? "bg-rose-500/10 text-rose-300 border-rose-500/30"
                      : "bg-amber-500/10 text-amber-300 border-amber-500/30"
                  }`}
                >
                  {alert.severity}
                </span>
              </div>
              <h3 className="text-base font-bold text-white mt-0.5">
                {alert.title}
              </h3>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="w-8 h-8 rounded-[10px] bg-white/[0.05] hover:bg-white/10 flex items-center justify-center text-white/50 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* DETALLE DE LA LAGUNA */}
        <div className="rounded-[16px] bg-black/40 border border-white/[0.06] p-4 space-y-2 text-xs">
          <div className="flex items-center justify-between">
            <span className="text-white/40">Identificador KC:</span>
            <span className="text-white/90 font-bold">{alert.kc_id}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-white/40">Probabilidad de Dominio P(L):</span>
            <span className="text-amber-400 font-bold">{(alert.p_L * 100).toFixed(1)}%</span>
          </div>
          <p className="text-white/60 text-[11px] pt-2 border-t border-white/[0.04] leading-relaxed">
            Se ha detectado una laguna conceptual crítica en este prerrequisito durante la evaluación determinista.
            Conforme a la norma pedagógica, el alumno debe seleccionar el modo de remediación:
          </p>
        </div>

        {/* MENSAJE DE ERROR */}
        {error && (
          <div className="rounded-[14px] bg-rose-500/10 border border-rose-500/20 p-3 text-xs text-rose-300 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* MENSAJE DE ÉXITO */}
        {result ? (
          <div className="rounded-[16px] bg-emerald-500/10 border border-emerald-500/20 p-4 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs">
              <CheckCircle2 className="w-4 h-4" />
              <span>Decisión Registrada en el Ledger TALOS ({selectedChoice})</span>
            </div>
            <p className="text-xs text-white/80 leading-relaxed">
              {result.next_action}
            </p>
            <div className="flex justify-end pt-2">
              <button
                onClick={handleClose}
                className="px-4 py-2 rounded-[12px] bg-emerald-400 text-black text-xs font-bold hover:bg-emerald-300 transition"
              >
                Continuar
              </button>
            </div>
          </div>
        ) : (
          /* OPCIONES DE REMEDIACIÓN NORMATIVAS */
          <div className="space-y-3">
            <span className="text-[10px] uppercase tracking-wider text-white/40 font-semibold block">
              Seleccione Directiva de Remediación:
            </span>

            {/* OPCIÓN 1 */}
            <button
              disabled={loading}
              onClick={() => handleChoose("PAUSE_AND_REMEDIATE")}
              className="w-full text-left rounded-[16px] bg-[#16161a] border border-rose-500/30 hover:border-rose-500/60 p-4 transition space-y-1 group disabled:opacity-50"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rose-300 group-hover:text-rose-200">
                  1. Pausar y Remediar (Prioridad Inmediata)
                </span>
                <span className="text-[9px] px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
                  PAUSE_AND_REMEDIATE
                </span>
              </div>
              <p className="text-[11px] text-white/50 leading-relaxed">
                Suspende la progresión temática actual. Abre sesión socrática focalizada para resolver el obstáculo y recalibrar BKT antes de avanzar.
              </p>
            </button>

            {/* OPCIÓN 2 */}
            <button
              disabled={loading}
              onClick={() => handleChoose("NOTE_AND_CONTINUE")}
              className="w-full text-left rounded-[16px] bg-[#16161a] border border-amber-500/30 hover:border-amber-500/60 p-4 transition space-y-1 group disabled:opacity-50"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-300 group-hover:text-amber-200">
                  2. Anotar y Continuar (Revisión Asíncrona)
                </span>
                <span className="text-[9px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 font-bold">
                  NOTE_AND_CONTINUE
                </span>
              </div>
              <p className="text-[11px] text-white/50 leading-relaxed">
                Registra la laguna en la agenda de repetición espaciada y permite continuar con el temario, con advertencia de riesgo de arrastre conceptual.
              </p>
            </button>

            {/* OPCIÓN 3 */}
            <button
              disabled={loading}
              onClick={() => handleChoose("DUAL_TRACK")}
              className="w-full text-left rounded-[16px] bg-[#16161a] border border-blue-500/30 hover:border-blue-500/60 p-4 transition space-y-1 group disabled:opacity-50"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-300 group-hover:text-blue-200">
                  3. Doble Vía (Andamiaje Simultáneo)
                </span>
                <span className="text-[9px] px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 font-bold">
                  DUAL_TRACK
                </span>
              </div>
              <p className="text-[11px] text-white/50 leading-relaxed">
                Permite avanzar inyectando andamiaje conceptual explícito y micro-comprobaciones continuas durante las explicaciones posteriores.
              </p>
            </button>

            {loading && (
              <div className="flex items-center justify-center gap-2 py-3 text-xs text-amber-400">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Registrando en el Ledger pedagógico...</span>
              </div>
            )}
          </div>
        )}

        <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[10px] text-white/30">
          <span className="flex items-center gap-1">
            <Shield className="w-3 h-3 text-amber-400/60" />
            Protocolo de Remediación Normada TALOS v1
          </span>
          <span>ADR-008 §4</span>
        </div>
      </div>
    </div>
  );
};

export default RemediationDialog;
