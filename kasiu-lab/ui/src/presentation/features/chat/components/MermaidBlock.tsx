import React, { useEffect, useState, useRef, useMemo } from "react";
import mermaid from "mermaid";
import {
  Check,
  Copy,
  Eye,
  Code2,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  AlertTriangle,
  Download,
  Maximize2,
  Minimize2,
  GitBranch,
} from "lucide-react";

// Inicialización de Mermaid con tema oscuro táctico y cálculo adaptativo de cajas
mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  fontSize: 12,
  fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
  htmlLabels: true,
  flowchart: {
    htmlLabels: true,
    padding: 24, // Respiración generosa entre el texto y el borde de la caja
    nodeSpacing: 50,
    rankSpacing: 50,
    curve: "basis",
    useMaxWidth: false,
  },
  themeVariables: {
    darkMode: true,
    fontSize: "12px",
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    background: "#0c0d12",
    mainBkg: "#12141d",
    nodeBorder: "#06b6d4",
    primaryColor: "#111827",
    primaryTextColor: "#f1f5f9",
    primaryBorderColor: "#0284c7",
    lineColor: "#38bdf8",
    secondaryColor: "#1e1b4b",
    tertiaryColor: "#0f172a",
    clusterBkg: "#09090e",
    clusterBorder: "#334155",
    titleColor: "#38bdf8",
    edgeLabelBackground: "#1e293b",
    actorBkg: "#12141d",
    actorBorder: "#06b6d4",
    actorTextColor: "#f1f5f9",
    signalColor: "#38bdf8",
    signalTextColor: "#f1f5f9",
  },
  securityLevel: "loose",
});

interface MermaidBlockProps {
  code: string;
}

/**
 * Sanitiza etiquetas de nodos para asegurar que caracteres especiales (paréntesis, flechas, signos)
 * estén entre comillas dobles y no rompan el parser de Mermaid.
 */
function sanitizeMermaidCode(raw: string): string {
  let clean = raw
    .trim()
    .replace(/^```(?:mermaid)?\r?\n?/, "")
    .replace(/\r?\n?```$/, "")
    .trim();

  // 1. Sanitizar nodos rectangulares con caracteres especiales no entrecomillados: id[Texto con () o : o <] -> id["Texto con () o : o <"]
  clean = clean.replace(/(\b[\w-]+)\[([^\]\n"]*[()<>:][^\]\n"]*)\]/g, '$1["$2"]');

  // 2. Sanitizar nodos rombo / decisión con caracteres especiales: id{Texto con () o ? o <} -> id["Texto con () o ? o <"]
  clean = clean.replace(/(\b[\w-]+)\{([^\}\n"]*[()<>=?:\/][^\}\n"]*)\}/g, '$1["$2"]');

  return clean;
}

