import React, { useMemo, useState } from "react";
import Prism from "prismjs";
import { Check, Copy, Code2, ChevronDown, ChevronUp } from "lucide-react";

// Cargar gramáticas de lenguajes esenciales para ingeniería y pedagogía
import "prismjs/components/prism-python";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-c";
import "prismjs/components/prism-cpp";
import "prismjs/components/prism-sql";
import "prismjs/components/prism-json";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-markdown";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-diff";

export interface CodeBlockProps {
  language?: string;
  children: React.ReactNode;
}

// Normalizar identificadores comunes de lenguaje a gramáticas de Prism
const normalizeLanguage = (lang?: string): { prismLang: string; displayLabel: string; badgeColor: string } => {
  if (!lang) {
    return {
      prismLang: "text",
      displayLabel: "TEXTO",
      badgeColor: "bg-white/[0.08] text-white/70 border-white/[0.1]",
    };
  }

  const l = lang.toLowerCase().trim();

  if (["python", "py"].includes(l)) {
    return {
      prismLang: "python",
      displayLabel: "PYTHON",
      badgeColor: "bg-sky-500/15 text-sky-300 border-sky-500/35",
    };
  }
  if (["pytest"].includes(l)) {
    return {
      prismLang: "python",
      displayLabel: "PYTEST",
      badgeColor: "bg-emerald-500/15 text-emerald-300 border-emerald-500/35",
    };
  }
  if (["sh", "bash", "shell", "zsh", "console"].includes(l)) {
    return {
      prismLang: "bash",
      displayLabel: "BASH / SHELL",
      badgeColor: "bg-emerald-500/15 text-emerald-300 border-emerald-500/35",
    };
  }
  if (["c"].includes(l)) {
    return {
      prismLang: "c",
      displayLabel: "C",
      badgeColor: "bg-purple-500/15 text-purple-300 border-purple-500/35",
    };
  }
  if (["cpp", "c++"].includes(l)) {
    return {
      prismLang: "cpp",
      displayLabel: "C++",
      badgeColor: "bg-purple-500/15 text-purple-300 border-purple-500/35",
    };
  }
  if (["sql"].includes(l)) {
    return {
      prismLang: "sql",
      displayLabel: "SQL",
      badgeColor: "bg-amber-500/15 text-amber-300 border-amber-500/35",
    };
  }
  if (["pseudo", "pseudocodigo", "pseudocódigo", "algoritmo"].includes(l)) {
    return {
      prismLang: "python",
      displayLabel: "PSEUDOCÓDIGO",
      badgeColor: "bg-indigo-500/15 text-indigo-300 border-indigo-500/35",
    };
  }
  if (["json"].includes(l)) {
    return {
      prismLang: "json",
      displayLabel: "JSON",
      badgeColor: "bg-teal-500/15 text-teal-300 border-teal-500/35",
    };
  }
  if (["yml", "yaml"].includes(l)) {
    return {
      prismLang: "yaml",
      displayLabel: "YAML",
      badgeColor: "bg-teal-500/15 text-teal-300 border-teal-500/35",
    };
  }
  if (["ts", "typescript"].includes(l)) {
    return {
      prismLang: "typescript",
      displayLabel: "TYPESCRIPT",
      badgeColor: "bg-blue-500/15 text-blue-300 border-blue-500/35",
    };
  }
  if (["js", "javascript"].includes(l)) {
    return {
      prismLang: "javascript",
      displayLabel: "JAVASCRIPT",
      badgeColor: "bg-yellow-500/15 text-yellow-300 border-yellow-500/35",
    };
  }
  if (["diff"].includes(l)) {
    return {
      prismLang: "diff",
      displayLabel: "DIFF",
      badgeColor: "bg-rose-500/15 text-rose-300 border-rose-500/35",
    };
  }
  if (["md", "markdown"].includes(l)) {
    return {
      prismLang: "markdown",
      displayLabel: "MARKDOWN",
      badgeColor: "bg-white/[0.08] text-white/70 border-white/[0.1]",
    };
  }

  return {
    prismLang: l in Prism.languages ? l : "text",
    displayLabel: l.toUpperCase(),
    badgeColor: "bg-cyan-500/15 text-cyan-300 border-cyan-500/35",
  };
};

