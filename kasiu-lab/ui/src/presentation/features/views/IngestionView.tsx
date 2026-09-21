import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRightLeft,
  CheckCircle2,
  Database,
  FileCode2,
  FileSpreadsheet,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { CALSourceItemDto, ConversionConflictDto } from "./types";

export const IngestionView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTrust, setFilterTrust] = useState<"all" | "verified" | "unverified">("all");
  const [filterConflictOnly, setFilterConflictOnly] = useState(false);

  // 1. Fetch CAL Catalog
  const {
    data: catalog,
    isLoading: isLoadingCatalog,
    error: catalogError,
    refetch: refetchCatalog,
  } = useQuery<CALSourceItemDto[]>({
    queryKey: ["ingestion-catalog"],
    queryFn: async () => {
      const res = await fetch("/api/ingestion/catalog");
      if (!res.ok) throw new Error("Error al obtener catálogo de fuentes CAL");
      return res.json();
    },
  });

  // 2. Fetch CAL Conversion Conflicts
  const {
    data: conflicts,
    refetch: refetchConflicts,
  } = useQuery<ConversionConflictDto[]>({
    queryKey: ["ingestion-conflicts"],
    queryFn: async () => {
      const res = await fetch("/api/ingestion/conflicts");
      if (!res.ok) throw new Error("Error al consultar discrepancias de conversión");
      return res.json();
    },
  });

  const sources = catalog || [];
  const conflictList = conflicts || [];

  // Computed metrics
  const totalChunks = sources.reduce((acc, s) => acc + s.chunk_count, 0);
  const avgScore = sources.length
    ? (sources.reduce((acc, s) => acc + s.conversion_score, 0) / sources.length).toFixed(2)
    : "0.00";
  const verifiedCount = sources.filter((s) => s.trust_level === "verified").length;
  const conflictCount = sources.filter((s) => s.conflict_flag).length + conflictList.length;
  const formulaFallbackCount = sources.filter((s) => s.formulas_unextracted).length;

  const filteredSources = sources.filter((s) => {
    const q = searchQuery.toLowerCase();
    const matchQuery =
      s.title.toLowerCase().includes(q) ||
      s.source_id.toLowerCase().includes(q) ||
      s.doc_hash.toLowerCase().includes(q) ||
      s.converter_id.toLowerCase().includes(q);

    const matchTrust = filterTrust === "all" || s.trust_level === filterTrust;
    const matchConflict = !filterConflictOnly || s.conflict_flag;

    return matchQuery && matchTrust && matchConflict;
  });

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-8">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.24em] text-emerald-400 font-bold">
                CAL · Conversion Arbitration Layer
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-white/50">
                FASE 4.1
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <Database className="w-7 h-7 text-emerald-400" />
              <span>Catálogo de Ingesta y Arbitraje</span>
            </h1>
            <p className="mt-1 text-xs text-white/50 max-w-2xl">
              Monitoreo soberano de pipeline CAL: integridad de chunks, puntuación de conversión fidedigna y arbitraje multiconversor.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                refetchCatalog();
                refetchConflicts();
              }}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
              title="Actualizar catálogo"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sincronizar</span>
            </button>
          </div>
        </div>

        {/* METRICS ROW */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <FileSpreadsheet className="w-3.5 h-3.5 text-blue-400" /> Fuentes / Chunks
            </span>
            <div className="text-xl font-bold text-white flex items-baseline gap-2">
              <span>{sources.length}</span>
              <span className="text-xs text-white/40 font-normal">({totalChunks} chunks)</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" /> CAL Score Promedio
            </span>
            <div className="text-xl font-bold text-emerald-400">
              {(parseFloat(avgScore) * 100).toFixed(0)}%
              <span className="ml-2 text-[11px] text-white/30 font-normal">calidad estricta</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> Doctrinal Verified
            </span>
            <div className="text-xl font-bold text-teal-300">
              {verifiedCount} / {sources.length}
              <span className="ml-2 text-[10px] text-teal-400/60 font-normal">sin riesgo</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <ArrowRightLeft className="w-3.5 h-3.5 text-amber-400" /> Conflictos / Fallbacks
            </span>
            <div className="text-xl font-bold text-amber-400">
              {conflictCount}
              <span className="ml-2 text-xs text-white/40 font-normal">
                ({formulaFallbackCount} fórmulas)
              </span>
            </div>
          </div>
        </div>

        {/* SECTION: CONVERSION CONFLICTS ARBITRATION */}
        {conflictList.length > 0 && (
          <div className="rounded-[22px] bg-amber-950/20 border border-amber-500/30 p-5 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-amber-500/20">
              <div className="flex items-center gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-400" />
                <h2 className="text-sm font-bold text-amber-300 tracking-wide uppercase">
                  Arbitraje de Discrepancias Multiconversor (CONVERSION_CONFLICT)
                </h2>
              </div>
              <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-bold">
                {conflictList.length} pendientes
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {conflictList.map((c) => (
                <div
                  key={c.conflict_id}
                  className="rounded-[16px] bg-[#101012] border border-white/[0.08] p-4 space-y-2.5 text-xs"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-emerald-400 text-[11px] font-bold">
                      {c.conflict_id}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-amber-950/60 border border-amber-500/30 text-amber-300 text-[10px]">
                      Divergencia {(c.diff_stat * 100).toFixed(1)}%
                    </span>
                  </div>

                  <p className="text-[11px] text-white/50 truncate font-mono">
                    SHA: {c.source_sha256}
                  </p>

                  <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/[0.06] text-[11px]">
                    <div className="bg-white/[0.03] p-2 rounded-lg border border-white/[0.05]">
                      <span className="block text-white/40 text-[9px] uppercase font-bold">
                        Candidato A ({c.converter_a})
                      </span>
                      <span className="font-mono text-white/80 truncate block text-[10px]">
                        {c.candidate_a_hash.slice(0, 16)}…
                      </span>
                    </div>
                    <div className="bg-white/[0.03] p-2 rounded-lg border border-white/[0.05]">
                      <span className="block text-white/40 text-[9px] uppercase font-bold">
                        Candidato B ({c.converter_b})
                      </span>
                      <span className="font-mono text-white/80 truncate block text-[10px]">
                        {c.candidate_b_hash.slice(0, 16)}…
                      </span>
                    </div>
                  </div>

                  <div className="pt-1 flex items-center justify-between text-[10px] text-white/40">
                    <span>Estado: <strong className="text-amber-400">{c.resolution}</strong></span>
                    <span>Registrado: {new Date(c.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CONTROLS / SEARCH */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex-1 max-w-md h-10 rounded-[14px] bg-[#101012] border border-white/[0.08] flex items-center px-3.5 gap-2.5">
            <Search className="w-4 h-4 text-white/35 shrink-0" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filtrar por título, ID, SHA256 o motor..."
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

          <div className="flex items-center gap-2">
            <div className="flex items-center bg-[#101012] rounded-[14px] border border-white/[0.08] p-1 text-xs">
              <button
                onClick={() => setFilterTrust("all")}
                className={`px-3 py-1.5 rounded-[10px] transition ${
                  filterTrust === "all"
                    ? "bg-white text-black font-semibold"
                    : "text-white/50 hover:text-white"
                }`}
              >
                Todos
              </button>
              <button
                onClick={() => setFilterTrust("verified")}
                className={`px-3 py-1.5 rounded-[10px] transition ${
                  filterTrust === "verified"
                    ? "bg-emerald-400 text-black font-semibold"
                    : "text-white/50 hover:text-white"
                }`}
              >
                Verified
              </button>
              <button
                onClick={() => setFilterTrust("unverified")}
                className={`px-3 py-1.5 rounded-[10px] transition ${
                  filterTrust === "unverified"
                    ? "bg-amber-400 text-black font-semibold"
                    : "text-white/50 hover:text-white"
                }`}
              >
                Unverified
              </button>
            </div>

            <button
              onClick={() => setFilterConflictOnly(!filterConflictOnly)}
              className={`h-10 px-3.5 rounded-[14px] border text-xs flex items-center gap-1.5 transition ${
                filterConflictOnly
                  ? "bg-amber-500/20 text-amber-300 border-amber-400/50"
                  : "bg-[#101012] text-white/50 border-white/[0.08] hover:text-white"
              }`}
            >
              <Filter className="w-3.5 h-3.5" />
              <span>Solo Conflictos</span>
            </button>
          </div>
        </div>

        {/* LOADING & ERROR STATES */}
        {isLoadingCatalog && (
          <div className="p-8 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            <span>Consultando fuentes y metadatos CAL en base soberana...</span>
          </div>
        )}

        {catalogError && (
          <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <div>
              <strong className="block font-semibold">Error al acceder a CAL</strong>
              <span>{(catalogError as Error).message}</span>
            </div>
          </div>
        )}

        {/* SOURCES TABLE */}
        {!isLoadingCatalog && !catalogError && (
          <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse font-mono">
                <thead>
                  <tr className="border-b border-white/[0.08] bg-black/40 text-[10px] text-white/40 uppercase tracking-wider">
                    <th className="py-3.5 px-4 font-semibold">Fuente / Documento</th>
                    <th className="py-3.5 px-4 font-semibold">Chunks</th>
                    <th className="py-3.5 px-4 font-semibold">Motor Ingesta</th>
                    <th className="py-3.5 px-4 font-semibold">CAL Score</th>
                    <th className="py-3.5 px-4 font-semibold">Fórmulas</th>
                    <th className="py-3.5 px-4 font-semibold">Confianza</th>
                    <th className="py-3.5 px-4 font-semibold">OCR Provenance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {filteredSources.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="py-8 text-center text-white/40 text-xs">
                        No se encontraron fuentes acordes al filtro.
                      </td>
                    </tr>
                  ) : (
                    filteredSources.map((s) => {
                      const isHighQuality = s.conversion_score >= 0.85;
                      const isMidQuality = s.conversion_score >= 0.70;

                      return (
                        <tr
                          key={s.source_id}
                          className="hover:bg-white/[0.02] transition group"
                        >
                          <td className="py-3.5 px-4 max-w-xs">
                            <div className="font-semibold text-white group-hover:text-emerald-300 transition truncate">
                              {s.title}
                            </div>
                            <div className="mt-0.5 text-[10px] text-white/40 flex items-center gap-2">
                              <span>ID: {s.source_id}</span>
                              <span>·</span>
                              <span className="font-mono text-white/30 truncate max-w-[120px]">
                                SHA: {s.doc_hash.slice(0, 10)}…
                              </span>
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <span className="px-2 py-0.5 rounded bg-white/[0.06] text-white/80 font-mono text-[11px]">
                              {s.chunk_count}
                            </span>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-1.5 text-white/70">
                              <FileCode2 className="w-3.5 h-3.5 text-white/30" />
                              <span className="capitalize">{s.converter_id}</span>
                              <span className="text-[10px] text-white/30">v{s.converter_version}</span>
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                  isHighQuality
                                    ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                                    : isMidQuality
                                    ? "bg-amber-950/60 text-amber-300 border border-amber-500/30"
                                    : "bg-red-950/60 text-red-400 border border-red-500/30"
                                }`}
                              >
                                {(s.conversion_score * 100).toFixed(0)}%
                              </span>
                              {s.conflict_flag && (
                                <span
                                  className="px-1.5 py-0.5 rounded bg-red-900/60 text-red-300 text-[9px] font-bold"
                                  title="Discrepancia detectada entre motores"
                                >
                                  CONFLICT
                                </span>
                              )}
                            </div>
                          </td>

                          <td className="py-3.5 px-4">
                            {s.formulas_unextracted ? (
                              <span className="px-2 py-0.5 rounded bg-amber-950/50 text-amber-300 border border-amber-500/30 text-[10px] font-semibold flex items-center gap-1 w-fit">
                                <AlertTriangle className="w-3 h-3 text-amber-400" />
                                Fallback Req
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded bg-white/[0.04] text-white/40 text-[10px]">
                                Extraídas
                              </span>
                            )}
                          </td>

                          <td className="py-3.5 px-4">
                            {s.trust_level === "verified" ? (
                              <span className="px-2 py-0.5 rounded-full bg-emerald-950/50 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold uppercase flex items-center gap-1 w-fit">
                                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                                Verified
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded-full bg-amber-950/50 text-amber-300 border border-amber-500/30 text-[10px] font-bold uppercase flex items-center gap-1 w-fit">
                                Unverified
                              </span>
                            )}
                          </td>

                          <td className="py-3.5 px-4">
                            <span className="text-[11px] text-white/50 uppercase">
                              {s.ocr_provenance === "none" ? "Digital nativo" : s.ocr_provenance}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </main>
  );
};

export default IngestionView;
