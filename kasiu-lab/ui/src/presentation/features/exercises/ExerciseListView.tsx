import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  Clock,
  Code2,
  FileCode2,
  FileText,
  HelpCircle,
  Loader2,
  RefreshCw,
  Terminal,
} from "lucide-react";
import { ExerciseAuditModal } from "./ExerciseAuditModal";

export interface ExerciseSummary {
  exercise_id: string;
  title: string;
  notebook_id: string;
  unit_or_tramo: string;
  relative_path: string;
  absolute_path: string;
  file_exists: boolean;
  status: "PENDING" | "SUBMITTED" | "VERIFIED" | "NEEDS_REVISION";
  last_score?: number;
  last_verified_at?: string;
}

interface ExerciseListViewProps {
  notebookId: string;
  unitFilter?: string;
}

export const ExerciseListView: React.FC<ExerciseListViewProps> = ({
  notebookId,
  unitFilter,
}) => {
  const [selectedExerciseId, setSelectedExerciseId] = useState<string | null>(null);

  const { data: exercises, isLoading, refetch, isFetching } = useQuery<ExerciseSummary[]>({
    queryKey: ["student-exercises", notebookId, unitFilter],
    queryFn: async () => {
      let url = `/api/student/exercises?notebook_id=${encodeURIComponent(notebookId)}`;
      if (unitFilter) {
        url += `&unit=${encodeURIComponent(unitFilter)}`;
      }
      const res = await fetch(url);
      if (!res.ok) throw new Error("No se pudo cargar la lista de ejercicios");
      return res.json();
    },
  });

  const getStatusBadge = (ex: ExerciseSummary) => {
    switch (ex.status) {
      case "VERIFIED":
        return (
          <span className="flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
            <CheckCircle2 className="w-3 h-3" />
            <span>Verificado {ex.last_score !== undefined ? `(${ex.last_score}/100)` : ""}</span>
          </span>
        );
      case "NEEDS_REVISION":
        return (
          <span className="flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-medium">
            <Clock className="w-3 h-3" />
            <span>Observaciones {ex.last_score !== undefined ? `(${ex.last_score}/100)` : ""}</span>
          </span>
        );
      case "SUBMITTED":
        return (
          <span className="flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
            <FileCode2 className="w-3 h-3" />
            <span>En Disco (Listo)</span>
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-white/[0.06] text-white/50 border border-white/[0.08] font-medium">
            <HelpCircle className="w-3 h-3" />
            <span>Pendiente en VSCode</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Code2 className="w-4 h-4 text-emerald-400" />
          <h4 className="text-xs uppercase tracking-wider text-white/70 font-semibold">
            Laboratorio de Ejercicios en VSCode
          </h4>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="flex items-center gap-1.5 text-xs text-white/50 hover:text-white transition-colors"
          title="Actualizar estado desde disco"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
          <span>Escanear disco</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-8 text-white/40 gap-2 text-xs">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Escaneando ejercicios locales en disco...</span>
        </div>
      ) : !exercises || exercises.length === 0 ? (
        <div className="rounded-xl p-6 bg-white/[0.02] border border-white/[0.06] text-center space-y-2">
          <FileText className="w-8 h-8 text-white/20 mx-auto" />
          <p className="text-xs text-white/60 font-medium">
            No se encontraron archivos de ejercicios en <code className="text-emerald-400/80">data/student_submissions/{notebookId}/</code>
          </p>
          <p className="text-[11px] text-white/40 max-w-md mx-auto">
            Creá tu primer archivo de ejercicio en VSCode usando las plantillas provistas y hacé clic en &quot;Escanear disco&quot;.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {exercises.map((ex) => (
            <div
              key={ex.exercise_id}
              onClick={() => setSelectedExerciseId(ex.exercise_id)}
              className="group p-4 rounded-xl bg-[#141416] hover:bg-[#18181c] border border-white/[0.06] hover:border-emerald-500/30 transition-all cursor-pointer space-y-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-white/40 block">
                    {ex.unit_or_tramo}
                  </span>
                  <h5 className="font-medium text-sm text-white group-hover:text-emerald-300 transition-colors">
                    {ex.title}
                  </h5>
                </div>
                {getStatusBadge(ex)}
              </div>

              <div className="flex items-center justify-between text-[11px] text-white/40 font-mono pt-1 border-t border-white/[0.04]">
                <span className="truncate max-w-[200px]" title={ex.relative_path}>
                  {ex.relative_path}
                </span>
                <span className="text-emerald-400/80 group-hover:text-emerald-300 transition-colors flex items-center gap-1">
                  <Terminal className="w-3 h-3" />
                  <span>Auditar →</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Audit Modal */}
      {selectedExerciseId && (
        <ExerciseAuditModal
          exerciseId={selectedExerciseId}
          notebookId={notebookId}
          onClose={() => setSelectedExerciseId(null)}
          onSelectNextExercise={(nextId) => setSelectedExerciseId(nextId)}
        />
      )}
    </div>
  );
};