export const MermaidBlock: React.FC<MermaidBlockProps> = ({ code }) => {
  const [svgContent, setSvgContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [isRendering, setIsRendering] = useState<boolean>(true);
  const [viewMode, setViewMode] = useState<"diagram" | "code">("diagram");
  const [zoom, setZoom] = useState<number>(1);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);

  const cleanCode = useMemo(() => sanitizeMermaidCode(code), [code]);

  useEffect(() => {
    let isMounted = true;
    const renderDiagram = async () => {
      if (!cleanCode) return;
      setIsRendering(true);
      setError(null);

      // Generar ID único válido para el SVG
      const renderId = "mermaid_" + Math.random().toString(36).substring(2, 10);

      try {
        const prevErr = document.getElementById("d" + renderId);
        if (prevErr) prevErr.remove();

        const { svg } = await mermaid.render(renderId, cleanCode);
        if (isMounted) {
          setSvgContent(svg);
          setError(null);
          setIsRendering(false);
        }
      } catch (err: any) {
        console.warn("Mermaid render error:", err);
        const injectedErr = document.getElementById("d" + renderId);
        if (injectedErr) injectedErr.remove();
        const injectedEl = document.getElementById(renderId);
        if (injectedEl) injectedEl.remove();

        if (isMounted) {
          setError(err?.message || "Error al renderizar el diagrama de flujo");
          setIsRendering(false);
          setViewMode("code");
        }
      }
    };

    renderDiagram();

    return () => {
      isMounted = false;
    };
  }, [cleanCode]);

  // Post-procesador dinámico en el DOM: garantiza que todas las cajas (rectángulos y rombos)
  // se adapten matemáticamente al ancho y alto real del texto renderizado sin cortes ni desbordes.
  useEffect(() => {
    if (!svgContent || viewMode !== "diagram") return;

    const rafId = requestAnimationFrame(() => {
      if (!containerRef.current) return;
      const svgEl = containerRef.current.querySelector("svg");
      if (!svgEl) return;

      const nodes = svgEl.querySelectorAll<SVGGElement>(".node");
      nodes.forEach((node) => {
        const foreignObj = node.querySelector<SVGForeignObjectElement>("foreignObject");
        const labelEl =
          foreignObj?.querySelector<HTMLElement>("div, span") ||
          node.querySelector<SVGTextElement>("text, .nodeLabel, .label");
        const rect = node.querySelector<SVGRectElement>("rect");
        const polygon = node.querySelector<SVGPolygonElement>("polygon");

        if (!labelEl) return;

        const textBBox = labelEl.getBoundingClientRect();
        if (textBBox.width === 0 || textBBox.height === 0) return;

        // Margen de seguridad para adaptación visual perfecta
        const padX = 28; // 14px a cada lado
        const padY = 18; // 9px arriba y abajo
        const targetW = Math.ceil(textBBox.width + padX);
        const targetH = Math.ceil(textBBox.height + padY);

        // 1. Adaptación de Cajas Rectangulares
        if (rect) {
          const currentW = parseFloat(rect.getAttribute("width") || "0");
          const currentH = parseFloat(rect.getAttribute("height") || "0");

          if (currentW < targetW || currentH < targetH) {
            const finalW = Math.max(currentW, targetW);
            const finalH = Math.max(currentH, targetH);

            rect.setAttribute("width", finalW.toString());
            rect.setAttribute("height", finalH.toString());
            rect.setAttribute("x", (-finalW / 2).toString());
            rect.setAttribute("y", (-finalH / 2).toString());

            if (foreignObj) {
              foreignObj.setAttribute("width", finalW.toString());
              foreignObj.setAttribute("height", finalH.toString());
              foreignObj.setAttribute("x", (-finalW / 2).toString());
              foreignObj.setAttribute("y", (-finalH / 2).toString());
            }
          }
        }

        // 2. Adaptación de Rombos de Decisión
        if (polygon) {
          // En un rombo, las diagonales restringen el área rectangular interna.
          // Para que el texto no toque las esquinas, dimensionamos los vértices proporcionalmente:
          const diamondW = Math.max(targetW * 1.35, targetH * 2.2, 90);
          const diamondH = Math.max(targetH * 1.65, 48);

          const points = `0,${-diamondH / 2} ${diamondW / 2},0 0,${diamondH / 2} ${-diamondW / 2},0`;
          polygon.setAttribute("points", points);

          if (foreignObj) {
            foreignObj.setAttribute("width", diamondW.toString());
            foreignObj.setAttribute("height", diamondH.toString());
            foreignObj.setAttribute("x", (-diamondW / 2).toString());
            foreignObj.setAttribute("y", (-diamondH / 2).toString());
          }
        }
      });
    });

    return () => cancelAnimationFrame(rafId);
  }, [svgContent, viewMode, zoom]);

  const handleCopy = () => {
    navigator.clipboard.writeText(cleanCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadSvg = () => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `diagrama_talos_${Date.now()}.svg`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleZoomIn = () => setZoom((z) => Math.min(2.5, +(z + 0.2).toFixed(1)));
  const handleZoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.2).toFixed(1)));
  const handleZoomReset = () => setZoom(1);

  return (
    <div
      className={`my-4 rounded-[14px] bg-[#090a0f] border border-cyan-500/25 overflow-hidden font-mono shadow-xl transition-all ${
        isExpanded ? "fixed inset-4 z-50 flex flex-col bg-[#07080c]/98 border-cyan-400 shadow-[0_0_50px_rgba(0,0,0,0.9)]" : ""
      }`}
    >
      {/* Barra de Controles Superior */}
      <div className="flex flex-wrap items-center justify-between px-3.5 py-2 bg-black/70 border-b border-white/[0.08] gap-2 text-xs">
        {/* Identificador de tipo */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 font-bold text-[11px] tracking-wide">
            <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
            <span>DIAGRAMA DE FLUJO</span>
          </div>

          {/* Toggle Gráfico / Código */}
          <div className="flex items-center bg-white/[0.05] p-0.5 rounded-lg border border-white/[0.08]">
            <button
              type="button"
              onClick={() => setViewMode("diagram")}
              disabled={Boolean(error)}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[10.5px] font-medium transition ${
                viewMode === "diagram"
                  ? "bg-cyan-500/25 text-cyan-200 shadow-sm border border-cyan-500/40"
                  : "text-white/50 hover:text-white/80"
              } ${error ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}
              title="Ver gráfico visual interactivo"
            >
              <Eye className="w-3 h-3" />
              <span>Gráfico</span>
            </button>
            <button
              type="button"
              onClick={() => setViewMode("code")}
              className={`flex items-center gap-1 px-2 py-1 rounded text-[10.5px] font-medium transition ${
                viewMode === "code"
                  ? "bg-cyan-500/25 text-cyan-200 shadow-sm border border-cyan-500/40"
                  : "text-white/50 hover:text-white/80"
              } cursor-pointer`}
              title="Ver código fuente Mermaid"
            >
              <Code2 className="w-3 h-3" />
              <span>Código</span>
            </button>
          </div>
        </div>

        {/* Acciones del diagrama */}
        <div className="flex items-center gap-1 text-[11px]">
          {viewMode === "diagram" && !error && (
            <>
              {/* Controles de Zoom */}
              <div className="flex items-center bg-white/[0.04] rounded border border-white/[0.06] mr-1">
                <button
                  type="button"
                  onClick={handleZoomOut}
                  disabled={zoom <= 0.5}
                  className="p-1 hover:bg-white/[0.08] text-white/70 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Alejar (-)"
                >
                  <ZoomOut className="w-3 h-3" />
                </button>
                <span className="px-1.5 text-[10px] text-white/60 font-mono select-none">
                  {Math.round(zoom * 100)}%
                </span>
                <button
                  type="button"
                  onClick={handleZoomIn}
                  disabled={zoom >= 2.5}
                  className="p-1 hover:bg-white/[0.08] text-white/70 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition"
                  title="Acercar (+)"
                >
                  <ZoomIn className="w-3 h-3" />
                </button>
                <button
                  type="button"
                  onClick={handleZoomReset}
                  className="p-1 hover:bg-white/[0.08] text-white/50 hover:text-white transition border-l border-white/[0.06]"
                  title="Restablecer escala (100%)"
                >
                  <RotateCcw className="w-2.5 h-2.5" />
                </button>
              </div>

              {/* Botón Descargar SVG */}
              <button
                type="button"
                onClick={handleDownloadSvg}
                className="p-1.5 rounded bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.08] text-white/70 hover:text-cyan-300 transition"
                title="Descargar diagrama en formato vectorial (.svg)"
              >
                <Download className="w-3 h-3" />
              </button>

              {/* Botón Pantalla Completa / Expandir */}
              <button
                type="button"
                onClick={() => setIsExpanded(!isExpanded)}
                className="p-1.5 rounded bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.08] text-white/70 hover:text-cyan-300 transition"
                title={isExpanded ? "Minimizar vista" : "Pantalla completa"}
              >
                {isExpanded ? <Minimize2 className="w-3 h-3" /> : <Maximize2 className="w-3 h-3" />}
              </button>
            </>
          )}

          {/* Botón Copiar */}
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 rounded bg-white/[0.04] border border-white/[0.06] hover:bg-white/[0.1] hover:text-white transition text-white/70 text-[10.5px]"
            title="Copiar definición Mermaid al portapapeles"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? "Copiado" : "Copiar"}</span>
          </button>
        </div>
      </div>

      {/* Contenido: Diagrama o Código */}
      <div className={`relative ${isExpanded ? "flex-1 overflow-hidden flex flex-col" : ""}`}>
        {viewMode === "diagram" ? (
          <div
            ref={containerRef}
            className={`p-6 overflow-auto talos-scroll flex items-center justify-center min-h-[220px] bg-[#090a10] ${
              isExpanded ? "flex-1" : "max-h-[550px]"
            }`}
          >
            {isRendering ? (
              <div className="flex items-center gap-2 text-cyan-300/70 text-xs font-mono">
                <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                <span>Renderizando diagrama de flujo...</span>
              </div>
            ) : error ? (
              <div className="p-4 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs max-w-md text-center space-y-2">
                <div className="flex items-center justify-center gap-1.5 font-bold text-rose-400">
                  <AlertTriangle className="w-4 h-4" />
                  <span>Error en sintaxis Mermaid</span>
                </div>
                <p className="text-[11px] text-white/70">{error}</p>
                <button
                  type="button"
                  onClick={() => setViewMode("code")}
                  className="px-2.5 py-1 rounded bg-white/[0.06] hover:bg-white/[0.12] text-white text-[11px] font-medium transition"
                >
                  Ver código crudo
                </button>
              </div>
            ) : (
              <div
                className="mermaid-svg-wrapper inline-block transition-transform duration-150 origin-center"
                style={{
                  transform: `scale(${zoom})`,
                  transformOrigin: "center center",
                }}
                dangerouslySetInnerHTML={{ __html: svgContent }}
              />
            )}
          </div>
        ) : (
          /* Vista de Código */
          <pre
            className={`p-4 overflow-auto talos-scroll font-mono text-xs text-cyan-200/90 leading-relaxed bg-[#08090d] select-text ${
              isExpanded ? "flex-1" : "max-h-[450px]"
            }`}
          >
            <code>{cleanCode}</code>
          </pre>
        )}
      </div>

      {/* Pie de diagrama */}
      {!isExpanded && viewMode === "diagram" && !error && (
        <div className="px-3.5 py-1 bg-black/40 border-t border-white/[0.04] text-[10px] text-white/40 flex items-center justify-between select-none">
          <span>Vista vectorial interactiva adaptativa</span>
          <span>Hacé zoom o cambiá a "Código" para editar/copiar</span>
        </div>
      )}
    </div>
  );
};

export default MermaidBlock;
