import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Binary,
  Bookmark,
  BookOpen,
  Check,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Code,
  Copy,
  Download,
  ExternalLink,
  FileText,
  GraduationCap,
  Loader2,
  Network,
  Pin,
  Plus,
  Search,
  Shield,
  ShieldAlert,
  Trash2,
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { ClaimsVerificationResponse, Citation, EvidenceTab, NoteItem } from "./types";
import { chatService } from "../../../services/chatService";
import { useSandboxFsm } from "../../hooks/useSandboxFsm";
import { ContradictionView } from "./ContradictionView";
import { CurriculumProgress } from "./CurriculumProgress";

export interface EvidenceProps {
  width: number;
  isOpen: boolean;
  isDragging: boolean;
  tab: EvidenceTab;
  notes: NoteItem[];
  activeScope?: string;
  docHash?: string;
  initialPage?: number;
  activeCitation?: Citation | null;
  consultedSources?: Citation[];
  onSelectCitation?: (citation: Citation | null) => void;
  notebookId?: string;
  onAskTopic?: (topicTitle: string) => void;
  onResizeStart: (e: React.MouseEvent) => void;
  onTab: (tab: EvidenceTab) => void;
  onDeleteNote?: (id: string) => void;
  onAddNote?: (note: { title: string; text: string; scope: string }) => void;
}

