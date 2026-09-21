import React from "react";
import { AlertOctagon, ArrowLeftRight, FileText, ShieldAlert } from "lucide-react";
import { ContradictionItemDto } from "./types";

export interface ContradictionViewProps {
  contradictions?: ContradictionItemDto[];
  sessionId?: string;
  onSelectDoc?: (docRef: string) => void;
}

export const ContradictionView: React.FC<ContradictionViewProps> = ({
  contradictions = [],
  sessionId = "sess_default",
  onSelectDoc,
}) => {
  return (
    <div className="space-y-6 font-mono text-xs">
      {/* CABECERA INFORMATIVA */}
      <div className="rounded-[18px] bg-purple-950/20 border border-purple-500/30 p-4 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-purple-300 font-bold uppercase tracking-wider text-[11px]">
            <ShieldAlert className="w-4 h-4 text-purple-400" />
            <span>Auditoría de Contradicciones Epistémicas (E2)</span>
          </div>
          <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/30 font-bold">
            {contradictions.length} Conflicto(s) Detectado(s)
          </span>
        </div>
        <p className="text-[11px] text-white/70 leading-relaxed">
          Comparativa lado a lado de aserciones mutuamente excluyentes detectadas entre fuentes indexadas o reportes de inteligencia.
          Conforme a ADR-008 §3, el sistema suspende autoridad sobre hechos en disputa y aplica abstención activa.
        </p>
      </div>

      {contradictions.length === 0 ? (
        <div className="rounded-[18px] bg-black/25 border border-dashed border-white/[0.08] p-8 text-center text-white/40">
          No se registran aserciones contradictorias en la sesión activa ({sessionId}).
        </div>
      ) : (
        <div className="space-y-6">
          {contradictions.map((c) => (
            <div
              key={c.claim_id}
              className="rounded-[20px] bg-[#121215] border border-white/[0.1] overflow-hidden space-y-4 p-5 shadow-xl"
            >
              {/* ENCABEZADO DEL CONFLICTO */}
              <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-white/[0.08]">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/30 text-[9px] font-bold uppercase">
                      {c.conflict_type}
                    </span>
                    <span className="text-[10px] text-white/40">{c.claim_id}</span>
                  </div>
                  <h4 className="text-sm font-semibold text-white mt-1">
                    {c.claim_text}
                  </h4>
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-rose-950/60 border border-rose-500/30 text-rose-300 text-[10px] font-bold">
                  <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
                  <span>{c.status}</span>
                </div>
              </div>

              {/* COMPARATIVA LADO A LADO */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* LADO A */}
                <div className="rounded-[16px] bg-black/40 border border-sky-500/20 p-4 space-y-2 flex flex-col justify-between">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
                        <FileText className="w-3 h-3" />
                        Fuente A (Canónica)
                      </span>
                      <span className="text-[9.5px] text-white/40 font-mono">Referencia Oficial</span>
                    </div>
                    <div className="text-xs font-semibold text-white/90 pb-1 border-b border-white/[0.05]">
                      {c.source_a}
                    </div>
                    <p className="text-[11.5px] text-sky-200/80 leading-relaxed font-sans italic bg-sky-950/20 p-2.5 rounded-[10px] border border-sky-500/10">
                      "{c.assertion_a}"
                    </p>
                  </div>

                  {onSelectDoc && (
                    <button
                      onClick={() => onSelectDoc(c.source_a)}
                      className="mt-2 text-left text-[10px] text-sky-400 hover:text-sky-300 font-semibold"
                    >
                      Inspeccionar Fuente A &rarr;
                    </button>
                  )}
                </div>

                {/* LADO B */}
                <div className="rounded-[16px] bg-black/40 border border-amber-500/20 p-4 space-y-2 flex flex-col justify-between">
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                        <FileText className="w-3 h-3" />
                        Fuente B (Contradictoria)
                      </span>
                      <span className="text-[9.5px] text-white/40 font-mono">Discrepancia</span>
                    </div>
                    <div className="text-xs font-semibold text-white/90 pb-1 border-b border-white/[0.05]">
                      {c.source_b}
                    </div>
                    <p className="text-[11.5px] text-amber-200/80 leading-relaxed font-sans italic bg-amber-950/20 p-2.5 rounded-[10px] border border-amber-500/10">
                      "{c.assertion_b}"
                    </p>
                  </div>

                  {onSelectDoc && (
                    <button
                      onClick={() => onSelectDoc(c.source_b)}
                      className="mt-2 text-left text-[10px] text-amber-400 hover:text-amber-300 font-semibold"
                    >
                      Inspeccionar Fuente B &rarr;
                    </button>
                  )}
                </div>
              </div>

              {/* DICTAMEN DE ABSTENCIÓN */}
              <div className="rounded-[14px] bg-black/30 border border-white/[0.06] p-3 text-[10.5px] text-white/50 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <ArrowLeftRight className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                  <span>
                    Acción de Política: <strong>Abstención Epistémica Activa</strong>. No se asume ninguna de las dos variantes sin resolución por parte del Auditor.
                  </span>
                </div>
                <span className="text-[9px] text-white/30 shrink-0 ml-2">ADR-008 §3</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ContradictionView;
