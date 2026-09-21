import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertOctagon,
  AlertTriangle,
  CheckCircle2,
  Globe,
  Hash,
  Info,
  Loader2,
  Radio,
  RefreshCw,
  Search,
  Server,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
} from "lucide-react";
import { ThreatIntelIOCDto } from "./types";

export const ThreatIntelView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterType, setFilterType] = useState<string>("all");
  const [filterTrust, setFilterTrust] = useState<string>("all");

  const {
    data: iocs,
    isLoading,
    error,
    refetch,
  } = useQuery<ThreatIntelIOCDto[]>({
    queryKey: ["threat-intel-feed"],
    queryFn: async () => {
      const res = await fetch("/api/threatintel/feed");
      if (!res.ok) throw new Error("Error al consultar el feed de Threat Intelligence");
      return res.json();
    },
  });

  const iocList = iocs || [];

  const maliciousCount = iocList.filter((i) => i.verdict === "malicious").length;
  const humanVerifiedCount = iocList.filter((i) => i.trust_level === "verified_human").length;
  const quorumStrongCount = iocList.filter((i) => i.quorum.feeds_agree >= 2).length;
  const conflictCount = iocList.filter((i) => i.conflicts && i.conflicts.length > 0).length;

  const filteredIocs = iocList.filter((i) => {
    const q = searchQuery.toLowerCase();
    const matchQuery =
      i.value.toLowerCase().includes(q) ||
      i.ioc_id.toLowerCase().includes(q) ||
      (i.promoter && i.promoter.toLowerCase().includes(q));

    const matchType = filterType === "all" || i.type === filterType;
    const matchTrust = filterTrust === "all" || i.trust_level === filterTrust;

    return matchQuery && matchType && matchTrust;
  });

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "ip":
        return <Server className="w-3.5 h-3.5" />;
      case "domain":
        return <Globe className="w-3.5 h-3.5" />;
      case "sha256":
        return <Hash className="w-3.5 h-3.5" />;
      default:
        return <Radio className="w-3.5 h-3.5" />;
    }
  };

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-8">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.24em] text-rose-400 font-bold">
                E2/E4 · External Threat Intelligence
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-white/50">
                FASE 4.3
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <ShieldAlert className="w-7 h-7 text-rose-400" />
              <span>Threat Intelligence Feed & Quórum</span>
            </h1>
            <p className="mt-1 text-xs text-white/50 max-w-2xl">
              Monitoreo de Indicadores de Compromiso (IOCs) con corroboración distribuida multifuente y aislamiento epistémico.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sincronizar Feeds</span>
            </button>
          </div>
        </div>

        {/* EPISTEMIC RISK DISCLAIMER (ADR-008 §4) */}
        <div className="p-4 rounded-[18px] bg-rose-950/30 border border-rose-500/40 flex items-start gap-3.5 text-rose-200 text-xs">
          <AlertOctagon className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="block text-rose-300 font-semibold uppercase tracking-wide">
              Aviso Epistémico Obligatorio (ADR-008 §4)
            </strong>
            <p className="text-[11px] text-rose-200/85 leading-relaxed">
              Los datos presentados provienen de feeds externos de inteligencia de amenazas (<code className="text-white font-mono bg-rose-950/80 px-1 py-0.2 rounded">[TF#]</code>). Tienen un nivel de confianza base <strong className="text-amber-300">unverified</strong> y <strong>NO constituyen doctrina curricular fidedigna</strong>. Están confinados epistemológicamente y no pueden promoverse a la base doctrinal sin atestación explícita de un auditor humano.
            </p>
          </div>
        </div>

        {/* METRICS ROW */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-blue-400" /> IOCs en Monitoreo
            </span>
            <div className="text-xl font-bold text-white">
              {iocList.length}
              <span className="ml-2 text-xs text-white/40 font-normal">indicadores</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-rose-400" /> Maliciosos Confirmados
            </span>
            <div className="text-xl font-bold text-rose-400">
              {maliciousCount}
              <span className="ml-2 text-xs text-white/40 font-normal">amenazas</span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> Quórum Fuerte (≥2)
            </span>
            <div className="text-xl font-bold text-emerald-400">
              {quorumStrongCount} / {iocList.length}
              <span className="ml-2 text-[10px] text-emerald-400/60 font-normal">
                ({conflictCount} en conflicto)
              </span>
            </div>
          </div>

          <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-1">
            <span className="text-[10px] text-white/40 uppercase tracking-wider flex items-center gap-1.5">
              <UserCheck className="w-3.5 h-3.5 text-teal-400" /> Human Verified
            </span>
            <div className="text-xl font-bold text-teal-300">
              {humanVerifiedCount}
              <span className="ml-2 text-xs text-teal-400/60 font-normal">promovidos</span>
            </div>
          </div>
        </div>

        {/* CONTROLS / SEARCH / FILTERS */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex-1 max-w-md h-10 rounded-[14px] bg-[#101012] border border-white/[0.08] flex items-center px-3.5 gap-2.5">
            <Search className="w-4 h-4 text-white/35 shrink-0" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar por IP, dominio, hash o promotor..."
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
            {/* Filter by Type */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="h-10 px-3 rounded-[14px] bg-[#101012] border border-white/[0.08] text-xs text-white/70 outline-none"
            >
              <option value="all">Todos los Tipos</option>
              <option value="ip">IP</option>
              <option value="domain">Dominio</option>
              <option value="sha256">SHA-256</option>
              <option value="url">URL</option>
            </select>

            {/* Filter by Trust */}
            <select
              value={filterTrust}
              onChange={(e) => setFilterTrust(e.target.value)}
              className="h-10 px-3 rounded-[14px] bg-[#101012] border border-white/[0.08] text-xs text-white/70 outline-none"
            >
              <option value="all">Todas las Confianzas</option>
              <option value="verified_human">Human Verified</option>
              <option value="unverified">Unverified [TF#]</option>
            </select>
          </div>
        </div>

        {/* LOADING & ERROR STATES */}
        {isLoading && (
          <div className="p-8 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs font-mono">
            <Loader2 className="w-4 h-4 animate-spin text-rose-400" />
            <span>Consultando feeds externos de Threat Intelligence...</span>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs font-mono">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <div>
              <strong className="block font-semibold">Error al consultar Threat Intelligence</strong>
              <span>{(error as Error).message}</span>
            </div>
          </div>
        )}

        {/* IOCS LIST */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredIocs.map((ioc) => {
            const hasStrongQuorum = ioc.quorum.feeds_agree >= 2;
            const isMalicious = ioc.verdict === "malicious";
            const isClean = ioc.verdict === "clean";
            const isHumanVerified = ioc.trust_level === "verified_human";

            return (
              <div
                key={ioc.ioc_id}
                className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5 space-y-4 hover:border-white/[0.18] transition shadow-lg flex flex-col justify-between"
              >
                <div>
                  {/* Encabezado: Tipo y Veredicto */}
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-white/[0.06] text-white/70 text-[10px] uppercase font-bold flex items-center gap-1.5">
                        {getTypeIcon(ioc.type)}
                        {ioc.type.toUpperCase()}
                      </span>
                      <span className="text-[10px] text-white/30 font-mono">
                        {ioc.ioc_id}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          isMalicious
                            ? "bg-rose-950/60 text-rose-400 border border-rose-500/30"
                            : isClean
                            ? "bg-emerald-950/60 text-emerald-400 border border-emerald-500/30"
                            : "bg-amber-950/60 text-amber-300 border border-amber-500/30"
                        }`}
                      >
                        {ioc.verdict}
                      </span>
                    </div>
                  </div>

                  {/* Valor del IOC */}
                  <div className="mt-3 p-3 rounded-xl bg-black/40 border border-white/[0.06]">
                    <span className="block text-[9px] uppercase tracking-wider text-white/30 mb-1">
                      Indicador Observado:
                    </span>
                    <code className="text-xs font-mono text-white/90 break-all select-all">
                      {ioc.value}
                    </code>
                  </div>

                  {/* Quórum de Feeds */}
                  <div className="mt-3.5 space-y-1.5">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-white/40 uppercase tracking-wider">
                        Quórum de Coincidencia Multifuente:
                      </span>
                      <span className={hasStrongQuorum ? "text-emerald-400 font-bold" : "text-amber-400 font-bold"}>
                        {ioc.quorum.feeds_agree} de {ioc.quorum.total_feeds} feeds
                      </span>
                    </div>

                    <div className="w-full h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          hasStrongQuorum ? "bg-emerald-400" : "bg-amber-400"
                        }`}
                        style={{
                          width: `${(ioc.quorum.feeds_agree / ioc.quorum.total_feeds) * 100}%`,
                        }}
                      />
                    </div>
                  </div>

                  {/* Conflictos entre feeds si existen */}
                  {ioc.conflicts && ioc.conflicts.length > 0 && (
                    <div className="mt-3 p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-xs space-y-1">
                      <span className="text-[10px] text-amber-300 font-bold flex items-center gap-1">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        Discrepancia entre Feeds:
                      </span>
                      {ioc.conflicts.map((c, cIdx) => (
                        <p key={cIdx} className="text-[10px] text-amber-200/80 leading-relaxed">
                          • {c}
                        </p>
                      ))}
                    </div>
                  )}
                </div>

                {/* Pie: Confianza y Auditoría */}
                <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-[10px]">
                  <div>
                    {isHumanVerified ? (
                      <span className="px-2 py-0.5 rounded-full bg-teal-950/60 text-teal-300 border border-teal-500/30 font-bold uppercase flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3 text-teal-400" />
                        Human Verified
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-amber-950/60 text-amber-300 border border-amber-500/30 font-bold uppercase flex items-center gap-1">
                        <Info className="w-3 h-3 text-amber-400" />
                        Unverified [TF#]
                      </span>
                    )}
                  </div>

                  {isHumanVerified && ioc.promoter ? (
                    <div className="text-right text-white/40">
                      <span className="block truncate max-w-[150px]">Por: {ioc.promoter}</span>
                      <span className="text-[9px] text-white/30">
                        {ioc.promoted_at ? new Date(ioc.promoted_at).toLocaleDateString() : ""}
                      </span>
                    </div>
                  ) : (
                    <div className="text-right text-white/30">
                      Confinado (ADR-008)
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </main>
  );
};

export default ThreatIntelView;
