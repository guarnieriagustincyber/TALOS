import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeftRight,
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Loader2,
  Lock,
  Network,
  RefreshCw,
  Search,
  Shield,
  Tag,
  UserCheck,
} from "lucide-react";
import { FederatedNotebookDto, FederationBridgeDto } from "./types";

export const FederationView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterBridgeStatus, setFilterBridgeStatus] = useState<"all" | "ACTIVE" | "EXPIRED">("all");

  // 1. Fetch Federated Notebooks
  const {
    data: notebooks,
    isLoading: isLoadingNbs,
    error: nbsError,
    refetch: refetchNbs,
  } = useQuery<FederatedNotebookDto[]>({
    queryKey: ["federation-notebooks"],
    queryFn: async () => {
      const res = await fetch("/api/federation/notebooks");
      if (!res.ok) throw new Error("Error al consultar cuadernos soberanos");
      return res.json();
    },
  });

  // 2. Fetch Cross-Notebook Bridges
  const {
    data: bridges,
    isLoading: isLoadingBridges,
    error: bridgesError,
    refetch: refetchBridges,
  } = useQuery<FederationBridgeDto[]>({
    queryKey: ["federation-bridges"],
    queryFn: async () => {
      const res = await fetch("/api/federation/bridges");
      if (!res.ok) throw new Error("Error al consultar puentes federados");
      return res.json();
    },
  });

  const nbs = notebooks || [];
  const bridgeList = bridges || [];

  const activeBridges = bridgeList.filter((b) => b.status === "ACTIVE").length;
  const expiredBridges = bridgeList.filter((b) => b.status === "EXPIRED").length;

  const filteredBridges = bridgeList.filter((b) => {
    const q = searchQuery.toLowerCase();
    const matchesQuery =
      b.bridge_id.toLowerCase().includes(q) ||
      b.source_notebook.toLowerCase().includes(q) ||
      b.target_notebook.toLowerCase().includes(q) ||
      b.topic_allowlist.some((t) => t.toLowerCase().includes(q)) ||
      b.reviewer.toLowerCase().includes(q);

    const matchesStatus =
      filterBridgeStatus === "all" || b.status === filterBridgeStatus;

    return matchesQuery && matchesStatus;
  });

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-8">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.24em] text-indigo-400 font-bold">
                E4 · Epistemic Federation
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-white/50">
                FASE 4.2
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <Network className="w-7 h-7 text-indigo-400" />
              <span>Federación Soberana de Cuadernos</span>
            </h1>
            <p className="mt-1 text-xs text-white/50 max-w-2xl">
              Control de aislamiento curricular por cuaderno y gobernanza contractual de puentes temáticos con expiración TTL estricta.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                refetchNbs();
                refetchBridges();
              }}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sincronizar</span>
            </button>
          </div>
        </div>

        {/* EPISTEMIC SOVEREIGNTY PRINCIPLE BANNER */}
        <div className="p-4 rounded-[18px] bg-indigo-950/30 border border-indigo-500/30 flex items-start gap-3 text-indigo-200 text-xs">
          <Shield className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="block text-indigo-300 font-semibold uppercase tracking-wide">
              Principio de Soberanía E4 (ADR-008 §3)
            </strong>
            <p className="text-[11px] text-indigo-200/80 leading-relaxed">
              Cada cuaderno opera en un perímetro epistémico confinado. Las consultas no pueden acceder a fuentes ni inferencias de otros cuadernos a menos que un <strong>puente explícito</strong> esté aprobado en la allowlist y se encuentre dentro de su período de validez (TTL).
            </p>
          </div>
        </div>

        {/* METRICS ROW */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <BookOpen className="w-3.5 h-3.5 text-blue-400" /> Cuadernos Soberanos
            </span>
            <div className="text-xl font-bold text-white">
              {nbs.length}
              <span className="ml-2 text-xs text-emerald-400 font-normal">confinados</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <Network className="w-3.5 h-3.5 text-indigo-400" /> Puentes Contractuales
            </span>
            <div className="text-xl font-bold text-indigo-300">
              {bridgeList.length}
              <span className="ml-2 text-xs text-white/40 font-normal">registrados</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Puentes Activos
            </span>
            <div className="text-xl font-bold text-emerald-400">
              {activeBridges}
              <span className="ml-2 text-[10px] text-emerald-400/60 font-normal">en regla</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-rose-400" /> Puentes Expirados (TTL)
            </span>
            <div className="text-xl font-bold text-rose-400">
              {expiredBridges}
              <span className="ml-2 text-[10px] text-rose-400/60 font-normal">fail-closed</span>
            </div>
          </div>
        </div>

        {/* SECTION 1: SOVEREIGN NOTEBOOKS */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Lock className="w-4 h-4 text-emerald-400" />
              <span>Cuadernos Registrados en la Federación</span>
            </h2>
            <span className="text-xs text-white/40">{nbs.length} soberanos</span>
          </div>

          {isLoadingNbs && (
            <div className="p-6 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Cargando registro de cuadernos...</span>
            </div>
          )}

          {nbsError && (
            <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 text-red-300 text-xs">
              Error al consultar cuadernos: {(nbsError as Error).message}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {nbs.map((nb) => (
              <div
                key={nb.notebook_id}
                className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-5 flex flex-col justify-between space-y-4 hover:border-white/[0.18] transition shadow-lg group"
              >
                <div>
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                    <span className="px-2 py-0.5 rounded-full bg-emerald-950/50 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold uppercase flex items-center gap-1">
                      <Lock className="w-3 h-3 text-emerald-400" />
                      {nb.default_scope}
                    </span>
                    <span className="text-[10px] text-white/40">{nb.level}</span>
                  </div>

                  <h3 className="mt-3 text-sm font-bold text-white group-hover:text-indigo-300 transition">
                    {nb.name}
                  </h3>
                  <p className="mt-1 text-xs text-white/50">{nb.subject}</p>
                </div>

                <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-white/40">
                  <span>ID: <code className="text-white/70">{nb.notebook_id}</code></span>
                  <span>{nb.source_count} fuentes</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* SECTION 2: CROSS-NOTEBOOK BRIDGES & TTL */}
        <section className="space-y-4 pt-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <ArrowLeftRight className="w-4 h-4 text-indigo-400" />
                <span>Puentes Cross-Notebook y Control de TTL</span>
              </h2>
              <p className="text-xs text-white/40 mt-0.5">
                Rutas autorizadas en <code>config/bridges.allowlist.json</code> para transferencia de contexto inter-cuaderno.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <div className="h-9 rounded-[12px] bg-[#101012] border border-white/[0.08] flex items-center px-3 gap-2">
                <Search className="w-3.5 h-3.5 text-white/35 shrink-0" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filtrar puentes..."
                  className="bg-transparent outline-none text-xs text-white placeholder:text-white/25 w-32 sm:w-40 font-mono"
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
                  onClick={() => setFilterBridgeStatus("all")}
                  className={`px-3 py-1 rounded-[10px] transition ${
                    filterBridgeStatus === "all" ? "bg-white text-black font-semibold" : "text-white/50 hover:text-white"
                  }`}
                >
                  Todos ({bridgeList.length})
                </button>
                <button
                  onClick={() => setFilterBridgeStatus("ACTIVE")}
                  className={`px-3 py-1 rounded-[10px] transition ${
                    filterBridgeStatus === "ACTIVE" ? "bg-emerald-400 text-black font-semibold" : "text-white/50 hover:text-white"
                  }`}
                >
                  Activos ({activeBridges})
                </button>
                <button
                  onClick={() => setFilterBridgeStatus("EXPIRED")}
                  className={`px-3 py-1 rounded-[10px] transition ${
                    filterBridgeStatus === "EXPIRED" ? "bg-rose-500 text-white font-semibold" : "text-white/50 hover:text-white"
                  }`}
                >
                  Expirados ({expiredBridges})
                </button>
              </div>
            </div>
          </div>

          {isLoadingBridges && (
            <div className="p-6 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              <span>Verificando puentes y cálculo de TTL...</span>
            </div>
          )}

          {bridgesError && (
            <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 text-red-300 text-xs">
              Error al consultar puentes: {(bridgesError as Error).message}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredBridges.map((b) => {
              const isActive = b.status === "ACTIVE";
              return (
                <div
                  key={b.bridge_id}
                  className={`rounded-[22px] bg-[#101012] border p-5 space-y-4 shadow-xl transition ${
                    isActive
                      ? "border-white/[0.08] hover:border-indigo-500/30"
                      : "border-rose-500/30 bg-rose-950/10"
                  }`}
                >
                  {/* Encabezado del puente */}
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-indigo-300 font-mono flex items-center gap-1.5">
                      <Network className="w-3.5 h-3.5 text-indigo-400" />
                      {b.bridge_id}
                    </span>

                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 ${
                        isActive
                          ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                          : "bg-rose-950/60 text-rose-400 border border-rose-500/30"
                      }`}
                    >
                      {isActive ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <Clock className="w-3 h-3 text-rose-400" />}
                      {b.status} · TTL {b.ttl_days}d
                    </span>
                  </div>

                  {/* Trayecto Origen -> Destino */}
                  <div className="p-3 rounded-xl bg-black/40 border border-white/[0.06] flex items-center justify-between text-xs font-mono">
                    <div className="truncate max-w-[140px] sm:max-w-[180px]">
                      <span className="block text-[9px] text-white/30 uppercase">Origen</span>
                      <strong className="text-white/90">{b.source_notebook}</strong>
                    </div>

                    <ArrowLeftRight className="w-4 h-4 text-indigo-400 shrink-0 mx-2" />

                    <div className="truncate max-w-[140px] sm:max-w-[180px] text-right">
                      <span className="block text-[9px] text-white/30 uppercase">Destino</span>
                      <strong className="text-white/90">{b.target_notebook}</strong>
                    </div>
                  </div>

                  {/* Allowlist de temas */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1">
                      <Tag className="w-3 h-3 text-white/30" />
                      Allowlist de Tópicos Autorizados:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {b.topic_allowlist.map((topic) => (
                        <span
                          key={topic}
                          className="px-2 py-0.5 rounded-md bg-white/[0.05] border border-white/[0.08] text-white/80 text-[11px]"
                        >
                          {topic}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Metadatos de Auditoría y Expiración */}
                  <div className="pt-3 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-2 text-[10px] text-white/40">
                    <div className="flex items-center gap-1.5">
                      <UserCheck className="w-3.5 h-3.5 text-white/30" />
                      <span>Auditor: <strong className="text-white/70">{b.reviewer}</strong></span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-white/30" />
                      <span>Expira: {new Date(b.expires_at).toLocaleDateString()}</span>
                    </div>

                    <div className="w-full text-[9px] text-white/30 font-mono truncate">
                      Provenanza: {b.provenance_tag}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </div>
    </main>
  );
};

export default FederationView;
