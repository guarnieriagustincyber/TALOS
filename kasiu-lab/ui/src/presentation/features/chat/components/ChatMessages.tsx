import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  ArrowDown,
  BookOpen,
  Bookmark,
  BookmarkCheck,
  Check,
  CheckCircle2,
  ChevronUp,
  Copy,
  Edit2,
  HelpCircle,
  Loader2,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  Citation,
  EvidenceTab,
  Message,
} from "../../views/types";
import { MessageBody } from "../MessageBody";
import { ClaimStatusBadge } from "../../views/ClaimStatusBadge";
import { OpeningBriefView, StudySessionSnapshotData } from "../OpeningBriefView";
import { DialogueView } from "../DialogueView";
import { SYSTEM_NAME } from "./shared";

export const AbstentionBanner: React.FC<{ reason?: string | null }> = ({ reason }) => (
  <div className="mt-4 p-3.5 rounded-xl bg-[#14120e] border border-amber-500/20 text-amber-200/90 font-mono text-xs flex items-start gap-3">
    <div className="w-5 h-5 rounded-md bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
      <AlertTriangle className="w-3 h-3 text-amber-400" />
    </div>
    <div className="space-y-0.5 min-w-0">
      <span className="font-semibold uppercase tracking-wider text-[10px] text-amber-400/90 block">
        Abstención Epistémica Calibrada (CAL §3.2)
      </span>
      <p className="text-white/75 text-xs leading-relaxed">
        {reason || "La evidencia recuperada no alcanza el umbral de suficiencia epistémica para una respuesta concluyente."}
      </p>
    </div>
  </div>
);

