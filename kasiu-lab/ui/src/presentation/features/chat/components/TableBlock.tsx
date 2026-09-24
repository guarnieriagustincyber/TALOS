import React, { useRef, useState, useEffect } from "react";
import { Table as TableIcon, Copy, Check, FileSpreadsheet } from "lucide-react";

export interface TableBlockProps {
  children: React.ReactNode;
}

export const TableBlock: React.FC<TableBlockProps> = ({ children }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [copiedType, setCopiedType] = useState<"tsv" | "md" | null>(null);
  const [rowCount, setRowCount] = useState<number>(0);
  const [colCount, setColCount] = useState<number>(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const table = containerRef.current.querySelector("table");
    if (!table) return;
    const rows = table.querySelectorAll("tr");
    setRowCount(rows.length > 0 ? rows.length - 1 : 0);
    const firstRow = rows[0];
    if (firstRow) {
      setColCount(firstRow.querySelectorAll("th, td").length);
    }
  }, [children]);

  const copyAsTSV = () => {
    if (!containerRef.current) return;
    const table = containerRef.current.querySelector("table");
    if (!table) return;
    const rows = Array.from(table.querySelectorAll("tr"));
    const tsv = rows
      .map((row) => {
        const cells = Array.from(row.querySelectorAll("th, td"));
        return cells.map((c) => (c.textContent || "").trim()).join("\t");
      })
      .join("\n");

    navigator.clipboard.writeText(tsv);
    setCopiedType("tsv");
    setTimeout(() => setCopiedType(null), 2000);
  };

  const copyAsMarkdown = () => {
    if (!containerRef.current) return;
    const table = containerRef.current.querySelector("table");
    if (!table) return;
    const rows = Array.from(table.querySelectorAll("tr"));
    if (rows.length === 0) return;

    const matrix = rows.map((row) =>
      Array.from(row.querySelectorAll("th, td")).map((c) => (c.textContent || "").trim())
    );
    const maxCols = Math.max(...matrix.map((r) => r.length));
    const header = [...(matrix[0] || [])];
    while (header.length < maxCols) header.push("");

    const divider = Array(maxCols).fill("---");
    const body = matrix.slice(1);

    const mdLines = [
      `| ${header.join(" | ")} |`,
      `| ${divider.join(" | ")} |`,
      ...body.map((r) => {
        const rowPadded = [...r];
        while (rowPadded.length < maxCols) rowPadded.push("");
        return `| ${rowPadded.join(" | ")} |`;
      }),
    ];

    navigator.clipboard.writeText(mdLines.join("\n"));
    setCopiedType("md");
    setTimeout(() => setCopiedType(null), 2000);
  };

  return (
    <div
      ref={containerRef}
      className="my-5 rounded-[14px] bg-[#090a0f] border border-white/[0.09] overflow-hidden shadow-2xl transition-all"
    >
      {/* Barra de cabecera táctica para Tablas */}
      <div className="flex items-center justify-between px-3.5 py-1.5 bg-black/75 border-b border-white/[0.07] text-white/50 text-[11px] select-none font-mono">
        <div className="flex items-center gap-2">
          <TableIcon className="w-3.5 h-3.5 text-emerald-400/80" />
          <span className="px-2 py-0.5 rounded text-[10px] font-bold border tracking-wider bg-emerald-500/10 text-emerald-300 border-emerald-500/25">
            MATRIZ TÉCNICA
          </span>
          {(rowCount > 0 || colCount > 0) && (
            <span className="text-[10.5px] text-white/35 hidden sm:inline">
              {rowCount > 0 ? `${rowCount} ${rowCount === 1 ? "fila" : "filas"}` : ""}
              {rowCount > 0 && colCount > 0 ? " × " : ""}
              {colCount > 0 ? `${colCount} cols` : ""}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={copyAsTSV}
            className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.08] hover:text-white transition text-[10.5px] text-white/70"
            title="Copiar tabla para Excel / Hojas de cálculo (TSV)"
          >
            {copiedType === "tsv" ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-300">Copiado</span>
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-3 h-3 text-white/50" />
                <span>TSV</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={copyAsMarkdown}
            className="flex items-center gap-1 px-2.5 py-0.5 rounded bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.08] hover:text-white transition text-[10.5px] text-white/70"
            title="Copiar tabla en formato Markdown"
          >
            {copiedType === "md" ? (
              <>
                <Check className="w-3 h-3 text-emerald-400" />
                <span className="text-emerald-300">Copiado</span>
              </>
            ) : (
              <>
                <Copy className="w-3 h-3 text-white/50" />
                <span>Markdown</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Contenedor desplazable con scrollbar estilizada */}
      <div className="overflow-x-auto talos-scroll bg-[#08090d]">
        {children}
      </div>
    </div>
  );
};

export default TableBlock;
