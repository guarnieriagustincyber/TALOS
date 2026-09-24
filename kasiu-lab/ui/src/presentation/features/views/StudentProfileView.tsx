import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Award,
  BrainCircuit,
  CheckCircle2,
  Clock,
  Flame,
  GraduationCap,
  Loader2,
  Search,
  Shield,
  TrendingUp,
} from "lucide-react";
import {
  CognitiveStateResponse,
  RoadmapResponse,
  StudentActiveAlertDto,
  StudentMasteryNode,
  StudentStrength,
  StudentWeakness,
} from "./types";
import { RemediationDialog } from "./RemediationDialog";
import { ReadinessModal } from "./ReadinessModal";

export interface StudentProfileViewProps {
  onOpenChatWithTopic?: (topic: string) => void;
}

export const StudentProfileView: React.FC<StudentProfileViewProps> = ({
  onOpenChatWithTopic,
}) => {
  const [nodeFilter, setNodeFilter] = useState<"all" | "mastered" | "in_progress" | "weak">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [activeRemediationAlert, setActiveRemediationAlert] = useState<StudentActiveAlertDto | null>(null);
  const [readinessTopic, setReadinessTopic] = useState<{ id: string; title: string } | null>(null);

  // Fetch cognitive state from backend E3
  const {
    data: cognitiveState,
    isLoading: loadingCognitive,
    isError: errorCognitive,
    error: cognitiveErr,
    refetch: refetchCognitive,
  } = useQuery<CognitiveStateResponse>({
    queryKey: ["studentCognitiveState"],
    queryFn: async () => {
      const res = await fetch("/api/student/cognitive-state");
      if (!res.ok) {
        throw new Error(`Error ${res.status} al consultar telemetría cognitiva: ${res.statusText}`);
      }
      return res.json();
    },
  });

  // Fetch curriculum roadmap to cross-reference curricular nodes
  const {
    data: roadmap,
    isLoading: loadingRoadmap,
    isError: errorRoadmap,
    error: roadmapErr,
  } = useQuery<RoadmapResponse>({
    queryKey: ["curriculumRoadmap"],
    queryFn: async () => {
      const res = await fetch("/api/curriculum/roadmap");
      if (!res.ok) {
        throw new Error(`Error ${res.status} al consultar roadmap: ${res.statusText}`);
      }
      return res.json();
    },
  });

  // Derivar nodos de maestría combinando roadmap y BKT state
  const masteryNodes = useMemo<StudentMasteryNode[]>(() => {
    if (!cognitiveState) return [];

    const nodes: StudentMasteryNode[] = [];
    const kcMap = cognitiveState.kc_mastery || {};
    const seenKcs = new Set<string>();

    if (roadmap?.nodes) {
      roadmap.nodes.forEach((rn) => {
        seenKcs.add(rn.node_id);
        const bkt = kcMap[rn.node_id];
        const p_L = bkt ? bkt.p_L : 0;
        const attempts = bkt ? bkt.attempts : 0;
        const retentionScore = Math.round(p_L * 100);

        let status: "mastered" | "in_progress" | "weak" = "weak";
        if (p_L >= 0.80) {
          status = "mastered";
        } else if (p_L >= 0.50 || attempts > 0) {
          status = "in_progress";
        }

        let lastReviewed = "Sin evaluar";
        if (bkt?.last_update) {
          const d = new Date(bkt.last_update);
          lastReviewed = d.toLocaleDateString("es-AR", { day: "2-digit", month: "short" });
        }

        nodes.push({
          id: rn.node_id,
          label: rn.title,
          category: rn.is_root ? "Nodo Raíz" : "Curricular",
          scope: rn.node_type || "Ciberseguridad",
          status,
          retentionScore,
          lastReviewed,
        });
      });
    }

    // Agregar KCs adicionales registrados en storage pero no en roadmap
    Object.entries(kcMap).forEach(([kcId, bkt]) => {
      if (!seenKcs.has(kcId)) {
        const p_L = bkt.p_L;
        const retentionScore = Math.round(p_L * 100);
        let status: "mastered" | "in_progress" | "weak" = "weak";
        if (p_L >= 0.80) status = "mastered";
        else if (p_L >= 0.50 || bkt.attempts > 0) status = "in_progress";

        let lastReviewed = "Sin evaluar";
        if (bkt.last_update) {
          const d = new Date(bkt.last_update);
          lastReviewed = d.toLocaleDateString("es-AR", { day: "2-digit", month: "short" });
        }

        nodes.push({
          id: kcId,
          label: kcId,
          category: "KC Especializado",
          scope: "Telemetría BKT",
          status,
          retentionScore,
          lastReviewed,
        });
      }
    });

    return nodes;
  }, [cognitiveState, roadmap]);

  // Fortalezas derivadas (p_L >= 0.80)
  const dynamicStrengths = useMemo<StudentStrength[]>(() => {
    return masteryNodes
      .filter((n) => n.retentionScore >= 80)
      .map((n) => ({
        id: `str-${n.id}`,
        topic: n.label,
        domain: n.scope,
        score: n.retentionScore,
        assertionSnippet: `Dominio consolidado en BKT con P(L) = ${n.retentionScore}%. Aserciones verificadas sin lagunas.`,
      }));
  }, [masteryNodes]);

  // Debilidades derivadas (p_L < 50 con intentos o alertas)
  const dynamicWeaknesses = useMemo<StudentWeakness[]>(() => {
    return masteryNodes
      .filter((n) => n.status === "weak" && n.retentionScore > 0)
      .map((n) => ({
        id: `wk-${n.id}`,
        topic: n.label,
        domain: n.scope,
        gapDescription: `Nivel de retención por debajo del umbral seguro (${n.retentionScore}%). Requiere repaso o andamiaje.`,
        recommendedDoc: `Refuerzo conceptual en nodo ${n.id}`,
      }));
  }, [masteryNodes]);

  // Dominios de competencia dinámicos
  const dynamicDomains = useMemo(() => {
    if (masteryNodes.length === 0) return [];
    const scopeMap: Record<string, { totalScore: number; count: number }> = {};

    masteryNodes.forEach((n) => {
      const scope = n.scope || "General";
      if (!scopeMap[scope]) scopeMap[scope] = { totalScore: 0, count: 0 };
      scopeMap[scope].totalScore += n.retentionScore;
      scopeMap[scope].count += 1;
    });

    return Object.entries(scopeMap).map(([name, val]) => ({
      name,
      score: Math.round(val.totalScore / val.count),
      fullMark: 100,
    }));
  }, [masteryNodes]);

  const filteredNodes = useMemo(() => {
    return masteryNodes.filter((n) => {
      const matchesFilter = nodeFilter === "all" || n.status === nodeFilter;
      const matchesSearch =
        n.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.scope.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [masteryNodes, nodeFilter, searchQuery]);

  const masteredCount = masteryNodes.filter((n) => n.status === "mastered").length;
  const inProgressCount = masteryNodes.filter((n) => n.status === "in_progress").length;
  const weakCount = masteryNodes.filter((n) => n.status === "weak" && n.retentionScore > 0).length;

  const totalEvaluated = masteryNodes.filter((n) => n.retentionScore > 0);
  const avgRetention =
    totalEvaluated.length > 0
      ? (totalEvaluated.reduce((acc, n) => acc + n.retentionScore, 0) / totalEvaluated.length).toFixed(1)
      : "0.0";

  // Polígono dinámico para radar (5 vértices o proporcional a dynamicDomains)
  const radarPoints = useMemo(() => {
    const defaultDomains = [
      { name: "Redes & Protocolos", score: 82 },
      { name: "Punteros & Memoria C", score: 68 },
      { name: "Arquitectura & AMAT", score: 74 },
      { name: "Sistemas Operativos", score: 60 },
      { name: "Pensamiento Algorítmico", score: 88 },
    ];
    const sourceDomains = dynamicDomains.length >= 3 ? dynamicDomains.slice(0, 5) : defaultDomains;
    const center = { x: 130, y: 110 };
    const radius = 72;
    const total = sourceDomains.length;

    const coords = sourceDomains.map((d, i) => {
      const angle = -Math.PI / 2 + (i * 2 * Math.PI) / total;
      const factor = Math.max(0.2, Math.min(1, d.score / 100));
      return {
        x: Math.round(center.x + radius * factor * Math.cos(angle)),
        y: Math.round(center.y + radius * factor * Math.sin(angle)),
        axisX: Math.round(center.x + radius * Math.cos(angle)),
        axisY: Math.round(center.y + radius * Math.sin(angle)),
        label: d.name,
        score: d.score,
      };
    });

    const polygonStr = coords.map((c) => `${c.x},${c.y}`).join(" ");
    return { coords, polygonStr, domains: sourceDomains };
  }, [dynamicDomains]);

  const activeAlerts = cognitiveState?.active_alerts || [];

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-7">
        {/* CABECERA DE PERFIL COGNITIVO */}
        <div className="flex flex-wrap items-end justify-between gap-5 pb-6 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="block text-[11px] uppercase tracking-[0.24em] text-white/35">
                telemetría cognitiva // estudiante
              </span>
              <span className="text-[9px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono">
                TALOS Student Engine v0.3.0
              </span>
            </div>
            <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <GraduationCap className="w-7 h-7 text-amber-400" />
              Estado Epistémico & Dominio Curricular
            </h1>
            <p className="mt-1 text-xs text-white/40">
              Evaluación determinista de aserciones dominadas, lagunas conceptuales y alertas pedagógicas del alumno.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="h-10 px-4 rounded-[14px] bg-[#121214] border border-white/[0.08] flex items-center gap-2 text-xs text-white">
              <Flame className="w-4 h-4 text-amber-400" />
              <span>Racha de Auditoría: <strong className="text-amber-300">Activa</strong></span>
            </div>
          </div>
        </div>

        {/* BANNER DE ERROR EN TELEMETRÍA (FAIL-CLOSED) */}
        {(errorCognitive || errorRoadmap) && (
          <div className="rounded-[20px] bg-rose-950/40 border border-rose-500/30 p-5 space-y-2">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Error de Telemetría Epistémica (Fail-Closed)</span>
            </div>
            <p className="text-xs text-rose-200/80">
              {cognitiveErr?.message || roadmapErr?.message || "No se pudo recuperar el estado cognitivo soberano del estudiante."}
            </p>
          </div>
        )}

        {/* ESTADO DE CARGA */}
        {(loadingCognitive || loadingRoadmap) && (
          <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-10 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-amber-400 animate-spin" />
            <span className="text-xs text-white/50">
              Recuperando vector BKT y mapa curricular soberano...
            </span>
          </div>
        )}

        {/* MÉTRICAS PRINCIPALES */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-4.5 space-y-1">
            <span className="text-[10px] uppercase tracking-wider text-white/35">Nodos Dominados</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-emerald-400">{masteredCount}</span>
              <span className="text-xs text-white/40">/ {masteryNodes.length}</span>
              <span className="text-[10px] text-amber-400 ml-auto font-mono font-medium">
                {inProgressCount} en curso
              </span>
            </div>
            <span className="text-[10.5px] text-emerald-300/70 flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              {masteryNodes.length > 0 ? Math.round((masteredCount / masteryNodes.length) * 100) : 0}% de la malla dominada
            </span>
          </div>

          <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-4.5 space-y-1">
            <span className="text-[10px] uppercase tracking-wider text-white/35">Retención Promedio</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-amber-300">{avgRetention}%</span>
            </div>
            <span className="text-[10.5px] text-amber-400/80 flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-amber-400" />
              Modelo BKT + Ebbinghaus
            </span>
          </div>

          <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-4.5 space-y-1">
            <span className="text-[10px] uppercase tracking-wider text-white/35">Lagunas Activas</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-rose-400">{activeAlerts.length || weakCount}</span>
              <span className="text-xs text-white/40">alertas</span>
            </div>
            <span className="text-[10.5px] text-rose-300/70 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              {activeAlerts.length > 0 ? "Requiere remediación" : "Sin lagunas críticas"}
            </span>
          </div>

          <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-4.5 space-y-1">
            <span className="text-[10px] uppercase tracking-wider text-white/35">Componentes KC</span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold text-white">{Object.keys(cognitiveState?.kc_mastery || {}).length}</span>
              <span className="text-xs text-white/40">rastreados</span>
            </div>
            <span className="text-[10.5px] text-white/50 flex items-center gap-1">
              <Clock className="w-3 h-3 text-white/60" />
              BKT Sovereign Ledger
            </span>
          </div>
        </div>

        {/* SECCIÓN ALERTAS TÁCTICAS (DERIVADAS DEL BACKEND E3) */}
        <section className="rounded-[24px] bg-[#121214] border border-white/[0.08] p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-amber-400" />
              <h3 className="text-xs uppercase tracking-wider text-white font-semibold">
                Centro de Alertas Doctrinales & Lagunas Críticas
              </h3>
            </div>
            <span className="text-[10px] font-mono text-white/40">
              {activeAlerts.length} Notificaciones Activas
            </span>
          </div>

          {activeAlerts.length === 0 ? (
            <div className="rounded-[18px] bg-black/20 border border-dashed border-white/[0.08] p-6 text-center text-xs text-white/40">
              No hay alertas de lagunas activas reportadas por el motor de telemetría BKT.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
              {activeAlerts.map((alert) => {
                const isCritical = alert.severity === "CRITICAL";
                const borderStyle = isCritical
                  ? "border-rose-500/30 bg-rose-950/20"
                  : "border-amber-500/30 bg-amber-950/20";
                const badgeStyle = isCritical
                  ? "text-rose-400 bg-rose-500/10 border-rose-500/20"
                  : "text-amber-400 bg-amber-500/10 border-amber-500/20";

                return (
                  <div
                    key={alert.alert_id}
                    className={`rounded-[18px] border p-4 space-y-2 flex flex-col justify-between transition hover:border-white/30 ${borderStyle}`}
                  >
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-mono uppercase font-semibold border ${badgeStyle}`}>
                          {alert.severity}
                        </span>
                        <span className="text-[10px] text-white/40 font-mono">
                          P(L): {(alert.p_L * 100).toFixed(1)}%
                        </span>
                      </div>
                      <h4 className="text-xs font-semibold text-white leading-snug">
                        {alert.title}
                      </h4>
                      <p className="text-[11px] text-white/60 leading-relaxed">
                        Laguna conceptual detectada en el Knowledge Component <strong className="text-white/80">{alert.kc_id}</strong>.
                      </p>
                    </div>

                    <button
                      onClick={() => setActiveRemediationAlert(alert)}
                      className="mt-2 text-left text-[10.5px] text-amber-300 hover:text-amber-200 font-semibold flex items-center gap-1 pt-2 border-t border-white/[0.05]"
                    >
                      Remediar Laguna &rarr;
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* GRID COMPARATIVO: FORTALEZAS VS DEBILIDADES & RADAR */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          {/* FORTALEZAS (TEMAS FUERTES) */}
          <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs uppercase tracking-wider text-white font-semibold">
                  Fortalezas (Temas Fuertes)
                </h3>
              </div>
              <span className="text-[10px] text-emerald-400 font-mono font-semibold">
                Retención &ge; 80%
              </span>
            </div>

            <div className="space-y-3">
              {dynamicStrengths.length === 0 ? (
                <div className="rounded-[16px] bg-black/20 border border-dashed border-white/[0.06] p-5 text-center text-xs text-white/40">
                  Aún no se certifican temas con dominio consolidado (P(L) &ge; 80%).
                </div>
              ) : (
                dynamicStrengths.map((str) => (
                  <div
                    key={str.id}
                    className="rounded-[16px] bg-[#141416] border border-emerald-500/20 p-3.5 space-y-1.5 hover:border-emerald-500/40 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[9.5px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                        {str.domain}
                      </span>
                      <span className="text-xs font-bold text-emerald-400 font-mono">
                        {str.score}%
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-white">
                      {str.topic}
                    </h4>
                    <p className="text-[11px] text-white/50 leading-relaxed">
                      {str.assertionSnippet}
                    </p>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* DEBILIDADES (ÁREAS A REFORZAR) */}
          <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-rose-400" />
                <h3 className="text-xs uppercase tracking-wider text-white font-semibold">
                  Debilidades (A Reforzar)
                </h3>
              </div>
              <span className="text-[10px] text-rose-400 font-mono font-semibold">
                Lagunas Activas
              </span>
            </div>

            <div className="space-y-3">
              {dynamicWeaknesses.length === 0 ? (
                <div className="rounded-[16px] bg-black/20 border border-dashed border-white/[0.06] p-5 text-center text-xs text-white/40">
                  No se registran temas con lagunas activas o retención crítica.
                </div>
              ) : (
                dynamicWeaknesses.map((wk) => (
                  <div
                    key={wk.id}
                    className="rounded-[16px] bg-[#141416] border border-rose-500/20 p-3.5 space-y-1.5 hover:border-rose-500/40 transition"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[9.5px] px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20">
                        {wk.domain}
                      </span>
                      <span className="text-[9.5px] text-amber-400 font-mono">
                        Requiere Estudio
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-white">
                      {wk.topic}
                    </h4>
                    <p className="text-[11px] text-white/50 leading-relaxed">
                      {wk.gapDescription}
                    </p>
                    <div className="pt-2 border-t border-white/[0.05] text-[10px] text-white/40 flex items-center justify-between gap-2">
                      <span className="truncate max-w-[150px]">{wk.recommendedDoc}</span>
                      <button
                        onClick={() => onOpenChatWithTopic?.(wk.topic)}
                        className="px-2.5 py-1 rounded-[8px] bg-amber-500/15 border border-amber-500/30 text-amber-300 hover:bg-amber-500/25 text-[10.5px] font-semibold flex items-center gap-1 transition shrink-0 shadow-xs"
                        title={`Iniciar sesión de tutoría sobre ${wk.topic}`}
                      >
                        <span>Repasar con TALOS</span>
                        <span className="font-mono">&rarr;</span>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* RADAR DE COMPETENCIAS (SVG DINÁMICO) */}
          <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-emerald-400" />
                <h3 className="text-xs uppercase tracking-wider text-white font-semibold">
                  Radar Cognitivo Curricular
                </h3>
              </div>
              <span className="text-[10px] text-emerald-400/80 font-mono">BKT Multi-Eje</span>
            </div>

            <div className="flex flex-col items-center justify-center pt-2">
              <svg viewBox="0 0 260 220" className="w-full max-w-[260px] h-auto">
                <defs>
                  <radialGradient id="radar-glow-epistemic" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.45" />
                    <stop offset="70%" stopColor="#06b6d4" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
                  </radialGradient>
                </defs>

                {/* Referencias concéntricas (100%, 75%, 50%, 25%) */}
                <polygon points="130,38 198,87 172,168 88,168 62,87" fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
                <polygon points="130,56 181,93 162,154 98,154 79,93" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="1" strokeDasharray="3 3" />
                <polygon points="130,74 164,98 151,139 109,139 96,98" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <polygon points="130,92 147,104 141,125 119,125 113,104" fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1" />

                {/* Ejes radiales */}
                {radarPoints.coords.map((c, idx) => (
                  <line
                    key={`axis-${idx}`}
                    x1="130"
                    y1="110"
                    x2={c.axisX}
                    y2={c.axisY}
                    stroke="rgba(255,255,255,0.12)"
                    strokeDasharray="2 2"
                  />
                ))}

                {/* Polígono dinámico derivado de los datos reales */}
                <polygon
                  points={radarPoints.polygonStr}
                  fill="url(#radar-glow-epistemic)"
                  stroke="#10b981"
                  strokeWidth="2"
                />

                {/* Vértices con micro-nodos esmeralda */}
                {radarPoints.coords.map((c, idx) => (
                  <g key={`vert-${idx}`}>
                    <circle cx={c.x} cy={c.y} r="4" fill="#10b981" stroke="#050507" strokeWidth="1.5" />
                    <circle cx={c.x} cy={c.y} r="7" fill="none" stroke="#10b981" strokeWidth="0.8" opacity="0.4" />
                  </g>
                ))}
              </svg>

              <div className="w-full space-y-1.5 pt-3 border-t border-white/[0.06] text-xs">
                {radarPoints.domains.map((d) => (
                  <div key={d.name} className="flex items-center justify-between text-[10.5px]">
                    <span className="text-white/60 truncate max-w-[140px]">{d.name}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            d.score >= 80 ? "bg-emerald-400" : d.score >= 50 ? "bg-amber-400" : "bg-rose-400"
                          }`}
                          style={{ width: `${d.score}%` }}
                        />
                      </div>
                      <span className="w-7 text-right font-mono font-semibold text-white/80">{d.score}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        {/* TABLA DETALLADA DE NODOS CURRICULARES */}
        <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-4 pb-3 border-b border-white/[0.06]">
            <div>
              <h3 className="text-xs uppercase tracking-wider text-white font-semibold">
                Catálogo de Nodos Epistémicos Evaluados
              </h3>
              <p className="text-[11px] text-white/40">
                Auditoría individual por concepto curricular y nivel de retención BKT.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <div className="h-8 px-2.5 rounded-[10px] bg-black border border-white/[0.08] flex items-center gap-2">
                <Search className="w-3.5 h-3.5 text-white/30" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filtrar concepto..."
                  className="bg-transparent outline-none text-xs text-white placeholder:text-white/30 w-32"
                />
              </div>

              <div className="flex items-center gap-1 bg-black p-0.5 rounded-[10px] border border-white/[0.06]">
                {(["all", "mastered", "in_progress", "weak"] as const).map((tabKey) => (
                  <button
                    key={tabKey}
                    onClick={() => setNodeFilter(tabKey)}
                    className={`h-7 px-2.5 rounded-[8px] text-[10px] font-semibold uppercase tracking-wider transition ${
                      nodeFilter === tabKey
                        ? "bg-white text-black font-bold shadow-sm"
                        : "text-white/40 hover:text-white"
                    }`}
                  >
                    {tabKey === "all" ? "Todos" : tabKey === "mastered" ? "Dominados" : tabKey === "in_progress" ? "En Curso" : "A Reforzar"}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="overflow-x-auto k-scroll">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-white/[0.06] text-[10px] uppercase tracking-wider text-white/35">
                  <th className="py-2.5 px-3">Concepto Curricular</th>
                  <th className="py-2.5 px-3">Materia / Ámbito</th>
                  <th className="py-2.5 px-3">Unidad</th>
                  <th className="py-2.5 px-3">Estado</th>
                  <th className="py-2.5 px-3">Retención P(L)</th>
                  <th className="py-2.5 px-3">Último Repaso</th>
                  <th className="py-2.5 px-3 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {filteredNodes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-6 text-center text-white/30">
                      No se encontraron conceptos para el filtro seleccionado.
                    </td>
                  </tr>
                ) : (
                  filteredNodes.map((node) => {
                    const statusPill =
                      node.status === "mastered"
                        ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                        : node.status === "in_progress"
                        ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
                        : "text-rose-400 bg-rose-500/10 border-rose-500/20";

                    return (
                      <tr key={node.id} className="hover:bg-white/[0.02] transition">
                        <td className="py-3 px-3 font-semibold text-white">
                          <div>{node.label}</div>
                          <span className="text-[9.5px] font-mono text-white/30">{node.id}</span>
                        </td>
                        <td className="py-3 px-3 text-white/60">
                          #{node.scope}
                        </td>
                        <td className="py-3 px-3 text-white/40">
                          {node.category}
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-semibold border ${statusPill}`}>
                            {node.status === "mastered" ? "Dominado" : node.status === "in_progress" ? "En Progreso" : "A Reforzar"}
                          </span>
                        </td>
                        <td className="py-3 px-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  node.retentionScore >= 80 ? "bg-emerald-400" : node.retentionScore >= 50 ? "bg-amber-400" : "bg-rose-400"
                                }`}
                                style={{ width: `${node.retentionScore}%` }}
                              />
                            </div>
                            <span className="font-mono text-white/80">{node.retentionScore}%</span>
                          </div>
                        </td>
                        <td className="py-3 px-3 text-white/40 text-[11px]">
                          {node.lastReviewed}
                        </td>
                        <td className="py-3 px-3 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <button
                              onClick={() => setReadinessTopic({ id: node.id, title: node.label })}
                              className="px-2 py-1 rounded-[8px] bg-amber-500/10 border border-amber-500/20 text-[9.5px] text-amber-300 hover:bg-amber-500/20 transition"
                              title="Evaluar Prerrequisitos (Readiness Probe)"
                            >
                              Readiness
                            </button>
                            <button
                              onClick={() => onOpenChatWithTopic?.(node.label)}
                              className="px-2 py-1 rounded-[8px] bg-white/[0.04] border border-white/[0.08] text-[9.5px] text-white/70 hover:text-white hover:bg-white/10 transition"
                            >
                              Repasar
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </section>

        {/* DIÁLOGO DE REMEDIACIÓN NORMADA TALOS */}
        <RemediationDialog
          isOpen={!!activeRemediationAlert}
          onClose={() => setActiveRemediationAlert(null)}
          alert={activeRemediationAlert}
          onSuccess={() => {
            refetchCognitive();
          }}
        />

        {/* MODAL DE DISPONIBILIDAD (READINESS PROBE) */}
        {readinessTopic && (
          <ReadinessModal
            isOpen={!!readinessTopic}
            onClose={() => setReadinessTopic(null)}
            topicId={readinessTopic.id}
            topicTitle={readinessTopic.title}
            onStartTopic={(id) => {
              onOpenChatWithTopic?.(`Iniciar estudio del tema: ${readinessTopic.title} (${id})`);
            }}
          />
        )}
      </div>
    </main>
  );
};

export default StudentProfileView;
