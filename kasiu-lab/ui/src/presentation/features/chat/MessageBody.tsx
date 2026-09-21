import React, { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { AlertTriangle, BookOpen, ExternalLink, FileText, Shield } from "lucide-react";
import { Citation, EvidenceTab } from "../views/types";
import { CodeBlock } from "./components/CodeBlock";
import { MermaidBlock } from "./components/MermaidBlock";

export interface MessageBodyProps {
  content: string;
  evidences?: Citation[];
  onOpenEvidence?: (tab: EvidenceTab, docHash?: string, page?: number, citation?: Citation) => void;
  onOpenCitation?: (citation: Citation) => void;
  className?: string;
}

interface CitationChipWithPopoverProps {
  citation: Citation;
  displayTag: string;
  onOpenEvidence?: (tab: EvidenceTab, docHash?: string, page?: number, citation?: Citation) => void;
  onOpenCitation?: (citation: Citation) => void;
}

const CitationChipWithPopover: React.FC<CitationChipWithPopoverProps> = ({
  citation,
  displayTag,
  onOpenEvidence,
  onOpenCitation,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isOpeningPdf, setIsOpeningPdf] = useState(false);

  const titleText = citation.source_title || citation.sourceTitle || citation.source_id || "Fuente canónica";
  const authorText = citation.author || "";
  const pageNum = citation.page || citation.pageStart || 1;
  const docHash = citation.docHash || "";
  const excerpt = citation.chunk_text || citation.chunkText || "";
  const epistemicRole = (citation.epistemic_role || citation.epistemicRole || "pedagogical").toLowerCase();

  const roleStyles: Record<string, { label: string; color: string }> = {
    pedagogical: { label: "Pedagógico", color: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40" },
    formal: { label: "Formal", color: "bg-indigo-500/20 text-indigo-300 border-indigo-500/40" },
    technical: { label: "Técnico", color: "bg-amber-500/20 text-amber-300 border-amber-500/40" },
  };
  const roleInfo = roleStyles[epistemicRole] || roleStyles.pedagogical;

  const handleOpenPdf = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!docHash) return;
    setIsOpeningPdf(true);
    try {
      await fetch(`/api/evidence/open-local-pdf?hash=${encodeURIComponent(docHash)}&page=${pageNum}`);
    } catch (err) {
      console.error("Fallo al abrir PDF local:", err);
    } finally {
      setIsOpeningPdf(false);
    }
  };

  const handleOpenPanel = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onOpenCitation) {
      onOpenCitation(citation);
    } else if (onOpenEvidence) {
      onOpenEvidence("evidencia", docHash || undefined, pageNum, citation);
    }
  };

  return (
    <span
      className="relative inline-block align-baseline group"
      onMouseEnter={() => setIsOpen(true)}
      onMouseLeave={() => setIsOpen(false)}
    >
      <button
        type="button"
        onClick={handleOpenPanel}
        className="citation-chip cursor-pointer focus:outline-none focus:ring-1 focus:ring-cyan-400"
      >
        <BookOpen className="w-3 h-3 shrink-0 opacity-80" />
        <span>[{displayTag}]</span>
        {pageNum ? <span className="text-[9.5px] opacity-70">p.{pageNum}</span> : null}
      </button>

      {/* Popover Card */}
      {isOpen && (
        <div
          onClick={(e) => e.stopPropagation()}
          className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 sm:w-80 p-3 rounded-[16px] bg-[#0d0d11]/95 backdrop-blur-md border border-cyan-500/30 shadow-[0_10px_35px_rgba(0,0,0,0.8)] text-left font-mono text-xs space-y-2 pointer-events-auto"
        >
          {/* Header */}
          <div className="flex items-start justify-between gap-2 border-b border-white/[0.08] pb-1.5">
            <div className="min-w-0">
              {authorText ? (
                <span className="text-[10px] text-cyan-300 font-semibold truncate block">
                  {authorText}
                </span>
              ) : null}
              <span className="text-white text-[11px] font-medium leading-tight line-clamp-1 block" title={titleText}>
                {titleText}
              </span>
            </div>
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold border shrink-0 ${roleInfo.color}`}>
              {roleInfo.label}
            </span>
          </div>

          {/* Meta: Página y SHA */}
          <div className="flex items-center justify-between text-[10px] text-white/50">
            <span className="flex items-center gap-1 text-cyan-300">
              <FileText className="w-3 h-3" />
              Página {pageNum}
            </span>
            {docHash ? (
              <span className="truncate max-w-[120px]" title={docHash}>
                SHA: {docHash.slice(0, 8)}...
              </span>
            ) : null}
          </div>

          {/* Excerpt Fragment */}
          {excerpt ? (
            <div className="p-2 rounded-[8px] bg-black/60 border border-white/[0.06] text-[11px] text-white/80 leading-relaxed max-h-24 overflow-y-auto k-scroll italic">
              "{excerpt.length > 200 ? excerpt.slice(0, 200) + "..." : excerpt}"
            </div>
          ) : null}

          {/* Botones de acción */}
          <div className="flex items-center gap-1.5 pt-1">
            {docHash ? (
              <button
                type="button"
                onClick={handleOpenPdf}
                disabled={isOpeningPdf}
                className="flex-1 px-2 py-1 rounded-[8px] bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 text-[10.5px] font-semibold flex items-center justify-center gap-1 transition"
              >
                <ExternalLink className="w-3 h-3" />
                <span>{isOpeningPdf ? "Abriendo..." : "Abrir PDF"}</span>
              </button>
            ) : null}
            <button
              type="button"
              onClick={handleOpenPanel}
              className="flex-1 px-2 py-1 rounded-[8px] bg-white/[0.05] hover:bg-white/[0.1] text-white/80 border border-white/[0.1] text-[10.5px] font-semibold flex items-center justify-center gap-1 transition"
            >
              <BookOpen className="w-3 h-3" />
              <span>Ver en Panel</span>
            </button>
          </div>
        </div>
      )}
    </span>
  );
};

/**
 * Replaces citation markers ([E#], [TF#], [LAB#], [1], [2], [SIN_RESPALDO]) in text nodes with interactive React badges.
 */
function processCitations(
  node: React.ReactNode,
  evidences?: Citation[],
  onOpenEvidence?: (tab: EvidenceTab, docHash?: string, page?: number, citation?: Citation) => void,
  onOpenCitation?: (citation: Citation) => void
): React.ReactNode {
  if (typeof node === "string") {
    const regex = /\[((?:E|TF|LAB)?\d+)\]|(\[SIN_RESPALDO\])/g;
    const parts: React.ReactNode[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(node)) !== null) {
      if (match.index > lastIndex) {
        parts.push(node.substring(lastIndex, match.index));
      }

      if (match[2]) {
        // H4 Redaction: Aserción no respaldada por el corpus
        parts.push(
          <span
            key={`sin-respaldo-${match.index}`}
            className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-[8px] text-[10.5px] font-mono bg-rose-500/20 text-rose-300 border border-rose-500/40 font-bold tracking-wider select-none align-baseline"
            title="Aserción excluida de autoridad por carecer de respaldo verificado en el corpus (ADR-008 H4 Redaction)"
          >
            <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />
            [SIN_RESPALDO]
          </span>
        );
        lastIndex = regex.lastIndex;
        continue;
      }

      const citationTag = match[0];
      const rawCitationId = match[1];
      const numVal = parseInt(rawCitationId.replace(/\D/g, ""), 10);

      const citation = evidences?.find((e, idx) => {
        if (!e) return false;
        const eId = (e.id || "").toLowerCase();
        const cId = (e.citationId || "").toLowerCase();
        const targetLower = rawCitationId.toLowerCase();
        const eNum = parseInt(eId.replace(/\D/g, ""), 10);
        const cNum = parseInt(cId.replace(/\D/g, ""), 10);

        return (
          eId === targetLower ||
          cId === targetLower ||
          eId === `e${targetLower}` ||
          cId === `e${targetLower}` ||
          (numVal > 0 && (eNum === numVal || cNum === numVal || idx === numVal - 1))
        );
      });

      if (citation && citation.namespace === "TF") {
        // Aislamiento FV-2: Namespace [TF#] -> Threat Intel externo (unverified)
        parts.push(
          <span
            key={`tf-${match.index}`}
            className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded text-[11px] font-mono bg-rose-500/15 text-rose-300 border border-rose-500/30 select-none align-baseline"
            title="Threat Intelligence Feed: Evidencia no curricular externa (unverified)"
          >
            <Shield className="w-3 h-3 text-rose-400 shrink-0" />
            {citationTag}
            <span className="text-[9px] uppercase tracking-wider text-rose-400 font-bold ml-0.5">unverified</span>
          </span>
        );
      } else if (citation) {
        // Cita canónica con metadata enriquecida: popover y botón interactivo
        parts.push(
          <CitationChipWithPopover
            key={`cit-${match.index}`}
            citation={citation}
            displayTag={rawCitationId}
            onOpenEvidence={onOpenEvidence}
            onOpenCitation={onOpenCitation}
          />
        );
      } else {
        // Cita presente en texto pero sin provenance vinculada aún: botón interactivo de consulta
        parts.push(
          <button
            key={`raw-${match.index}`}
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              if (onOpenEvidence) {
                onOpenEvidence("evidencia");
              }
            }}
            className="citation-chip opacity-85"
            title={`Cita documental ${citationTag}`}
          >
            <BookOpen className="w-3 h-3 shrink-0 opacity-70" />
            <span>{citationTag}</span>
          </button>
        );
      }

      lastIndex = regex.lastIndex;
    }

    if (lastIndex < node.length) {
      parts.push(node.substring(lastIndex));
    }

    return parts.length > 0 ? parts : node;
  }

  if (Array.isArray(node)) {
    return node.flatMap((child) => processCitations(child, evidences, onOpenEvidence, onOpenCitation));
  }

  if (React.isValidElement(node)) {
    const props = node.props as { className?: string; children?: React.ReactNode };
    const className = props?.className;

    // CRÍTICO: Si el nodo pertenece a KaTeX (fórmula matemática), NO manipular su árbol DOM interno.
    if (
      typeof className === "string" &&
      (className.includes("katex") ||
        className.includes("katex-html") ||
        className.includes("katex-mathml") ||
        className.includes("katex-display") ||
        className.includes("math-display") ||
        className.includes("math-inline"))
    ) {
      return node;
    }

    if (props && props.children) {
      return React.cloneElement(
        node,
        { ...props },
        processCitations(props.children, evidences, onOpenEvidence, onOpenCitation)
      );
    }
  }

  return node;
}


export const MessageBody: React.FC<MessageBodyProps> = ({
  content,
  evidences,
  onOpenEvidence,
  onOpenCitation,
  className = "",
}) => {
  // Pre-procesamiento de delimitadores matemáticos:
  // 1. Normaliza delimitadores LaTeX estándar \[ ... \] y \( ... \) a $$ y $
  // 2. Aísla bloques de doble signo de dólar ($$ ... $$) con saltos de línea limpios
  //    para garantizar que remark-math active 'math' (displayMode: true) en lugar de inline.
  const normalizedContent = useMemo(() => {
    if (!content) return "";
    let formatted = content;

    // Normalizar \[ ... \] a $$ ... $$
    formatted = formatted.replace(/\\\[([\s\S]*?)\\\]/g, (_, eq) => `\n\n$$\n${eq.trim()}\n$$\n\n`);
    // Normalizar \( ... \) a $ ... $
    formatted = formatted.replace(/\\\(([\s\S]*?)\\\)/g, (_, eq) => `$${eq.trim()}$`);

    // Asegurar que $$ tenga saltos de línea para activar displayMode
    formatted = formatted.replace(/(^|[^\n])\n*\$\$\s*([\s\S]*?)\s*\$\$\n*([^\n]|$)/g, (_, before, math, after) => {
      const b = before ? `${before}\n\n` : "";
      const a = after ? `\n\n${after}` : "";
      return `${b}$$\n${math.trim()}\n$$${a}`;
    });

    return formatted;
  }, [content]);

  // CRÍTICO: useMemo evita que ReactMarkdown reconstruya y re-parsee el AST completo
  // en cada render. Sin esto, cada actualización de estado del padre (streaming, scroll,
  // etc.) causaba que cada mensaje re-parseara su markdown desde cero.
  const components = useMemo(() => ({
    p: ({ children }: { children?: React.ReactNode }) => (
      <p className="my-2.5 font-sans text-[15px] md:text-base leading-[1.8] text-neutral-200 selection:bg-amber-400 selection:text-black">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </p>
    ),
    h1: ({ children }: { children?: React.ReactNode }) => (
      <h1 className="text-xl md:text-2xl font-sans font-bold text-white mt-6 mb-3 tracking-tight border-b border-white/[0.08] pb-2">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </h1>
    ),
    h2: ({ children }: { children?: React.ReactNode }) => (
      <h2 className="text-lg md:text-xl font-sans font-semibold text-white mt-5 mb-2.5 tracking-tight border-b border-white/[0.06] pb-1.5">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </h2>
    ),
    h3: ({ children }: { children?: React.ReactNode }) => (
      <h3 className="text-base md:text-lg font-sans font-semibold text-cyan-200 mt-4 mb-2">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </h3>
    ),
    h4: ({ children }: { children?: React.ReactNode }) => (
      <h4 className="text-sm md:text-base font-sans font-semibold text-amber-300/90 mt-3 mb-1.5">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </h4>
    ),
    ul: ({ children }: { children?: React.ReactNode }) => (
      <ul className="styled-list list-disc list-outside ml-6 my-2.5 space-y-1.5 font-sans text-neutral-200">
        {children}
      </ul>
    ),
    ol: ({ children }: { children?: React.ReactNode }) => (
      <ol className="styled-list ordered list-decimal list-outside ml-6 my-2.5 space-y-1.5 font-sans text-neutral-200">
        {children}
      </ol>
    ),
    li: ({ children }: { children?: React.ReactNode }) => (
      <li className="text-[15px] md:text-base leading-relaxed pl-1 text-neutral-200">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </li>
    ),
    blockquote: ({ children }: { children?: React.ReactNode }) => (
      <blockquote className="my-3 pl-4 border-l-2 border-amber-400/60 bg-amber-500/[0.03] py-1.5 text-white/80 italic rounded-r-[8px]">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </blockquote>
    ),
    strong: ({ children }: { children?: React.ReactNode }) => (
      <strong className="font-semibold text-white">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </strong>
    ),
    em: ({ children }: { children?: React.ReactNode }) => (
      <em className="italic text-neutral-300">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </em>
    ),
    hr: () => (
      <div className="my-6 relative flex items-center justify-center">
        <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-white/[0.14] to-transparent" />
      </div>
    ),
    table: ({ children }: { children?: React.ReactNode }) => (
      <div className="table-wrapper my-4 overflow-x-auto talos-scroll rounded-[12px] border border-white/[0.08]">
        <table className="styled-table w-full text-left font-sans text-xs md:text-sm border-collapse">
          {children}
        </table>
      </div>
    ),
    thead: ({ children }: { children?: React.ReactNode }) => (
      <thead className="bg-white/[0.04] border-b border-white/[0.08] text-white/70 uppercase text-[11px] font-mono tracking-wider">
        {children}
      </thead>
    ),
    th: ({ children }: { children?: React.ReactNode }) => (
      <th className="px-3.5 py-2.5 font-semibold text-white/90">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </th>
    ),
    td: ({ children }: { children?: React.ReactNode }) => (
      <td className="px-3.5 py-2 border-t border-white/[0.04] text-neutral-300">
        {processCitations(children, evidences, onOpenEvidence, onOpenCitation)}
      </td>
    ),
    code: ({
      className,
      children,
      ...props
    }: React.HTMLAttributes<HTMLElement> & { className?: string; children?: React.ReactNode }) => {
      const match = /language-(\w+)/.exec(className || "");
      const lang = (match ? match[1] : "").toLowerCase();
      const codeString = String(children || "");
      const isMultiline = codeString.includes("\n");
      const isCodeBlock = Boolean(match || isMultiline);

      if (!isCodeBlock) {
        return (
          <code
            className="inline-code font-mono text-amber-300 bg-[#141416] border border-white/[0.08] px-1.5 py-0.5 rounded text-[13px] font-medium"
            {...props}
          >
            {children}
          </code>
        );
      }

      // Diagramas Mermaid: Renderizado gráfico visual e interactivo
      if (lang === "mermaid") {
        return <MermaidBlock code={codeString} />;
      }

      return (
        <CodeBlock language={match ? match[1] : undefined}>
          {codeString}
        </CodeBlock>
      );
    },
  }), [evidences, onOpenEvidence, onOpenCitation]);

  return (
    <div className={`markdown-content font-sans text-sm md:text-base leading-relaxed text-neutral-200 max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[
          [
            rehypeKatex,
            {
              output: "htmlAndMathml",
              strict: false,
              throwOnError: false,
            },
          ],
        ]}
        components={components}
      >
        {normalizedContent}
      </ReactMarkdown>
    </div>
  );
};

export const MemoizedMessageBody = React.memo(MessageBody);
export default MemoizedMessageBody;
