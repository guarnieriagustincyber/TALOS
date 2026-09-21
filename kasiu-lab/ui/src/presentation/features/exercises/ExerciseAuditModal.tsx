import React, { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Copy,
  FileCode,
  Loader2,
  Sparkles,
  Terminal,
  X,
  XCircle,
} from "lucide-react";

export interface AuditCheck {
  name: string;
  passed: boolean;
  feedback: string;
  severity: "ERROR" | "WARNING" | "INFO";
}

export interface ExerciseAuditReport {
  exercise_id: string;
  notebook_id: string;
  score: number;
  passed: boolean;
  checks: AuditCheck[];
  bkt_updated: boolean;
  p_L_before?: number;
  p_L_after?: number;
  observations: string[];
  next_exercise?: string;
  timestamp: string;
}

export interface ExerciseDetail {
  exercise_id: string;
  title: string;
  notebook_id: string;
  unit_or_tramo: string;
  relative_path: string;
  absolute_path: string;
  template_type: string;
  template_content: string;
  file_exists: boolean;
  current_content?: string;
  vscode_command: string;
}

interface ExerciseAuditModalProps {
  exerciseId: string;
  notebookId: string;
  onClose: () => void;
  onSelectNextExercise?: (nextId: string) => void;
}

export const ExerciseAuditModal: React.FC<ExerciseAuditModalProps> = ({
  exerciseId,
  notebookId,
  onClose,
  onSelectNextExercise,
}) => {
  const queryClient = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [templateCopied, setTemplateCopied] = useState(false);

  // Fetch exercise details
  const { data: detail, isLoading: isLoadingDetail } = useQuery<ExerciseDetail>({
    queryKey: ["exercise-detail", exerciseId, notebookId],
    queryFn: async () => {
      const res = await fetch(`/api/student/exercises/${encodeURIComponent(exerciseId)}?notebook_id=${encodeURIComponent(notebookId)}`);
      if (!res.ok) throw new Error("No se pudo cargar el detalle del ejercicio");
      return res.json();
    },
  });

  // Mutation to initialize template file
  const initTemplateMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(
        `/api/student/exercises/${encodeURIComponent(exerciseId)}/init-template?notebook_id=${encodeURIComponent(notebookId)}`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error("No se pudo crear la plantilla en disco");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["exercise-detail", exerciseId, notebookId] });
      queryClient.invalidateQueries({ queryKey: ["student-exercises"] });
    },
  });

  const handleCopyTemplate = () => {
    if (detail?.template_content) {
      navigator.clipboard.writeText(detail.template_content);
      setTemplateCopied(true);
      setTimeout(() => setTemplateCopied(false), 2000);
    }
  };

  // Fetch last audit report if available
  const { data: initialReport } = useQuery<ExerciseAuditReport>({
    queryKey: ["exercise-report", exerciseId],
    queryFn: async () => {
      const res = await fetch(`/api/student/exercises/${encodeURIComponent(exerciseId)}/report`);
      if (!res.ok) return null;
      return res.json();
    },
    retry: false,
  });

  const [activeReport, setActiveReport] = useState<ExerciseAuditReport | null>(null);

  // Mutation to verify
  const verifyMutation = useMutation({
    mutationFn: async () => {
      const res = await fetch(`/api/student/exercises/${encodeURIComponent(exerciseId)}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Error al verificar" }));
        throw new Error(err.detail || "Error en la auditoría");
      }
      return res.json() as Promise<ExerciseAuditReport>;
    },
    onSuccess: (data) => {
      setActiveReport(data);
      queryClient.invalidateQueries({ queryKey: ["student-exercises"] });
      queryClient.invalidateQueries({ queryKey: ["exercise-report", exerciseId] });
      queryClient.invalidateQueries({ queryKey: ["student-cognitive-state"] });
    },
  });

  const currentReport = activeReport || initialReport;

  const handleCopyCommand = () => {
    if (detail?.vscode_command) {
      navigator.clipboard.writeText(detail.vscode_command);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-2xl bg-[#121214] border border-white/[0.12] shadow-2xl overflow-hidden text-white">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08] bg-white/[0.02]">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-base leading-tight">
                {detail?.title || exerciseId}
              </h3>
              <p className="text-xs text-white/50 font-mono mt-0.5">
                {detail?.relative_path || exerciseId}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 k-scroll">
          {isLoadingDetail ? (
            <div className="flex items-center justify-center py-12 text-white/40 gap-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span>Cargando ejercicio...</span>
            </div>
          ) : (
            <>
              {/* VSCode Command Banner */}
              <div className="rounded-xl p-4 bg-black/40 border border-white/[0.08] space-y-2">
                <div className="flex items-center justify-between text-xs text-white/60">
                  <span className="flex items-center gap-1.5 font-mono">
                    <Terminal className="w-3.5 h-3.5 text-emerald-400" />
                    Abrir archivo en tu VSCode local:
                  </span>
                  <button
                    onClick={handleCopyCommand}
                    className="flex items-center gap-1 text-[11px] text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    <Copy className="w-3 h-3" />
                    {copied ? "¡Copiado!" : "Copiar comando"}
                  </button>
                </div>
                <div className="bg-black/60 rounded-lg p-2.5 font-mono text-xs text-emerald-300/90 break-all select-all border border-emerald-500/10">
                  {detail?.vscode_command}
                </div>
                <div className="flex items-center justify-between pt-1">
                  <div className="text-[11px] text-white/40">
                    {detail?.file_exists ? (
                      <span className="text-emerald-400">● Archivo detectado en disco. Listo para auditar.</span>
                    ) : (
                      <span className="text-amber-400">○ El archivo aún no existe en disco.</span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {detail?.template_content && (
                      <button
                        onClick={handleCopyTemplate}
                        className="text-[11px] text-white/60 hover:text-white flex items-center gap-1 transition-colors px-2 py-1 rounded bg-white/[0.04] border border-white/[0.08]"
                        title="Copiar plantilla Markdown al portapapeles"
                      >
                        <Copy className="w-3 h-3 text-cyan-400" />
                        {templateCopied ? "¡Plantilla Copiada!" : "Copiar plantilla"}
                      </button>
                    )}
                    {!detail?.file_exists && (
                      <button
                        onClick={() => initTemplateMutation.mutate()}
                        disabled={initTemplateMutation.isPending}
                        className="text-[11px] text-emerald-300 hover:text-emerald-200 flex items-center gap-1 transition-colors px-2.5 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 hover:bg-emerald-500/20"
                        title="Crear el archivo en disco automáticamente con la estructura canónica"
                      >
                        {initTemplateMutation.isPending ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <Sparkles className="w-3 h-3 text-emerald-400" />
                        )}
                        Crear archivo con plantilla
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="flex items-center justify-between pt-2">
                <div>
                  <h4 className="text-sm font-medium">Auditoría Forense TALOS</h4>
                  <p className="text-xs text-white/50">
                    Evalúa sintaxis, contratos formales, mermaid, aserciones y complejidad Big O.
                  </p>
                </div>
                <button
                  onClick={() => verifyMutation.mutate()}
                  disabled={verifyMutation.isPending || !detail?.file_exists}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-sm transition-all shadow-lg disabled:opacity-40 disabled:cursor-not-allowed bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30"
                >
                  {verifyMutation.isPending ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Auditando...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Verificar en TALOS</span>
                    </>
                  )}
                </button>
              </div>

              {/* Error Message */}
              {verifyMutation.isError && (
                <div className="rounded-xl p-4 bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400 mt-0.5" />
                  <div className="space-y-1">
                    <p className="font-semibold">Error al auditar archivo:</p>
                    <p className="font-mono text-[11px] whitespace-pre-wrap">
                      {verifyMutation.error instanceof Error ? verifyMutation.error.message : "Error inesperado"}
                    </p>
                  </div>
                </div>
              )}

              {/* Report Section */}
              {currentReport && (
                <div className="rounded-xl p-5 bg-white/[0.03] border border-white/[0.08] space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                    <div>
                      <span className="text-[11px] font-mono uppercase tracking-wider text-white/50">
                        Resultado de la Auditoría
                      </span>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className={`text-2xl font-bold font-mono ${currentReport.passed ? "text-emerald-400" : "text-amber-400"}`}>
                          {currentReport.score}/100
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${currentReport.passed ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-amber-500/20 text-amber-300 border border-amber-500/30"}`}>
                          {currentReport.passed ? "Aprobado" : "Requiere Revisión"}
                        </span>
                      </div>
                    </div>

                    {currentReport.bkt_updated && currentReport.p_L_before !== undefined && currentReport.p_L_after !== undefined && (
                      <div className="text-right">
                        <span className="text-[11px] text-white/50 block">Maestría BKT P(L)</span>
                        <span className="text-xs font-mono text-emerald-400 font-semibold">
                          {currentReport.p_L_before} → {currentReport.p_L_after}
                          {currentReport.p_L_after > currentReport.p_L_before && (
                            <span className="text-emerald-400 ml-1">
                              (+{(currentReport.p_L_after - currentReport.p_L_before).toFixed(2)})
                            </span>
                          )}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Checks List */}
                  <div className="space-y-2">
                    <h5 className="text-xs font-medium text-white/70">Aserciones y Verificaciones Forenses:</h5>
                    <div className="space-y-1.5">
                      {currentReport.checks.map((c, i) => (
                        <div
                          key={i}
                          className={`flex items-start gap-2.5 p-2.5 rounded-lg border text-xs ${
                            c.passed
                              ? "bg-emerald-500/[0.04] border-emerald-500/20 text-emerald-300"
                              : c.severity === "ERROR"
                              ? "bg-rose-500/[0.04] border-rose-500/20 text-rose-300"
                              : "bg-amber-500/[0.04] border-amber-500/20 text-amber-300"
                          }`}
                        >
                          {c.passed ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                          ) : c.severity === "ERROR" ? (
                            <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                          ) : (
                            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <span className="font-semibold uppercase text-[10px] tracking-wider opacity-70 block">
                              {c.name}
                            </span>
                            <span>{c.feedback}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Observations */}
                  {currentReport.observations && currentReport.observations.length > 0 && (
                    <div className="space-y-1 pt-2">
                      <span className="text-xs font-medium text-white/60">Observaciones:</span>
                      <ul className="list-disc list-inside text-xs text-white/70 space-y-0.5">
                        {currentReport.observations.map((obs, idx) => (
                          <li key={idx}>{obs}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Next Exercise Recommendation */}
                  {currentReport.next_exercise && onSelectNextExercise && (
                    <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between">
                      <span className="text-xs text-white/60">Próximo ejercicio sugerido:</span>
                      <button
                        onClick={() => onSelectNextExercise(currentReport.next_exercise!)}
                        className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
                      >
                        <span>{currentReport.next_exercise}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};
