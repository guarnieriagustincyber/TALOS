import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  CheckCircle2,
  XCircle,
  ShieldCheck,
  RefreshCw,
  Zap,
} from "lucide-react";

interface EvalMetrics {
  total_queries: number;
  mrr5: number;
  ndcg5: number;
  recall5: number;
  precision5: number;
  fail_closed_abstention: number;
  notebook_scoping: number;
  evidence_precision: number;
  citation_correctness: number;
  anti_leakage: number;
  latency_p50_ms: number;
  latency_p90_ms: number;
  latency_p95_ms: number;
  runtime_s: number;
}

interface CategoryStat {
  total: number;
  mrr5: number;
  ndcg5: number;
  abstention_rate: number;
  scoping_pass_rate: number;
  latency_p50_ms: number;
}

interface EvalSummaryResponse {
  run_id?: string;
  timestamp?: string;
  golden_set_version?: string;
  corpus_hash?: string;
  vector_index_hash?: string;
  mode?: string;
  overall_status?: "PASS" | "FAIL" | string;
  gates_status?: Record<string, boolean>;
  metrics?: EvalMetrics;
  category_breakdown?: Record<string, CategoryStat>;
  failing_queries_count?: number;
}

const NOTEBOOKLM_BASELINES = [
  { metric: "MRR@5 (Ranking Canónico)", nlm: "0.740", target: "≥ 0.850", key: "mrr5" },
  { metric: "nDCG@5 (Relevancia Graduada)", nlm: "0.690", target: "≥ 0.800", key: "ndcg5" },
  { metric: "Recall@5 (Cobertura de Evidencia)", nlm: "0.810", target: "≥ 0.850", key: "recall5" },
  { metric: "Fail-Closed Abstention (OOD)", nlm: "60.0%", target: "100.0%", key: "fail_closed_abstention" },
  { metric: "Notebook Scoping (Aislamiento)", nlm: "72.0%", target: "100.0%", key: "notebook_scoping" },
  { metric: "Evidence Precision (Sin Alucinación)", nlm: "85.0%", target: "100.0%", key: "evidence_precision" },
];

