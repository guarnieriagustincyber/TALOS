import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Check,
  Copy,
  FileCode,
  Loader2,
  Lock,
  RefreshCw,
  Settings,
  Shield,
} from "lucide-react";
import { ReadOnlyConfigDto } from "./types";

export const ConfigView: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<string>("bridges");
  const [copied, setCopied] = useState(false);

  const {
    data: config,
    isLoading,
    error,
    refetch,
  } = useQuery<ReadOnlyConfigDto>({
    queryKey: ["read-only-config"],
    queryFn: async () => {
      const res = await fetch("/api/config/read-only");
      if (!res.ok) throw new Error("Error al consultar configuración del sistema");
      return res.json();
    },
  });

  const getFileContent = () => {
    if (!config) return "{}";
    switch (selectedFile) {
      case "bridges":
        return JSON.stringify(config.bridges_allowlist, null, 2);
      case "routing":
        return JSON.stringify(config.routing_table_frozen, null, 2);
      case "namespaces":
        return JSON.stringify(config.namespace_registry, null, 2);
      case "lab_kc":
        return JSON.stringify(config.lab_kc_map, null, 2);
      case "e1_policy":
        return JSON.stringify(config.e1_category_policy, null, 2);
      default:
        return "{}";
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(getFileContent());
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-8">
        {/* HEADER */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] uppercase tracking-[0.24em] text-zinc-400 font-bold">
                Governance · ADR-008 Immutability
              </span>
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-[10px] text-white/50">
                FASE 5.3
              </span>
            </div>
            <h1 className="mt-1.5 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <Settings className="w-7 h-7 text-zinc-300" />
              <span>Configuración Soberana (Read-Only)</span>
            </h1>
            <p className="mt-1 text-xs text-white/50 max-w-2xl">
              Inspección determinista de reglas doctrinales, tablas de ruteo y perímetros congelados. Cero mutación desde la interfaz.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Sincronizar</span>
            </button>
          </div>
        </div>

        {/* IMMUTABILITY MANDATE BANNER */}
        <div className="p-4 rounded-[18px] bg-zinc-950/60 border border-white/[0.12] flex items-start gap-3.5 text-white/80 text-xs">
          <Lock className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <strong className="block text-white font-semibold uppercase tracking-wide">
              Mandato de Inmutabilidad Epistémica (ADR-008)
            </strong>
            <p className="text-[11px] text-white/60 leading-relaxed">
              El frontend de TALOS/KASIU <strong>carece de autoridad epistémica</strong> y facultades para alterar parámetros de arbitraje, allowlists o perímetros de verificación. Cualquier cambio de configuración requiere validación criptográfica y auditoría en código fuente.
            </p>
          </div>
        </div>

        {/* FROZEN PERIMETERS LIST */}
        <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5 space-y-4 shadow-xl">
          <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
            <h2 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              <span>Perímetros Arquitectónicos Congelados</span>
            </h2>
            <span className="text-xs text-emerald-400 font-bold bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full">
              4 NÚCLEOS PROTEGIDOS
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {config?.frozen_perimeters.map((p) => (
              <div
                key={p.path}
                className="p-3 rounded-xl bg-black/40 border border-white/[0.06] flex items-center justify-between text-xs font-mono"
              >
                <div className="truncate max-w-[260px] sm:max-w-[320px]">
                  <span className="block text-[9px] text-white/30 uppercase">{p.adr_rule}</span>
                  <code className="text-white/90 truncate">{p.path}</code>
                </div>
                <span className="px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30 text-[10px] font-bold">
                  {p.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* CONFIGURATION FILES BROWSER */}
        <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] overflow-hidden shadow-xl space-y-0">
          {/* File Tabs Header */}
          <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.08] bg-black/40 flex-wrap gap-2">
            <div className="flex items-center gap-1.5 overflow-x-auto">
              {[
                { id: "bridges", label: "bridges.allowlist.json" },
                { id: "routing", label: "routing_table.frozen.json" },
                { id: "namespaces", label: "namespace_registry.json" },
                { id: "lab_kc", label: "lab_kc_map.json" },
                { id: "e1_policy", label: "e1_category_policy.json" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedFile(tab.id)}
                  className={`h-8 px-3 rounded-[10px] text-xs font-mono transition flex items-center gap-1.5 ${
                    selectedFile === tab.id
                      ? "bg-white text-black font-semibold shadow-sm"
                      : "text-white/50 hover:text-white hover:bg-white/[0.04]"
                  }`}
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            <button
              onClick={handleCopy}
              className="h-8 px-3 rounded-[10px] bg-white/[0.06] hover:bg-white/[0.1] border border-white/[0.08] text-white/80 text-xs flex items-center gap-1.5 transition"
              title="Copiar JSON al portapapeles"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copiado" : "Copiar"}</span>
            </button>
          </div>

          {/* JSON Code Viewer */}
          {isLoading && (
            <div className="p-8 flex items-center justify-center gap-3 text-white/60 text-xs">
              <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
              <span>Leyendo configuración soberana...</span>
            </div>
          )}

          {error && (
            <div className="p-4 m-5 rounded-[18px] bg-red-950/40 border border-red-500/30 text-red-300 text-xs">
              Error al consultar configuración: {(error as Error).message}
            </div>
          )}

          {!isLoading && !error && (
            <div className="p-5 bg-black/60 overflow-x-auto max-h-[500px] k-scroll font-mono text-xs text-white/80 leading-relaxed select-all">
              <pre>
                <code>{getFileContent()}</code>
              </pre>
            </div>
          )}
        </div>
      </div>
    </main>
  );
};

export default ConfigView;
