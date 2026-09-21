import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  CheckCircle2, 
  XCircle, 
  ShieldCheck, 
  AlertTriangle,
  Sparkles,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Terminal,
  Cpu,
  Database,
  Network
} from 'lucide-react';

interface KCItem {
  kc_id: string;
  title: string;
  unit: number;
  priority: string;
  contextual_status: string;
  bkt: {
    p_L: number;
    attempts: number;
  };
}

interface ConceptPacketData {
  kc_id: string;
  notebook_id: string;
  objective: string;
  core_concept: string;
  mental_model: string;
  reasoning_guidance: string;
  formalization?: string;
  implementation_guidance?: string;
  pitfalls: string[];
  audit_verdict: string;
}

interface ExerciseData {
  exercise_id: string;
  prompt: string;
  exercise_type: 'MC' | 'EXACT_TEXT' | 'NUMERIC';
  options?: string[];
  verification_status: string;
}

interface NotebookKCsResponse {
  notebook_id: string;
  name: string;
  kcs: KCItem[];
  consultive_student_context: {
    current_position: string;
    errors_recurring: string[];
    topics_seen: string[];
  };
}

interface CurricularFolder {
  id: string;
  name: string;
  subfolders?: CurricularFolder[];
  notebooks?: {
    id: string;
    name: string;
    icon: 'terminal' | 'cpu' | 'database' | 'network';
    path: string;
  }[];
}

const CURRICULUM_TREE: CurricularFolder[] = [
  {
    id: 'fadena',
    name: 'fadena',
    subfolders: [
      {
        id: 'fadena_1ano',
        name: '1erAño',
        subfolders: [
          {
            id: 'fadena_1ano_2cuat',
            name: '2doCuatrimestre',
            notebooks: [
              {
                id: 'fadena-lenguajes',
                name: 'Lenguajes de Programación',
                icon: 'terminal',
                path: 'fadena / 1erAño / 2doCuatrimestre / Lenguajes de Programación',
              },
              {
                id: 'fadena-so2',
                name: 'Sistemas Operativos II',
                icon: 'cpu',
                path: 'fadena / 1erAño / 2doCuatrimestre / Sistemas Operativos II',
              },
              {
                id: 'fadena-std',
                name: 'Sistema de Tratamiento de Datos',
                icon: 'database',
                path: 'fadena / 1erAño / 2doCuatrimestre / Sistema de Tratamiento de Datos',
              },
              {
                id: 'fadena-teleco',
                name: 'Infraestructura de Telecomunicaciones',
                icon: 'network',
                path: 'fadena / 1erAño / 2doCuatrimestre / Telecomunicaciones',
              },
            ],
          },
        ],
      },
    ],
  },
  {
    id: 'roadmap',
    name: 'Roadmap',
    subfolders: [
      {
        id: 'roadmap_fase0',
        name: 'Fase0',
        notebooks: [
          {
            id: 'fase0-soc',
            name: 'Programación y Pensamiento Algorítmico',
            icon: 'terminal',
            path: 'Roadmap / Fase0 / Programación',
          },
        ],
      },
    ],
  },
];

const renderNbIcon = (icon: string) => {
  switch (icon) {
    case 'cpu':
      return <Cpu className="h-3.5 w-3.5 text-purple-400 shrink-0" />;
    case 'database':
      return <Database className="h-3.5 w-3.5 text-amber-400 shrink-0" />;
    case 'network':
      return <Network className="h-3.5 w-3.5 text-rose-400 shrink-0" />;
    default:
      return <Terminal className="h-3.5 w-3.5 text-cyan-400 shrink-0" />;
  }
};