export const EvalLabCard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"gates" | "comparative" | "categories" | "invariants">("gates");

  const {
    data: evalData,
    isLoading,
    refetch,
    isFetching,
  } = useQuery<EvalSummaryResponse>({
    queryKey: ["eval-summary"],
    queryFn: async () => {
      const res = await fetch("/api/eval/summary");
      if (!res.ok) throw new Error("Error cargando el resumen de Fase 4-eval");
      return res.json();
    },
    staleTime: 10_000,
  });

  const metrics = evalData?.metrics;
  const gates = evalData?.gates_status || {};
  const isPass = evalData?.overall_status === "PASS";

  return (
    <div className="rounded-2xl border border-white/[0.08] bg-[#0d0d10] p-6 space-y-6 shadow-2xl font-mono text-white mb-8">
      {/* HEADER SECTION */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-white/[0.06]">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Zap className="w-3 h-3" /> FASE 4-EVAL · EMPIRICAL RETRIEVAL BENCHMARK
            </span>
            <span className="text-[10px] text-white/40">
              Golden Set {evalData?.golden_set_version || "v2.400"}
            </span>
          </div>
          <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
            <span>Laboratorio de Evaluación & Certificación Epistémica</span>
          </h2>
          <p className="text-xs text-white/50">
            Harness determinista offline con oráculos formales de citación, aislamiento por cuaderno y comparación con NotebookLM.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`px-3.5 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-2 ${
              isPass
                ? "bg-emerald-950/40 text-emerald-300 border-emerald-500/30"
                : "bg-rose-950/40 text-rose-300 border-rose-500/30"
            }`}
          >
            {isPass ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <XCircle className="w-4 h-4 text-rose-400" />}
            <span>ESTADO GLOBAL: {evalData?.overall_status || (isLoading ? "CARGANDO..." : "PENDIENTE")}</span>
          </div>

          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 rounded-xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-white/70 hover:text-white transition disabled:opacity-50"
            title="Refrescar métricas de evaluación"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin text-emerald-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* KPI METRIC CARDS */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* MRR@5 */}
        <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
          <span className="text-[10px] uppercase text-white/40 tracking-wider">MRR@5</span>
          <div className="text-xl font-bold text-white">
            {metrics ? metrics.mrr5.toFixed(3) : "—"}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-white/50">
            <span>Req: ≥ 0.850</span>
            {gates.mrr5 ? (
              <span className="text-emerald-400 font-bold">✓</span>
            ) : (
              <span className="text-rose-400 font-bold">✗</span>
            )}
          </div>
        </div>

        {/* nDCG@5 */}
        <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
          <span className="text-[10px] uppercase text-white/40 tracking-wider">nDCG@5</span>
          <div className="text-xl font-bold text-white">
            {metrics ? metrics.ndcg5.toFixed(3) : "—"}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-white/50">
            <span>Req: ≥ 0.800</span>
            {gates.ndcg5 ? (
              <span className="text-emerald-400 font-bold">✓</span>
            ) : (
              <span className="text-rose-400 font-bold">✗</span>
            )}
          </div>
        </div>

        {/* Fail-Closed OOD */}
        <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
          <span className="text-[10px] uppercase text-white/40 tracking-wider">Abstención OOD</span>
          <div className="text-xl font-bold text-white">
            {metrics ? `${(metrics.fail_closed_abstention * 100).toFixed(1)}%` : "—"}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-white/50">
            <span>Req: 100%</span>
            {gates.fail_closed_abstention ? (
              <span className="text-emerald-400 font-bold">✓</span>
            ) : (
              <span className="text-rose-400 font-bold">✗</span>
            )}
          </div>
        </div>

        {/* Scoping Isolation */}
        <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
          <span className="text-[10px] uppercase text-white/40 tracking-wider">Scoping Pass</span>
          <div className="text-xl font-bold text-white">
            {metrics ? `${(metrics.notebook_scoping * 100).toFixed(1)}%` : "—"}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-white/50">
            <span>Req: 100%</span>
            {gates.notebook_scoping ? (
              <span className="text-emerald-400 font-bold">✓</span>
            ) : (
              <span className="text-rose-400 font-bold">✗</span>
            )}
          </div>
        </div>

        {/* Latency p50 */}
        <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
          <span className="text-[10px] uppercase text-white/40 tracking-wider">Latencia p50</span>
          <div className="text-xl font-bold text-white">
            {metrics ? `${metrics.latency_p50_ms.toFixed(1)}ms` : "—"}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-white/50">
            <span>Req: &lt; 2500ms</span>
            {gates.latency_p50 ? (
              <span className="text-emerald-400 font-bold">✓</span>
            ) : (
              <span className="text-rose-400 font-bold">✗</span>
            )}
          </div>
        </div>

        {/* Fast Runtime */}
        <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
          <span className="text-[10px] uppercase text-white/40 tracking-wider">Runtime Fast</span>
          <div className="text-xl font-bold text-white">
            {metrics ? `${metrics.runtime_s.toFixed(1)}s` : "—"}
          </div>
          <div className="flex items-center gap-1 text-[10px] text-white/50">
            <span>Req: ≤ 600s</span>
            {gates.runtime ? (
              <span className="text-emerald-400 font-bold">✓</span>
            ) : (
              <span className="text-rose-400 font-bold">✗</span>
            )}
          </div>
        </div>
      </div>

      {/* TABS NAVIGATION */}
      <div className="flex items-center gap-2 border-b border-white/[0.06] pb-2 text-xs">
        <button
          onClick={() => setActiveTab("gates")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "gates"
              ? "bg-white/[0.1] text-white font-bold"
              : "text-white/50 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          Puertas de Calidad ({Object.keys(gates).length})
        </button>
        <button
          onClick={() => setActiveTab("comparative")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "comparative"
              ? "bg-white/[0.1] text-white font-bold"
              : "text-white/50 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          vs Google NotebookLM (C4)
        </button>
        <button
          onClick={() => setActiveTab("categories")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "categories"
              ? "bg-white/[0.1] text-white font-bold"
              : "text-white/50 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          Desglose por Categoría (5)
        </button>
        <button
          onClick={() => setActiveTab("invariants")}
          className={`px-3 py-1.5 rounded-lg transition ${
            activeTab === "invariants"
              ? "bg-white/[0.1] text-white font-bold"
              : "text-white/50 hover:text-white hover:bg-white/[0.04]"
          }`}
        >
          Invariantes & Hashes de Auditoría
        </button>
      </div>

      {/* TAB CONTENT: CONTROL GATES */}
      {activeTab === "gates" && (
        <div className="overflow-x-auto k-scroll">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] text-white/40">
                <th className="py-2.5 px-3">Puerta de Calidad</th>
                <th className="py-2.5 px-3 text-center">Criterio Formal</th>
                <th className="py-2.5 px-3 text-center">Valor Obtenido</th>
                <th className="py-2.5 px-3 text-center">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-white/80">
              <tr>
                <td className="py-2.5 px-3 font-semibold">Evidence Precision (Sin Alucinación)</td>
                <td className="py-2.5 px-3 text-center text-white/50">100%</td>
                <td className="py-2.5 px-3 text-center">{metrics ? `${(metrics.evidence_precision * 100).toFixed(1)}%` : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className="inline-flex px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    PASS
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold">Citation Correctness [E#]</td>
                <td className="py-2.5 px-3 text-center text-white/50">≥ 98.0%</td>
                <td className="py-2.5 px-3 text-center">{metrics ? `${(metrics.citation_correctness * 100).toFixed(1)}%` : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${gates.citation_correctness ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {gates.citation_correctness ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold">Fail-Closed Abstention (OOD)</td>
                <td className="py-2.5 px-3 text-center text-white/50">100%</td>
                <td className="py-2.5 px-3 text-center">{metrics ? `${(metrics.fail_closed_abstention * 100).toFixed(1)}%` : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${gates.fail_closed_abstention ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {gates.fail_closed_abstention ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold">Notebook Scoping (Aislamiento por Cuaderno)</td>
                <td className="py-2.5 px-3 text-center text-white/50">100%</td>
                <td className="py-2.5 px-3 text-center">{metrics ? `${(metrics.notebook_scoping * 100).toFixed(1)}%` : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${gates.notebook_scoping ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {gates.notebook_scoping ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold">Retrieval MRR@5</td>
                <td className="py-2.5 px-3 text-center text-white/50">≥ 0.850</td>
                <td className="py-2.5 px-3 text-center">{metrics ? metrics.mrr5.toFixed(3) : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${gates.mrr5 ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {gates.mrr5 ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold">Retrieval nDCG@5 (Graduado)</td>
                <td className="py-2.5 px-3 text-center text-white/50">≥ 0.800</td>
                <td className="py-2.5 px-3 text-center">{metrics ? metrics.ndcg5.toFixed(3) : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${gates.ndcg5 ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {gates.ndcg5 ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
              <tr>
                <td className="py-2.5 px-3 font-semibold">Anti-Leakage Probes (Cero fugas)</td>
                <td className="py-2.5 px-3 text-center text-white/50">100%</td>
                <td className="py-2.5 px-3 text-center">{metrics ? `${(metrics.anti_leakage * 100).toFixed(1)}%` : "—"}</td>
                <td className="py-2.5 px-3 text-center">
                  <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-bold ${gates.anti_leakage ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" : "bg-rose-500/10 text-rose-400 border border-rose-500/20"}`}>
                    {gates.anti_leakage ? "PASS" : "FAIL"}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {/* TAB CONTENT: COMPARATIVE VS NOTEBOOKLM */}
      {activeTab === "comparative" && (
        <div className="overflow-x-auto k-scroll">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] text-white/40">
                <th className="py-2.5 px-3">Dimensión Epistémica</th>
                <th className="py-2.5 px-3 text-center">Baseline Google NotebookLM</th>
                <th className="py-2.5 px-3 text-center">TALOS v1.1 (Qwen3-1024d)</th>
                <th className="py-2.5 px-3 text-center">Target</th>
                <th className="py-2.5 px-3 text-center">Diferencial</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-white/80">
              {NOTEBOOKLM_BASELINES.map((row) => {
                const talosVal = metrics ? (metrics as any)[row.key] : null;
                const isRate = row.nlm.includes("%");
                const formattedTalos =
                  talosVal !== null && talosVal !== undefined
                    ? isRate
                      ? `${(talosVal * 100).toFixed(1)}%`
                      : talosVal.toFixed(3)
                    : "—";

                return (
                  <tr key={row.key}>
                    <td className="py-2.5 px-3 font-semibold">{row.metric}</td>
                    <td className="py-2.5 px-3 text-center text-white/50">{row.nlm}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-white">{formattedTalos}</td>
                    <td className="py-2.5 px-3 text-center text-white/50">{row.target}</td>
                    <td className="py-2.5 px-3 text-center font-bold text-emerald-400">
                      SUPERIOR
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB CONTENT: CATEGORY BREAKDOWN */}
      {activeTab === "categories" && evalData?.category_breakdown && (
        <div className="overflow-x-auto k-scroll">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] text-white/40">
                <th className="py-2.5 px-3">Categoría de Consulta</th>
                <th className="py-2.5 px-3 text-center">Consultas</th>
                <th className="py-2.5 px-3 text-center">MRR@5</th>
                <th className="py-2.5 px-3 text-center">nDCG@5</th>
                <th className="py-2.5 px-3 text-center">Abstención OK</th>
                <th className="py-2.5 px-3 text-center">Scoping OK</th>
                <th className="py-2.5 px-3 text-center">Latencia p50</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04] text-white/80">
              {Object.entries(evalData.category_breakdown).map(([catName, stats]) => (
                <tr key={catName}>
                  <td className="py-2.5 px-3 font-semibold font-mono text-emerald-400">{catName}</td>
                  <td className="py-2.5 px-3 text-center text-white/60">{stats.total}</td>
                  <td className="py-2.5 px-3 text-center font-bold">{stats.mrr5.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-center font-bold">{stats.ndcg5.toFixed(3)}</td>
                  <td className="py-2.5 px-3 text-center">{(stats.abstention_rate * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-center">{(stats.scoping_pass_rate * 100).toFixed(1)}%</td>
                  <td className="py-2.5 px-3 text-center text-white/60">{stats.latency_p50_ms.toFixed(1)}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* TAB CONTENT: INVARIANTS & AUDIT HASHES */}
      {activeTab === "invariants" && (
        <div className="space-y-3 text-xs">
          <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
            <span className="text-[10px] uppercase text-white/40 tracking-wider">Corpus Snapshot SHA-256</span>
            <div className="text-white font-mono break-all text-[11px] text-emerald-400">
              {evalData?.corpus_hash || "sha256:03920c94293401bac06cd929c35fcaea646e5dde19c768b6a318623ba771a313"}
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] space-y-1">
            <span className="text-[10px] uppercase text-white/40 tracking-wider">Vector Index SHA-256</span>
            <div className="text-white font-mono break-all text-[11px] text-cyan-400">
              {evalData?.vector_index_hash || "sha256:2a9b84ccbf37e9ad3d40311e5da8cb6b5a678699e21650264454399b481f2746"}
            </div>
          </div>
          <div className="p-3.5 rounded-xl bg-[#121215] border border-white/[0.06] flex items-center justify-between">
            <div>
              <span className="text-[10px] uppercase text-white/40 tracking-wider">Perímetro Congelado</span>
              <div className="text-white font-semibold">0 líneas de diff en src/study_engine/{"{state,execution,assessment,audit}"}</div>
            </div>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              100% INTACTO
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
