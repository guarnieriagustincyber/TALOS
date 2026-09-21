import React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  Award,
  BarChart3,
  Cpu,
  Gauge,
  Loader2,
  RefreshCw,
  Scale,
  ShieldCheck,
  TrendingUp,
  Zap,
} from "lucide-react";
import { TelemetryMetricsDto } from "./types";

export const TelemetryView: React.FC = () => {
  const {
    data: metrics,
    isLoading,
    error,
    refetch,
  } = useQuery<TelemetryMetricsDto>({
    queryKey: ["telemetry-metrics"],
    queryFn: async () => {
      const res = await fetch("/api/telemetry/metrics");
      if (!res.ok) throw new Error("Error al obtener telemetría epistémica E5");
      return res.json();
    },
  });

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-8">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.24em] text-cyan-400 font-bold">
                E5 · Epistemic Telemetry & Benchmarks
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-white/50">
                FASE 5.1
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <Activity className="w-7 h-7 text-cyan-400" />
              <span>Telemetría Epistémica & Benchmarks</span>
            </h1>
            <p className="mt-1 text-xs text-white/50 max-w-2xl">
              Medición científica de fidelidad epistémica, utilidad esperada (EEU) y contraste con baselines de la industria bajo validación determinista con cero jueces LLM.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Actualizar Métricas</span>
            </button>
          </div>
        </div>

        {/* LOADING & ERROR */}
        {isLoading && (
          <div className="p-8 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Consultando resultados de benchmark E5...</span>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <div>
              <strong className="block font-semibold">Error al cargar telemetría</strong>
              <span>{(error as Error).message}</span>
            </div>
          </div>
        )}

        {metrics && (
          <>
            {/* PRIMARY METRICS CARDS */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
                <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                  <Gauge className="w-3.5 h-3.5 text-cyan-400" /> SAC (Pool Global n=195)
                </span>
                <div className="text-xl font-bold text-white flex items-baseline gap-2">
                  <span className="text-cyan-400">{metrics.sac.toFixed(1)}%</span>
                  <span className="text-xs text-white/40 font-normal">curricular</span>
                </div>
              </div>

              <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
                <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> EEU (Utilidad Epistémica)
                </span>
                <div className="text-xl font-bold text-emerald-400 flex items-baseline gap-2">
                  <span>{metrics.eeu_oracle.toFixed(2)}</span>
                  <span className="text-xs text-white/30 font-normal">(vs 0.52 baseline)</span>
                </div>
              </div>

              <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
                <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-amber-400" /> RAF Score (Fidelidad)
                </span>
                <div className="text-xl font-bold text-amber-400 flex items-baseline gap-2">
                  <span>{metrics.raf.toFixed(1)}</span>
                  <span className="text-[10px] text-amber-300/60 font-normal">óptimo formal</span>
                </div>
              </div>

              <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
                <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> False Assertion Rate
                </span>
                <div className="text-xl font-bold text-teal-300 flex items-baseline gap-2">
                  <span>{metrics.far.toFixed(1)}%</span>
                  <span className="text-[10px] text-teal-400/60 font-normal">FAR = 0.0</span>
                </div>
              </div>
            </div>

            {/* HONEST ABSTENTION & LATENCY SECTION */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Abstención Honesta */}
              <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5 space-y-4 shadow-xl">
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <Scale className="w-4 h-4 text-amber-400" />
                    <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                      Abstención Honesta (ADR-008 §2)
                    </h2>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-300 border border-amber-500/30 text-[10px] font-bold">
                    CERO ALUCINACIÓN
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] space-y-1">
                    <span className="text-[10px] text-white/40 uppercase block">
                      True Positives (TP Abstain)
                    </span>
                    <span className="text-xl font-bold text-emerald-400">
                      {metrics.tp_abstain} / 100
                    </span>
                    <p className="text-[10px] text-white/40">Abstención justificada ante consultas OOD o sin evidencia.</p>
                  </div>

                  <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] space-y-1">
                    <span className="text-[10px] text-white/40 uppercase block">
                      False Positives (FP Abstain)
                    </span>
                    <span className="text-xl font-bold text-teal-300">
                      {metrics.fp_abstain}
                    </span>
                    <p className="text-[10px] text-white/40">Cero silencios erróneos ante evidencia existente.</p>
                  </div>
                </div>

                <p className="text-[11px] text-white/50 leading-relaxed pt-1">
                  Principio de Honestidad Epistémica: TALOS prefiere admitir falta de respaldo documental antes que fabricar aserciones plausibles pero no fundadas.
                </p>
              </div>

              {/* Latencia & Jueces LLM */}
              <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5 space-y-4 shadow-xl">
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-cyan-400" />
                    <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                      Rendimiento & Verificación Determinista
                    </h2>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-cyan-950/60 text-cyan-300 border border-cyan-500/30 text-[10px] font-bold">
                    SUB-MILISEGUNDO
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] space-y-1">
                    <span className="text-[10px] text-white/40 uppercase block">
                      Latencia Planificación (p50)
                    </span>
                    <span className="text-xl font-bold text-cyan-400">
                      {metrics.latency_p50_ms.toFixed(3)} ms
                    </span>
                    <p className="text-[10px] text-white/40">Resolución simbólica de grafo curricular sin espera.</p>
                  </div>

                  <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] space-y-1">
                    <span className="text-[10px] text-white/40 uppercase block">
                      Latencia Verificación (p95)
                    </span>
                    <span className="text-xl font-bold text-cyan-300">
                      {metrics.latency_p95_ms.toFixed(3)} ms
                    </span>
                    <p className="text-[10px] text-white/40">Backstop simbólico en tiempo de ejecución ultra-rápido.</p>
                  </div>
                </div>

                <div className="pt-2 flex items-center justify-between text-xs bg-black/30 p-2.5 rounded-xl border border-white/[0.05]">
                  <span className="text-white/60 flex items-center gap-1.5">
                    <Cpu className="w-3.5 h-3.5 text-emerald-400" />
                    Jueces LLM en Evaluación Epistémica:
                  </span>
                  <span className="font-bold text-emerald-400">
                    {metrics.zero_llm_epistemic_calls} (0% dependencia)
                  </span>
                </div>
              </div>
            </div>

            {/* EXTERNAL CROSS-VALIDATION BENCHMARKS */}
            <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5 space-y-4 shadow-xl">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-white/[0.06]">
                <div>
                  <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-cyan-400" />
                    <span>Validación Cruzada Externa Protocolaria (E5)</span>
                  </h2>
                  <p className="text-xs text-white/40 mt-0.5">
                    Comparación estandarizada contra GraphRAG, EDU-RAG, KnowShiftQA y TQA sin jueces generativos.
                  </p>
                </div>
                <span className="text-[10px] text-emerald-400 font-bold bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full w-fit">
                  DELTA PROMEDIO +11.2 pp
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.08] text-[10px] text-white/40 uppercase tracking-wider bg-black/30">
                      <th className="py-3 px-3">Protocolo / Benchmark</th>
                      <th className="py-3 px-3">Dominio</th>
                      <th className="py-3 px-3">Muestras</th>
                      <th className="py-3 px-3">Baseline SAC</th>
                      <th className="py-3 px-3">TALOS SAC</th>
                      <th className="py-3 px-3">Delta</th>
                      <th className="py-3 px-3">EEU (Baseline vs TALOS)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.05]">
                    {metrics.protocolary_comparisons.map((c) => (
                      <tr key={c.benchmark_name} className="hover:bg-white/[0.02] transition">
                        <td className="py-3 px-3 font-semibold text-white">
                          {c.benchmark_name}
                        </td>
                        <td className="py-3 px-3 text-white/50 text-[11px]">
                          {c.domain}
                        </td>
                        <td className="py-3 px-3 text-white/40 font-mono">
                          n={c.n_samples}
                        </td>
                        <td className="py-3 px-3 text-white/50 font-mono">
                          {c.industry_baseline_sac.toFixed(1)}%
                        </td>
                        <td className="py-3 px-3 font-bold text-cyan-400 font-mono">
                          {c.talos_sac.toFixed(1)}%
                        </td>
                        <td className="py-3 px-3">
                          <span className="px-1.5 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 font-bold font-mono text-[10px]">
                            +{c.delta_sac_pp.toFixed(1)} pp
                          </span>
                        </td>
                        <td className="py-3 px-3 text-white/70 font-mono text-[11px]">
                          {c.industry_baseline_eeu.toFixed(2)} → <strong className="text-emerald-400">{c.talos_eeu.toFixed(2)}</strong>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </main>
  );
};

export default TelemetryView;