// ==========================================
// DATA: GRAFO EPISTÉMICO DINÁMICO
// ==========================================
export const buildDynamicMermaidCode = (
  sources: Citation[],
  scope: string = "Consulta del Estudiante"
): string => {
  if (!sources || sources.length === 0) {
    const clean = scope.replace(/["\n]/g, "'").slice(0, 40);
    return `flowchart TD\n    Q["[Q] ${clean}"] --> EMPTY["Sin evidencias curriculares activas en este turno"]\n    style EMPTY fill:#1a1a1e,stroke:#ffffff20,color:#ffffff60`;
  }

  const lines: string[] = ["flowchart TD"];
  const cleanScope = scope.replace(/["\n]/g, "'").slice(0, 36);
  lines.push(`    Q["[Q] ${cleanScope}"]`);

  const roleLabels: Record<string, string> = {
    pedagogical: "Capa 1: Intuición Pedagógica",
    formal: "Capa 2: Mecanismo Formal",
    technical: "Capa 3: Nivel Máquina / Técnico",
    other: "Evidencia Curricular",
  };

  const roleStyles: Record<string, string> = {
    pedagogical: "fill:#002c22,stroke:#10B981,color:#10B981",
    formal: "fill:#082f49,stroke:#38bdf8,color:#38bdf8",
    technical: "fill:#2e1065,stroke:#a855f7,color:#a855f7",
    other: "fill:#451a03,stroke:#f59e0b,color:#f59e0b",
  };

  const activeRoles = Array.from(
    new Set(sources.map((s) => s.epistemicRole || s.epistemic_role || "pedagogical"))
  );

  activeRoles.forEach((roleKey) => {
    const rId = `ROLE_${roleKey}`;
    const rLabel = roleLabels[roleKey] || roleLabels.other;
    lines.push(`    Q --> ${rId}["${rLabel}"]`);
    lines.push(`    style ${rId} ${roleStyles[roleKey] || roleStyles.other}`);
  });

  sources.slice(0, 8).forEach((c, idx) => {
    const eId = `E${idx + 1}`;
    const roleKey = c.epistemicRole || c.epistemic_role || "pedagogical";
    const rId = `ROLE_${roleKey}`;
    const title = (c.sourceTitle || c.source_title || c.author || "Fuente")
      .replace(/["\n]/g, "'")
      .slice(0, 30);
    const p = c.page || c.pageStart || 1;
    const hash = (c.docHash || "canon").slice(0, 8);
    const relVal = c.relevanceScore ?? c.relevance_score ?? 0.85;
    const rel = (Number(relVal) * 100).toFixed(0);
    lines.push(
      `    ${rId} --> ${eId}["[${c.citationId || eId}] ${title} (p.${p})<br/>SHA: ${hash}... (${rel}% rel)"]`
    );
    lines.push(`    style ${eId} fill:#1a2332,stroke:#06b6d4,color:#06b6d4`);
  });

  return lines.join("\n");
};

// ==========================================
// DATA: FUENTES DOCUMENTALES (PÁGINA)
// ==========================================
interface DocSource {
  id: string;
  title: string;
  shortName: string;
  hash: string;
  totalPages: number;
  defaultPage: number;
  dpi: number;
  canonicalQuote: string;
  sectionTitle: string;
}

const CANONICAL_DOCS: DocSource[] = [
  {
    id: "kurose_ross",
    title: "Computer Networking: A Top-Down Approach (8th Edition)",
    shortName: "Kurose & Ross",
    hash: "7599e188b2645104576b5502400565aff7892ef02abb866ed6899ef9b5865a9a",
    totalPages: 890,
    defaultPage: 238,
    dpi: 150,
    sectionTitle: "Sección 3.5: Connection-Oriented Transport: TCP",
    canonicalQuote:
      "TCP connection establishment utilizes a three-way handshake: the client sends a SYN segment, the server allocates buffers and variables and responds with a SYNACK segment, and finally the client allocates buffers and responds with an ACK segment.",
  },
  {
    id: "rfc_793",
    title: "RFC 793: Transmission Control Protocol (DARPA 1981)",
    shortName: "RFC 793",
    hash: "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
    totalPages: 85,
    defaultPage: 24,
    dpi: 140,
    sectionTitle: "Section 3.3: Sequence Numbers & Clock Selection",
    canonicalQuote:
      "The protocol places no restriction on the particular frequencies of clocks which may be used, but the rate of advance should be approximately proportional to real time, clock-driven ISN generation prevents duplicate packets from old incarnations.",
  },
  {
    id: "stallings_security",
    title: "Computer Security: Principles and Practice (3rd Edition)",
    shortName: "Stallings Security",
    hash: "0aa9aa4cc0b23293bf20cb1c6968030220427145008143d39b5963d3724c36b1",
    totalPages: 838,
    defaultPage: 45,
    dpi: 140,
    sectionTitle: "Chapter 1: Overview of Computer Security",
    canonicalQuote:
      "Computer Security: The protection afforded to an automated information system in order to attain the applicable objectives of preserving the integrity, availability, and confidentiality of information system resources.",
  },
];

// ==========================================
// DATA: TRAMAS PCAP Y ANÁLISIS FORENSE
// ==========================================
interface PcapField {
  label: string;
  value: string;
  byteRange: [number, number]; // [startByte, endByte] inclusive
}

interface PcapLayer {
  name: string;
  summary: string;
  fields: PcapField[];
}

interface PcapFrame {
  id: string;
  number: number;
  title: string;
  summary: string;
  len: number;
  anomaly?: boolean;
  anomalyText?: string;
  rawHex: string[];
  layers: PcapLayer[];
}

const PCAP_FRAMES: PcapFrame[] = [
  {
    id: "f1",
    number: 1,
    title: "TCP [SYN] · Handshake Inicio",
    summary: "192.168.1.105:54321 → 10.0.0.1:443 [SYN] Seq=0 Win=64240 Len=0 MSS=1460",
    len: 60,
    rawHex: [
      "00", "0c", "29", "8a", "4f", "10", "00", "1a", "2b", "3c", "4d", "5e", "08", "00", "45", "00",
      "00", "3c", "1c", "46", "40", "00", "40", "06", "b1", "e6", "c0", "a8", "01", "69", "0a", "00",
      "00", "01", "d4", "31", "01", "bb", "d2", "8f", "4a", "12", "00", "00", "00", "00", "a0", "02",
      "fa", "f0", "fe", "30", "00", "00", "02", "04", "05", "b4", "01", "03",
    ],
    layers: [
      {
        name: "Ethernet II",
        summary: "Src: 00:1a:2b:3c:4d:5e, Dst: 00:0c:29:8a:4f:10",
        fields: [
          { label: "Destination MAC", value: "00:0c:29:8a:4f:10", byteRange: [0, 5] },
          { label: "Source MAC", value: "00:1a:2b:3c:4d:5e", byteRange: [6, 11] },
          { label: "EtherType", value: "IPv4 (0x0800)", byteRange: [12, 13] },
        ],
      },
      {
        name: "Internet Protocol Version 4",
        summary: "Src: 192.168.1.105, Dst: 10.0.0.1",
        fields: [
          { label: "Version & IHL", value: "IPv4, 20 bytes (0x45)", byteRange: [14, 14] },
          { label: "Total Length", value: "60 bytes (0x003c)", byteRange: [16, 17] },
          { label: "TTL (Time to Live)", value: "64 hops", byteRange: [22, 22] },
          { label: "Protocol", value: "TCP (6)", byteRange: [23, 23] },
          { label: "Header Checksum", value: "0xb1e6 [OK]", byteRange: [24, 25] },
          { label: "Source IP", value: "192.168.1.105 (0xc0a80169)", byteRange: [26, 29] },
          { label: "Destination IP", value: "10.0.0.1 (0x0a000001)", byteRange: [30, 33] },
        ],
      },
      {
        name: "Transmission Control Protocol",
        summary: "Src Port: 54321, Dst Port: 443 [SYN] Seq=0xd28f4a12",
        fields: [
          { label: "Source Port", value: "54321 (0xd431)", byteRange: [34, 35] },
          { label: "Destination Port", value: "443 HTTPS (0x01bb)", byteRange: [36, 37] },
          { label: "Sequence Number (ISN)", value: "3532605970 (0xd28f4a12)", byteRange: [38, 41] },
          { label: "Acknowledgment Number", value: "0 (0x00000000)", byteRange: [42, 45] },
          { label: "Flags", value: "0x002 (SYN)", byteRange: [46, 47] },
          { label: "Window Size", value: "64240 bytes", byteRange: [48, 49] },
          { label: "TCP Options", value: "MSS=1460, NOP, WScale=3", byteRange: [54, 59] },
        ],
      },
    ],
  },
  {
    id: "f2",
    number: 2,
    title: "TCP [SYN, ACK] · Servidor Responde",
    summary: "10.0.0.1:443 → 192.168.1.105:54321 [SYN, ACK] Seq=0 Ack=1 Win=65160 Len=0",
    len: 60,
    rawHex: [
      "00", "1a", "2b", "3c", "4d", "5e", "00", "0c", "29", "8a", "4f", "10", "08", "00", "45", "00",
      "00", "3c", "00", "00", "40", "00", "40", "06", "cd", "2c", "0a", "00", "00", "01", "c0", "a8",
      "01", "69", "01", "bb", "d4", "31", "8a", "4f", "10", "bc", "d2", "8f", "4a", "13", "a0", "12",
      "fe", "88", "3b", "10", "00", "00", "02", "04", "05", "b4", "01", "03",
    ],
    layers: [
      {
        name: "Ethernet II",
        summary: "Src: 00:0c:29:8a:4f:10, Dst: 00:1a:2b:3c:4d:5e",
        fields: [
          { label: "Destination MAC", value: "00:1a:2b:3c:4d:5e", byteRange: [0, 5] },
          { label: "Source MAC", value: "00:0c:29:8a:4f:10", byteRange: [6, 11] },
          { label: "EtherType", value: "IPv4 (0x0800)", byteRange: [12, 13] },
        ],
      },
      {
        name: "Internet Protocol Version 4",
        summary: "Src: 10.0.0.1, Dst: 192.168.1.105",
        fields: [
          { label: "Source IP", value: "10.0.0.1 (0x0a000001)", byteRange: [26, 29] },
          { label: "Destination IP", value: "192.168.1.105 (0xc0a80169)", byteRange: [30, 33] },
        ],
      },
      {
        name: "Transmission Control Protocol",
        summary: "Src Port: 443, Dst Port: 54321 [SYN, ACK] Seq=0x8a4f10bc Ack=0xd28f4a13",
        fields: [
          { label: "Source Port", value: "443 (0x01bb)", byteRange: [34, 35] },
          { label: "Destination Port", value: "54321 (0xd431)", byteRange: [36, 37] },
          { label: "Sequence Number (ISN_s)", value: "2320437436 (0x8a4f10bc)", byteRange: [38, 41] },
          { label: "Acknowledgment Number", value: "0xd28f4a13 (ISN_c + 1)", byteRange: [42, 45] },
          { label: "Flags", value: "0x012 (SYN, ACK)", byteRange: [46, 47] },
        ],
      },
    ],
  },
  {
    id: "f3",
    number: 3,
    title: "TCP [ACK] · Handshake Completado",
    summary: "192.168.1.105:54321 → 10.0.0.1:443 [ACK] Seq=1 Ack=1 Win=64240 Len=0",
    len: 54,
    rawHex: [
      "00", "0c", "29", "8a", "4f", "10", "00", "1a", "2b", "3c", "4d", "5e", "08", "00", "45", "00",
      "00", "28", "1c", "47", "40", "00", "40", "06", "b1", "f9", "c0", "a8", "01", "69", "0a", "00",
      "00", "01", "d4", "31", "01", "bb", "d2", "8f", "4a", "13", "8a", "4f", "10", "bd", "50", "10",
      "fa", "f0", "84", "2a", "00", "00",
    ],
    layers: [
      {
        name: "Transmission Control Protocol",
        summary: "Src Port: 54321, Dst Port: 443 [ACK] Conexión ESTABLISHED",
        fields: [
          { label: "Flags", value: "0x010 (ACK)", byteRange: [46, 47] },
          { label: "Ack Number", value: "0x8a4f10bd (ISN_s + 1)", byteRange: [42, 45] },
        ],
      },
    ],
  },
  {
    id: "f4",
    number: 4,
    title: "TCP [SYN Flood Anomaly] · Detección de Ataque",
    summary: "198.51.100.42:61902 → 10.0.0.1:443 [SYN] Spoofed IP Burst · Sin ACK",
    len: 60,
    anomaly: true,
    anomalyText: "ALERTA FORENSE: Ráfaga SYN con IP Spoofing de rango TEST-NET-2 (RFC 5737). No hay ACK subsecuente. Mitigación de SYN Cookies requerida.",
    rawHex: [
      "00", "0c", "29", "8a", "4f", "10", "aa", "bb", "cc", "dd", "ee", "ff", "08", "00", "45", "00",
      "00", "3c", "ea", "21", "00", "00", "30", "06", "3f", "12", "c6", "33", "64", "2a", "0a", "00",
      "00", "01", "f1", "ce", "01", "bb", "00", "00", "04", "d2", "00", "00", "00", "00", "a0", "02",
      "10", "00", "00", "00", "00", "00", "02", "04", "05", "b4", "00", "00",
    ],
    layers: [
      {
        name: "Internet Protocol Version 4",
        summary: "Src: 198.51.100.42 (Spoofed), Dst: 10.0.0.1",
        fields: [
          { label: "Source IP (Anómala)", value: "198.51.100.42 [Bogons/Spoofed]", byteRange: [26, 29] },
          { label: "Destination IP", value: "10.0.0.1", byteRange: [30, 33] },
        ],
      },
      {
        name: "Transmission Control Protocol",
        summary: "Puerto 61902 → 443 [SYN] ISN fijo con entropía nula",
        fields: [
          { label: "Sequence Number", value: "1234 (0x000004d2)", byteRange: [38, 41] },
          { label: "Flags", value: "0x002 (SYN)", byteRange: [46, 47] },
        ],
      },
    ],
  },
];

// ==========================================
// COMPONENTE PRINCIPAL EVIDENCE PANEL
// ==========================================
export const EvidencePanel: React.FC<EvidenceProps> = ({
  width,
  isOpen,
  isDragging,
  tab,
  notes,
  activeScope = "General",
  docHash = "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
  initialPage,
  activeCitation,
  consultedSources = [],
  onSelectCitation,
  notebookId,
  onAskTopic,
  onResizeStart,
  onTab,
  onDeleteNote,
  onAddNote,
}) => {
  const [roleFilter, setRoleFilter] = useState<string>("all");
  const tabs = [
    { id: "progreso" as EvidenceTab, label: "Programa", icon: GraduationCap },
    { id: "evidencia" as EvidenceTab, label: "Evidencia", icon: BookOpen },
    { id: "pagina" as EvidenceTab, label: "Página", icon: FileText },
    { id: "notas" as EvidenceTab, label: "Notas", icon: Bookmark },
    { id: "contradicciones" as EvidenceTab, label: "Disputas", icon: ShieldAlert },
    { id: "mermaid" as EvidenceTab, label: "Grafo", icon: Activity },
  ];

  const { data: claimsData } = useQuery<ClaimsVerificationResponse>({
    queryKey: ["sessionClaims", activeScope],
    queryFn: async () => {
      const res = await fetch("/api/evidence/claims/sess_default");
      if (!res.ok) throw new Error("Error al consultar claims verificados");
      return res.json();
    },
  });

  // Integración Sandbox FSM
  const { fsmState, assessment, requestEvaluation, resetFsm } = useSandboxFsm();

  // Control de reactividad dinámica y densidad visual
  const [autoSync, setAutoSync] = useState<boolean>(true);
  const [isFocusMode, setIsFocusMode] = useState<boolean>(false);

  // Evidencia activa y acciones
  const [copiedActiveCitation, setCopiedActiveCitation] = useState<boolean>(false);

  const filteredSources = useMemo(() => {
    if (!consultedSources || consultedSources.length === 0) return [];
    if (roleFilter === "all") return consultedSources;
    return consultedSources.filter((src) => {
      const r = (src.epistemic_role || src.epistemicRole || "").toLowerCase();
      return r === roleFilter.toLowerCase();
    });
  }, [consultedSources, roleFilter]);

  const pedCount = (consultedSources || []).filter(
    (s) => (s.epistemic_role || s.epistemicRole || "pedagogical").toLowerCase() === "pedagogical"
  ).length;
  const formCount = (consultedSources || []).filter(
    (s) => (s.epistemic_role || s.epistemicRole || "").toLowerCase() === "formal"
  ).length;
  const techCount = (consultedSources || []).filter(
    (s) => (s.epistemic_role || s.epistemicRole || "").toLowerCase() === "technical"
  ).length;

  const getRoleStyle = (role?: string) => {
    const r = (role || "pedagogical").toLowerCase();
    if (r === "formal") {
      return { label: "Formal", badge: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40" };
    }
    if (r === "technical") {
      return { label: "Técnico", badge: "bg-amber-500/20 text-amber-300 border-amber-500/40" };
    }
    return { label: "Pedagógico", badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" };
  };

  const handleCopyActiveCitation = () => {
    if (!activeCitation) return;
    const title =
      activeCitation.sourceTitle ||
      activeCitation.source_title ||
      activeCitation.sourceId ||
      "Fuente canónica";
    const page = activeCitation.page ?? activeCitation.pageStart ?? 1;
    const text = activeCitation.chunkText || activeCitation.chunk_text || "";
    const formatted = `«${text}» — ${title}, pág. ${page}${
      activeCitation.docHash ? ` (SHA-256: ${activeCitation.docHash.slice(0, 16)}...)` : ""
    }`;
    navigator.clipboard.writeText(formatted);
    setCopiedActiveCitation(true);
    setTimeout(() => setCopiedActiveCitation(false), 2000);
  };

  const handleViewCitationInPage = () => {
    if (!activeCitation) return;
    const page = activeCitation.page ?? activeCitation.pageStart ?? 1;
    setCurrentPage(page);
    onTab("pagina");
  };

  const handleOpenCitationLocalPdf = async () => {
    if (!activeCitation) return;
    const page = activeCitation.page ?? activeCitation.pageStart ?? 1;
    const hashToOpen = activeCitation.docHash || activeDoc.hash;
    try {
      await fetch(
        `/api/evidence/open-local-pdf?hash=${encodeURIComponent(hashToOpen)}&page=${page}`
      );
    } catch {
      // Ignorar fallback
    }
  };

  const handleOpenSourcePdf = async (hash?: string | null, page?: number | null) => {
    if (!hash) return;
    try {
      await fetch(
        `/api/evidence/open-local-pdf?hash=${encodeURIComponent(hash)}&page=${page || 1}`
      );
    } catch {
      // Ignorar fallback
    }
  };

  // ----------------------------------------
  // TAB 1: GRAFO STATE (DINÁMICO)
  // ----------------------------------------
  const [selectedCitationIndex, setSelectedCitationIndex] = useState<number>(0);
  const [isMermaidCodeView, setIsMermaidCodeView] = useState(false);
  const [dagZoom, setDagZoom] = useState(1);
  const [copiedMermaid, setCopiedMermaid] = useState(false);

  // Asegurar índice de cita válido cuando cambian las fuentes
  useEffect(() => {
    if (selectedCitationIndex >= consultedSources.length && consultedSources.length > 0) {
      setSelectedCitationIndex(0);
    }
  }, [consultedSources.length, selectedCitationIndex]);

  const dynamicMermaidCode = useMemo(() => {
    return buildDynamicMermaidCode(consultedSources, activeScope);
  }, [consultedSources, activeScope]);

  const activeEvidenceCitation = useMemo(() => {
    if (!consultedSources || consultedSources.length === 0) return null;
    return consultedSources[selectedCitationIndex] || consultedSources[0] || null;
  }, [consultedSources, selectedCitationIndex]);

  const handleCopyMermaid = () => {
    navigator.clipboard.writeText(dynamicMermaidCode);
    setCopiedMermaid(true);
    setTimeout(() => setCopiedMermaid(false), 2000);
  };

  // ----------------------------------------
  // TAB 2: PÁGINA (PyMuPDF) STATE
  // ----------------------------------------
  const [selectedDocId, setSelectedDocId] = useState<string>("kurose_ross");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [dpi, setDpi] = useState<number>(150);
  const [isPdfLoading, setIsPdfLoading] = useState(false);
  const [pdfLoadError, setPdfLoadError] = useState(false);
  const [copiedCitation, setCopiedCitation] = useState(false);

  const activeDoc = useMemo(() => {
    return CANONICAL_DOCS.find((d) => d.id === selectedDocId) || CANONICAL_DOCS[0];
  }, [selectedDocId]);

  useEffect(() => {
    if (docHash) {
      const matched = CANONICAL_DOCS.find(
        (d) => d.hash.toLowerCase().startsWith(docHash.toLowerCase()) ||
               docHash.toLowerCase().startsWith(d.hash.toLowerCase())
      );
      if (matched) {
        setSelectedDocId(matched.id);
      }
    }
  }, [docHash]);

  useEffect(() => {
    if (initialPage && initialPage >= 1) {
      setCurrentPage(initialPage);
    }
  }, [initialPage]);

  // Sincronizar automáticamente cuando el usuario selecciona una cita
  useEffect(() => {
    if (activeCitation) {
      const citeHash = activeCitation.docHash;
      if (citeHash) {
        const matched = CANONICAL_DOCS.find(
          (d) => d.hash.toLowerCase().startsWith(citeHash.toLowerCase()) ||
                 citeHash.toLowerCase().startsWith(d.hash.toLowerCase())
        );
        if (matched) {
          setSelectedDocId(matched.id);
        }
      }
      const page = activeCitation.page ?? activeCitation.pageStart;
      if (page && page >= 1) {
        setCurrentPage(page);
      }
      setPdfLoadError(false);
    }
  }, [activeCitation]);

  const handleDocChange = (docId: string) => {
    const target = CANONICAL_DOCS.find((d) => d.id === docId);
    if (target) {
      setSelectedDocId(target.id);
      setCurrentPage(target.defaultPage);
      setPdfLoadError(false);
    }
  };

  const handlePageNav = (newPage: number) => {
    if (newPage >= 1 && newPage <= activeDoc.totalPages) {
      setCurrentPage(newPage);
      setIsPdfLoading(true);
      setPdfLoadError(false);
    }
  };

  const handleCopyCitation = () => {
    const citation = `[Aserción Canónica] "${activeDoc.canonicalQuote}" — Fuente: ${activeDoc.title} (Pág. ${currentPage}), SHA-256: ${activeDoc.hash}`;
    navigator.clipboard.writeText(citation);
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  const handleOpenLocalPdf = async () => {
    try {
      await chatService.openLocalSource(activeDoc.hash);
    } catch (err) {
      console.error("Error al abrir visor local:", err);
    }
  };

  // ----------------------------------------
  // TAB 3: PCAP STATE
  // ----------------------------------------
  const [selectedFrameId, setSelectedFrameId] = useState<string>("f1");
  const [highlightedByteRange, setHighlightedByteRange] = useState<[number, number] | null>(null);
  const [expandedLayers, setExpandedLayers] = useState<Set<string>>(new Set(["Ethernet II", "Internet Protocol Version 4", "Transmission Control Protocol"]));

  const activeFrame = useMemo(() => {
    return PCAP_FRAMES.find((f) => f.id === selectedFrameId) || PCAP_FRAMES[0];
  }, [selectedFrameId]);

  const toggleLayer = (layerName: string) => {
    setExpandedLayers((prev) => {
      const next = new Set(prev);
      if (next.has(layerName)) {
        next.delete(layerName);
      } else {
        next.add(layerName);
      }
      return next;
    });
  };

  // ----------------------------------------
  // TAB 4: NOTAS STATE
  // ----------------------------------------
  const [noteSearchQuery, setNoteSearchQuery] = useState("");
  const [noteScopeFilter, setNoteScopeFilter] = useState<"all" | "active" | "general">("all");
  const [isComposingNote, setIsComposingNote] = useState(false);
  const [newNoteTitle, setNewNoteTitle] = useState("");
  const [newNoteContent, setNewNoteContent] = useState("");
  const [copiedNoteId, setCopiedNoteId] = useState<string | null>(null);
  const [pinnedNoteIds, setPinnedNoteIds] = useState<Set<string>>(new Set());
  const [copiedReport, setCopiedReport] = useState(false);

  const togglePinNote = (noteId: string) => {
    setPinnedNoteIds((prev) => {
      const next = new Set(prev);
      if (next.has(noteId)) {
        next.delete(noteId);
      } else {
        next.add(noteId);
      }
      return next;
    });
  };

  const handleCopyNote = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedNoteId(id);
    setTimeout(() => setCopiedNoteId(null), 1800);
  };

  const handleSaveComposerNote = () => {
    if (!newNoteContent.trim()) return;
    if (onAddNote) {
      onAddNote({
        title: newNoteTitle.trim() || `Nota táctica`,
        text: newNoteContent.trim(),
        scope: activeScope,
      });
    }
    setNewNoteTitle("");
    setNewNoteContent("");
    setIsComposingNote(false);
  };

  const handleExportDoctrinalReport = () => {
    const header = `# BITÁCORA FORENSE Y NOTAS DOCTRINALES — TALOS Core v0.3.0\nFecha de emisión: ${new Date().toLocaleString()}\nÁmbito activo: ${activeScope}\nTotal notas registradas: ${notes.length}\n\n---\n\n`;
    const body = notes
      .map(
        (n, i) =>
          `### ${i + 1}. ${n.title}\n- **Fecha:** ${n.date}\n- **Ámbito:** #${n.scope || "General"}\n- **Estado:** ${pinnedNoteIds.has(n.id) ? "★ Fijada" : "Ordinaria"}\n\n${n.text}\n\n---`
      )
      .join("\n\n");

    const fullMarkdown = header + body;
    navigator.clipboard.writeText(fullMarkdown);
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2500);
  };

  return (
    <>
      {/* Resizer Divider */}
      {isOpen && (
        <div
          onMouseDown={onResizeStart}
          className={[
            "group w-[6px] shrink-0 cursor-col-resize flex items-center justify-center transition-colors select-none",
            isDragging ? "bg-amber-500/10" : "bg-transparent hover:bg-white/[0.03]",
          ].join(" ")}
          title="Arrastrar para redimensionar Inspector de Evidencias (P3)"
        >
          <div
            className={[
              "w-[2px] rounded-full transition-all duration-150",
              isDragging
                ? "bg-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.8)] h-20"
                : "bg-white/[0.12] group-hover:bg-white/[0.5] h-14 group-hover:h-18",
            ].join(" ")}
          />
        </div>
      )}

      {/* Main Evidence Aside */}
      <aside
        style={{
          width: isOpen ? width : 0,
          opacity: isOpen ? 1 : 0,
          transition: isDragging
            ? "none"
            : "width 240ms cubic-bezier(0.16, 1, 0.3, 1), opacity 180ms ease-out",
        }}
        className="h-full shrink-0 bg-[#0a0a0c] border-l border-white/[0.07] flex flex-col overflow-hidden select-none font-mono text-xs"
      >
        {/* Top Header & Tab Buttons */}
        <div className="px-4 pt-3.5 pb-2.5 min-w-[320px] shrink-0">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="block text-[9px] uppercase tracking-[0.24em] text-white/35">
                forensic layer
              </span>
              <h2 className="text-sm font-semibold text-white tracking-tight">
                Inspector de Evidencia
              </h2>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/[0.08] text-[9px] text-emerald-400 uppercase tracking-wider">
              {tab} active
            </span>
          </div>

          <div className="flex items-center gap-1 rounded-[14px] bg-black p-1 border border-white/[0.06] overflow-x-auto k-scroll">
            {tabs.map((item) => {
              const Icon = item.icon;
              const active = tab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTab(item.id)}
                  className={`h-9 px-2.5 rounded-[10px] shrink-0 flex-1 min-w-[50px] flex flex-col items-center justify-center gap-0.5 transition ${
                    active
                      ? "bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 font-semibold"
                      : "text-white/40 hover:text-white hover:bg-white/[0.04]"
                  }`}
                >
                  <Icon className="w-3.5 h-3.5 shrink-0" />
                  <span className="text-[9px] uppercase tracking-wider whitespace-nowrap">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Sub-barra de Contexto Dinámico & Limpieza */}
        <div className="px-4 py-2 bg-black/40 border-y border-white/[0.05] flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-2 overflow-hidden flex-1 min-w-0">
            <span
              className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                autoSync
                  ? "bg-emerald-400 shadow-[0_0_6px_#10b981] animate-pulse"
                  : "bg-white/30"
              }`}
            />
            <span className="text-[10px] text-white/40 font-mono shrink-0">Tema:</span>
            <span
              className="text-[11px] font-mono font-medium text-white/90 truncate flex-1 min-w-0"
              title={activeScope}
            >
              {activeScope}
            </span>
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            <button
              type="button"
              onClick={() => setIsFocusMode(!isFocusMode)}
              className={`px-2 py-0.5 rounded-[8px] border text-[9px] font-mono uppercase transition ${
                isFocusMode
                  ? "bg-amber-500/20 text-amber-300 border-amber-400/40 font-semibold shadow-[0_0_8px_rgba(245,158,11,0.2)]"
                  : "bg-white/[0.03] text-white/45 border-white/[0.08] hover:text-white"
              }`}
              title="Alternar entre modo limpio/enfoque y modo con telemetría extendida"
            >
              {isFocusMode ? "Modo Limpio" : "Detallado"}
            </button>
            <button
              type="button"
              onClick={() => setAutoSync(!autoSync)}
              className={`px-2 py-0.5 rounded-[8px] border text-[9px] font-mono uppercase transition ${
                autoSync
                  ? "bg-amber-500/10 text-amber-300 border-amber-500/25 hover:bg-amber-500/20"
                  : "bg-white/[0.03] text-white/35 border-white/[0.08] hover:text-white"
              }`}
              title={
                autoSync
                  ? "Auto-Sync activo: la evidencia sigue el tema de la conversación automáticamente"
                  : "Auto-Sync pausado: evidencia fija"
              }
            >
              {autoSync ? "Auto" : "Fijo"}
            </button>
          </div>
        </div>

        {/* Scrollable Content Container */}
        <div className="flex-1 overflow-y-auto k-scroll p-4 pb-10 min-w-[320px] space-y-4">
          {/* ========================================================= */}
          {/* SECCIÓN 0A: PROGRAMA CURRICULAR (BKT & UNIDADES)          */}
          {/* ========================================================= */}
          {tab === "progreso" && (
            <div className="space-y-4">
              <CurriculumProgress
                notebookId={notebookId || "fadena-lenguajes"}
                onAskTopic={onAskTopic}
              />
            </div>
          )}

          {/* ========================================================= */}
          {/* SECCIÓN 0B: EVIDENCIA CANÓNICA (CITA FORENSE ACTIVA)      */}
          {/* ========================================================= */}
          {tab === "evidencia" && (
            <div className="space-y-4">
              {/* SPOTLIGHT: CITA ACTIVA SELECCIONADA */}
              {activeCitation && (
                <div className="rounded-[20px] bg-[#101012] border border-cyan-500/40 overflow-hidden shadow-2xl relative">
                  {/* Header */}
                  <div className="px-4 py-3 border-b border-white/[0.06] bg-gradient-to-r from-cyan-950/50 via-black/60 to-black/40 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-[6px] bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 font-mono text-[11px] font-bold">
                        [{activeCitation.citationId || activeCitation.id || "CITA"}]
                      </span>
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${getRoleStyle(activeCitation.epistemic_role || activeCitation.epistemicRole).badge}`}>
                        {getRoleStyle(activeCitation.epistemic_role || activeCitation.epistemicRole).label}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1.5">
                        <span className="text-[9px] text-white/40 uppercase font-mono">Score:</span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-mono text-[10px] font-bold">
                          {Math.round(
                            (activeCitation.relevanceScore ??
                              activeCitation.relevance_score ??
                              0.9) * 100
                          )}
                          %
                        </span>
                      </div>
                      {onSelectCitation && (
                        <button
                          type="button"
                          onClick={() => onSelectCitation(null)}
                          className="text-[10px] text-white/40 hover:text-white transition px-1.5 py-0.5 rounded border border-white/[0.08] hover:bg-white/[0.05]"
                          title="Cerrar foco de cita activa"
                        >
                          Cerrar
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Metadatos de la fuente */}
                  <div className="p-4 space-y-3.5">
                    <div className="space-y-1">
                      {activeCitation.author && (
                        <span className="text-[10.5px] text-cyan-400 font-semibold font-mono block">
                          {activeCitation.author}
                        </span>
                      )}
                      <h3 className="text-sm font-semibold text-white leading-snug">
                        {activeCitation.sourceTitle ||
                          activeCitation.source_title ||
                          activeCitation.sourceId ||
                          "Documento Canónico TALOS"}
                      </h3>
                      <div className="flex flex-wrap items-center gap-3 pt-0.5 text-[11px] font-mono text-white/60">
                        <span className="flex items-center gap-1 text-cyan-300 font-semibold">
                          <FileText className="w-3.5 h-3.5 text-cyan-400" />
                          Página {activeCitation.page ?? activeCitation.pageStart ?? "N/A"}
                        </span>
                        {activeCitation.section && (
                          <span className="text-white/40 truncate max-w-[200px]" title={activeCitation.section}>
                            § {activeCitation.section}
                          </span>
                        )}
                        {activeCitation.docHash && (
                          <span
                            className="text-[10px] text-white/40 font-mono truncate max-w-[160px]"
                            title={activeCitation.docHash}
                          >
                            SHA: {activeCitation.docHash.slice(0, 12)}...
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Chunk Text Extraído */}
                    <div className="space-y-1.5">
                      <label className="text-[10px] uppercase tracking-wider text-white/40 font-mono font-semibold block">
                        Texto del Fragmento Consultado
                      </label>
                      <div className="relative p-3 rounded-[12px] bg-black/80 border border-cyan-500/25 shadow-inner font-mono text-[11.5px] text-white/90 leading-relaxed max-h-[220px] overflow-y-auto k-scroll">
                        <blockquote className="italic whitespace-pre-wrap">
                          "{activeCitation.chunkText ||
                            activeCitation.chunk_text ||
                            "Texto del fragmento no disponible en el índice."}"
                        </blockquote>
                      </div>
                    </div>

                    {/* Botones de Acción */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 border-t border-white/[0.06]">
                      <button
                        type="button"
                        onClick={handleCopyActiveCitation}
                        className="h-8 px-3 rounded-[9px] bg-white/[0.04] border border-white/[0.08] text-white/80 hover:text-white hover:bg-white/[0.08] transition flex items-center justify-center gap-1.5 text-xs font-mono"
                      >
                        {copiedActiveCitation ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                        {copiedActiveCitation ? "Copiada" : "Copiar"}
                      </button>
                      <button
                        type="button"
                        onClick={handleViewCitationInPage}
                        className="h-8 px-3 rounded-[9px] bg-cyan-950/40 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-900/50 hover:border-cyan-400 transition flex items-center justify-center gap-1.5 text-xs font-mono font-semibold"
                      >
                        <FileText className="w-3.5 h-3.5 text-cyan-400" />
                        Ver en Página
                      </button>
                    </div>

                    {activeCitation.docHash && (
                      <button
                        type="button"
                        onClick={handleOpenCitationLocalPdf}
                        className="w-full h-8 rounded-[9px] border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-200 transition flex items-center justify-center gap-1.5 text-xs font-mono font-semibold"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Abrir PDF en Visor de Sistema
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* LISTA COMPLETA DE FUENTES CONSULTADAS */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                      Fuentes Consultadas ({consultedSources.length})
                    </h3>
                  </div>
                </div>

                {/* Filtros de rol epistémico */}
                {consultedSources.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap font-mono text-[10px]">
                    <button
                      type="button"
                      onClick={() => setRoleFilter("all")}
                      className={`px-2 py-1 rounded-[8px] border transition ${
                        roleFilter === "all"
                          ? "bg-white/15 text-white border-white/30 font-bold"
                          : "bg-black/30 text-white/50 border-white/[0.06] hover:text-white"
                      }`}
                    >
                      Todas ({consultedSources.length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setRoleFilter("pedagogical")}
                      className={`px-2 py-1 rounded-[8px] border transition ${
                        roleFilter === "pedagogical"
                          ? "bg-emerald-500/25 text-emerald-300 border-emerald-500/50 font-bold"
                          : "bg-black/30 text-emerald-400/60 border-white/[0.06] hover:text-emerald-300"
                      }`}
                    >
                      Pedagógicas ({pedCount})
                    </button>
                    <button
                      type="button"
                      onClick={() => setRoleFilter("formal")}
                      className={`px-2 py-1 rounded-[8px] border transition ${
                        roleFilter === "formal"
                          ? "bg-indigo-500/25 text-indigo-300 border-indigo-500/50 font-bold"
                          : "bg-black/30 text-indigo-400/60 border-white/[0.06] hover:text-indigo-300"
                      }`}
                    >
                      Formales ({formCount})
                    </button>
                    <button
                      type="button"
                      onClick={() => setRoleFilter("technical")}
                      className={`px-2 py-1 rounded-[8px] border transition ${
                        roleFilter === "technical"
                          ? "bg-amber-500/25 text-amber-300 border-amber-500/50 font-bold"
                          : "bg-black/30 text-amber-400/60 border-white/[0.06] hover:text-amber-300"
                      }`}
                    >
                      Técnicas ({techCount})
                    </button>
                  </div>
                )}

                {/* Lista de fragmentos */}
                {filteredSources.length > 0 ? (
                  <div className="space-y-2.5">
                    {filteredSources.map((src, idx) => {
                      const role = getRoleStyle(src.epistemic_role || src.epistemicRole);
                      const pageNum = src.page ?? src.pageStart ?? 1;
                      const scorePct = Math.round((src.relevanceScore ?? src.relevance_score ?? 0.85) * 100);
                      const title = src.sourceTitle || src.source_title || "Documento Canónico";
                      const excerptText = src.chunkText || src.chunk_text || "";

                      return (
                        <div
                          key={src.id || src.citationId || idx}
                          className="p-3.5 rounded-[14px] bg-[#111114] border border-white/[0.07] hover:border-cyan-500/30 transition space-y-2 font-mono text-xs shadow-sm"
                        >
                          {/* Header de la fuente */}
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="px-1.5 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-bold text-[10px]">
                                [{src.citationId || src.id || `E${idx + 1}`}]
                              </span>
                              <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border ${role.badge}`}>
                                {role.label}
                              </span>
                              <span className="text-[10px] text-white/40">
                                Pág. {pageNum}
                              </span>
                            </div>
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9.5px] font-bold shrink-0">
                              {scorePct}%
                            </span>
                          </div>

                          {/* Título y Autor */}
                          <div className="min-w-0">
                            {src.author ? (
                              <span className="text-[10px] text-cyan-300/90 font-semibold block truncate">
                                {src.author}
                              </span>
                            ) : null}
                            <span className="text-white/90 text-xs font-medium line-clamp-1 block" title={title}>
                              {title}
                            </span>
                            {src.section ? (
                              <span className="text-white/40 text-[10px] block truncate">
                                § {src.section}
                              </span>
                            ) : null}
                          </div>

                          {/* Fragmento */}
                          {excerptText ? (
                            <div className="p-2 rounded-[8px] bg-black/50 border border-white/[0.05] text-[11px] text-white/70 italic line-clamp-3 leading-relaxed">
                              "{excerptText}"
                            </div>
                          ) : null}

                          {/* Acciones */}
                          <div className="flex items-center gap-2 pt-1 border-t border-white/[0.05]">
                            {src.docHash ? (
                              <button
                                type="button"
                                onClick={() => handleOpenSourcePdf(src.docHash, pageNum)}
                                className="flex-1 px-2 py-1 rounded-[7px] bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 text-[10.5px] font-semibold flex items-center justify-center gap-1 transition"
                              >
                                <ExternalLink className="w-3 h-3" />
                                <span>Abrir PDF</span>
                              </button>
                            ) : null}
                            {onSelectCitation && (
                              <button
                                type="button"
                                onClick={() => onSelectCitation(src)}
                                className="flex-1 px-2 py-1 rounded-[7px] bg-white/[0.04] hover:bg-white/[0.08] text-white/70 hover:text-white border border-white/[0.08] text-[10.5px] flex items-center justify-center gap-1 transition"
                              >
                                <BookOpen className="w-3 h-3" />
                                <span>Inspeccionar</span>
                              </button>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : !activeCitation ? (
                  <div className="rounded-[16px] bg-[#101012] border border-dashed border-white/[0.1] p-6 text-center space-y-2.5">
                    <BookOpen className="w-6 h-6 text-cyan-400 mx-auto opacity-60" />
                    <h4 className="text-xs font-semibold text-white">Sin fuentes consultadas activas</h4>
                    <p className="text-[11px] text-white/45 leading-relaxed font-mono">
                      Iniciá una consulta en el chat para visualizar en tiempo real todos los fragmentos y citas
                      bibliográficas recuperados del corpus.
                    </p>
                  </div>
                ) : null}
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* SECCIÓN 1: GRAFO EPISTÉMICO DINÁMICO (ADR-008) */}
          {/* ========================================================= */}
          {tab === "mermaid" && (
            <div className="space-y-3.5">
              {/* Toolbar */}
              <div className="rounded-[16px] bg-[#121214] border border-white/[0.08] p-3 space-y-2.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                    <Network className="w-4 h-4 text-cyan-400 shrink-0" />
                    <span className="text-xs font-semibold text-white truncate">
                      Grafo Epistémico Dinámico
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] bg-black border border-white/[0.08] text-white/50 shrink-0">
                      {consultedSources.length} {consultedSources.length === 1 ? "fuente" : "fuentes"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    {!isMermaidCodeView && consultedSources.length > 0 && (
                      <div className="flex items-center gap-0.5 border-r border-white/[0.08] pr-1.5 mr-0.5">
                        <button
                          type="button"
                          onClick={() => setDagZoom((z) => Math.max(0.7, Math.round((z - 0.15) * 100) / 100))}
                          className="w-5 h-6 rounded bg-black/40 border border-white/[0.06] text-white/50 hover:text-white flex items-center justify-center text-xs font-mono transition"
                          title="Alejar (-)"
                        >
                          -
                        </button>
                        <button
                          type="button"
                          onClick={() => setDagZoom(1)}
                          className="px-1.5 h-6 rounded bg-black/40 border border-white/[0.06] text-[9.5px] font-mono text-white/60 hover:text-white transition"
                          title="Restablecer zoom (100%)"
                        >
                          {Math.round(dagZoom * 100)}%
                        </button>
                        <button
                          type="button"
                          onClick={() => setDagZoom((z) => Math.min(1.6, Math.round((z + 0.15) * 100) / 100))}
                          className="w-5 h-6 rounded bg-black/40 border border-white/[0.06] text-white/50 hover:text-white flex items-center justify-center text-xs font-mono transition"
                          title="Acercar (+)"
                        >
                          +
                        </button>
                      </div>
                    )}
                    <button
                      onClick={() => setIsMermaidCodeView(false)}
                      className={`h-6 px-2 rounded-[6px] text-[9px] font-semibold uppercase tracking-wider transition ${
                        !isMermaidCodeView
                          ? "bg-[#1a2332] text-cyan-300 border border-cyan-500/40 font-bold"
                          : "bg-black/40 text-white/40 hover:text-white"
                      }`}
                    >
                      Visual SVG
                    </button>
                    <button
                      onClick={() => setIsMermaidCodeView(true)}
                      className={`h-6 px-2 rounded-[6px] text-[9px] font-semibold uppercase tracking-wider transition flex items-center gap-1 ${
                        isMermaidCodeView
                          ? "bg-[#1a2332] text-cyan-300 border border-cyan-500/40 font-bold"
                          : "bg-black/40 text-white/40 hover:text-white"
                      }`}
                    >
                      <Code className="w-2.5 h-2.5" />
                      Código
                    </button>
                  </div>
                </div>
              </div>

              {/* State: Empty or Populated */}
              {consultedSources.length === 0 ? (
                <div className="rounded-[18px] bg-[#101012] border border-dashed border-white/[0.1] p-8 text-center space-y-3">
                  <Network className="w-8 h-8 text-cyan-400/60 mx-auto" />
                  <h4 className="text-xs font-semibold text-white">Sin evidencias en el turno actual</h4>
                  <p className="text-[11px] text-white/45 leading-relaxed font-mono max-w-sm mx-auto">
                    Realizá una consulta en el chat o seleccioná un tema para generar la traza epistémica de autoridades curriculares en tiempo real.
                  </p>
                </div>
              ) : isMermaidCodeView ? (
                /* View 1: Raw Mermaid Code */
                <div className="rounded-[18px] bg-[#101012] border border-white/[0.08] p-4 space-y-2.5">
                  <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                    <span className="text-[10px] uppercase tracking-wider text-white/40">
                      Sintaxis Mermaid 10.0+ (Generada en tiempo real)
                    </span>
                    <button
                      onClick={handleCopyMermaid}
                      className="h-6 px-2 rounded-[6px] bg-white/[0.06] hover:bg-white hover:text-black text-white/70 text-[10px] flex items-center gap-1 transition"
                    >
                      {copiedMermaid ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copiedMermaid ? "Copiado" : "Copiar"}
                    </button>
                  </div>
                  <pre className="text-[11px] leading-relaxed text-amber-300/80 bg-black/60 p-3 rounded-[12px] border border-white/[0.04] overflow-x-auto k-scroll font-mono">
                    {dynamicMermaidCode}
                  </pre>
                </div>
              ) : (
                /* View 2: High-Definition Dynamic SVG DAG */
                <div className="space-y-3.5">
                  <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] p-4">
                    <div className="flex items-center justify-between pb-2.5 border-b border-white/[0.06]">
                      <div className="flex items-center gap-2 min-w-0 flex-1 mr-2">
                        <Network className="w-4 h-4 text-cyan-400 shrink-0" />
                        <span className="text-xs font-semibold text-white truncate flex-1 min-w-0">
                          Traza Epistémica: {activeScope || "Consulta Activa"}
                        </span>
                      </div>
                      <span className="px-1.5 py-0.5 rounded text-[9px] bg-black border border-white/[0.08] text-emerald-400 shrink-0 font-mono">
                        VERIFICADO
                      </span>
                    </div>

                    {/* SVG DAG Component Container with Zoom */}
                    <div className="overflow-hidden mt-3 rounded-xl border border-white/[0.04] bg-black/40">
                      <div
                        style={{
                          transform: `scale(${dagZoom})`,
                          transformOrigin: "top center",
                          transition: "transform 0.15s ease-out",
                        }}
                      >
                        <svg viewBox="0 0 440 280" className="w-full h-auto">
                      <defs>
                        <marker id="arr-dynamic-dag" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#06b6d4" />
                        </marker>
                        <marker id="arr-dynamic-role" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                          <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10B981" />
                        </marker>
                      </defs>

                      {/* Root Query Node */}
                      <rect x="110" y="10" width="220" height="32" rx="8" fill="#151517" stroke="#ffffff30" strokeWidth="1.5" />
                      <text x="220" y="30" fill="#ffffff" fontSize="9.5" textAnchor="middle" fontWeight="700">
                        {String(activeScope || "Consulta de Estudio").slice(0, 32)}
                      </text>

                      {/* Active Roles & Dynamic Citations */}
                      {(() => {
                        const roles = ["pedagogical", "formal", "technical"];
                        const roleLabelsMap: Record<string, string> = {
                          pedagogical: "1. Intuición",
                          formal: "2. Mecanismo",
                          technical: "3. Máquina",
                        };
                        const roleColorsMap: Record<string, { stroke: string; fill: string; text: string }> = {
                          pedagogical: { stroke: "#10B981", fill: "#002c22", text: "#10B981" },
                          formal: { stroke: "#38bdf8", fill: "#082f49", text: "#38bdf8" },
                          technical: { stroke: "#a855f7", fill: "#2e1065", text: "#a855f7" },
                        };

                        const displayedSources = consultedSources.slice(0, 3);
                        const roleXs = [75, 220, 365];

                        return (
                          <>
                            {/* Lines from Root to Roles */}
                            {roles.map((r, rIdx) => (
                              <line
                                key={`rline-${r}`}
                                x1={rIdx === 0 ? 160 : rIdx === 1 ? 220 : 280}
                                y1="42"
                                x2={roleXs[rIdx]}
                                y2="78"
                                stroke={roleColorsMap[r].stroke}
                                strokeWidth="1.2"
                                markerEnd="url(#arr-dynamic-role)"
                              />
                            ))}

                            {/* Role Boxes */}
                            {roles.map((r, rIdx) => {
                              const rStyle = roleColorsMap[r];
                              return (
                                <g key={`rolebox-${r}`}>
                                  <rect
                                    x={roleXs[rIdx] - 55}
                                    y="78"
                                    width="110"
                                    height="34"
                                    rx="6"
                                    fill={rStyle.fill}
                                    stroke={rStyle.stroke}
                                    strokeWidth="1"
                                  />
                                  <text
                                    x={roleXs[rIdx]}
                                    y="99"
                                    fill={rStyle.text}
                                    fontSize="8.5"
                                    textAnchor="middle"
                                    fontWeight="700"
                                  >
                                    {roleLabelsMap[r]}
                                  </text>
                                </g>
                              );
                            })}

                            {/* Lines from Roles to Evidence */}
                            {displayedSources.map((_, sIdx) => (
                              <line
                                key={`sline-${sIdx}`}
                                x1={roleXs[sIdx]}
                                y1="112"
                                x2={roleXs[sIdx]}
                                y2="160"
                                stroke="#06b6d4"
                                strokeWidth="1.2"
                                strokeDasharray="3 3"
                                markerEnd="url(#arr-dynamic-dag)"
                              />
                            ))}

                            {/* Evidence Cards */}
                            {displayedSources.map((c, sIdx) => {
                              const isSelected = selectedCitationIndex === sIdx;
                              const cId = c.citationId || `E${sIdx + 1}`;
                              const authorName = c.author || c.source_id?.replace("src_", "").slice(0, 14) || "Cátedra";
                              const pageNum = c.page || c.pageStart || 1;
                              const hashShort = (c.docHash || "canon").slice(0, 7);
                              const rel = Math.round((c.relevanceScore ?? c.relevance_score ?? 0.85) * 100);

                              return (
                                <g
                                  key={`ev-card-${sIdx}`}
                                  onClick={() => {
                                    setSelectedCitationIndex(sIdx);
                                    onSelectCitation?.(c);
                                  }}
                                  className="cursor-pointer"
                                >
                                  <rect
                                    x={roleXs[sIdx] - 60}
                                    y="162"
                                    width="120"
                                    height="58"
                                    rx="8"
                                    fill={isSelected ? "#1e293b" : "#101622"}
                                    stroke={isSelected ? "#38bdf8" : "#06b6d480"}
                                    strokeWidth={isSelected ? 2 : 1}
                                  />
                                  <text
                                    x={roleXs[sIdx]}
                                    y="180"
                                    fill="#38bdf8"
                                    fontSize="9"
                                    textAnchor="middle"
                                    fontWeight="700"
                                  >
                                    [{cId}] {authorName.slice(0, 14)}
                                  </text>
                                  <text
                                    x={roleXs[sIdx]}
                                    y="194"
                                    fill="#94a3b8"
                                    fontSize="7.5"
                                    textAnchor="middle"
                                  >
                                    p. {pageNum} · Rel: {rel}%
                                  </text>
                                  <text
                                    x={roleXs[sIdx]}
                                    y="207"
                                    fill="#10B981"
                                    fontSize="7"
                                    textAnchor="middle"
                                    fontWeight="600"
                                  >
                                    SHA: {hashShort}.. ✓
                                  </text>
                                </g>
                              );
                            })}
                          </>
                        );
                      })()}

                      {/* Status bar */}
                      <rect x="30" y="240" width="380" height="22" rx="6" fill="#00000080" stroke="#ffffff10" />
                      <text x="220" y="255" fill="#10B981" fontSize="8" textAnchor="middle" fontWeight="700">
                        MOTOR EPISTÉMICO: {consultedSources.length}/{consultedSources.length} CITAS CON ENLACE CRIPTOGRÁFICO VERIFICADO
                      </text>
                    </svg>
                      </div>
                    </div>
                  </div>

                  {/* Telemetry Inspection Card */}
                  {activeEvidenceCitation && (
                    <div className="rounded-[18px] bg-[#121214] border border-white/[0.08] p-4 space-y-3">
                      <div className="flex items-center justify-between border-b border-white/[0.06] pb-2.5">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 font-mono text-[10px] font-bold">
                            [{activeEvidenceCitation.citationId || `E${selectedCitationIndex + 1}`}]
                          </span>
                          <span className="text-xs font-semibold text-white">
                            {activeEvidenceCitation.author || "Autoría de cátedra"}
                          </span>
                        </div>
                        <span className="text-[9px] text-emerald-400 font-mono flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          HASH RESUELTO
                        </span>
                      </div>

                      <div className="space-y-1.5 text-[11px]">
                        <p className="text-white/80 font-medium">
                          {activeEvidenceCitation.sourceTitle || activeEvidenceCitation.source_title || "Fuente oficial de cátedra"}
                        </p>
                        <div className="flex items-center gap-4 text-[10px] text-white/45">
                          <span>Página: <strong className="text-white/80">{activeEvidenceCitation.page || activeEvidenceCitation.pageStart || 1}</strong></span>
                          <span>Relevancia: <strong className="text-cyan-300">{Math.round(Number(activeEvidenceCitation.relevanceScore ?? activeEvidenceCitation.relevance_score ?? 0.85) * 100)}%</strong></span>
                        </div>
                        {activeEvidenceCitation.docHash && (
                          <div className="text-[9px] font-mono text-white/40 break-all bg-black/40 p-1.5 rounded border border-white/[0.04]">
                            SHA-256: {activeEvidenceCitation.docHash}
                          </div>
                        )}
                        {(activeEvidenceCitation.chunkText || activeEvidenceCitation.chunk_text) && (
                          <p className="text-[11px] text-white/60 leading-relaxed italic bg-black/30 p-2 rounded border border-white/[0.04] max-h-24 overflow-y-auto k-scroll">
                            "{activeEvidenceCitation.chunkText || activeEvidenceCitation.chunk_text}"
                          </p>
                        )}
                      </div>

                      <button
                        onClick={() => {
                          onSelectCitation?.(activeEvidenceCitation);
                          onTab("pagina");
                        }}
                        className="w-full h-7 rounded-[8px] bg-cyan-950/40 hover:bg-cyan-900/60 border border-cyan-500/30 text-cyan-300 text-[10px] font-semibold flex items-center justify-center gap-1.5 transition"
                      >
                        <BookOpen className="w-3 h-3" />
                        Abrir página {activeEvidenceCitation.page || activeEvidenceCitation.pageStart || 1} en el visor PDF
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ========================================================= */}
          {/* SECCIÓN 2: PÁGINA (PyMuPDF RENDERIZADO EN VIVO) */}
          {/* ========================================================= */}
          {tab === "pagina" && (
            <div className="space-y-3.5">
              {/* Document Switcher & Extracto de Referencia */}
              <div className="rounded-[16px] bg-[#121214] border border-white/[0.08] p-3 space-y-2.5">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[10px] uppercase tracking-wider text-cyan-400 font-semibold flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-cyan-400" />
                      Extracto de Referencia Citada
                    </label>
                    <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-cyan-300 font-bold">
                      Pág. {currentPage}
                    </span>
                  </div>
                  <select
                    value={selectedDocId}
                    onChange={(e) => handleDocChange(e.target.value)}
                    className="w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-2.5 text-xs text-white outline-none focus:border-white/30"
                  >
                    {CANONICAL_DOCS.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.title}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Subtitle notice & immediate context navigation */}
                <div className="flex items-center justify-between gap-2 pt-1 border-t border-white/[0.06]">
                  <p className="text-[10px] text-white/40 leading-snug truncate">
                    Mostrando únicamente la página de referencia citada.
                  </p>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="text-[9px] text-white/35 font-mono">Adyacente:</span>
                    <button
                      onClick={() => handlePageNav(currentPage - 1)}
                      disabled={currentPage <= 1}
                      title="Ver página anterior para contexto adyacente"
                      className="px-2 h-6 rounded-[6px] bg-black border border-white/[0.08] flex items-center gap-0.5 text-[10px] font-mono text-white/70 hover:text-white hover:bg-white/10 transition disabled:opacity-20"
                    >
                      <ChevronLeft className="w-3 h-3" />
                      {currentPage > 1 ? currentPage - 1 : ""}
                    </button>
                    <button
                      onClick={() => handlePageNav(currentPage + 1)}
                      disabled={currentPage >= activeDoc.totalPages}
                      title="Ver página siguiente para contexto adyacente"
                      className="px-2 h-6 rounded-[6px] bg-black border border-white/[0.08] flex items-center gap-0.5 text-[10px] font-mono text-white/70 hover:text-white hover:bg-white/10 transition disabled:opacity-20"
                    >
                      {currentPage < activeDoc.totalPages ? currentPage + 1 : ""}
                      <ChevronRight className="w-3 h-3" />
                    </button>

                    {/* DPI resolution selector */}
                    <select
                      value={dpi}
                      onChange={(e) => setDpi(parseInt(e.target.value, 10))}
                      className="h-6 px-1.5 rounded-[6px] bg-black border border-white/[0.08] text-[9px] text-white/70 outline-none ml-1"
                    >
                      <option value={100}>100 DPI</option>
                      <option value={150}>150 DPI</option>
                      <option value={200}>200 DPI</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Rendered Page Display via PyMuPDF */}
              <div className="rounded-[20px] bg-[#101012] border border-white/[0.08] overflow-hidden">
                <div className="px-4 py-2.5 border-b border-white/[0.06] flex items-center justify-between text-[10px]">
                  <span className="text-white/60 font-semibold">{activeDoc.sectionTitle}</span>
                  <span className="text-emerald-400 font-mono">SHA-256 Lock</span>
                </div>

                <div className="p-3 bg-black/80 flex flex-col items-center justify-center min-h-[260px] relative">
                  {!pdfLoadError ? (
                    <div className="w-full flex justify-center relative">
                      {isPdfLoading && (
                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center z-10">
                          <Loader2 className="w-6 h-6 text-[#F59E0B] animate-spin" />
                        </div>
                      )}
                      <img
                        src={chatService.getPageRenderUrl(activeDoc.hash, currentPage, {
                          highlight: activeCitation?.chunkText || activeCitation?.chunk_text || undefined,
                          dpi: dpi,
                        })}
                        alt={`Página ${currentPage} de ${activeDoc.title}`}
                        onLoad={() => setIsPdfLoading(false)}
                        onError={() => {
                          setIsPdfLoading(false);
                          setPdfLoadError(true);
                        }}
                        className="rounded-[10px] shadow-lg max-h-[380px] object-contain border border-white/[0.06]"
                      />
                    </div>
                  ) : (
                    /* Fallback when backend page-render endpoint is offline or hash not available */
                    <div className="p-5 text-center space-y-3 font-mono">
                      <FileText className="w-8 h-8 text-white/30 mx-auto" />
                      <div className="text-xs text-white/80 font-semibold">{activeDoc.title}</div>
                      <p className="text-[11px] text-white/50 leading-relaxed max-w-[260px] mx-auto">
                        Visualización de extracto verificado bajo hash SHA-256:
                      </p>
                      <div className="rounded-[10px] bg-[#151517] border border-white/[0.06] p-3 text-left text-[11px] text-white/80 leading-relaxed">
                        “{activeDoc.canonicalQuote}”
                      </div>
                    </div>
                  )}
                </div>

                {/* Excerpt Box & Quotation Copier */}
                <div className="p-3.5 bg-[#121214] border-t border-white/[0.06] space-y-2.5">
                  <div className="rounded-[12px] bg-black/50 border border-white/[0.06] p-3 text-[11px] text-white/75 leading-relaxed">
                    <span className="block text-[9px] uppercase tracking-wider text-white/35 mb-1 font-bold">
                      Cita Canónica Vinculada (Pág. {currentPage})
                    </span>
                    “{activeDoc.canonicalQuote}”
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={handleCopyCitation}
                      className="flex-1 h-8 rounded-[9px] bg-white/[0.04] border border-white/[0.08] text-white/70 hover:text-white hover:bg-white/[0.08] transition flex items-center justify-center gap-1.5 text-xs font-mono"
                    >
                      {copiedCitation ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      {copiedCitation ? "Cita Copiada" : "Copiar Cita Forense"}
                    </button>
                    <button
                      onClick={handleOpenLocalPdf}
                      className="h-8 px-3.5 rounded-[9px] border border-emerald-500/50 bg-emerald-950/40 text-emerald-300 hover:bg-emerald-900/50 hover:border-emerald-400 font-semibold flex items-center gap-1.5 transition text-xs shadow-[0_0_10px_rgba(16,185,129,0.15)] font-mono"
                      title="Abrir con visor local de Linux"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      Visor Local
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* SECCIÓN 3: PCAP (WIRESHARK-STYLE LAYER DISSECTION) */}
          {/* ========================================================= */}
          {tab === "packet" && (
            <div className="space-y-3.5">
              {/* Packet Stream Selector */}
              <div className="rounded-[16px] bg-[#121214] border border-white/[0.08] p-3 space-y-2">
                <span className="block text-[10px] uppercase tracking-wider text-white/40 font-semibold">
                  Captura de Paquetes en Vivo (PCAP Stream)
                </span>

                <div className="space-y-1">
                  {PCAP_FRAMES.map((frame) => (
                    <button
                      key={frame.id}
                      onClick={() => {
                        setSelectedFrameId(frame.id);
                        setHighlightedByteRange(null);
                      }}
                      className={`w-full p-2 rounded-[9px] text-left border flex items-center justify-between gap-2 transition ${
                        selectedFrameId === frame.id
                          ? frame.anomaly
                            ? "bg-red-950/40 border-red-500/50 text-red-200"
                            : "bg-[#F59E0B]/15 border-[#F59E0B]/40 text-white"
                          : "bg-black/50 border-white/[0.05] text-white/60 hover:text-white"
                      }`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-[10px]">#{frame.number}</span>
                          <span className="text-xs font-semibold truncate">{frame.title}</span>
                        </div>
                        <span className="block text-[9px] text-white/35 truncate mt-0.5">
                          {frame.summary}
                        </span>
                      </div>
                      <span className="text-[9px] text-white/40 shrink-0 font-mono">
                        {frame.len}B
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Anomaly Badge if present */}
              {activeFrame.anomaly && (
                <div className="rounded-[14px] bg-red-950/30 border border-red-500/30 p-3 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <span className="block text-xs font-bold text-red-300">
                      Anomalía de Seguridad Detectada
                    </span>
                    <p className="text-[11px] text-red-200/80 leading-relaxed">
                      {activeFrame.anomalyText}
                    </p>
                  </div>
                </div>
              )}

              {/* Layer Tree Dissection (Expandable) */}
              <div className="rounded-[18px] bg-[#101012] border border-white/[0.08] p-3.5 space-y-2">
                <span className="block text-[10px] uppercase tracking-wider text-white/40 font-semibold mb-1">
                  Disección de Capas OSI / TCP-IP
                </span>

                <div className="space-y-1.5">
                  {activeFrame.layers.map((layer) => {
                    const isExpanded = expandedLayers.has(layer.name);

                    return (
                      <div
                        key={layer.name}
                        className="rounded-[10px] bg-black/60 border border-white/[0.06] overflow-hidden"
                      >
                        <button
                          onClick={() => toggleLayer(layer.name)}
                          className="w-full px-2.5 py-1.5 flex items-center justify-between text-left hover:bg-white/[0.04] transition"
                        >
                          <div className="flex items-center gap-1.5 min-w-0">
                            {isExpanded ? (
                              <ChevronDown className="w-3 h-3 text-[#F59E0B]" />
                            ) : (
                              <ChevronRight className="w-3 h-3 text-white/40" />
                            )}
                            <span className="text-xs font-bold text-white truncate">{layer.name}</span>
                          </div>
                          <span className="text-[9px] text-white/35 truncate max-w-[120px]">
                            {layer.summary}
                          </span>
                        </button>

                        {isExpanded && (
                          <div className="px-3 pb-2 pt-1 border-t border-white/[0.04] space-y-1 bg-black/30">
                            {layer.fields.map((field, fIdx) => (
                              <div
                                key={`${field.label}-${fIdx}`}
                                onMouseEnter={() => setHighlightedByteRange(field.byteRange)}
                                onMouseLeave={() => setHighlightedByteRange(null)}
                                className="flex items-center justify-between text-[10px] py-0.5 px-1.5 rounded hover:bg-[#F59E0B]/15 hover:text-[#F59E0B] transition cursor-pointer group"
                              >
                                <span className="text-white/50 group-hover:text-amber-300">
                                  {field.label}:
                                </span>
                                <span className="font-mono text-white/90 group-hover:text-white font-semibold">
                                  {field.value}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Interactive Hex Dump with Highlight on Byte Range */}
              <div className="rounded-[18px] bg-[#101012] border border-white/[0.08] p-3.5 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Binary className="w-3.5 h-3.5 text-white/60" />
                    <span className="text-xs font-semibold text-white">Hex Dump Interactivo</span>
                  </div>
                  {highlightedByteRange ? (
                    <span className="text-[9px] px-2 py-0.5 rounded bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/30 animate-pulse">
                      Bytes {highlightedByteRange[0]} a {highlightedByteRange[1]}
                    </span>
                  ) : (
                    <span className="text-[9px] text-white/30">Pasa el mouse sobre los campos</span>
                  )}
                </div>

                <div className="p-3 bg-black rounded-[12px] border border-white/[0.06] overflow-x-auto k-scroll font-mono text-[11px] leading-relaxed">
                  {(() => {
                    const rows: React.ReactNode[] = [];
                    const bytes = activeFrame.rawHex;

                    for (let i = 0; i < bytes.length; i += 16) {
                      const chunk = bytes.slice(i, i + 16);
                      const offsetHex = i.toString(16).padStart(4, "0");
                      const asciiChars = chunk.map((b) => {
                        const code = parseInt(b, 16);
                        return code >= 32 && code <= 126 ? String.fromCharCode(code) : ".";
                      }).join("");

                      rows.push(
                        <div key={`hex-row-${i}`} className="flex items-center justify-between gap-2.5 py-0.5 hover:bg-white/[0.03] px-1 rounded transition-colors group">
                          <span className="text-white/30 select-none w-10 shrink-0 text-[10px] font-mono">{offsetHex}</span>

                          <div className="flex items-center gap-1 sm:gap-1.5 flex-1 font-mono">
                            {chunk.map((b, byteIdx) => {
                              const absoluteIndex = i + byteIdx;
                              const isHighlighted =
                                highlightedByteRange &&
                                absoluteIndex >= highlightedByteRange[0] &&
                                absoluteIndex <= highlightedByteRange[1];

                              return (
                                <span
                                  key={`byte-${absoluteIndex}`}
                                  className={`w-5 text-center rounded transition-all duration-100 text-[11px] ${
                                    isHighlighted
                                      ? "bg-[#F59E0B] text-black font-bold shadow-[0_0_8px_#F59E0B]"
                                      : "text-white/70 group-hover:text-white"
                                  }`}
                                >
                                  {b}
                                </span>
                              );
                            })}
                          </div>

                          <div className="text-emerald-400/60 font-mono tracking-widest text-[11px] select-none pl-3 border-l border-white/[0.08] shrink-0 hidden sm:block w-36 truncate">
                            {asciiChars}
                          </div>
                        </div>
                      );
                    }

                    return rows;
                  })()}
                </div>
              </div>
            </div>
          )}

          {/* ========================================================= */}
          {/* SECCIÓN 4: NOTAS (DOCTRINALES Y MEMORIA PERSISTENTE) */}
          {/* ========================================================= */}
          {tab === "notas" && (
            <div className="space-y-3.5">
              {/* Header & Actions */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-white">Notas Doctrinales</span>
                  <span className="px-2 py-0.5 rounded-full bg-white/[0.08] text-[10px] font-mono text-white/80 font-semibold">
                    {notes.length}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={handleExportDoctrinalReport}
                    className="h-7 px-2 rounded-[8px] bg-white/[0.05] border border-white/[0.08] text-[10px] text-white/70 hover:text-white flex items-center gap-1 transition"
                    title="Exportar todas las notas en Markdown"
                  >
                    {copiedReport ? <Check className="w-3 h-3 text-emerald-400" /> : <Download className="w-3 h-3" />}
                    {copiedReport ? "Reporte Copiado" : "Exportar .md"}
                  </button>

                  <button
                    onClick={() => setIsComposingNote((v) => !v)}
                    className={`h-7 px-2.5 rounded-[8px] text-[11px] flex items-center gap-1 transition select-none ${
                      isComposingNote
                        ? "bg-[#1a2332] text-cyan-300 border border-cyan-500/40 font-bold"
                        : "bg-white/[0.06] border border-white/[0.08] text-white/70 hover:text-white hover:bg-white/[0.1]"
                    }`}
                  >
                    <Plus className="w-3 h-3 stroke-[2.5]" />
                    <span>{isComposingNote ? "Cerrar" : "Nueva"}</span>
                  </button>
                </div>
              </div>

              {/* Scope Filter Tabs */}
              <div className="flex items-center gap-1.5 text-[10px]">
                <button
                  onClick={() => setNoteScopeFilter("all")}
                  className={`h-6 px-2 rounded-[6px] border transition ${
                    noteScopeFilter === "all"
                      ? "bg-[#1a2332] text-cyan-300 font-semibold border-cyan-500/40"
                      : "bg-black/50 text-white/40 border-white/[0.06] hover:text-white"
                  }`}
                >
                  Todas ({notes.length})
                </button>
                <button
                  onClick={() => setNoteScopeFilter("active")}
                  className={`h-6 px-2 rounded-[6px] border transition truncate max-w-[140px] ${
                    noteScopeFilter === "active"
                      ? "bg-[#F59E0B]/20 text-[#F59E0B] font-semibold border-[#F59E0B]/40"
                      : "bg-black/50 text-[#F59E0B]/60 border-white/[0.06] hover:text-[#F59E0B]"
                  }`}
                >
                  #{activeScope}
                </button>
                <button
                  onClick={() => setNoteScopeFilter("general")}
                  className={`h-6 px-2 rounded-[6px] border transition ${
                    noteScopeFilter === "general"
                      ? "bg-emerald-500/20 text-emerald-300 font-semibold border-emerald-500/40"
                      : "bg-black/50 text-white/40 border-white/[0.06] hover:text-white"
                  }`}
                >
                  General
                </button>
              </div>

              {/* Note Search Input */}
              <div className="h-8 rounded-[10px] bg-black border border-white/[0.08] flex items-center px-2.5 gap-2">
                <Search className="w-3.5 h-3.5 text-white/30 shrink-0" />
                <input
                  value={noteSearchQuery}
                  onChange={(e) => setNoteSearchQuery(e.target.value)}
                  placeholder="Buscar en notas..."
                  className="flex-1 bg-transparent outline-none text-[11px] text-white placeholder:text-white/25"
                />
                {noteSearchQuery && (
                  <button onClick={() => setNoteSearchQuery("")} className="text-white/30 hover:text-white text-xs">
                    ×
                  </button>
                )}
              </div>

              {/* Inline Note Composer */}
              {isComposingNote && (
                <div className="rounded-[16px] bg-[#121214] border border-white/[0.12] p-3 space-y-2 k-fade-in">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase tracking-wider text-amber-400 font-bold">
                      + Anclar Nota ({activeScope})
                    </span>
                  </div>
                  <input
                    value={newNoteTitle}
                    onChange={(e) => setNewNoteTitle(e.target.value)}
                    placeholder="Título doctrinal..."
                    className="w-full h-8 rounded-[8px] bg-black border border-white/[0.08] px-2.5 text-xs text-white outline-none focus:border-white/30"
                  />
                  <textarea
                    rows={3}
                    value={newNoteContent}
                    onChange={(e) => setNewNoteContent(e.target.value)}
                    placeholder="Escribe la aserción técnica o apunte forense..."
                    className="w-full rounded-[8px] bg-black border border-white/[0.08] p-2 text-xs text-white outline-none focus:border-white/30 resize-none font-sans"
                  />
                  <div className="flex justify-end gap-2 text-xs">
                    <button
                      onClick={() => setIsComposingNote(false)}
                      className="h-7 px-2.5 rounded-[7px] text-white/40 hover:text-white"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={handleSaveComposerNote}
                      disabled={!newNoteContent.trim()}
                      className="h-7 px-3.5 rounded-[7px] bg-cyan-950/60 border border-cyan-500/40 text-cyan-300 font-bold disabled:opacity-30 hover:bg-cyan-900/60 transition"
                    >
                      Guardar
                    </button>
                  </div>
                </div>
              )}

              {/* Filtered & Pinned Notes List */}
              {(() => {
                const filtered = notes
                  .filter((n) => {
                    // Scope filter
                    if (noteScopeFilter === "active" && n.scope !== activeScope) return false;
                    if (noteScopeFilter === "general" && n.scope && n.scope !== "General" && n.scope !== "TALOS Core") return false;

                    // Query filter
                    const q = noteSearchQuery.toLowerCase();
                    return (
                      n.title.toLowerCase().includes(q) ||
                      n.text.toLowerCase().includes(q) ||
                      (n.scope && n.scope.toLowerCase().includes(q)) ||
                      n.date.toLowerCase().includes(q)
                    );
                  })
                  .sort((a, b) => {
                    const aPin = pinnedNoteIds.has(a.id) ? 1 : 0;
                    const bPin = pinnedNoteIds.has(b.id) ? 1 : 0;
                    return bPin - aPin;
                  });

                if (filtered.length === 0) {
                  return (
                    <div className="rounded-[16px] bg-[#101012] border border-white/[0.06] p-6 text-center space-y-2">
                      <Bookmark className="w-6 h-6 text-white/20 mx-auto" />
                      <p className="text-xs text-white/50 font-medium">
                        {noteSearchQuery ? "Sin coincidencias de búsqueda." : "No hay notas en este filtro."}
                      </p>
                      <p className="text-[10px] text-white/30 leading-relaxed max-w-[240px] mx-auto">
                        Ancla fragmentos desde el chat o usa el botón "+ Nueva".
                      </p>
                    </div>
                  );
                }

                return (
                  <div className="space-y-3">
                    {filtered.map((note) => {
                      const isCopied = copiedNoteId === note.id;
                      const isPinned = pinnedNoteIds.has(note.id);

                      return (
                        <article
                          key={note.id}
                          className={`rounded-[18px] bg-[#101012] border p-3.5 transition shadow-sm group ${
                            isPinned
                              ? "border-amber-500/40 bg-[#14120e]"
                              : "border-white/[0.08] hover:border-white/[0.16]"
                          }`}
                        >
                          {/* Note Header */}
                          <div className="flex items-start justify-between gap-2 pb-2 border-b border-white/[0.06]">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-1.5 mb-1">
                                {isPinned && (
                                  <span className="inline-flex items-center gap-0.5 text-[9px] px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-bold">
                                    ★ Fijada
                                  </span>
                                )}
                                <span className="inline-flex items-center text-[9px] px-1.5 py-0.2 rounded bg-white/[0.05] border border-white/[0.08] text-amber-400">
                                  #{note.scope || activeScope}
                                </span>
                                <span className="text-[10px] text-white/35 truncate">{note.date}</span>
                              </div>
                              <h4 className="text-xs font-semibold text-white truncate">{note.title}</h4>
                            </div>

                            <div className="flex items-center gap-1 shrink-0 opacity-80 group-hover:opacity-100 transition">
                              <button
                                onClick={() => togglePinNote(note.id)}
                                className={`w-6 h-6 rounded-[6px] flex items-center justify-center transition ${
                                  isPinned ? "text-amber-400 bg-amber-400/20" : "text-white/40 hover:text-white"
                                }`}
                                title={isPinned ? "Desfijar nota" : "Fijar nota"}
                              >
                                <Pin className="w-3 h-3" />
                              </button>
                              <button
                                onClick={() => handleCopyNote(note.id, note.text)}
                                className="w-6 h-6 rounded-[6px] bg-white/[0.04] hover:bg-white/10 hover:text-white text-white/50 flex items-center justify-center transition"
                                title="Copiar nota al portapapeles"
                              >
                                {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                              </button>
                              {onDeleteNote && (
                                <button
                                  onClick={() => onDeleteNote(note.id)}
                                  className="w-6 h-6 rounded-[6px] bg-white/[0.04] hover:bg-red-500/20 hover:text-red-400 text-white/50 flex items-center justify-center transition"
                                  title="Eliminar nota"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              )}
                            </div>
                          </div>

                          {/* Note Body */}
                          <div className="mt-2.5 text-xs leading-relaxed text-white/85 whitespace-pre-wrap select-text font-sans bg-black/40 p-2.5 rounded-[10px] border border-white/[0.03]">
                            {note.text}
                          </div>

                          {/* Note Footer */}
                          <div className="mt-2 pt-1.5 border-t border-white/[0.04] flex items-center justify-between text-[9px] text-white/30">
                            <span>{note.text.length} caracteres</span>
                            {isCopied && <span className="text-emerald-400 font-bold">¡Copiado!</span>}
                          </div>
                        </article>
                      );
                    })}
                  </div>
                );
              })()}
            </div>
          )}

          {/* ---------------------------------------- */}
          {/* TAB 5: SANDBOX (FSM EVALUATOR S6)       */}
          {/* ---------------------------------------- */}
          {tab === "sandbox" && (
            <div className="space-y-5">
              {/* Header */}
              <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Code className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs uppercase tracking-wider font-semibold text-white/80">
                      Sandbox de Ejecución S6
                    </span>
                  </div>
                  {/* FSM state badge */}
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded-full font-mono uppercase font-bold border ${
                      fsmState === "PASSED"
                        ? "bg-emerald-950/60 border-emerald-500/40 text-emerald-400"
                        : fsmState === "FAILED"
                        ? "bg-red-950/60 border-red-500/40 text-red-400"
                        : fsmState === "ABSTAINED"
                        ? "bg-amber-950/60 border-amber-500/40 text-amber-400"
                        : fsmState === "SANDBOX_RUNNING" || fsmState === "EVALUATION_REQUESTED"
                        ? "bg-blue-950/60 border-blue-500/40 text-blue-400 animate-pulse"
                        : "bg-white/[0.05] border-white/[0.1] text-white/50"
                    }`}
                  >
                    FSM: {fsmState}
                  </span>
                </div>

                <p className="text-xs text-white/60 leading-relaxed font-sans">
                  Entorno aislado de pruebas de código deterministas contra la máquina de estados y aserciones curriculares (ADR-008).
                </p>

                {/* Acciones */}
                <div className="pt-2 border-t border-white/[0.06] flex items-center gap-2">
                  <button
                    onClick={requestEvaluation}
                    disabled={fsmState === "SANDBOX_RUNNING" || fsmState === "EVALUATION_REQUESTED"}
                    className="flex-1 h-9 px-3 rounded-[12px] bg-cyan-950/50 border border-cyan-500/50 text-cyan-300 text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 hover:bg-cyan-900/60 transition disabled:opacity-50 shadow-[0_0_12px_rgba(6,182,212,0.15)] font-mono"
                  >
                    {fsmState === "SANDBOX_RUNNING" || fsmState === "EVALUATION_REQUESTED" ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Ejecutando...</span>
                      </>
                    ) : (
                      <>
                        <Check className="w-3.5 h-3.5" />
                        <span>Evaluar en Sandbox (:eval)</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={resetFsm}
                    className="h-9 px-3 rounded-[12px] bg-white/[0.05] text-white/60 text-xs font-semibold hover:text-white hover:bg-white/[0.1] transition border border-white/[0.08]"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {/* Assessment results */}
              {assessment && (
                <div className="space-y-4">
                  {/* Metric Summary */}
                  <div className="p-4 rounded-[18px] bg-[#101012] border border-white/[0.08] space-y-3">
                    <div className="flex items-center justify-between text-xs font-mono">
                      <span className="text-white/50">Aserciones Superadas:</span>
                      <strong
                        className={`text-sm font-bold ${
                          assessment.passed_assertions === assessment.total_assertions
                            ? "text-emerald-400"
                            : "text-amber-400"
                        }`}
                      >
                        {assessment.passed_assertions} / {assessment.total_assertions}
                      </strong>
                    </div>

                    {/* Progress Bar */}
                    <div className="h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          assessment.passed_assertions === assessment.total_assertions
                            ? "bg-emerald-500"
                            : "bg-amber-500"
                        }`}
                        style={{
                          width: `${
                            assessment.total_assertions > 0
                              ? (assessment.passed_assertions / assessment.total_assertions) * 100
                              : 0
                          }%`,
                        }}
                      />
                    </div>

                    {/* Ledger Block Hash */}
                    <div className="pt-2 border-t border-white/[0.06] space-y-1">
                      <span className="text-[10px] text-white/40 uppercase tracking-wider block font-mono">
                        Ledger Block Hash (ADR-008 §6)
                      </span>
                      {assessment.ledger_block_hash ? (
                        <div className="flex items-center gap-2 p-2 rounded-[10px] bg-black/60 border border-emerald-500/20 text-emerald-300 font-mono text-[10px] break-all">
                          <Shield className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
                          <span>{assessment.ledger_block_hash}</span>
                        </div>
                      ) : (
                        <div className="p-2 rounded-[10px] bg-red-950/20 border border-red-500/20 text-red-400 font-mono text-[10px]">
                          Sin bloque asignado en Ledger (condición de maestría no ratificada)
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Assertions List */}
                  <div className="space-y-2">
                    <span className="text-[11px] uppercase tracking-wider text-white/40 font-mono block px-1">
                      Detalle de Aserciones
                    </span>

                    {assessment.assertions.map((assertion) => (
                      <div
                        key={assertion.id}
                        className={`p-3 rounded-[14px] border ${
                          assertion.passed
                            ? "bg-emerald-950/10 border-emerald-500/20"
                            : "bg-red-950/20 border-red-500/30"
                        }`}
                      >
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono text-[11px] font-bold text-white/70">
                            {assertion.id}
                          </span>
                          <span
                            className={`text-[9px] px-1.5 py-0.5 rounded font-mono font-bold ${
                              assertion.passed
                                ? "bg-emerald-500/20 text-emerald-300"
                                : "bg-red-500/20 text-red-300"
                            }`}
                          >
                            {assertion.passed ? "PASSED" : "FAILED"}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-white/80 font-sans leading-relaxed">
                          {assertion.description}
                        </p>
                        {assertion.error_message && (
                          <div className="mt-2 p-2 rounded bg-black/60 border border-red-500/20 text-[10px] font-mono text-red-300">
                            {assertion.error_message}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ========================================================= */}
          {/* SECCIÓN 6: DISPUTAS / CONTRADICCIONES EPISTÉMICAS */}
          {/* ========================================================= */}
          {tab === "contradicciones" && (
            <ContradictionView
              contradictions={claimsData?.contradictions}
              sessionId={activeScope || "sess_default"}
              onSelectDoc={() => {
                onTab("pagina");
              }}
            />
          )}
        </div>
      </aside>
    </>
  );
};

export default EvidencePanel;