export const CodeBlock: React.FC<CodeBlockProps> = ({ language, children }) => {
  const [copied, setCopied] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  const rawCode = String(children || "").replace(/\n$/, "");
  const lines = useMemo(() => rawCode.split("\n"), [rawCode]);
  const lineCount = lines.length;

  const { prismLang, displayLabel, badgeColor } = useMemo(
    () => normalizeLanguage(language),
    [language]
  );

  // Resaltado de sintaxis con Prism
  const highlightedLines = useMemo(() => {
    const grammar = Prism.languages[prismLang];
    return lines.map((line) => {
      if (!grammar) return line;
      try {
        return Prism.highlight(line, grammar, prismLang);
      } catch {
        return line;
      }
    });
  }, [lines, prismLang]);

  const handleCopy = () => {
    navigator.clipboard.writeText(rawCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isLongCode = lineCount > 25;

  return (
    <div className="my-4 rounded-[14px] bg-[#090a0f] border border-white/[0.09] overflow-hidden font-mono shadow-xl transition-all">
      {/* Encabezado Táctico del Bloque de Código */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-black/70 border-b border-white/[0.07] text-white/50 text-[11px]">
        {/* Identificador y Lenguaje */}
        <div className="flex items-center gap-2">
          <Code2 className="w-3.5 h-3.5 text-white/40" />
          <span className={`px-2 py-0.5 rounded text-[10px] font-bold border tracking-wider font-mono ${badgeColor}`}>
            {displayLabel}
          </span>
          <span className="text-[10px] text-white/30 hidden sm:inline">
            {lineCount} {lineCount === 1 ? "línea" : "líneas"}
          </span>
        </div>

        {/* Acciones */}
        <div className="flex items-center gap-1.5">
          {/* Toggle colapsar/expandir en bloques largos */}
          {isLongCode && (
            <button
              type="button"
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="flex items-center gap-1 px-2 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.08] text-white/60 hover:text-white transition text-[10px]"
              title={isCollapsed ? "Expandir código completo" : "Colapsar código"}
            >
              {isCollapsed ? (
                <>
                  <ChevronDown className="w-3 h-3" />
                  <span>Ver {lineCount} líneas</span>
                </>
              ) : (
                <>
                  <ChevronUp className="w-3 h-3" />
                  <span>Compactar</span>
                </>
              )}
            </button>
          )}

          {/* Botón Copiar */}
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-0.5 rounded bg-white/[0.04] border border-white/[0.06] hover:bg-cyan-500/20 hover:text-cyan-200 hover:border-cyan-500/30 transition text-white/70 text-[10.5px]"
            title="Copiar código al portapapeles"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? "Copiado" : "Copiar"}</span>
          </button>
        </div>
      </div>

      {/* Contenedor de Código con Gutter de Líneas */}
      <div
        className={`flex overflow-x-auto talos-scroll bg-[#08090d] text-xs leading-relaxed transition-all ${
          isCollapsed ? "max-h-48 overflow-y-hidden relative" : "max-h-[580px] overflow-y-auto"
        }`}
      >
        {/* Números de línea laterales (no seleccionables para no ensuciar el copiado manual) */}
        <div className="select-none py-3 pl-2 pr-3 text-right text-white/20 border-r border-white/[0.05] bg-black/25 font-mono text-[11px] leading-relaxed shrink-0">
          {lines.map((_, idx) => (
            <div key={`ln-${idx}`}>{idx + 1}</div>
          ))}
        </div>

        {/* Código con Resaltado Sintáctico Prism */}
        <pre className="p-3 font-mono text-xs leading-relaxed flex-1 overflow-x-auto talos-scroll text-neutral-200 selection:bg-cyan-500/30 selection:text-white">
          <code>
            {highlightedLines.map((lineHtml, idx) => (
              <div
                key={`cl-${idx}`}
                dangerouslySetInnerHTML={{ __html: lineHtml || "&nbsp;" }}
              />
            ))}
          </code>
        </pre>

        {/* Gradiente de atenuación si está colapsado */}
        {isCollapsed && (
          <div
            onClick={() => setIsCollapsed(false)}
            className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#08090d] via-[#08090d]/80 to-transparent flex items-end justify-center pb-2 cursor-pointer group"
          >
            <span className="px-3 py-1 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 text-[11px] font-mono group-hover:bg-cyan-500/30 transition">
              Mostrar {lineCount - 6} líneas más...
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default CodeBlock;
