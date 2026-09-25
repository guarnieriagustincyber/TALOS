import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  GitCommit,
  Layers,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import { GateVerificationDto } from "./types";
import { EvalLabCard } from "./EvalLabCard";

export const GatesView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterStatus, setFilterStatus] = useState<"all" | "PASSED" | "CONDICIONAL" | "BLOCKED">("all");

  const {
    data: gates,
    isLoading,
    error,
    refetch,
  } = useQuery<GateVerificationDto[]>({
    queryKey: ["telemetry-gates"],
    queryFn: async () => {
      const res = await fetch("/api/telemetry/gates");
      if (!res.ok) throw new Error("Error al consultar el registro de gates");
      return res.json();
    },
  });

  const gateList = gates || [];

  const passedCount = gateList.filter((g) => g.status === "PASSED").length;
  const condCount = gateList.filter((g) => g.status === "CONDICIONAL").length;
  const blockedCount = gateList.filter((g) => g.status === "BLOCKED").length;

  const filteredGates = gateList.filter((g) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      g.gate_id.toLowerCase().includes(q) ||
      g.name.toLowerCase().includes(q) ||
      g.layer.toLowerCase().includes(q) ||
      g.criteria.toLowerCase().includes(q);

    const matchesStatus = filterStatus === "all" || g.status === filterStatus;

    return matchesSearch && matchesStatus;
  });

  const getLayerBadge = (layer: string) => {
    switch (layer) {
      case "E1":
        return "bg-blue-950/60 text-blue-300 border-blue-500/30";
      case "E2":
        return "bg-purple-950/60 text-purple-300 border-purple-500/30";
      case "E3":
        return "bg-indigo-950/60 text-indigo-300 border-indigo-500/30";
      case "CAL":
        return "bg-emerald-950/60 text-emerald-300 border-emerald-500/30";
      case "E4":
        return "bg-teal-950/60 text-teal-300 border-teal-500/30";
      case "E5":
        return "bg-cyan-950/60 text-cyan-300 border-cyan-500/30";
      default:
        return "bg-white/[0.06] text-white/70 border-white/20";
    }
  };

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-8">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.24em] text-emerald-400 font-bold">
                E5 · Formal Quality Gates
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-white/50">
                FASE 5.2
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <ShieldCheck className="w-7 h-7 text-emerald-400" />
              <span>Registro Criptográfico de Gates</span>
            </h1>
            <p className="mt-1 text-xs text-white/50 max-w-2xl">
              Barreras formales de aceptación y certificación matemática por capas (E1 a E5 + CAL) con commits pineados y trazabilidad inmutable.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sincronizar Gates</span>
            </button>
          </div>
        </div>

        {/* FASE 4-EVAL: LABORATORIO DE EVALUACIÓN Y CERTIFICACIÓN */}
        <EvalLabCard />

        {/* METRICS ROW */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-blue-400" /> Gates Totales
            </span>
            <div className="text-xl font-bold text-white">
              {gateList.length}
              <span className="ml-2 text-xs text-white/40 font-normal">evaluados</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Aprobados (Passed)
            </span>
            <div className="text-xl font-bold text-emerald-400">
              {passedCount}
              <span className="ml-2 text-xs text-emerald-400/60 font-normal">sin objeción</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <AlertCircle className="w-3.5 h-3.5 text-amber-400" /> Condicionales
            </span>
            <div className="text-xl font-bold text-amber-400">
              {condCount}
              <span className="ml-2 text-xs text-amber-300/60 font-normal">G5b acotado</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <XCircle className="w-3.5 h-3.5 text-rose-400" /> Bloqueados (Blocked)
            </span>
            <div className="text-xl font-bold text-white/70">
              {blockedCount}
              <span className="ml-2 text-xs text-white/40 font-normal">0 bloqueos</span>
            </div>
          </div>
        </div>

        {/* CONTROLS */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex-1 max-w-md h-10 rounded-[14px] bg-[#101012] border border-white/[0.08] flex items-center px-3.5 gap-2.5">
            <Search className="w-4 h-4 text-white/35 shrink-0" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar gate, capa o criterio..."
              className="flex-1 bg-transparent outline-none text-xs text-white placeholder:text-white/25 font-mono"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="text-white/30 hover:text-white text-xs"
              >
                ×
              </button>
            )}
          </div>

          <div className="flex items-center bg-[#101012] rounded-[14px] border border-white/[0.08] p-1 text-xs">
            <button
              onClick={() => setFilterStatus("all")}
              className={`px-3 py-1.5 rounded-[10px] transition ${
                filterStatus === "all" ? "bg-white text-black font-semibold" : "text-white/50 hover:text-white"
              }`}
            >
              Todos ({gateList.length})
            </button>
            <button
              onClick={() => setFilterStatus("PASSED")}
              className={`px-3 py-1.5 rounded-[10px] transition ${
                filterStatus === "PASSED" ? "bg-emerald-400 text-black font-semibold" : "text-white/50 hover:text-white"
              }`}
            >
              Passed ({passedCount})
            </button>
            <button
              onClick={() => setFilterStatus("CONDICIONAL")}
              className={`px-3 py-1.5 rounded-[10px] transition ${
                filterStatus === "CONDICIONAL" ? "bg-amber-400 text-black font-semibold" : "text-white/50 hover:text-white"
              }`}
            >
              Condicional ({condCount})
            </button>
          </div>
        </div>

        {/* LOADING & ERROR */}
        {isLoading && (
          <div className="p-8 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            <span>Verificando atestaciones formales de gates...</span>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <div>
              <strong className="block font-semibold">Error al consultar gates</strong>
              <span>{(error as Error).message}</span>
            </div>
          </div>
        )}

        {/* GATES GRID */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredGates.map((g) => {
            const isPassed = g.status === "PASSED";
            const isCond = g.status === "CONDICIONAL";

            return (
              <div
                key={g.gate_id}
                className={`rounded-[22px] bg-[#101012] border p-5 space-y-4 shadow-xl transition flex flex-col justify-between ${
                  isPassed
                    ? "border-white/[0.08] hover:border-emerald-500/30"
                    : isCond
                    ? "border-amber-500/30 bg-amber-950/10"
                    : "border-rose-500/30 bg-rose-950/10"
                }`}
              >
                <div className="space-y-3">
                  {/* Encabezado */}
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded-md border text-[10px] font-bold uppercase ${getLayerBadge(g.layer)}`}>
                        {g.layer}
                      </span>
                      <span className="font-mono text-xs font-bold text-white">
                        {g.gate_id}
                      </span>
                    </div>

                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${
                        isPassed
                          ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                          : isCond
                          ? "bg-amber-950/60 text-amber-300 border border-amber-500/30"
                          : "bg-rose-950/60 text-rose-400 border border-rose-500/30"
                      }`}
                    >
                      {isPassed ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <AlertCircle className="w-3 h-3 text-amber-400" />}
                      {g.status}
                    </span>
                  </div>

                  {/* Nombre y Criterio */}
                  <div>
                    <h3 className="text-sm font-bold text-white">{g.name}</h3>
                    <p className="mt-1 text-xs text-white/60 leading-relaxed">
                      {g.criteria}
                    </p>
                  </div>

                  {/* Valores Medidos vs Umbral */}
                  <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] space-y-1 text-xs">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/40 uppercase">Valor Observado:</span>
                      <strong className={isPassed ? "text-emerald-300 font-mono" : "text-amber-300 font-mono"}>
                        {g.measured_value}
                      </strong>
                    </div>
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-white/40 uppercase">Umbral Requerido:</span>
                      <span className="text-white/70 font-mono">{g.threshold}</span>
                    </div>
                  </div>

                  {/* Nota de Limitación si es Condicional */}
                  {g.limitation_note && (
                    <div className="p-2.5 rounded-lg bg-amber-950/40 border border-amber-500/30 text-[11px] text-amber-200/90 leading-relaxed">
                      <strong>Condición E5:</strong> {g.limitation_note}
                    </div>
                  )}
                </div>

                {/* Footer Criptográfico */}
                <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[10px] text-white/40">
                  <span className="flex items-center gap-1 font-mono truncate max-w-[160px]">
                    <GitCommit className="w-3.5 h-3.5 text-white/30" />
                    Commit: {g.pinned_commit.slice(0, 10)}
                  </span>
                  <span className="truncate max-w-[180px] font-mono text-white/30" title={g.report_path}>
                    {g.report_path.split("/").pop()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
};

export default GatesView;