export const FacetCoverageBar: React.FC<{ coverage?: Record<string, "SUFFICIENT" | "PARTIAL" | "MISSING"> }> = ({ coverage }) => {
  if (!coverage || Object.keys(coverage).length === 0) return null;
  const entries = Object.entries(coverage);
  const statusColors = {
    SUFFICIENT: "bg-emerald-500/10 border-emerald-500/25 text-emerald-400",
    PARTIAL: "bg-amber-500/10 border-amber-500/25 text-amber-400",
    MISSING: "bg-rose-500/10 border-rose-500/25 text-rose-400",
  };
  const statusLabels = {
    SUFFICIENT: "Suficiente",
    PARTIAL: "Parcial",
    MISSING: "Faltante",
  };
  return (
    <div className="mt-3 p-3 rounded-xl bg-black/40 border border-white/[0.07] space-y-1.5 font-mono">
      <span className="text-[10px] uppercase tracking-wider text-white/40 block font-medium">
        Cobertura por Facetas Epistémicas
      </span>
      <div className="flex flex-wrap gap-1.5">
        {entries.map(([facet, status]) => (
          <div
            key={facet}
            className={`px-2 py-0.5 rounded-lg border text-[11px] flex items-center gap-1.5 ${statusColors[status] || "bg-white/[0.04] border-white/[0.08] text-white/60"}`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
            <span className="font-medium text-white/80">{facet}:</span>
            <span className="opacity-80">{statusLabels[status] || status}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export interface ClaimTextProps {
  text: string;
  evidences?: Citation[];
  onOpenEvidence: (tab: EvidenceTab, docHash?: string, page?: number, citation?: Citation) => void;
  onOpenCitation?: (citation: Citation) => void;
}

export const ClaimText = React.memo<ClaimTextProps>(({ text, evidences, onOpenEvidence, onOpenCitation }) => {
  return (
    <MessageBody
      content={text}
      evidences={evidences}
      onOpenEvidence={onOpenEvidence}
      onOpenCitation={
        onOpenCitation ||
        ((c) => onOpenEvidence("evidencia", c.docHash || undefined, c.page || undefined, c))
      }
    />
  );
});

export interface ChatMessagesProps {
  messages: Message[];
  activeScope: string;
  isThinking: boolean;
  thinkingStep: string;
  isStreaming: boolean;
  streamedText: string;
  onEditMessage?: (messageId: string, newContent: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onOpenEvidence: (tab: EvidenceTab, docHash?: string, page?: number, citation?: Citation) => void;
  onOpenCitation?: (citation: Citation) => void;
  onSaveNote: (msgId: string, text: string) => void;
  studySessionSnapshot?: StudySessionSnapshotData | null;
  onExecuteStudyAction?: (action: string, payload?: Record<string, any>) => void;
  isStudyActionLoading?: boolean;
  hasMore?: boolean;
  isLoadingMore?: boolean;
  onLoadMore?: () => void;
  onPromptChange?: never;
  onSend: (text: string) => void;
}

interface SocraticChallengeData {
  hasChallenge: boolean;
  questionText: string;
  options: { key: string; text: string }[];
  isMultipleChoice: boolean;
}

function extractSocraticChallenge(text: string): SocraticChallengeData {
  if (!text) return { hasChallenge: false, questionText: "", options: [], isMultipleChoice: false };

  const match = text.match(/(?:###\s*Desafío Socrático|\*\*Desafío Socrático:\*\*|###\s*Pregunta Socrática|Desafío Socrático:)([\s\S]*)$/i);
  if (!match) {
    return { hasChallenge: false, questionText: "", options: [], isMultipleChoice: false };
  }

  const rawSection = match[1].trim();
  const optionRegex = /^(?:([A-D])\)|([1-4])\))\s*(.+)$/gm;
  const options: { key: string; text: string }[] = [];
  let optMatch: RegExpExecArray | null;

  while ((optMatch = optionRegex.exec(rawSection)) !== null) {
    const key = (optMatch[1] || optMatch[2]).toUpperCase();
    const optText = optMatch[3].trim();
    options.push({ key, text: optText });
  }

  const questionText = rawSection.replace(/^(?:[A-D]|[1-4])\)\s*.+$/gm, "").trim();

  return {
    hasChallenge: true,
    questionText: questionText || rawSection,
    options,
    isMultipleChoice: options.length >= 2,
  };
}

interface PedagogicalBadgeInfo {
  label: string;
  colorClass: string;
  borderClass: string;
  bgClass: string;
}

const detectPedagogicalBadge = (text: string): PedagogicalBadgeInfo | null => {
  if (!text) return null;
  const lower = text.toLowerCase();
  if (
    lower.includes("auditoría técnica") ||
    lower.includes("auditoría forense") ||
    lower.includes("análisis de bugs") ||
    lower.includes("cve-2021-29921") ||
    lower.includes("parser differential") ||
    lower.includes("protocolo talos")
  ) {
    return {
      label: "Auditoría Forense",
      colorClass: "text-white/80",
      borderClass: "border-white/[0.12]",
      bgClass: "bg-white/[0.04]",
    };
  }
  if (
    lower.includes("conflicto epistémico") ||
    lower.includes("validación cognitiva") ||
    lower.includes("base octal") ||
    lower.includes("odómetro") ||
    lower.includes("salto de magnitud") ||
    lower.includes("desarme de la frustración")
  ) {
    return {
      label: "Andamiaje Socrático",
      colorClass: "text-emerald-300",
      borderClass: "border-emerald-500/25",
      bgClass: "bg-emerald-500/10",
    };
  }
  if (
    lower.includes("síntesis dialéctica") ||
    lower.includes("intuición conceptual") ||
    lower.includes("mecanismo formal") ||
    lower.includes("nivel de máquina")
  ) {
    return {
      label: "Síntesis Tri-Capa",
      colorClass: "text-emerald-300",
      borderClass: "border-emerald-500/25",
      bgClass: "bg-emerald-500/10",
    };
  }
  if (
    lower.includes("desafío socrático") ||
    lower.includes("pregunta socrática")
  ) {
    return {
      label: "Tutoría Epistémica",
      colorClass: "text-emerald-300",
      borderClass: "border-emerald-500/25",
      bgClass: "bg-emerald-500/10",
    };
  }
  return null;
};

export const ThinkingIndicator: React.FC<{ thinkingStep: string }> = ({ thinkingStep }) => {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const timer = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 100) / 10);
    }, 100);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="rounded-[20px] border border-white/[0.08] bg-gradient-to-b from-[#111114] to-[#09090b] p-4 sm:p-5 shadow-[0_12px_45px_rgba(0,0,0,0.5)] k-fade-in relative overflow-hidden backdrop-blur-md">
      <div className="absolute top-0 left-0 right-0 h-[1.5px] bg-gradient-to-r from-transparent via-emerald-400/40 to-transparent pointer-events-none" />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-emerald-400 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold text-white">
                {SYSTEM_NAME} · Razonamiento Epistémico
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono font-medium bg-white/[0.05] text-white/50 border border-white/[0.08]">
                {elapsed.toFixed(1)}s
              </span>
            </div>
            <span className="text-[10px] font-mono text-emerald-400/75 block mt-0.5">
              Verificando consistencia en fuentes canónicas
            </span>
          </div>
        </div>
      </div>

      <div className="mt-3.5 rounded-[12px] bg-black/70 border border-white/[0.06] px-3.5 py-2.5 flex items-center gap-2.5">
        <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400/90 shrink-0" />
        <span className="font-mono text-xs text-white/75 truncate">
          {thinkingStep || "Analizando consulta y verificando aserciones en el corpus..."}
        </span>
      </div>
    </div>
  );
};

export const ChatMessages: React.FC<ChatMessagesProps> = ({
  messages,
  activeScope,
  isThinking,
  thinkingStep,
  isStreaming,
  streamedText,
  onEditMessage,
  onDeleteMessage,
  onOpenEvidence,
  onOpenCitation,
  onSaveNote,
  studySessionSnapshot,
  onExecuteStudyAction,
  isStudyActionLoading,
  hasMore,
  isLoadingMore,
  onLoadMore,
  onSend,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const scrollBottomAnchorRef = useRef<HTMLDivElement>(null);
  const prevMessagesCountRef = useRef(messages.length);
  const prevScrollHeightRef = useRef<number>(0);

  // Estados locales para Edición y Borrado en Cascada
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);
  const [editDraftText, setEditDraftText] = useState<string>("");
  const [deleteCandidateId, setDeleteCandidateId] = useState<string | null>(null);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  const handleCopyMessage = async (msgId: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageId(msgId);
      setTimeout(() => {
        setCopiedMessageId((prev) => (prev === msgId ? null : prev));
      }, 2000);
    } catch (err) {
      console.error("Error al copiar texto:", err);
    }
  };

  // Estados locales para desafío socrático interactivo y BKT en vivo
  const [socraticAnswers, setSocraticAnswers] = useState<Record<string, string>>({});
  const [socraticEvaluating, setSocraticEvaluating] = useState<Record<string, boolean>>({});
  const [bktProgress, setBktProgress] = useState<
    Record<string, {
      p_L: number;
      delta_p_L?: number;
      feedback: string;
      is_correct: boolean | null;
      status?: string;
      hint?: string;
      hints?: string[];
      generic_message?: string;
    }>
  >({});
  const [showHints, setShowHints] = useState<Record<string, boolean>>({});

  const handleEvaluateSocratic = async (msgId: string, userAns: string, isMC: boolean = false) => {
    if (!userAns.trim()) return;
    setSocraticEvaluating((prev) => ({ ...prev, [msgId]: true }));
    try {
      const resp = await fetch("/api/pedagogy/episode/ep_live_socratic/dialogue/evaluate-socratic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_response: userAns.trim(),
          kc_id: activeScope || "general",
          is_mc: isMC,
        }),
      });
      if (resp.ok) {
        const data = await resp.json();
        setBktProgress((prev) => ({
          ...prev,
          [msgId]: {
            p_L: data.p_L,
            delta_p_L: data.delta_p_L,
            feedback: data.feedback,
            is_correct: data.is_correct,
            status: data.status,
            hint: data.hint,
            hints: data.hints,
            generic_message: data.generic_message,
          },
        }));
      }
    } catch {
      setBktProgress((prev) => ({
        ...prev,
        [msgId]: {
          p_L: 0.0,
          delta_p_L: 0.0,
          feedback: "Error de conexión al evaluar desafío socrático. Reintentá en unos momentos.",
          is_correct: null,
          status: "NETWORK_ERROR",
        },
      }));
    } finally {
      setSocraticEvaluating((prev) => ({ ...prev, [msgId]: false }));
    }
  };

  const startEditing = (msg: Message) => {
    setEditingMessageId(msg.id);
    setEditDraftText(msg.text);
  };

  const cancelEditing = () => {
    setEditingMessageId(null);
    setEditDraftText("");
  };

  const handleSaveEdit = (messageId: string) => {
    if (editDraftText.trim() && onEditMessage) {
      onEditMessage(messageId, editDraftText.trim());
    }
    setEditingMessageId(null);
    setEditDraftText("");
  };

  const confirmCascadeDelete = () => {
    if (deleteCandidateId && onDeleteMessage) {
      onDeleteMessage(deleteCandidateId);
    }
    setDeleteCandidateId(null);
  };

  const [showScrollBottomBtn, setShowScrollBottomBtn] = useState(false);
  const prevScopeRef = useRef(activeScope);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior,
      });
    }
  }, []);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight;
    // Mostrar botón flotante si el usuario se alejó más de 140px del fondo
    setShowScrollBottomBtn(distanceFromBottom > 140);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.addEventListener("scroll", handleScroll, { passive: true });
    return () => el.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // Al cambiar de cuaderno o al montar, posicionar de inmediato en el último mensaje sin animación ni vibración
  useEffect(() => {
    prevScopeRef.current = activeScope;
    prevMessagesCountRef.current = messages.length;
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [activeScope]);

  const handleLoadMore = () => {
    if (scrollRef.current) {
      prevScrollHeightRef.current = scrollRef.current.scrollHeight;
    }
    if (onLoadMore) {
      onLoadMore();
    }
  };

  useEffect(() => {
    // Si acaba de cambiar de cuaderno, el scroll instantáneo ya lo posicionó
    if (prevScopeRef.current !== activeScope) {
      prevScopeRef.current = activeScope;
      prevMessagesCountRef.current = messages.length;
      return;
    }

    // Si la cantidad de mensajes aumentó dentro del mismo chat (usuario envió o asistente respondió)
    if (messages.length > prevMessagesCountRef.current) {
      if (prevScrollHeightRef.current > 0 && scrollRef.current) {
        // Carga de mensajes anteriores hacia arriba (lazy load)
        const delta = scrollRef.current.scrollHeight - prevScrollHeightRef.current;
        if (delta > 0) {
          scrollRef.current.scrollTop += delta;
        }
        prevScrollHeightRef.current = 0;
      } else {
        // Mensaje nuevo enviado o recibido: auto-scroll suave único
        scrollToBottom("smooth");
      }
    }
    prevMessagesCountRef.current = messages.length;
  }, [messages.length, activeScope, scrollToBottom]);

  // Al entrar en modo de procesamiento socrático / thinking
  useEffect(() => {
    if (isThinking) {
      scrollToBottom("smooth");
    }
  }, [isThinking, scrollToBottom]);

  useEffect(() => {
    if (isStreaming && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [streamedText, isStreaming]);

  return (
    <div className="flex-1 relative flex flex-col min-h-0 overflow-hidden">
      {/* MODAL DE CONFIRMACIÓN: BORRADO EN CASCADA */}
      {deleteCandidateId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 k-fade-in font-mono">
          <div className="w-full max-w-md rounded-[20px] bg-[#141417] border border-rose-500/30 p-6 shadow-[0_16px_50px_rgba(244,63,94,0.15)] space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-[10px] bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-white">¿Borrar mensaje en cascada?</h3>
                <span className="text-[11px] text-rose-400/80">Esta acción no se puede deshacer</span>
              </div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Al eliminar este mensaje, se eliminarán también <strong>todos los mensajes posteriores</strong> para mantener la coherencia contextual del diálogo. Se actualizará la vista y el almacenamiento local.
            </p>
            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-white/[0.06]">
              <button
                type="button"
                onClick={() => setDeleteCandidateId(null)}
                className="h-8 px-3 rounded-[10px] bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-white/60 hover:text-white text-xs transition"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={confirmCascadeDelete}
                className="h-8 px-3.5 rounded-[10px] bg-rose-500/20 border border-rose-500/40 hover:bg-rose-500/30 text-rose-300 text-xs font-semibold transition"
              >
                Confirmar Borrado
              </button>
            </div>
          </div>
        </div>
      )}

      <div ref={scrollRef} className="flex-1 overflow-y-auto k-scroll px-4 sm:px-8 md:px-14 lg:px-20 py-4 md:py-8 space-y-6">
        <div className="w-full max-w-[980px] mx-auto space-y-6">
          {/* BOTÓN DE LAZY LOAD AL TOPE DE LA CONVERSACIÓN */}
          {hasMore && (
            <div className="flex justify-center pb-2">
              <button
                type="button"
                onClick={handleLoadMore}
                disabled={isLoadingMore}
                className="h-8 px-4 rounded-[12px] bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] hover:border-white/20 text-white/50 hover:text-white text-xs font-mono flex items-center gap-2 transition select-none disabled:opacity-50 shadow-sm"
              >
                <ChevronUp className="w-3.5 h-3.5" />
                <span>{isLoadingMore ? "Cargando mensajes anteriores..." : "Cargar mensajes anteriores"}</span>
              </button>
            </div>
          )}

          {studySessionSnapshot && studySessionSnapshot.episode_phase === "OPENING_BRIEF" && onExecuteStudyAction && (
            <OpeningBriefView
              snapshot={studySessionSnapshot}
              onExecuteAction={onExecuteStudyAction}
              isLoading={isStudyActionLoading}
            />
          )}

          {studySessionSnapshot && (
            studySessionSnapshot.episode_phase === "SOCRATIC_DIALOGUE" ||
            studySessionSnapshot.episode_phase === "DIALOGUE" ||
            studySessionSnapshot.episode_phase === "DIALOGUE_LIMIT_REACHED" ||
            studySessionSnapshot.episode_phase === "SUGGEST_EXERCISE"
          ) && (
            <DialogueView
              episode={{ phase: studySessionSnapshot.episode_phase }}
              dialogueState={{
                turns: [],
                turn_count: 0,
                dialogue_limit_reached: studySessionSnapshot.episode_phase === "DIALOGUE_LIMIT_REACHED",
              }}
              dialogueResponse={{}}
              MAX_DIALOGUE_TURNS={5}
              sendDialogueMessage={(msg) => {
                onSend(msg);
              }}
              acceptExercise={() => onExecuteStudyAction && onExecuteStudyAction("REQUEST_EXERCISE")}
              rejectExercise={() => onExecuteStudyAction && onExecuteStudyAction("CONTINUE_EXPLORATION")}
              endDialogue={() => onExecuteStudyAction && onExecuteStudyAction("END_DIALOGUE")}
            />
          )}
          {messages.map((msg) => {
            if (msg.sender === "user") {
              const isEditingThis = editingMessageId === msg.id;
              return (
                <div
                  key={msg.id}
                  className="flex justify-end k-fade-in group"
                >
                  <div className="max-w-[85%] sm:max-w-[80%] md:max-w-[75%] flex flex-col items-end">
                    <div className="flex items-center gap-2 text-[10px] md:text-xs uppercase tracking-[0.18em] font-mono text-white/35 mb-1.5 px-1">
                      {msg.edited && (
                        <span className="text-cyan-400/70 lowercase tracking-normal text-[10px] italic">
                          (editado)
                        </span>
                      )}
                      <span>Agustín</span>
                      <span>·</span>
                      <span>{msg.timestamp}</span>

                      {/* Botones de acción en hover */}
                      {!isEditingThis && (
                        <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 ml-1.5">
                          {onEditMessage && (
                            <button
                              type="button"
                              onClick={() => startEditing(msg)}
                              className="p-1 rounded text-white/40 hover:text-white hover:bg-white/10 transition"
                              title="Editar mensaje"
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                          )}
                          {onDeleteMessage && (
                            <button
                              type="button"
                              onClick={() => setDeleteCandidateId(msg.id)}
                              className="p-1 rounded text-white/40 hover:text-rose-400 hover:bg-rose-500/10 transition"
                              title="Borrar en cascada"
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="rounded-[18px] bg-gradient-to-b from-white/[0.08] to-white/[0.04] border border-white/[0.08] px-4 py-2.5 text-left inline-block shadow-[0_4px_20px_rgba(0,0,0,0.2)] hover:border-white/[0.14] transition-colors">
                      {isEditingThis ? (
                        <div className="space-y-2 min-w-[280px]">
                          <textarea
                            value={editDraftText}
                            onChange={(e) => setEditDraftText(e.target.value)}
                            className="w-full bg-black/40 border border-cyan-500/40 rounded-[10px] p-2.5 font-mono text-sm text-white focus:outline-none resize-y min-h-[70px]"
                            rows={3}
                          />
                          <div className="flex justify-end gap-2 font-mono text-xs">
                            <button
                              type="button"
                              onClick={cancelEditing}
                              className="px-2.5 py-1 rounded-[8px] bg-white/[0.05] text-white/60 hover:text-white transition"
                            >
                              Cancelar
                            </button>
                            <button
                              type="button"
                              onClick={() => handleSaveEdit(msg.id)}
                              className="px-2.5 py-1 rounded-[8px] bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/30 transition font-semibold"
                            >
                              Guardar
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="font-sans text-sm md:text-[15px] leading-relaxed text-neutral-100 font-normal break-words whitespace-pre-wrap">
                          {msg.text}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            }

            if (msg.errorState) {
              return (
                <article key={msg.id} className="rounded-[24px] border border-rose-500/40 bg-[#160a0c] p-6 shadow-[0_12px_45px_rgba(244,63,94,0.12)] k-fade-in font-mono group">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-[11px] bg-rose-500/20 text-rose-300 border border-rose-500/40 flex items-center justify-center font-bold text-xs">
                        ⚠️
                      </div>
                      <div>
                        <span className="block text-xs md:text-sm font-semibold text-rose-300">
                          Error de Comunicación Epistémica
                        </span>
                        <span className="block mt-0.5 text-[10px] uppercase tracking-wider text-rose-400/70">
                          ADR-008 §2 · Ejecución Detenida · Cero Generación Local
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase tracking-wider text-white/30">
                        {msg.timestamp}
                      </span>
                      {onDeleteMessage && (
                        <button
                          type="button"
                          onClick={() => setDeleteCandidateId(msg.id)}
                          className="opacity-0 group-hover:opacity-100 p-1 rounded text-white/40 hover:text-rose-400 hover:bg-rose-500/10 transition"
                          title="Borrar en cascada"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                  <p className="mt-4 text-sm md:text-[15px] leading-relaxed text-rose-200/90">
                    {msg.text}
                  </p>
                </article>
              );
            }

            const isEditingAssistant = editingMessageId === msg.id;
            const pedagogicalBadge = detectPedagogicalBadge(msg.text);

            return (
              <article
                key={msg.id}
                className="rounded-[24px] border border-white/[0.06] bg-gradient-to-b from-[#131316] to-[#0c0c0e] p-6 shadow-[0_16px_50px_rgba(0,0,0,0.35)] hover:border-white/[0.1] transition-all duration-200 k-fade-in font-sans group relative overflow-hidden"
              >
                {/* Micro-glow top border highlight */}
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/[0.14] to-transparent pointer-events-none" />

                <div className="flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 flex items-center justify-center font-bold text-xs font-mono shrink-0 shadow-xs">
                      T
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs md:text-sm font-semibold text-white font-mono">
                          {SYSTEM_NAME} Core · Tutor Epistémico
                        </span>
                        {pedagogicalBadge && (
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-wide uppercase border flex items-center gap-1 ${pedagogicalBadge.colorClass} ${pedagogicalBadge.borderClass} ${pedagogicalBadge.bgClass}`}>
                            <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0 animate-pulse" />
                            <span>{pedagogicalBadge.label}</span>
                          </span>
                        )}
                      </div>
                      <span className="block mt-0.5 text-[10px] uppercase tracking-wider text-white/35 font-mono truncate">
                        scope · {activeScope}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 font-mono">
                    {msg.edited && (
                      <span className="text-emerald-400/70 lowercase tracking-normal text-[10px] italic">
                        (editado)
                      </span>
                    )}
                    <span className="text-[10px] uppercase tracking-wider text-white/30">
                      {msg.timestamp}
                    </span>

                    {/* Botones de acción en hover para asistente */}
                    {!isEditingAssistant && (
                      <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1 ml-1.5">
                        <button
                          type="button"
                          onClick={() => handleCopyMessage(msg.id, msg.text)}
                          className="p-1.5 rounded-lg text-white/40 hover:text-emerald-300 hover:bg-white/[0.06] transition flex items-center gap-1"
                          title={copiedMessageId === msg.id ? "¡Copiado al portapapeles!" : "Copiar respuesta"}
                        >
                          {copiedMessageId === msg.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        {onEditMessage && (
                          <button
                            type="button"
                            onClick={() => startEditing(msg)}
                            className="p-1.5 rounded-lg text-white/40 hover:text-white hover:bg-white/[0.06] transition"
                            title="Editar mensaje"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                        {onDeleteMessage && (
                          <button
                            type="button"
                            onClick={() => setDeleteCandidateId(msg.id)}
                            className="p-1.5 rounded-lg text-white/40 hover:text-rose-400 hover:bg-rose-500/10 transition"
                            title="Borrar en cascada"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-5">
                  {isEditingAssistant ? (
                    <div className="space-y-2 font-mono">
                      <textarea
                        value={editDraftText}
                        onChange={(e) => setEditDraftText(e.target.value)}
                        className="w-full bg-black/40 border border-cyan-500/40 rounded-[10px] p-2.5 font-mono text-sm text-white focus:outline-none resize-y min-h-[90px]"
                        rows={4}
                      />
                      <div className="flex justify-end gap-2 text-xs">
                        <button
                          type="button"
                          onClick={cancelEditing}
                          className="px-2.5 py-1 rounded-[8px] bg-white/[0.05] text-white/60 hover:text-white transition"
                        >
                          Cancelar
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSaveEdit(msg.id)}
                          className="px-2.5 py-1 rounded-[8px] bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/30 transition font-semibold"
                        >
                          Guardar
                        </button>
                      </div>
                    </div>
                  ) : (
                    (() => {
                      const socraticData = extractSocraticChallenge(msg.text);
                      const socraticMatch = msg.text.match(/(?:###\s*Desafío Socrático|\*\*Desafío Socrático:\*\*|###\s*Pregunta Socrática|Desafío Socrático:)/i);
                      const cleanBody = socraticData.hasChallenge && socraticMatch && socraticMatch.index !== undefined
                        ? msg.text.substring(0, socraticMatch.index).trim()
                        : msg.text;

                      return (
                        <>
                          <ClaimText
                            text={cleanBody}
                            evidences={msg.evidences}
                            onOpenEvidence={onOpenEvidence}
                            onOpenCitation={onOpenCitation}
                          />

                          {msg.abstained && <AbstentionBanner reason={msg.abstentionReason} />}
                          {msg.facetCoverage && <FacetCoverageBar coverage={msg.facetCoverage} />}
                          {msg.claims && msg.claims.length > 0 && (
                            <div className="mt-3.5 p-3 rounded-[14px] bg-black/40 border border-white/[0.08] space-y-2 font-mono">
                              <span className="text-[10px] uppercase tracking-wider text-white/40 block font-semibold">
                                Aserciones Epistémicas Verificadas (E2)
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {msg.claims.map((c) => (
                                  <ClaimStatusBadge
                                    key={c.claim_id}
                                    claimId={c.claim_id}
                                    status={c.status}
                                    groundingRatio={c.grounding_ratio}
                                    hasRedaction={c.has_redaction}
                                  />
                                ))}
                              </div>
                            </div>
                          )}

                          {/* DESAFÍO SOCRÁTICO INTERACTIVO Y BKT EN VIVO */}
                          {socraticData.hasChallenge && (
                            <div className="mt-4 p-4 rounded-[16px] bg-gradient-to-b from-emerald-950/20 to-black/50 border border-emerald-500/25 space-y-3 font-mono shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <HelpCircle className="w-4 h-4 text-emerald-400" />
                                  <span className="text-xs font-semibold text-emerald-300">Desafío Socrático Interactivo</span>
                                </div>
                                {bktProgress[msg.id] && (
                                  <div className="flex items-center gap-2">
                                    {bktProgress[msg.id].delta_p_L !== undefined && bktProgress[msg.id].delta_p_L !== 0 && (
                                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold font-mono border ${
                                        bktProgress[msg.id].delta_p_L! > 0
                                          ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                                          : "bg-rose-500/20 text-rose-300 border-rose-500/40"
                                      }`}>
                                        {bktProgress[msg.id].delta_p_L! > 0 ? `+${(bktProgress[msg.id].delta_p_L! * 100).toFixed(1)}%` : `${(bktProgress[msg.id].delta_p_L! * 100).toFixed(1)}%`} ΔP(L)
                                      </span>
                                    )}
                                    <span className={`text-[11px] px-2.5 py-0.5 rounded-full border flex items-center gap-1.5 font-bold ${
                                      bktProgress[msg.id].is_correct
                                        ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                                        : "bg-amber-500/20 text-amber-300 border-amber-500/40"
                                    }`}>
                                      {bktProgress[msg.id].is_correct ? (
                                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                      ) : (
                                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                                      )}
                                      BKT P(L): {(bktProgress[msg.id].p_L * 100).toFixed(1)}%
                                    </span>
                                  </div>
                                )}
                              </div>

                              {/* Enunciado del Desafío */}
                              <div className="p-3 rounded-[10px] bg-black/60 border border-emerald-500/20 text-xs text-white/90 leading-relaxed font-sans">
                                <p className="whitespace-pre-wrap">{socraticData.questionText}</p>
                              </div>

                              {/* Estado de Evaluación */}
                              {bktProgress[msg.id] ? (
                                <div className={`p-3.5 rounded-[12px] border text-xs leading-relaxed space-y-2.5 ${
                                  bktProgress[msg.id].is_correct
                                    ? "bg-emerald-950/30 border-emerald-500/40 text-emerald-200"
                                    : "bg-amber-950/30 border-amber-500/40 text-amber-200"
                                }`}>
                                  <div className="flex items-center justify-between">
                                    <span className="font-bold uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                                      {bktProgress[msg.id].is_correct ? "¡Desafío Superado!" : "Respuesta Parcial / Incorrecta"}
                                    </span>
                                    <div className="flex items-center gap-2">
                                      {bktProgress[msg.id].hints && bktProgress[msg.id].hints!.length > 0 && (
                                        <button
                                          type="button"
                                          onClick={() => setShowHints((prev) => ({ ...prev, [msg.id]: !prev[msg.id] }))}
                                          className="px-2 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-[10px] font-semibold transition"
                                        >
                                          {showHints[msg.id] ? "Ocultar Pistas" : "Ver Pistas Socráticas"}
                                        </button>
                                      )}
                                      {!bktProgress[msg.id].is_correct && (
                                        <button
                                          type="button"
                                          onClick={() => setBktProgress((prev) => {
                                            const next = { ...prev };
                                            delete next[msg.id];
                                            return next;
                                          })}
                                          className="px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 text-[10px] font-semibold transition"
                                        >
                                          Reintentar
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                  <p className="text-[11.5px] opacity-90">{bktProgress[msg.id].feedback}</p>

                                  {showHints[msg.id] && bktProgress[msg.id].hints && (
                                    <div className="mt-2 p-2.5 rounded-[8px] bg-black/50 border border-emerald-500/30 space-y-1.5 font-mono text-[11px] text-emerald-200">
                                      <span className="font-bold text-emerald-400 block text-[10px] uppercase tracking-wider">
                                        Pistas Epistémicas Guiadas:
                                      </span>
                                      <ul className="list-disc list-inside space-y-1">
                                        {bktProgress[msg.id].hints!.map((h, i) => (
                                          <li key={i}>{h}</li>
                                        ))}
                                      </ul>
                                    </div>
                                  )}
                                </div>
                              ) : (
                                <div className="space-y-2.5">
                                  {/* Opciones Múltiples si están presentes */}
                                  {socraticData.isMultipleChoice && (
                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                      {socraticData.options.map((opt) => (
                                        <button
                                          key={opt.key}
                                          type="button"
                                          disabled={socraticEvaluating[msg.id]}
                                          onClick={() => {
                                            setSocraticAnswers((prev) => ({ ...prev, [msg.id]: opt.key }));
                                            handleEvaluateSocratic(msg.id, opt.key, true);
                                          }}
                                          className={`p-2.5 rounded-[10px] border text-left text-xs transition flex items-start gap-2 ${
                                            socraticAnswers[msg.id] === opt.key
                                              ? "bg-emerald-500/20 border-emerald-400 text-white font-semibold"
                                              : "bg-black/40 border-white/[0.08] hover:border-emerald-500/30 text-white/80 hover:text-white"
                                          }`}
                                        >
                                          <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center justify-center text-[10px] font-bold shrink-0">
                                            {opt.key}
                                          </span>
                                          <span className="leading-snug">{opt.text}</span>
                                        </button>
                                      ))}
                                    </div>
                                  )}

                                  {/* Campo de Entrada Libre o Justificación */}
                                  <div className="flex gap-2">
                                    <input
                                      type="text"
                                      placeholder={socraticData.isMultipleChoice ? "O escribí tu justificación o respuesta..." : "Escribí tu respuesta al desafío socrático..."}
                                      value={socraticAnswers[msg.id] || ""}
                                      onChange={(e) => setSocraticAnswers((prev) => ({ ...prev, [msg.id]: e.target.value }))}
                                      onKeyDown={(e) => {
                                        if (e.key === "Enter" && (socraticAnswers[msg.id] || "").trim()) {
                                          handleEvaluateSocratic(msg.id, socraticAnswers[msg.id], socraticData.isMultipleChoice);
                                        }
                                      }}
                                      className="flex-1 bg-black/60 border border-white/[0.1] focus:border-emerald-500/50 rounded-[10px] px-3 py-1.5 text-xs text-white placeholder-white/30 outline-none"
                                    />
                                    <button
                                      type="button"
                                      disabled={socraticEvaluating[msg.id] || !(socraticAnswers[msg.id] || "").trim()}
                                      onClick={() => handleEvaluateSocratic(msg.id, socraticAnswers[msg.id], socraticData.isMultipleChoice)}
                                      className="px-3.5 py-1.5 rounded-[10px] bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 text-xs font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition flex items-center gap-1.5"
                                    >
                                      {socraticEvaluating[msg.id] ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Verificar"}
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </>
                      );
                    })()
                  )}
                </div>

                <div className="mt-6 pt-4 border-t border-white/[0.06] flex flex-wrap items-center justify-between gap-3">
                  <div className="flex flex-wrap items-center gap-2">
                    {msg.evidences && msg.evidences.length > 0 ? (
                      <button
                        type="button"
                        onClick={() => {
                          if (onOpenEvidence) {
                            onOpenEvidence("evidencia");
                          }
                        }}
                        className="text-[11px] text-white/60 hover:text-emerald-300 flex items-center gap-1.5 transition cursor-pointer"
                        title="Abrir panel de fuentes consultadas"
                      >
                        <BookOpen className="w-3.5 h-3.5 text-emerald-400" />
                        {msg.evidences.length} {msg.evidences.length === 1 ? "fuente consultada" : "fuentes consultadas"}
                      </button>
                    ) : null}
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleCopyMessage(msg.id, msg.text)}
                      className={[
                        "h-8 px-3 rounded-full font-mono text-xs flex items-center gap-1.5 transition cursor-pointer",
                        copiedMessageId === msg.id
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          : "bg-white/[0.04] border border-white/[0.08] text-white/60 hover:text-white hover:bg-white/[0.08]",
                      ].join(" ")}
                      title="Copiar texto completo al portapapeles"
                    >
                      {copiedMessageId === msg.id ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>¡Copiado!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copiar</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => onSaveNote(msg.id, msg.text)}
                      className={[
                        "h-8 px-3 rounded-full font-mono text-xs flex items-center gap-2 transition cursor-pointer",
                        msg.isSaved
                          ? "bg-white text-black font-semibold"
                          : "bg-white/[0.04] border border-white/[0.08] text-white/60 hover:text-white hover:bg-white/[0.08]",
                      ].join(" ")}
                    >
                      {msg.isSaved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                      {msg.isSaved ? "Nota anclada" : "Guardar nota"}
                    </button>
                  </div>
                </div>
              </article>
            );
          })}

          {isThinking && (
            <ThinkingIndicator thinkingStep={thinkingStep} />
          )}

          {isStreaming && (
            <article className="rounded-[24px] border border-white/[0.06] bg-gradient-to-b from-[#131316] to-[#0c0c0e] p-6 shadow-[0_16px_50px_rgba(0,0,0,0.35)] k-fade-in font-sans relative overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-emerald-400/20 to-transparent pointer-events-none" />
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/25 flex items-center justify-center text-xs font-bold font-mono shrink-0 shadow-xs">
                  T
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold text-white">
                    {SYSTEM_NAME} Core · Emitiendo
                  </span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-medium tracking-wide uppercase border border-emerald-500/25 bg-emerald-500/10 text-emerald-300 flex items-center gap-1 shadow-xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0 animate-pulse" />
                    <span>En vivo</span>
                  </span>
                </div>
              </div>

              <div className="mt-4">
                <MessageBody
                  content={streamedText}
                  onOpenEvidence={onOpenEvidence}
                  onOpenCitation={onOpenCitation}
                />
                <span className="inline-block w-2 h-4 bg-emerald-400 ml-1 align-middle animate-pulse shadow-[0_0_8px_#10b981]" />
              </div>
            </article>
          )}

          <div ref={scrollBottomAnchorRef} className="h-2 w-full" />
        </div>
      </div>

      {/* BOTÓN FLOTANTE PARA VOLVER AL ÚLTIMO MENSAJE */}
      {showScrollBottomBtn && (
        <div className="absolute bottom-4 right-6 sm:right-10 z-30 pointer-events-auto k-fade-in">
          <button
            type="button"
            onClick={() => scrollToBottom("smooth")}
            className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-[#141417]/95 hover:bg-[#1f1f26] text-white/80 hover:text-white border border-white/[0.14] hover:border-emerald-500/30 shadow-[0_8px_30px_rgba(0,0,0,0.7)] backdrop-blur-md transition-all duration-200 group text-xs font-mono active:scale-95 cursor-pointer select-none"
            title="Ir al último mensaje"
          >
            <ArrowDown className="w-3.5 h-3.5 text-emerald-400 group-hover:translate-y-0.5 transition-transform" />
            <span className="text-[11px] font-medium tracking-wide">Último mensaje</span>
          </button>
        </div>
      )}
    </div>
  );
};

export { DialogueView };

export default ChatMessages;
