import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BookOpen,
  ChevronDown,
  ChevronRight,
  GraduationCap,
  Loader2,
  Sparkles,
} from "lucide-react";


export interface SubtopicProgress {
  id: string;
  name: string;
  status: "pending" | "in_progress" | "covered" | "mastered";
  evidence_count: number;
}


export interface TopicProgress {
  unit: string;
  unit_name: string;
  subtopics: SubtopicProgress[];
}


export interface CurriculumProgressProps {
  notebookId: string;
  onAskTopic?: (topicName: string) => void;
}


export const CurriculumProgress: React.FC<CurriculumProgressProps> = ({
  notebookId,
  onAskTopic,
}) => {
  const [collapsedUnits, setCollapsedUnits] = useState<Record<string, boolean>>({});
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });


  const { data: progress, isLoading, error, refetch } = useQuery<TopicProgress[]>({
    queryKey: ["curriculum-progress", notebookId],
    queryFn: async () => {
      const res = await fetch(`/api/notebook/${encodeURIComponent(notebookId)}/curriculum-progress`);
      if (!res.ok) throw new Error("No se pudo cargar el progreso curricular");
      return res.json();
    },
    refetchInterval: 10_000,
  });


  const toggleUnit = (unitKey: string) => {
    setCollapsedUnits((prev) => ({
      ...prev,
      [unitKey]: !prev[unitKey],
    }));
  };


  const resetTransform = () => setTransform({ x: 0, y: 0, scale: 1 });
  const zoomIn = () => setTransform(prev => ({ ...prev, scale: Math.min(prev.scale * 1.2, 3) }));
  const zoomOut = () => setTransform(prev => ({ ...prev, scale: Math.max(prev.scale / 1.2, 0.5) }));


  const handleWheel = (e: React.WheelEvent) => {
    if (!e.ctrlKey) return;
    e.preventDefault();
    setTransform(prev => {
      const newScale = Math.min(Math.max(prev.scale * (e.deltaY > 0 ? 0.9 : 1.1), 0.5), 3);
      return { ...prev, scale: newScale };
    });
  };


  const handleMouseDown = (e: React.MouseEvent) => {
    const startX = e.clientX - transform.x;
    const startY = e.clientY - transform.y;
    const handleMouseMove = (e: MouseEvent) => {
      setTransform(prev => ({ ...prev, x: e.clientX - startX, y: e.clientY - startY }));
    };
    const handleMouseUp = () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  };


  const handleDoubleClick = () => setTransform({ x: 0, y: 0, scale: 1 });


  const totalSubtopics = progress?.reduce((acc, u) => acc + u.subtopics.length, 0) || 0;
  const completedSubtopics =
    progress?.reduce(
      (acc, u) =>
        acc + u.subtopics.filter((s) => s.status === "covered" || s.status === "mastered").length,
      0
    ) || 0;


  const pct = totalSubtopics > 0 ? Math.round((completedSubtopics / totalSubtopics) * 100) : 0;


  const getStatusInfo = (status: SubtopicProgress["status"]) => {
    switch (status) {
      case "mastered":
        return { icon: "🏆", textColor: "text-emerald-400", bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/30" };
      case "covered":
        return { icon: "✅", textColor: "text-emerald-400", bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/30" };
      case "in_progress":
        return { icon: "🟡", textColor: "text-amber-400", bgColor: "bg-amber-500/10", borderColor: "border-amber-500/30" };
      default:
        return { icon: "⬜", textColor: "text-zinc-500", bgColor: "transparent", borderColor: "transparent" };
    }
  };


  const getUnitProgress = (unit: TopicProgress) => {
    const total = unit.subtopics.length;
    const completed = unit.subtopics.filter((s) => s.status === "covered" || s.status === "mastered").length;
    return total > 0 ? Math.round((completed / total) * 100) : 0;
  };


  const getUnitBorderColor = (unit: TopicProgress) => {
    const pct = getUnitProgress(unit);
    if (pct === 100) return "border-emerald-500/50";
    if (pct >= 50) return "border-amber-500/50";
    return "border-zinc-700/50";
  };


  return (
    <div className="h-full flex flex-col font-mono text-xs text-white/90">
      <div className="p-4 border-b border-white/[0.08] space-y-3 bg-[#101012]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-cyan-400" />
            <h3 className="font-semibold text-white tracking-tight text-sm">Programa de Cátedra</h3>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={zoomOut} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors" title="Alejar">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            </button>
            <button onClick={resetTransform} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors" title="Resetear vista">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5m0 0h5m-5 0V4" />
              </svg>
            </button>
            <button onClick={zoomIn} className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 transition-colors" title="Acercar">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
            <button onClick={() => refetch()} className="text-[10px] text-white/40 hover:text-cyan-400 transition" title="Recargar progreso">
              Actualizar
            </button>
          </div>
        </div>


        <div className="space-y-1.5">
          <div className="flex justify-between text-[11px] text-white/50">
            <span>Avance global</span>
            <span className="font-semibold text-cyan-300">
              {completedSubtopics} / {totalSubtopics} ({pct}%)
            </span>
          </div>
          <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 transition-all duration-500 rounded-full"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>


        <div className="flex flex-wrap items-center gap-3 pt-1 text-[10px] text-white/40">
          <span className="flex items-center gap-1">⬜ Pendiente</span>
          <span className="flex items-center gap-1">🟡 En curso</span>
          <span className="flex items-center gap-1">✅ Con evidencia</span>
          <span className="flex items-center gap-1">🏆 Dominado</span>
        </div>
      </div>


      <div
        className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden relative"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onDoubleClick={handleDoubleClick}
      >
        <div
          className="relative min-h-full transition-transform duration-200"
          style={{
            transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
            transformOrigin: "0 0",
          }}
        >
          <div className="min-h-full p-4 space-y-3">
            {isLoading && (
              <div className="py-12 flex flex-col items-center justify-center gap-2 text-white/40">
                <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                <span>Consultando programa oficial...</span>
              </div>
            )}


            {error && (
              <div className="p-3 rounded-[12px] bg-red-950/30 border border-red-500/30 text-red-300 text-xs">
                Error al consultar el progreso curricular: {(error as Error).message}
              </div>
            )}


            {!isLoading && !error && progress && progress.length === 0 && (
              <div className="py-8 text-center text-white/40 space-y-1">
                <BookOpen className="w-6 h-6 mx-auto opacity-40" />
                <p>No se encontraron unidades registradas para este cuaderno.</p>
              </div>
            )}


            {!isLoading && !error && progress && progress.map((unit) => {
              const isCollapsed = collapsedUnits[unit.unit];
              const unitTotal = unit.subtopics.length;
              const unitCompleted = unit.subtopics.filter(
                (s) => s.status === "covered" || s.status === "mastered"
              ).length;


              return (
                <div
                  key={unit.unit}
                  className="rounded-[14px] border bg-[#121215] overflow-hidden"
                  style={{ borderColor: getUnitBorderColor(unit) }}
                >
                  <div
                    onClick={() => toggleUnit(unit.unit)}
                    className="px-3.5 py-2.5 bg-black/40 flex items-center justify-between cursor-pointer hover:bg-white/[0.02] transition select-none"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      {isCollapsed ? (
                        <ChevronRight className="w-3.5 h-3.5 text-white/40 shrink-0" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                      )}
                      <span className="font-semibold text-white/90 text-xs truncate">
                        {unit.unit}: {unit.unit_name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-300"
                          style={{ width: `${getUnitProgress(unit)}%` }}
                        />
                      </div>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-white/50 shrink-0">
                        {unitCompleted}/{unitTotal}
                      </span>
                    </div>
                  </div>


                  {!isCollapsed && (
                    <ul className="divide-y divide-white/[0.04] p-1">
                      {unit.subtopics.map((sub) => {
                        const statusInfo = getStatusInfo(sub.status);
                        return (
                          <li
                            key={sub.id}
                            className="px-3 py-2 flex items-center justify-between gap-2.5 hover:bg-white/[0.03] transition rounded-[8px] group"
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="text-xs select-none">{statusInfo.icon}</span>
                              <span
                                className={`text-[11.5px] leading-snug truncate ${
                                  sub.status === "pending" ? "text-white/60" : "text-white/90 font-medium"
                                }`}
                                title={sub.name}
                              >
                                {sub.name}
                              </span>
                            </div>


                            <div className="flex items-center gap-2 shrink-0">
                              {sub.evidence_count > 0 && (
                                <span
                                  className="text-[9.5px] px-1.5 py-0.2 rounded bg-sky-950/60 text-sky-300 border border-sky-500/20"
                                  title={`${sub.evidence_count} citas canónicas vinculadas`}
                                >
                                  {sub.evidence_count} [E]
                                </span>
                              )}


                              {onAskTopic && (
                                <button
                                  onClick={() => onAskTopic(sub.name)}
                                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-white/[0.08] text-cyan-400 transition"
                                  title="Preguntar al tutor sobre este tema"
                                >
                                  <Sparkles className="w-3 h-3" />
                                </button>
                              )}
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};


export default CurriculumProgress;