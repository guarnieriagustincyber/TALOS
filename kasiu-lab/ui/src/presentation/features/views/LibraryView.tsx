import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BookOpen,
  Check,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Eye,
  Folder,
  FolderOpen,
  GraduationCap,
  Hash,
  Layers,
  LayoutGrid,
  List,
  Loader2,
  Search,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { chatService } from "../../../services/chatService";
import { CALSourceItemDto } from "./types";

export interface BookItem {
  id: string;
  title: string;
  subtitle: string;
  author: string;
  notebooks: string[];
  category: "curriculares" | "rfc" | "manuales";
  pages: number;
  year: string;
  docHash: string;
  coverImage?: string;
  theme: "kurose" | "rfc" | "vintage-c" | "fadena" | "rhel";
  description: string;
  conversionScore?: number;
  formulasUnextracted?: boolean;
  trustLevel?: string;
  chunkCount: number;
}

const NOTEBOOK_CONFIG: Record<
  string,
  { label: string; badgeCls: string; dotColor: string }
> = {
  "fadena-lenguajes": {
    label: "Lenguajes de Prog.",
    badgeCls: "bg-emerald-950/40 text-emerald-400 border-emerald-500/25",
    dotColor: "bg-emerald-400",
  },
  "fadena-so2": {
    label: "Sist. Operativos II",
    badgeCls: "bg-amber-950/40 text-amber-400 border-amber-500/25",
    dotColor: "bg-amber-400",
  },
  "fadena-std": {
    label: "Tratamiento de Datos",
    badgeCls: "bg-cyan-950/40 text-cyan-400 border-cyan-500/25",
    dotColor: "bg-cyan-400",
  },
  "fadena-teleco": {
    label: "Telecomunicaciones",
    badgeCls: "bg-sky-950/40 text-sky-400 border-sky-500/25",
    dotColor: "bg-sky-400",
  },
  "fase0-soc": {
    label: "Fase 0 (Algoritmos)",
    badgeCls: "bg-purple-950/40 text-purple-400 border-purple-500/25",
    dotColor: "bg-purple-400",
  },
  "NB-SEC-01-C-PTR": {
    label: "C & Sistemas",
    badgeCls: "bg-rose-950/40 text-rose-400 border-rose-500/25",
    dotColor: "bg-rose-400",
  },
};