export const StudySliceModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  initialNotebookId?: string;
}> = ({
  isOpen,
  onClose,
  initialNotebookId,
}) => {
  const [selectedNotebook, setSelectedNotebook] = useState<string>('fase0-soc');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set(['fadena', 'fadena_1ano', 'fadena_1ano_2cuat', 'roadmap', 'roadmap_fase0'])
  );
  const [catalog, setCatalog] = useState<NotebookKCsResponse | null>(null);
  const [loadingCatalog, setLoadingCatalog] = useState(false);
  const [activeEpisodeId, setActiveEpisodeId] = useState<string | null>(null);
  const [concept, setConcept] = useState<ConceptPacketData | null>(null);
  const [exercise, setExercise] = useState<ExerciseData | null>(null);
  const [stepId, setStepId] = useState<string | null>(null);
  const [userResponse, setUserResponse] = useState('');
  const [gradingResult, setGradingResult] = useState<any | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Sync initialNotebookId when modal opens
  useEffect(() => {
    if (!isOpen) return;
    const validIds = ['fase0-soc', 'fadena-lenguajes', 'fadena-so2', 'fadena-std', 'fadena-teleco'];
    if (initialNotebookId && validIds.includes(initialNotebookId)) {
      setSelectedNotebook(initialNotebookId);
    }
  }, [isOpen, initialNotebookId]);

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(folderId)) {
        next.delete(folderId);
      } else {
        next.add(folderId);
      }
      return next;
    });
  };

  useEffect(() => {
    if (!isOpen) return;
    const controller = new AbortController();
    setLoadingCatalog(true);
    setConcept(null);
    setExercise(null);
    setGradingResult(null);
    setUserResponse('');
    setActiveEpisodeId(null);
    setStepId(null);

    fetch(`/api/pedagogy/notebook/${selectedNotebook}/kcs`, { signal: controller.signal })
      .then((res) => res.json())
      .then((data) => {
        setCatalog(data);
        setLoadingCatalog(false);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          console.error('Failed to load KCs:', err);
          setLoadingCatalog(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [isOpen, selectedNotebook]);

  const handleStartStudy = async (kcId: string) => {
    setConcept(null);
    setExercise(null);
    setGradingResult(null);
    setUserResponse('');

    try {
      // 1. Start Episode
      const startRes = await fetch('/api/pedagogy/episode/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notebook_id: selectedNotebook, kc_id: kcId }),
      });
      const startData = await startRes.json();
      const epId = startData.episode_id;
      setActiveEpisodeId(epId);

      // 2. Fetch Concept
      const cRes = await fetch(`/api/pedagogy/episode/${epId}/concept`);
      const cData = await cRes.json();
      if (cData.status === 'PRESENTABLE' && cData.packet) {
        setConcept(cData.packet);
      }

      // 3. Fetch Next Intervention (Exercise)
      const nextRes = await fetch(`/api/pedagogy/episode/${epId}/next`);
      const nextData = await nextRes.json();
      if (nextData.intervention_type === 'EXERCISE') {
        setExercise(nextData.exercise);
        setStepId(nextData.step_id);
      }
    } catch (err) {
      console.error('Error in study flow:', err);
    }
  };

  const handleSendResponse = async () => {
    if (!activeEpisodeId || !stepId || !userResponse.trim()) return;
    setIsSubmitting(true);
    try {
      const res = await fetch(`/api/pedagogy/episode/${activeEpisodeId}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step_id: stepId, response_text: userResponse.trim() }),
      });
      const data = await res.json();
      setGradingResult(data);
      setIsSubmitting(false);

      // Refresh catalog BKT
      fetch(`/api/pedagogy/notebook/${selectedNotebook}/kcs`)
        .then((r) => r.json())
        .then((d) => setCatalog(d))
        .catch((err) => console.error('Error refreshing KCs catalog:', err));
    } catch (err) {
      console.error('Error submitting response:', err);
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 text-white">
      <div className="flex h-[90vh] w-[95vw] max-w-6xl flex-col rounded-xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-6 py-3.5">
          <div className="flex items-center space-x-3">
            <BookOpen className="h-5 w-5 text-emerald-400" />
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-base font-bold text-slate-100">TALOS — Modo de Estudio Curricular</h2>
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800/40">
                  ARQUITECTURA CURRICULAR
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                {selectedNotebook === 'fase0-soc' && 'Roadmap / Fase0 / Programación y Pensamiento Algorítmico'}
                {selectedNotebook === 'fadena-lenguajes' && 'fadena / 1erAño / 2doCuatrimestre / Lenguajes de Programación'}
                {selectedNotebook === 'fadena-so2' && 'fadena / 1erAño / 2doCuatrimestre / Sistemas Operativos II'}
                {selectedNotebook === 'fadena-std' && 'fadena / 1erAño / 2doCuatrimestre / Sistema de Tratamiento de Datos'}
                {selectedNotebook === 'fadena-teleco' && 'fadena / 1erAño / 2doCuatrimestre / Telecomunicaciones'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-white transition"
          >
            ✕
          </button>
        </div>

        {/* Content Body: 3-column layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Column 1: Curricular Tree Navigation */}
          <div className="w-64 shrink-0 border-r border-slate-800 bg-slate-950 p-3 overflow-y-auto font-mono text-xs flex flex-col">
            <div className="mb-2.5 pb-2 border-b border-slate-800/80 flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Árbol Curricular
              </span>
              <span className="text-[9px] text-slate-500">2 ramas</span>
            </div>

            <div className="space-y-1 select-none flex-1">
              {CURRICULUM_TREE.map((root) => {
                const isRootExpanded = expandedFolders.has(root.id);
                return (
                  <div key={root.id} className="space-y-0.5">
                    {/* Root Folder */}
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={() => toggleFolder(root.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          toggleFolder(root.id);
                        }
                      }}
                      className="flex items-center gap-1.5 px-2 py-1.5 rounded cursor-pointer text-slate-300 hover:bg-slate-900 hover:text-white transition group focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      {isRootExpanded ? (
                        <ChevronDown className="h-3.5 w-3.5 text-slate-500 group-hover:text-slate-300" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5 text-slate-500 group-hover:text-slate-300" />
                      )}
                      {isRootExpanded ? (
                        <FolderOpen className="h-3.5 w-3.5 text-emerald-400" />
                      ) : (
                        <Folder className="h-3.5 w-3.5 text-emerald-400" />
                      )}
                      <span className="font-semibold text-slate-200">{root.name}</span>
                    </div>

                    {/* Root Subfolders */}
                    {isRootExpanded &&
                      root.subfolders?.map((sub1) => {
                        const isSub1Expanded = expandedFolders.has(sub1.id);
                        return (
                          <div key={sub1.id} className="pl-3 space-y-0.5 border-l border-slate-800/60 ml-3">
                            <div
                              role="button"
                              tabIndex={0}
                              onClick={() => toggleFolder(sub1.id)}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter' || e.key === ' ') {
                                  e.preventDefault();
                                  toggleFolder(sub1.id);
                                }
                              }}
                              className="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer text-slate-300 hover:bg-slate-900 hover:text-white transition group focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            >
                              {isSub1Expanded ? (
                                <ChevronDown className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                              ) : (
                                <ChevronRight className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                              )}
                              {isSub1Expanded ? (
                                <FolderOpen className="h-3 w-3 text-emerald-400/80" />
                              ) : (
                                <Folder className="h-3 w-3 text-emerald-400/80" />
                              )}
                              <span className="text-slate-300">{sub1.name}</span>
                            </div>

                            {/* Sub1 Notebooks (e.g. Fase 0) */}
                            {isSub1Expanded &&
                              sub1.notebooks?.map((nb) => {
                                const isSelected = selectedNotebook === nb.id;
                                return (
                                  <div
                                    key={nb.id}
                                    role="button"
                                    tabIndex={0}
                                    onClick={() => setSelectedNotebook(nb.id)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter' || e.key === ' ') {
                                        e.preventDefault();
                                        setSelectedNotebook(nb.id);
                                      }
                                    }}
                                    className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer ml-3 transition focus:outline-none focus:ring-1 focus:ring-emerald-500 ${
                                      isSelected
                                        ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)] font-semibold'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                                    }`}
                                  >
                                    {renderNbIcon(nb.icon)}
                                    <span className="truncate">{nb.name}</span>
                                  </div>
                                );
                              })}

                            {/* Sub1 Nested Subfolders (e.g. 2doCuatrimestre) */}
                            {isSub1Expanded &&
                              sub1.subfolders?.map((sub2) => {
                                const isSub2Expanded = expandedFolders.has(sub2.id);
                                return (
                                  <div key={sub2.id} className="pl-3 space-y-0.5 border-l border-slate-800/60 ml-2">
                                    <div
                                      role="button"
                                      tabIndex={0}
                                      onClick={() => toggleFolder(sub2.id)}
                                      onKeyDown={(e) => {
                                        if (e.key === 'Enter' || e.key === ' ') {
                                          e.preventDefault();
                                          toggleFolder(sub2.id);
                                        }
                                      }}
                                      className="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer text-slate-300 hover:bg-slate-900 hover:text-white transition group focus:outline-none focus:ring-1 focus:ring-emerald-500"
                                    >
                                      {isSub2Expanded ? (
                                        <ChevronDown className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                                      ) : (
                                        <ChevronRight className="h-3 w-3 text-slate-500 group-hover:text-slate-300" />
                                      )}
                                      {isSub2Expanded ? (
                                        <FolderOpen className="h-3 w-3 text-emerald-400/70" />
                                      ) : (
                                        <Folder className="h-3 w-3 text-emerald-400/70" />
                                      )}
                                      <span className="text-slate-300">{sub2.name}</span>
                                    </div>

                                    {/* Sub2 Notebooks */}
                                    {isSub2Expanded &&
                                      sub2.notebooks?.map((nb) => {
                                        const isSelected = selectedNotebook === nb.id;
                                        return (
                                          <div
                                            key={nb.id}
                                            role="button"
                                            tabIndex={0}
                                            onClick={() => setSelectedNotebook(nb.id)}
                                            onKeyDown={(e) => {
                                              if (e.key === 'Enter' || e.key === ' ') {
                                                e.preventDefault();
                                                setSelectedNotebook(nb.id);
                                              }
                                            }}
                                            className={`flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer ml-3 transition focus:outline-none focus:ring-1 focus:ring-emerald-500 ${
                                              isSelected
                                                ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40 shadow-[0_0_8px_rgba(16,185,129,0.15)] font-semibold'
                                                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                                            }`}
                                          >
                                            {renderNbIcon(nb.icon)}
                                            <span className="truncate">{nb.name}</span>
                                          </div>
                                        );
                                      })}
                                  </div>
                                );
                              })}
                          </div>
                        );
                      })}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Column 2: KC Catalog of Selected Notebook */}
          <div className="w-80 shrink-0 border-r border-slate-800 bg-slate-950/60 p-4 overflow-y-auto">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                KCs del Cuaderno
              </span>
              <span className="text-[10px] text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 rounded px-1.5 py-0.5 font-mono">
                BKT Activo
              </span>
            </div>

            {loadingCatalog ? (
              <div className="p-4 text-center text-xs text-slate-500">Cargando catálogo...</div>
            ) : (
              <div className="space-y-2">
                {catalog?.kcs.map((kc) => (
                  <div
                    key={kc.kc_id}
                    onClick={() => handleStartStudy(kc.kc_id)}
                    className="group flex cursor-pointer flex-col rounded-lg border border-slate-800 bg-slate-900/60 p-3 transition hover:border-emerald-500/50 hover:bg-slate-800/50"
                  >
                    <div className="flex items-start justify-between">
                      <span className="text-xs font-medium text-slate-200 group-hover:text-emerald-300 leading-snug">
                        {kc.title}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 shrink-0 ml-2">
                        P(L): {kc.bkt.p_L.toFixed(2)}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
                      <span>U{kc.unit} · {kc.contextual_status}</span>
                      <span className="text-slate-400 group-hover:translate-x-1 transition font-mono">Estudiar →</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Pane: Study Area */}
          <div className="flex-1 flex flex-col p-6 overflow-y-auto bg-slate-900/30">
            {!concept && !exercise ? (
              <div className="m-auto flex flex-col items-center justify-center text-center max-w-md text-slate-500">
                <Sparkles className="h-12 w-12 text-slate-600 mb-3" />
                <h3 className="text-base font-semibold text-slate-300">Seleccioná un KC para comenzar</h3>
                <p className="text-xs text-slate-400 mt-1">
                  TALOS integrará evidencia multifuente validada con S4.4 y presentará un ejercicio real del corpus con grading determinista.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Concept Presentation */}
                {concept && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                      <div>
                        <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wide">
                          Explicación Integrada Multifuente
                        </span>
                        <h3 className="text-base font-bold text-slate-100">{concept.objective}</h3>
                      </div>
                      <div className="flex items-center space-x-1 text-xs text-emerald-400 bg-emerald-950/50 border border-emerald-800/40 px-2 py-1 rounded">
                        <ShieldCheck className="h-3.5 w-3.5" />
                        <span>S4.4: {concept.audit_verdict}</span>
                      </div>
                    </div>

                    <div className="space-y-3 text-sm leading-relaxed text-slate-300">
                      <div>
                        <span className="text-xs font-semibold text-slate-400 uppercase">Concepto Fundamental (PRIMARY):</span>
                        <p className="mt-0.5 text-slate-200">{concept.core_concept}</p>
                      </div>

                      <div>
                        <span className="text-xs font-semibold text-slate-400 uppercase">Modelo Mental (METHODOLOGICAL):</span>
                        <p className="mt-0.5 text-slate-200">{concept.mental_model}</p>
                      </div>

                      {concept.formalization && (
                        <div className="rounded-lg bg-slate-900 border border-slate-800 p-3 font-mono text-xs text-sky-300">
                          {concept.formalization}
                        </div>
                      )}

                      {concept.pitfalls && concept.pitfalls.length > 0 && (
                        <div className="rounded-lg bg-amber-950/30 border border-amber-800/30 p-3">
                          <div className="flex items-center space-x-2 text-amber-400 text-xs font-semibold">
                            <AlertTriangle className="h-4 w-4" />
                            <span>Errores Frecuentes y Puntos Críticos:</span>
                          </div>
                          <ul className="mt-1.5 list-disc pl-4 text-xs text-amber-200/80 space-y-1">
                            {concept.pitfalls.map((p, idx) => (
                              <li key={idx}>{p}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Exercise Section */}
                {exercise && (
                  <div className="rounded-xl border border-slate-800 bg-slate-950/90 p-5 shadow-sm space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                      <span className="text-xs font-bold uppercase tracking-wider text-sky-400">
                        Ejercicio Real del Corpus (QUALIFIABLE)
                      </span>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">
                        Formato: {exercise.exercise_type}
                      </span>
                    </div>

                    <p className="text-sm font-medium text-slate-200">{exercise.prompt}</p>

                    {exercise.exercise_type === 'MC' && exercise.options && (
                      <div className="space-y-2 pt-2">
                        {exercise.options.map((opt, idx) => {
                          const optKey = opt.trim().charAt(0);
                          return (
                            <button
                              key={idx}
                              onClick={() => setUserResponse(optKey)}
                              className={`w-full text-left p-3 rounded-lg border text-xs font-medium transition ${
                                userResponse === optKey
                                  ? 'border-emerald-500 bg-emerald-950/40 text-emerald-200'
                                  : 'border-slate-800 bg-slate-900/60 text-slate-300 hover:bg-slate-800'
                              }`}
                            >
                              {opt}
                            </button>
                          );
                        })}
                      </div>
                    )}

                    {exercise.exercise_type !== 'MC' && (
                      <div className="pt-2">
                        <input
                          type="text"
                          value={userResponse}
                          onChange={(e) => setUserResponse(e.target.value)}
                          placeholder="Escribí tu respuesta exacta o valor numérico..."
                          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none focus:border-emerald-500"
                        />
                      </div>
                    )}

                    {!gradingResult && (
                      <div className="flex justify-end pt-2">
                        <button
                          disabled={!userResponse.trim() || isSubmitting}
                          onClick={handleSendResponse}
                          className="rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-50"
                        >
                          {isSubmitting ? 'Evaluando...' : 'Enviar Respuesta'}
                        </button>
                      </div>
                    )}

                    {/* Grading Result */}
                    {gradingResult && (
                      <div
                        className={`rounded-lg border p-4 text-xs ${
                          gradingResult.is_correct
                            ? 'border-emerald-800/60 bg-emerald-950/40 text-emerald-200'
                            : 'border-rose-800/60 bg-rose-950/40 text-rose-200'
                        }`}
                      >
                        <div className="flex items-center space-x-2 font-bold text-sm">
                          {gradingResult.is_correct ? (
                            <>
                              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                              <span>Evaluación: Correcto</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-4 w-4 text-rose-400" />
                              <span>Evaluación: Incorrecto</span>
                            </>
                          )}
                        </div>
                        <p className="mt-2 text-xs leading-relaxed">{gradingResult.feedback}</p>

                        <div className="mt-3 flex items-center justify-between border-t border-slate-800/60 pt-3 text-[11px] text-slate-400">
                          <span>
                            BKT P(L) actualizado a:{' '}
                            <strong className="text-white font-mono">
                              {gradingResult.bkt_update?.p_L.toFixed(2)}
                            </strong>{' '}
                            (Intentos: {gradingResult.bkt_update?.attempts})
                          </span>
                          <span>
                            Próxima acción:{' '}
                            <strong className="text-emerald-400">
                              {gradingResult.next_eligible_action?.recommendation}
                            </strong>
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
