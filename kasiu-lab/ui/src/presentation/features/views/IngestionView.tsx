import React, { useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowRightLeft,
  CheckCircle2,
  Cloud,
  CloudUpload,
  Database,
  Download,
  ExternalLink,
  FileCode2,
  FileSpreadsheet,
  Filter,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Upload,
} from "lucide-react";
import {
  CALSourceItemDto,
  ColabExportDto,
  ColabStatusDto,
  ColabSyncDto,
  ConversionConflictDto,
} from "./types";

async function getResponseErrorMessage(response: Response, fallback: string): Promise<string> {
  const body = await response.text();
  if (!body.trim()) return `${fallback} (HTTP ${response.status})`;

  try {
    const data: unknown = JSON.parse(body);
    if (typeof data === "object" && data !== null) {
      const payload = data as { detail?: unknown; message?: unknown };
      if (typeof payload.detail === "string" && payload.detail.trim()) return payload.detail;
      if (Array.isArray(payload.detail)) return payload.detail.map(String).join("; ");
      if (typeof payload.message === "string" && payload.message.trim()) return payload.message;
    }
  } catch {
    return body;
  }

  return body;
}

export const IngestionView: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTrust, setFilterTrust] = useState<"all" | "verified" | "unverified">("all");
  const [filterConflictOnly, setFilterConflictOnly] = useState(false);

  // Colab & Drive Sync Operations State
  const [isExporting, setIsExporting] = useState(false);
  const [isSyncingDrive, setIsSyncingDrive] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);
  const pipelineLockRef = useRef(false);
  const [actionResult, setActionResult] = useState<{
    type: "success" | "error" | "info";
    message: string;
    downloadUrl?: string;
    filename?: string;
  } | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const beginPipelineOperation = () => {
    if (pipelineLockRef.current) return false;
    pipelineLockRef.current = true;
    setIsPipelineRunning(true);
    return true;
  };

  const endPipelineOperation = () => {
    pipelineLockRef.current = false;
    setIsPipelineRunning(false);
  };

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

  // 3. Fetch Colab & Google Drive Vector Status
  const {
    data: colabStatus,
    isFetching: isFetchingColab,
    refetch: refetchColab,
  } = useQuery<ColabStatusDto>({
    queryKey: ["ingestion-colab-status"],
    queryFn: async () => {
      const res = await fetch("/api/ingestion/colab/status");
      if (!res.ok) throw new Error("Error al obtener estado de Colab / Drive");
      return res.json();
    },
  });

  const handleExportColab = async (uploadToDrive: boolean = true) => {
    if (!beginPipelineOperation()) return;
    setIsExporting(true);
    setActionResult(null);
    try {
      const res = await fetch(`/api/ingestion/colab/export?upload_to_gdrive=${uploadToDrive}`, {
        method: "POST",
      });
      if (!res.ok) throw new Error(await getResponseErrorMessage(res, "Error al exportar"));
      const data: ColabExportDto = await res.json();
      setActionResult({
        type: "success",
        message: data.message,
        downloadUrl: data.download_url || undefined,
        filename: data.filename || undefined,
      });
      refetchColab();
    } catch (err: any) {
      setActionResult({
        type: "error",
        message: err.message || "Error al exportar chunks para Colab",
      });
    } finally {
      setIsExporting(false);
      endPipelineOperation();
    }
  };

  const handleSyncDrive = async () => {
    if (!beginPipelineOperation()) return;
    setIsSyncingDrive(true);
    setActionResult(null);
    try {
      const res = await fetch("/api/ingestion/colab/sync-drive", {
        method: "POST",
      });
      if (!res.ok) throw new Error(await getResponseErrorMessage(res, "Error al sincronizar desde Google Drive"));
      const data: ColabSyncDto = await res.json();
      setActionResult({
        type: "success",
        message: data.message,
        filename: data.file_used || undefined,
      });
      refetchColab();
      refetchCatalog();
    } catch (err: any) {
      setActionResult({
        type: "error",
        message: err.message || "Error al sincronizar vectores desde Google Drive",
      });
    } finally {
      setIsSyncingDrive(false);
      endPipelineOperation();
    }
  };

  const handleManualUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !beginPipelineOperation()) return;
    setIsUploading(true);
    setActionResult(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/ingestion/colab/upload-vectors", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await getResponseErrorMessage(res, "Error al subir vectors.jsonl"));
      const data: ColabSyncDto = await res.json();
      setActionResult({
        type: "success",
        message: data.message,
        filename: data.file_used || undefined,
      });
      refetchColab();
      refetchCatalog();
    } catch (err: any) {
      setActionResult({
        type: "error",
        message: err.message || "Error al subir vectores",
      });
    } finally {
      setIsUploading(false);
      endPipelineOperation();
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

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
                refetchColab();
              }}
              className="h-10 px-4 rounded-[14px] bg-[#101012] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition shadow-sm"
              title="Actualizar catálogo y estado vectorial"
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

        {/* SECTION: COLAB & GOOGLE DRIVE VECTOR PIPELINE */}
        <div className="rounded-[22px] bg-[#101012] border border-cyan-500/20 p-5 space-y-4 shadow-lg relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-cyan-500 to-blue-500 opacity-80" />

          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider text-cyan-400 font-bold flex items-center gap-1.5">
                  <Cloud className="w-3.5 h-3.5" /> Pipeline Distribuido GPU / Drive
                </span>
                {colabStatus && (
                  colabStatus.pending_chunks === 0 ? (
                    <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                      100% Vectorizado
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/30 text-amber-300 text-[10px] font-bold flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 text-amber-400" />
                      {colabStatus.pending_chunks.toLocaleString()} pendientes
                    </span>
                  )
                )}
              </div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <span>Ciclo de Embeddings (Google Colab & Google Drive)</span>
              </h2>
              <p className="text-xs text-white/50 max-w-3xl">
                Exporta chunks pendientes de vectorizar a Google Drive (<code>{colabStatus?.remote_path || "gdrive:TALOS"}</code>),
                ejecuta el notebook de embedding con GPU en Google Colab, y sincroniza los vectores en TALOS con un solo clic.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <a
                href="https://colab.research.google.com"
                target="_blank"
                rel="noreferrer"
                className="h-9 px-3 rounded-[12px] bg-white/[0.04] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-1.5 transition"
                title="Abrir Google Colab en nueva pestaña"
              >
                <span>Google Colab</span>
                <ExternalLink className="w-3 h-3 text-white/40" />
              </a>

              <button
                onClick={() => refetchColab()}
                disabled={isFetchingColab}
                className="h-9 w-9 rounded-[12px] bg-white/[0.04] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white flex items-center justify-center transition disabled:opacity-50"
                title="Actualizar estado vectorial"
              >
                {isFetchingColab ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>

          {/* COLAB METRICS / STATUS STRIP */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3 rounded-[14px] bg-black/40 border border-white/[0.05]">
              <span className="text-[10px] text-white/40 uppercase">Total Chunks</span>
              <div className="text-base font-bold text-white mt-0.5">
                {colabStatus ? colabStatus.total_chunks.toLocaleString() : "..."}
              </div>
            </div>

            <div className="p-3 rounded-[14px] bg-black/40 border border-white/[0.05]">
              <span className="text-[10px] text-white/40 uppercase">Vectores E5</span>
              <div className="text-base font-bold text-emerald-400 mt-0.5">
                {colabStatus ? colabStatus.total_vectors.toLocaleString() : "..."}
              </div>
            </div>

            <div className="p-3 rounded-[14px] bg-black/40 border border-white/[0.05]">
              <span className="text-[10px] text-white/40 uppercase">Pendientes</span>
              <div className="text-base font-bold text-amber-400 mt-0.5">
                {colabStatus ? colabStatus.pending_chunks.toLocaleString() : "..."}
              </div>
            </div>

            <div className="p-3 rounded-[14px] bg-black/40 border border-white/[0.05]">
              <span className="text-[10px] text-white/40 uppercase">Estado Drive</span>
              <div className="text-xs font-semibold text-cyan-300 mt-1 flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${colabStatus?.rclone_installed ? "bg-emerald-400" : "bg-red-400"}`} />
                <span>{colabStatus?.gdrive_configured ? "gdrive: listo" : colabStatus?.rclone_installed ? "rclone activo" : "rclone offline"}</span>
              </div>
            </div>
          </div>

          {/* ACTION BUTTONS BAR */}
          <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-white/[0.06]">
            {/* Action 1: Export to Drive / Colab */}
            <button
              onClick={() => handleExportColab(true)}
              disabled={isPipelineRunning || (colabStatus?.pending_chunks === 0)}
              className="h-10 px-4 rounded-[14px] bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {isExporting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
                  <span>Exportando y subiendo...</span>
                </>
              ) : (
                <>
                  <CloudUpload className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Generar para Colab & Subir a Drive</span>
                </>
              )}
            </button>

            {/* Action 2: Sync from Drive */}
            <button
              onClick={() => handleSyncDrive()}
              disabled={isPipelineRunning}
              className="h-10 px-4 rounded-[14px] bg-cyan-500/20 hover:bg-cyan-500/30 border border-cyan-500/40 text-cyan-300 text-xs font-semibold flex items-center gap-2 transition disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            >
              {isSyncingDrive ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                  <span>Sincronizando desde Drive...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Recargar y Sincronizar desde Drive</span>
                </>
              )}
            </button>

            {/* Action 3: Manual Upload Fallback */}
            <input
              type="file"
              ref={fileInputRef}
              accept=".jsonl"
              onChange={handleManualUpload}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isPipelineRunning}
              className="h-10 px-4 rounded-[14px] bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-xs flex items-center gap-2 transition disabled:opacity-50 shadow-sm"
              title="Subir archivo vectors_*.jsonl descargado de Colab"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin text-white/60" />
                  <span>Subiendo vectores...</span>
                </>
              ) : (
                <>
                  <Upload className="w-3.5 h-3.5 text-white/40" />
                  <span>Subir vectors.jsonl manual</span>
                </>
              )}
            </button>
          </div>

          {/* ACTION FEEDBACK ALERT */}
          {actionResult && (
            <div
              className={`p-4 rounded-[16px] text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3 border transition ${
                actionResult.type === "success"
                  ? "bg-emerald-950/30 border-emerald-500/30 text-emerald-200"
                  : actionResult.type === "error"
                  ? "bg-red-950/30 border-red-500/30 text-red-200"
                  : "bg-blue-950/30 border-blue-500/30 text-blue-200"
              }`}
            >
              <div className="flex items-center gap-2.5">
                {actionResult.type === "success" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                )}
                <span>{actionResult.message}</span>
              </div>

              {actionResult.downloadUrl && (
                <a
                  href={actionResult.downloadUrl}
                  download={actionResult.filename || "pending_chunks.jsonl"}
                  className="h-8 px-3 rounded-[10px] bg-emerald-500 text-black font-semibold text-[11px] flex items-center gap-1.5 hover:bg-emerald-400 transition shrink-0"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Descargar {actionResult.filename || ".jsonl"}</span>
                </a>
              )}
            </div>
          )}
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