export const LibraryView: React.FC<{ onOpen: () => void }> = ({ onOpen }) => {
  const [activeNotebook, setActiveNotebook] = useState<string>("todos");
  const [isTreeExpanded, setIsTreeExpanded] = useState<boolean>(true);
  const [expandedNodes, setExpandedNodes] = useState<Record<string, boolean>>({
    fadena: true,
    fadena_1ano_2cuat: true,
    roadmap: true,
  });
  const [activeCategory, setActiveCategory] = useState<
    "todos" | "curriculares" | "rfc" | "manuales"
  >("todos");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [selectedBook, setSelectedBook] = useState<BookItem | null>(null);
  const [openingHash, setOpeningHash] = useState<string | null>(null);
  const [failedCovers, setFailedCovers] = useState<Set<string>>(new Set());

  // Consumir /api/ingestion/catalog (CAL autoritativo)
  const { data: rawCatalog, isLoading, error } = useQuery<CALSourceItemDto[]>({
    queryKey: ["ingestion-catalog"],
    queryFn: async () => {
      const res = await fetch("/api/ingestion/catalog");
      if (!res.ok) throw new Error("No se pudo cargar el catálogo doctrinal CAL");
      return res.json();
    },
  });

  const books: BookItem[] = useMemo(() => {
    return (rawCatalog || []).map((s) => {
      const isRfc =
        s.title.toLowerCase().includes("rfc") ||
        s.source_id.toLowerCase().includes("rfc");
      const isManual =
        s.title.toLowerCase().includes("manual") ||
        s.title.toLowerCase().includes("red hat") ||
        s.title.toLowerCase().includes("guía");
      const category: "curriculares" | "rfc" | "manuales" = isRfc
        ? "rfc"
        : isManual
        ? "manuales"
        : "curriculares";

      const isC =
        s.title.toLowerCase().includes(" c") ||
        s.title.toLowerCase().includes("punteros");
      const isRhel =
        s.title.toLowerCase().includes("red hat") ||
        s.title.toLowerCase().includes("linux");
      const theme: "kurose" | "rfc" | "vintage-c" | "fadena" | "rhel" = isRfc
        ? "rfc"
        : isC
        ? "vintage-c"
        : isRhel
        ? "rhel"
        : "fadena";

      return {
        id: s.source_id,
        title: s.title,
        subtitle: `Motor: ${s.converter_id} v${s.converter_version}`,
        author: s.author || "Cátedra FADENA",
        notebooks: s.notebooks || [],
        category,
        pages: Math.max(1, Math.round(s.chunk_count / 3)),
        year: s.ingested_at
          ? new Date(s.ingested_at).getFullYear().toString()
          : "2026",
        docHash: s.doc_hash,
        coverImage: `/api/sources/${s.doc_hash}/page-render?page=1`,
        theme,
        description: `Documento procesado con ${s.chunk_count} chunks lógicos. Integridad CAL: ${
          s.conflict_flag ? "ADJUDICADO" : "VERIFICADO"
        }. OCR: ${s.ocr_provenance}.`,
        conversionScore: s.conversion_score,
        formulasUnextracted: s.formulas_unextracted,
        trustLevel: s.trust_level,
        chunkCount: s.chunk_count,
      };
    });
  }, [rawCatalog]);

  const filteredBooks = useMemo(() => {
    return books.filter((book) => {
      const matchCategory =
        activeCategory === "todos" || book.category === activeCategory;
      const matchNotebook =
        activeNotebook === "todos" || book.notebooks.includes(activeNotebook);
      const q = searchQuery.toLowerCase().trim();
      const matchSearch =
        !q ||
        book.title.toLowerCase().includes(q) ||
        book.author.toLowerCase().includes(q) ||
        book.subtitle.toLowerCase().includes(q) ||
        book.description.toLowerCase().includes(q) ||
        book.notebooks.some((nb) => nb.toLowerCase().includes(q));
      return matchCategory && matchNotebook && matchSearch;
    });
  }, [books, activeCategory, activeNotebook, searchQuery]);

  const stats = useMemo(() => {
    const totalDocs = books.length;
    const totalChunks = books.reduce((acc, b) => acc + b.chunkCount, 0);
    const totalPages = books.reduce((acc, b) => acc + b.pages, 0);
    return { totalDocs, totalChunks, totalPages };
  }, [books]);

  const handleOpenLocal = async (docHash: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setOpeningHash(docHash);
    try {
      await chatService.openLocalSource(docHash);
    } catch {
      // Handled silently
    } finally {
      setTimeout(() => setOpeningHash(null), 1200);
    }
  };

  return (
    <main className="flex-1 overflow-y-auto talos-scroll bg-[#0b0b0d] px-6 sm:px-8 py-7 font-mono text-white/90">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-6">
        {/* ENCABEZADO TÁCTICO TALOS */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] uppercase tracking-[0.2em] bg-white/[0.04] border border-white/[0.08] text-cyan-400 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                TALOS CORPUS · DOCTRINAL LAYER
              </span>
              <span className="text-[10px] text-white/30 uppercase tracking-widest hidden sm:inline">
                / SEC-STORAGE-V1
              </span>
            </div>
            <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-white tracking-tight flex items-center gap-3">
              <BookOpen className="w-7 h-7 text-white/70" />
              Biblioteca Doctrinal
            </h1>
            <p className="mt-1 text-xs text-white/45">
              Corpus académico soberano, textos canónicos y referencias técnicas auditadas con firma criptográfica.
            </p>
          </div>

          {/* TELEMETRÍA DE LA BIBLIOTECA */}
          <div className="flex items-center gap-3 self-start md:self-end">
            <div className="px-3 py-1.5 rounded-[12px] bg-[#111113] border border-white/[0.08] flex items-center gap-2.5 text-[11px]">
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-white/35">Textos</span>
                <strong className="text-white font-semibold">{stats.totalDocs}</strong>
              </div>
              <div className="w-px h-6 bg-white/[0.08]" />
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-white/35">Chunks</span>
                <strong className="text-cyan-400 font-semibold">{stats.totalChunks.toLocaleString()}</strong>
              </div>
              <div className="w-px h-6 bg-white/[0.08]" />
              <div className="flex flex-col">
                <span className="text-[9px] uppercase tracking-wider text-white/35">Páginas</span>
                <strong className="text-white/70 font-semibold">{stats.totalPages.toLocaleString()}</strong>
              </div>
            </div>

            {/* Alternar vista Cuadrícula / Tabla */}
            <div className="flex items-center rounded-[12px] bg-[#111113] border border-white/[0.08] p-1">
              <button
                onClick={() => setViewMode("grid")}
                className={`p-1.5 rounded-[8px] transition ${
                  viewMode === "grid"
                    ? "bg-white/[0.12] text-white"
                    : "text-white/40 hover:text-white"
                }`}
                title="Vista en tarjetas"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode("table")}
                className={`p-1.5 rounded-[8px] transition ${
                  viewMode === "table"
                    ? "bg-white/[0.12] text-white"
                    : "text-white/40 hover:text-white"
                }`}
                title="Vista compacta de lista"
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        {/* BARRA DE BÚSQUEDA Y FILTRADO */}
        <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-4 space-y-3.5">
          <div className="flex flex-col md:flex-row gap-3 items-center justify-between">
            {/* Buscador */}
            <div className="w-full md:w-96 h-10 rounded-[12px] bg-black/40 border border-white/[0.08] flex items-center px-3.5 gap-2.5 focus-within:border-cyan-500/40 transition">
              <Search className="w-4 h-4 text-white/35 shrink-0" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Buscar por título, autor, temática o hash..."
                className="flex-1 bg-transparent outline-none text-xs text-white placeholder:text-white/30 min-w-0"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery("")}
                  className="text-white/30 hover:text-white text-xs px-1"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Clasificación por Tipo de Documento */}
            <div className="flex items-center gap-1.5 overflow-x-auto w-full md:w-auto">
              {[
                { id: "todos", label: "Todos", count: books.length },
                {
                  id: "curriculares",
                  label: "Curriculares",
                  count: books.filter((b) => b.category === "curriculares").length,
                },
                {
                  id: "rfc",
                  label: "Estándares RFC",
                  count: books.filter((b) => b.category === "rfc").length,
                },
                {
                  id: "manuales",
                  label: "Manuales",
                  count: books.filter((b) => b.category === "manuales").length,
                },
              ].map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveCategory(cat.id as any)}
                  className={`h-8 px-3 rounded-[9px] text-[11px] font-mono flex items-center gap-1.5 transition whitespace-nowrap select-none ${
                    activeCategory === cat.id
                      ? "bg-white/[0.14] text-white border border-white/30 font-semibold"
                      : "bg-white/[0.03] text-white/45 border border-white/[0.06] hover:text-white hover:bg-white/[0.06]"
                  }`}
                >
                  <span>{cat.label}</span>
                  <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-white/[0.08] text-white/60">
                    {cat.count}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* FILTRO JERÁRQUICO POR ÁRBOL DE CÁTEDRAS Y RAMAS */}
          <div className="pt-2.5 border-t border-white/[0.06] space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase tracking-wider text-white/40 flex items-center gap-1.5">
                  <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" />
                  Árbol Académico & Cátedras
                </span>
                {activeNotebook !== "todos" && (
                  <span className="text-[10px] text-cyan-300 bg-cyan-950/60 border border-cyan-500/30 px-2 py-0.5 rounded-md flex items-center gap-1">
                    <span>Filtro activo:</span>
                    <strong>{NOTEBOOK_CONFIG[activeNotebook]?.label || activeNotebook}</strong>
                    <button
                      onClick={() => setActiveNotebook("todos")}
                      className="ml-1 hover:text-white"
                      title="Quitar filtro"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                )}
              </div>

              <button
                onClick={() => setIsTreeExpanded(!isTreeExpanded)}
                className="text-[11px] text-white/40 hover:text-white flex items-center gap-1 transition select-none"
              >
                <span>{isTreeExpanded ? "Colapsar árbol" : "Expandir árbol"}</span>
                {isTreeExpanded ? (
                  <ChevronDown className="w-3.5 h-3.5" />
                ) : (
                  <ChevronRight className="w-3.5 h-3.5" />
                )}
              </button>
            </div>

            {isTreeExpanded && (
              <div className="p-2.5 rounded-[12px] bg-black/40 border border-white/[0.05] space-y-1.5 text-xs font-mono">
                {/* Opción Todos */}
                <div className="flex items-center justify-between px-2 py-1.5 rounded-[8px] hover:bg-white/[0.04] transition group">
                  <button
                    onClick={() => setActiveNotebook("todos")}
                    className={`flex items-center gap-2 text-left flex-1 ${
                      activeNotebook === "todos"
                        ? "text-cyan-300 font-semibold"
                        : "text-white/70 group-hover:text-white"
                    }`}
                  >
                    <Layers className="w-4 h-4 text-cyan-400 shrink-0" />
                    <span>Todas las Fuentes / Cátedras</span>
                  </button>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full ${
                      activeNotebook === "todos"
                        ? "bg-cyan-950 text-cyan-300 border border-cyan-500/30"
                        : "bg-white/[0.06] text-white/40"
                    }`}
                  >
                    {books.length} libros
                  </span>
                </div>

                {/* Rama 1: FADENA */}
                <div className="border-t border-white/[0.04] pt-1">
                  <div className="flex items-center justify-between px-2 py-1 rounded-[8px] hover:bg-white/[0.03] transition">
                    <button
                      onClick={() =>
                        setExpandedNodes((prev) => ({
                          ...prev,
                          fadena: !prev.fadena,
                        }))
                      }
                      className="flex items-center gap-2 text-white/80 hover:text-white select-none text-[11.5px] font-semibold"
                    >
                      {expandedNodes.fadena ? (
                        <FolderOpen className="w-3.5 h-3.5 text-amber-400/80 shrink-0" />
                      ) : (
                        <Folder className="w-3.5 h-3.5 text-amber-400/80 shrink-0" />
                      )}
                      <span>FADENA · Grado Universitario</span>
                      {expandedNodes.fadena ? (
                        <ChevronDown className="w-3 h-3 text-white/30" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-white/30" />
                      )}
                    </button>
                    <span className="text-[10px] text-white/30">Cátedras 2025/2026</span>
                  </div>

                  {expandedNodes.fadena && (
                    <div className="ml-3 pl-3 border-l border-white/[0.08] mt-1 space-y-1">
                      {/* Sub-nodo 1er Año / 2do Cuatrimestre */}
                      <div className="flex items-center justify-between px-2 py-1 text-[11px] text-white/50">
                        <span className="flex items-center gap-1.5">
                          <span className="text-white/25">└─</span>
                          <GraduationCap className="w-3.5 h-3.5 text-emerald-400/70" />
                          <span className="text-white/60">1° Año · 2° Cuatrimestre:</span>
                        </span>
                      </div>

                      {/* Lista de Materias FADENA */}
                      <div className="ml-4 pl-2 space-y-1">
                        {[
                          {
                            id: "fadena-lenguajes",
                            name: "Lenguajes de Programación",
                            tag: "FADENA 2026",
                            color: "text-emerald-400",
                            activeBg: "bg-emerald-950/40 border-emerald-500/30 text-emerald-300",
                          },
                          {
                            id: "fadena-so2",
                            name: "Sistemas Operativos II",
                            tag: "FADENA 2026",
                            color: "text-amber-400",
                            activeBg: "bg-amber-950/40 border-amber-500/30 text-amber-300",
                          },
                          {
                            id: "fadena-std",
                            name: "Sistema de Tratamiento de Datos",
                            tag: "FADENA 2026",
                            color: "text-cyan-400",
                            activeBg: "bg-cyan-950/40 border-cyan-500/30 text-cyan-300",
                          },
                          {
                            id: "fadena-teleco",
                            name: "Infraestructura de Telecomunicaciones",
                            tag: "FADENA 2025",
                            color: "text-sky-400",
                            activeBg: "bg-sky-950/40 border-sky-500/30 text-sky-300",
                          },
                        ].map((materia) => {
                          const count = books.filter((b) =>
                            b.notebooks.includes(materia.id)
                          ).length;
                          const isSelected = activeNotebook === materia.id;

                          return (
                            <div
                              key={materia.id}
                              onClick={() =>
                                setActiveNotebook(isSelected ? "todos" : materia.id)
                              }
                              className={`flex items-center justify-between px-2.5 py-1.5 rounded-[7px] cursor-pointer transition border select-none ${
                                isSelected
                                  ? `${materia.activeBg} font-semibold shadow-sm`
                                  : "border-transparent text-white/60 hover:text-white hover:bg-white/[0.04]"
                              }`}
                            >
                              <div className="flex items-center gap-2 min-w-0">
                                <span className="text-white/20 text-[10px]">├─</span>
                                <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? "bg-cyan-400 animate-pulse" : "bg-white/30"}`} />
                                <span className="truncate text-[11.5px]">{materia.name}</span>
                                <span className="text-[9px] text-white/30 px-1 py-0.2 bg-white/[0.04] rounded hidden sm:inline">
                                  {materia.tag}
                                </span>
                              </div>
                              <span
                                className={`text-[10px] px-2 py-0.2 rounded-full shrink-0 ${
                                  isSelected
                                    ? "bg-white/10 text-white font-bold"
                                    : "bg-white/[0.04] text-white/40"
                                }`}
                              >
                                {count} libros
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                {/* Rama 2: ROADMAP KASIU TECH */}
                <div className="border-t border-white/[0.04] pt-1">
                  <div className="flex items-center justify-between px-2 py-1 rounded-[8px] hover:bg-white/[0.03] transition">
                    <button
                      onClick={() =>
                        setExpandedNodes((prev) => ({
                          ...prev,
                          roadmap: !prev.roadmap,
                        }))
                      }
                      className="flex items-center gap-2 text-white/80 hover:text-white select-none text-[11.5px] font-semibold"
                    >
                      {expandedNodes.roadmap ? (
                        <FolderOpen className="w-3.5 h-3.5 text-purple-400/80 shrink-0" />
                      ) : (
                        <Folder className="w-3.5 h-3.5 text-purple-400/80 shrink-0" />
                      )}
                      <span>Roadmap KASIU TECH · Trayectoria Técnica</span>
                      {expandedNodes.roadmap ? (
                        <ChevronDown className="w-3 h-3 text-white/30" />
                      ) : (
                        <ChevronRight className="w-3 h-3 text-white/30" />
                      )}
                    </button>
                    <span className="text-[10px] text-white/30">Pensamiento Algorítmico</span>
                  </div>

                  {expandedNodes.roadmap && (
                    <div className="ml-3 pl-3 border-l border-white/[0.08] mt-1 space-y-1">
                      {[
                        {
                          id: "fase0-soc",
                          name: "Fase 0 · Fundamentos, Algoritmos & SoC",
                          tag: "Roadmap v4",
                          activeBg: "bg-purple-950/40 border-purple-500/30 text-purple-300",
                        },
                      ].map((materia) => {
                        const count = books.filter((b) =>
                          b.notebooks.includes(materia.id)
                        ).length;
                        const isSelected = activeNotebook === materia.id;

                        return (
                          <div
                            key={materia.id}
                            onClick={() =>
                              setActiveNotebook(isSelected ? "todos" : materia.id)
                            }
                            className={`flex items-center justify-between px-2.5 py-1.5 rounded-[7px] cursor-pointer transition border select-none ${
                              isSelected
                                ? `${materia.activeBg} font-semibold shadow-sm`
                                : "border-transparent text-white/60 hover:text-white hover:bg-white/[0.04]"
                            }`}
                          >
                            <div className="flex items-center gap-2 min-w-0">
                              <span className="text-white/20 text-[10px]">└─</span>
                              <span className={`w-1.5 h-1.5 rounded-full ${isSelected ? "bg-purple-400 animate-pulse" : "bg-purple-400/40"}`} />
                              <span className="truncate text-[11.5px]">{materia.name}</span>
                              <span className="text-[9px] text-white/30 px-1 py-0.2 bg-white/[0.04] rounded hidden sm:inline">
                                {materia.tag}
                              </span>
                            </div>
                            <span
                              className={`text-[10px] px-2 py-0.2 rounded-full shrink-0 ${
                                isSelected
                                  ? "bg-white/10 text-white font-bold"
                                  : "bg-white/[0.04] text-white/40"
                              }`}
                            >
                              {count} libros
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Rama 3: NÚCLEO C & SISTEMAS (Soberano) */}
                <div className="border-t border-white/[0.04] pt-1">
                  <div
                    onClick={() =>
                      setActiveNotebook(
                        activeNotebook === "NB-SEC-01-C-PTR" ? "todos" : "NB-SEC-01-C-PTR"
                      )
                    }
                    className={`flex items-center justify-between px-2 py-1.5 rounded-[8px] cursor-pointer transition border select-none ${
                      activeNotebook === "NB-SEC-01-C-PTR"
                        ? "bg-rose-950/40 border-rose-500/30 text-rose-300 font-semibold"
                        : "border-transparent text-white/70 hover:text-white hover:bg-white/[0.03]"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-rose-400" />
                      <span className="text-[11.5px]">Cybersecurity & Systems Engineering (C & Kernel)</span>
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.2 rounded-full ${
                        activeNotebook === "NB-SEC-01-C-PTR"
                          ? "bg-white/10 text-white font-bold"
                          : "bg-white/[0.04] text-white/40"
                      }`}
                    >
                      {books.filter((b) => b.notebooks.includes("NB-SEC-01-C-PTR")).length} libros
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ESTADOS DE CARGA Y ERROR */}
        {isLoading && (
          <div className="p-12 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center justify-center gap-3 text-white/60 text-xs font-mono">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Consultando catálogo de fuentes soberano...</span>
          </div>
        )}

        {error && (
          <div className="p-5 rounded-[18px] bg-red-950/40 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs font-mono">
            <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
            <div>
              <strong className="block font-semibold">Fallo en Consulta Doctrinal</strong>
              <span>{(error as Error).message}</span>
            </div>
          </div>
        )}

        {/* RESULTADO VACÍO */}
        {!isLoading && !error && filteredBooks.length === 0 && (
          <div className="p-12 rounded-[20px] bg-[#101012] border border-dashed border-white/[0.1] text-center space-y-2">
            <BookOpen className="w-8 h-8 text-white/20 mx-auto" />
            <p className="text-xs text-white/50">
              No se encontraron textos para los criterios de filtrado seleccionados.
            </p>
            <button
              onClick={() => {
                setActiveNotebook("todos");
                setActiveCategory("todos");
                setSearchQuery("");
              }}
              className="text-xs text-cyan-400 hover:underline inline-block mt-2"
            >
              Restablecer filtros
            </button>
          </div>
        )}

        {/* VISTA EN CUADRÍCULA (GRID VIEW) */}
        {!isLoading && !error && viewMode === "grid" && filteredBooks.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredBooks.map((book) => {
              const hasCoverImg = book.coverImage && !failedCovers.has(book.id);

              return (
                <article
                  key={book.id}
                  onClick={() => setSelectedBook(book)}
                  className="rounded-[18px] border border-white/[0.08] bg-[#111113] p-4 flex flex-col justify-between transition hover:border-white/25 hover:bg-[#151518] group cursor-pointer shadow-lg"
                >
                  <div className="space-y-3">
                    {/* Encabezado de la tarjeta: Portada mini + Metadatos clave */}
                    <div className="flex gap-3.5 items-start">
                      {/* Miniatura de libro táctil */}
                      <div className="w-16 h-22 shrink-0 rounded-[8px] overflow-hidden bg-black/80 border border-white/10 relative shadow-md">
                        {hasCoverImg ? (
                          <img
                            src={book.coverImage}
                            alt={book.title}
                            className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                            onError={() => {
                              setFailedCovers((prev) => new Set(prev).add(book.id));
                            }}
                          />
                        ) : (
                          <div className="w-full h-full flex flex-col items-center justify-center p-1 text-center bg-gradient-to-br from-white/[0.05] to-transparent">
                            <BookOpen className="w-5 h-5 text-white/30 mb-1" />
                            <span className="text-[7px] text-white/40 uppercase font-bold truncate w-full">
                              {book.title.slice(0, 10)}
                            </span>
                          </div>
                        )}
                        <div className="absolute inset-y-0 left-0 w-1 bg-white/20" />
                      </div>

                      {/* Título y Autor */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-[9px] uppercase tracking-wider text-white/40 font-semibold truncate">
                            {book.category}
                          </span>
                          <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-white/[0.05] border border-white/[0.08] text-white/60 shrink-0">
                            CAL {(book.conversionScore! * 100).toFixed(0)}%
                          </span>
                        </div>

                        <h3
                          className="mt-1 text-xs font-bold text-white leading-snug line-clamp-2 group-hover:text-cyan-300 transition"
                          title={book.title}
                        >
                          {book.title}
                        </h3>

                        <p
                          className="mt-0.5 text-[11px] text-white/60 truncate italic"
                          title={book.author}
                        >
                          {book.author}
                        </p>
                      </div>
                    </div>

                    {/* Descripción sintética */}
                    <p className="text-[11px] text-white/45 leading-relaxed line-clamp-2">
                      {book.description}
                    </p>

                    {/* Cátedras / Cuadernos vinculados */}
                    {book.notebooks.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {book.notebooks.map((nbId) => {
                          const conf = NOTEBOOK_CONFIG[nbId] || {
                            label: nbId,
                            badgeCls: "bg-white/[0.05] text-white/60 border-white/10",
                            dotColor: "bg-white/40",
                          };
                          return (
                            <span
                              key={nbId}
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-[6px] text-[9px] font-mono border ${conf.badgeCls}`}
                            >
                              <span className={`w-1 h-1 rounded-full ${conf.dotColor}`} />
                              {conf.label}
                            </span>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Pie de tarjeta con acciones rápidas */}
                  <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[10px] text-white/40">
                    <span className="flex items-center gap-1 font-mono">
                      <Hash className="w-3 h-3 text-white/25" />
                      {book.chunkCount} chunks · {book.pages} págs
                    </span>

                    <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                      <button
                        onClick={(e) => handleOpenLocal(book.docHash, e)}
                        className="h-7 px-2 rounded-[7px] bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.12] text-white text-[10px] flex items-center gap-1 transition"
                        title="Abrir con visor local de Linux"
                      >
                        {openingHash === book.docHash ? (
                          <Check className="w-3 h-3 text-emerald-400" />
                        ) : (
                          <ExternalLink className="w-3 h-3" />
                        )}
                        <span className="hidden sm:inline">Abrir</span>
                      </button>

                      <button
                        onClick={() => setSelectedBook(book)}
                        className="h-7 px-2 rounded-[7px] bg-cyan-950/40 border border-cyan-500/30 hover:bg-cyan-900/60 text-cyan-300 text-[10px] font-semibold flex items-center gap-1 transition"
                      >
                        <Eye className="w-3 h-3" />
                        <span>Detalle</span>
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}

        {/* VISTA EN TABLA / LISTA (TABLE VIEW) */}
        {!isLoading && !error && viewMode === "table" && filteredBooks.length > 0 && (
          <div className="rounded-[18px] border border-white/[0.08] bg-[#111113] overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-white/[0.03] border-b border-white/[0.08] text-[10px] uppercase text-white/40 font-semibold tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Documento & Autor</th>
                    <th className="px-4 py-3">Materias Asignadas</th>
                    <th className="px-4 py-3 text-right">Volumen</th>
                    <th className="px-4 py-3 text-center">Score CAL</th>
                    <th className="px-4 py-3 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.04]">
                  {filteredBooks.map((book) => (
                    <tr
                      key={book.id}
                      onClick={() => setSelectedBook(book)}
                      className="hover:bg-white/[0.03] transition cursor-pointer group"
                    >
                      <td className="px-4 py-3 min-w-[280px]">
                        <div className="font-semibold text-white group-hover:text-cyan-300 transition truncate max-w-md">
                          {book.title}
                        </div>
                        <div className="text-[11px] text-white/50 italic truncate">
                          {book.author}
                        </div>
                      </td>
                      <td className="px-4 py-3 min-w-[200px]">
                        <div className="flex flex-wrap gap-1">
                          {book.notebooks.map((nbId) => {
                            const conf = NOTEBOOK_CONFIG[nbId] || {
                              label: nbId,
                              badgeCls: "bg-white/[0.05] text-white/60 border-white/10",
                            };
                            return (
                              <span
                                key={nbId}
                                className={`px-1.5 py-0.2 rounded text-[9px] font-mono border ${conf.badgeCls}`}
                              >
                                {conf.label}
                              </span>
                            );
                          })}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-right font-mono text-[11px] text-white/50 shrink-0">
                        <div>{book.chunkCount} chunks</div>
                        <div className="text-[9px] text-white/30">{book.pages} págs</div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950/60 text-emerald-400 border border-emerald-500/25">
                          {(book.conversionScore! * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={(e) => handleOpenLocal(book.docHash, e)}
                          className="h-7 px-2.5 rounded-[7px] bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1] text-white text-[10px] inline-flex items-center gap-1 transition"
                        >
                          <ExternalLink className="w-3 h-3" />
                          <span>PDF</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* MODAL DE DETALLES DEL LIBRO (DRAWER / OVERLAY) */}
        {selectedBook && (
          <div
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setSelectedBook(null)}
          >
            <div
              className="w-full max-w-2xl rounded-[22px] bg-[#111113] border border-white/[0.14] p-6 shadow-2xl space-y-5 k-fade-in"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Encabezado del Modal */}
              <div className="flex items-start justify-between gap-4 pb-4 border-b border-white/[0.08]">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-[12px] bg-cyan-950/50 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                    <BookOpen className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] uppercase tracking-wider text-cyan-400 font-semibold block">
                      Ficha Doctrinal de Fuente
                    </span>
                    <h2 className="text-base font-bold text-white leading-snug">
                      {selectedBook.title}
                    </h2>
                    <p className="text-xs text-white/60 italic">{selectedBook.author}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedBook(null)}
                  className="p-1.5 rounded-[9px] bg-white/[0.05] hover:bg-white/[0.1] text-white/50 hover:text-white transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Ficha técnica y métricas CAL */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
                <div className="p-3 rounded-[12px] bg-black/50 border border-white/[0.06]">
                  <span className="text-[9px] uppercase text-white/35 block">Chunks</span>
                  <strong className="text-white text-sm">{selectedBook.chunkCount}</strong>
                </div>
                <div className="p-3 rounded-[12px] bg-black/50 border border-white/[0.06]">
                  <span className="text-[9px] uppercase text-white/35 block">Páginas Estimadas</span>
                  <strong className="text-white text-sm">{selectedBook.pages}</strong>
                </div>
                <div className="p-3 rounded-[12px] bg-black/50 border border-white/[0.06]">
                  <span className="text-[9px] uppercase text-white/35 block">CAL Score</span>
                  <strong className="text-emerald-400 text-sm">
                    {(selectedBook.conversionScore! * 100).toFixed(0)}%
                  </strong>
                </div>
                <div className="p-3 rounded-[12px] bg-black/50 border border-white/[0.06]">
                  <span className="text-[9px] uppercase text-white/35 block">Audit Level</span>
                  <strong className="text-cyan-400 text-sm">{selectedBook.trustLevel}</strong>
                </div>
              </div>

              {/* Materias asignadas */}
              <div className="space-y-1.5">
                <span className="text-[10px] uppercase tracking-wider text-white/40 block">
                  Materias / Cuadernos vinculados:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedBook.notebooks.map((nbId) => {
                    const conf = NOTEBOOK_CONFIG[nbId] || {
                      label: nbId,
                      badgeCls: "bg-white/[0.05] text-white/70 border-white/10",
                      dotColor: "bg-white/40",
                    };
                    return (
                      <span
                        key={nbId}
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[8px] text-xs font-mono border ${conf.badgeCls}`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${conf.dotColor}`} />
                        {conf.label}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Hash Criptográfico y Ruta */}
              <div className="p-3 rounded-[12px] bg-black/60 border border-white/[0.06] space-y-1">
                <div className="flex items-center justify-between text-[10px] text-white/40 font-mono">
                  <span>SHA-256 Digest:</span>
                  <span className="text-white/70 truncate max-w-md" title={selectedBook.docHash}>
                    {selectedBook.docHash}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-white/40 font-mono">
                  <span>ID Canónico:</span>
                  <span className="text-cyan-400/90">{selectedBook.id}</span>
                </div>
              </div>

              {/* Acciones en Modal */}
              <div className="pt-2 flex items-center justify-end gap-2.5 border-t border-white/[0.08]">
                <button
                  onClick={() => setSelectedBook(null)}
                  className="h-9 px-4 rounded-[11px] bg-white/[0.05] border border-white/[0.08] hover:bg-white/[0.1] text-xs text-white/70 transition"
                >
                  Cerrar
                </button>
                <button
                  onClick={() => {
                    setSelectedBook(null);
                    onOpen();
                  }}
                  className="h-9 px-4 rounded-[11px] bg-[#162235] text-cyan-300 border border-cyan-500/40 hover:bg-[#1a2b42] font-semibold text-xs flex items-center gap-1.5 transition shadow-sm"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Ver en Panel Lateral</span>
                </button>
                <button
                  onClick={(e) => handleOpenLocal(selectedBook.docHash, e)}
                  className="h-9 px-4 rounded-[11px] bg-white text-black hover:bg-white/90 font-semibold text-xs flex items-center gap-1.5 transition shadow"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Abrir Documento en Linux</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
};

export default LibraryView;

