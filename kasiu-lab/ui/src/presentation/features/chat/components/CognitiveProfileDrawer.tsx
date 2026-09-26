import React, { useEffect, useState } from "react";
import ReactDOM from "react-dom";
import { X, Brain, AlertTriangle, TrendingUp } from "lucide-react";

// ── Tipos — mapeados al endpoint real /api/student/cognitive-state ─────────────
interface BktKcMastery {
  p_L: number;
  attempts: number;
  last_update: string;
}

interface ActiveAlert {
  alert_id: string;
  kc_id: string;
  title: string;
  p_L: number;
  severity: "CRITICAL" | "WARNING";
  detected_at: string;
}

interface CognitiveStateResponse {
  student_id: string;
  kc_mastery: Record<string, BktKcMastery>;
  active_alerts: ActiveAlert[];
  readiness_cache: Record<string, unknown>;
}

// ── Props ──────────────────────────────────────────────────────────────────────
interface CognitiveProfileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

// ── Componente ─────────────────────────────────────────────────────────────────
const DrawerContent: React.FC<CognitiveProfileDrawerProps> = ({ isOpen, onClose }) => {
  const [data, setData] = useState<CognitiveStateResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    let active = true;
    setIsLoading(true);
    setError(null);
    setData(null);

    fetch("/api/student/cognitive-state")
      .then((res) => {
        if (!res.ok) throw new Error(`Error ${res.status}: ${res.statusText}`);
        return res.json() as Promise<CognitiveStateResponse>;
      })
      .then((d) => { if (active) setData(d); })
      .catch((err: Error) => { if (active) setError(err.message); })
      .finally(() => { if (active) setIsLoading(false); });

    return () => { active = false; };
  }, [isOpen]);

  // Derivar debilidades (p_L < 0.5 con al menos 1 intento) y fortalezas (p_L >= 0.70) desde kc_mastery
  const weaknesses = data
    ? Object.entries(data.kc_mastery)
        .filter(([, v]) => v.attempts > 0 && v.p_L < 0.5)
        .sort((a, b) => a[1].p_L - b[1].p_L)
        .slice(0, 8)
    : [];

  const strengths = data
    ? Object.entries(data.kc_mastery)
        .filter(([, v]) => v.attempts > 0 && v.p_L >= 0.70)
        .sort((a, b) => b[1].p_L - a[1].p_L)
        .slice(0, 6)
    : [];

  const alerts = data?.active_alerts ?? [];

  const pLBar = (pL: number) => {
    const pct = Math.round(pL * 100);
    const color =
      pL >= 0.70 ? "bg-emerald-500" :
      pL >= 0.40 ? "bg-amber-500" : "bg-rose-500";
    return (
      <div className="mt-1.5 flex items-center gap-2">
        <div className="flex-1 h-1.5 bg-zinc-700 rounded-full overflow-hidden">
          <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
        </div>
        <span className="text-[10px] font-mono text-zinc-400 shrink-0 tabular-nums">{pct}%</span>
      </div>
    );
  };

  return (
    <>
      {/* ── Overlay ── captura clicks fuera del panel */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm"
        style={{ zIndex: 9998 }}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* ── Panel ── */}
      <aside
        className="fixed right-0 top-0 h-full flex flex-col bg-zinc-900 border-l border-zinc-700/60 shadow-2xl"
        style={{ zIndex: 9999, width: "320px" }}
        aria-label="Panel de Perfil Cognitivo"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-700/60 bg-zinc-900 shrink-0">
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-mono font-semibold text-zinc-100">Perfil Cognitivo</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-zinc-700 text-zinc-400 hover:text-white transition cursor-pointer"
            title="Cerrar"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-5" style={{ scrollbarWidth: "thin", scrollbarColor: "#3f3f46 transparent" }}>
          {isLoading && (
            <div className="space-y-3 pt-2">
              {[0.7, 1, 0.55].map((w, i) => (
                <div key={i} className="h-3 bg-zinc-800 animate-pulse rounded-md" style={{ width: `${w * 100}%` }} />
              ))}
            </div>
          )}

          {error && !isLoading && (
            <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/25 text-rose-300 text-xs font-mono flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-400" />
              <div>
                <p className="font-semibold mb-0.5">Error al cargar</p>
                <p className="opacity-80">{error}</p>
              </div>
            </div>
          )}

          {data && !isLoading && (
            <>
              {/* Alertas Críticas del BKT */}
              {alerts.length > 0 && (
                <section>
                  <div className="flex items-center gap-2 mb-2.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                    <span className="text-[10px] font-mono font-semibold text-zinc-400 uppercase tracking-widest">
                      Alertas Activas
                    </span>
                    <span className="px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-[10px] font-mono font-bold border border-rose-500/30">
                      {alerts.length}
                    </span>
                  </div>
                  <ul className="space-y-2">
                    {alerts.map((a) => (
                      <li key={a.alert_id} className="p-3 rounded-xl bg-zinc-800/80 border border-rose-500/20 hover:border-rose-500/40 transition">
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-[10px] font-mono text-rose-400 font-bold uppercase tracking-wider leading-snug">
                            {a.kc_id}
                          </span>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold border shrink-0 ${
                            a.severity === "CRITICAL"
                              ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                              : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                          }`}>
                            {a.severity}
                          </span>
                        </div>
                        <p className="text-xs text-zinc-300 leading-snug mt-1">{a.title}</p>
                        {pLBar(a.p_L)}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              {/* Debilidades (p_L < 0.5) */}
              <section>
                <div className="flex items-center gap-2 mb-2.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-[10px] font-mono font-semibold text-zinc-400 uppercase tracking-widest">
                    Lagunas de Conocimiento
                  </span>
                  {weaknesses.length > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-mono font-bold border border-amber-500/30">
                      {weaknesses.length}
                    </span>
                  )}
                </div>
                {weaknesses.length === 0 ? (
                  <p className="text-xs text-zinc-500 font-mono pl-1">Sin lagunas detectadas ✓</p>
                ) : (
                  <ul className="space-y-2">
                    {weaknesses.map(([kcId, v]) => (
                      <li key={kcId} className="p-3 rounded-xl bg-zinc-800/60 border border-amber-500/15 hover:border-amber-500/30 transition">
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-[10px] font-mono text-amber-400 font-bold uppercase tracking-wider">{kcId}</span>
                          <span className="text-[9px] font-mono text-zinc-500 shrink-0">{v.attempts} intentos</span>
                        </div>
                        {pLBar(v.p_L)}
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {/* Fortalezas (p_L >= 0.70) */}
              <section>
                <div className="flex items-center gap-2 mb-2.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[10px] font-mono font-semibold text-zinc-400 uppercase tracking-widest">
                    Fortalezas
                  </span>
                  {strengths.length > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-mono font-bold border border-emerald-500/30">
                      {strengths.length}
                    </span>
                  )}
                </div>
                {strengths.length === 0 ? (
                  <p className="text-xs text-zinc-500 font-mono pl-1">Aún no hay KCs consolidados</p>
                ) : (
                  <ul className="space-y-2">
                    {strengths.map(([kcId, v]) => (
                      <li key={kcId} className="p-3 rounded-xl bg-zinc-800/60 border border-emerald-500/15 hover:border-emerald-500/30 transition">
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase tracking-wider">{kcId}</span>
                          <span className="text-[9px] font-mono text-zinc-500 shrink-0">{v.attempts} intentos</span>
                        </div>
                        {pLBar(v.p_L)}
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              {/* Stats generales */}
              <section className="p-3 rounded-xl bg-zinc-800/40 border border-zinc-700/40 text-[10px] font-mono space-y-1.5">
                <p className="text-zinc-500 uppercase tracking-widest font-semibold mb-1">Estadísticas BKT</p>
                <div className="flex justify-between text-zinc-300">
                  <span>KCs rastreados</span>
                  <span className="font-bold">{Object.keys(data.kc_mastery).length}</span>
                </div>
                <div className="flex justify-between text-zinc-300">
                  <span>Intentos totales</span>
                  <span className="font-bold">
                    {Object.values(data.kc_mastery).reduce((sum, v) => sum + v.attempts, 0)}
                  </span>
                </div>
              </section>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-zinc-700/60 bg-zinc-900 shrink-0">
          <p className="text-[10px] text-zinc-600 font-mono text-center">
            Motor BKT · TALOS Cognitive Engine
          </p>
        </div>
      </aside>
    </>
  );
};

// Envuelve en Portal para escapar del overflow:hidden del workspace
export const CognitiveProfileDrawer: React.FC<CognitiveProfileDrawerProps> = (props) => {
  if (!props.isOpen) return null;

  const portalTarget = document.body;
  return ReactDOM.createPortal(<DrawerContent {...props} />, portalTarget);
};

export default CognitiveProfileDrawer;
