import React, { useState } from 'react';
import {
  MessageSquare,
  Sparkles,
  HelpCircle,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Send,
  AlertCircle,
  CheckCircle2
} from 'lucide-react';

export interface CitationRecord {
  citation_id: string;
  source_id: string;
  text: string;
}

export interface SocraticQuestion {
  question_id: string;
  question_text: string;
  target_dimension?: string;
}

export interface DialogueTurn {
  turn_id: string;
  student_message: string;
  presented_response?: string;
  presented_socratic_question?: SocraticQuestion;
  evidence_used?: CitationRecord[];
}

export interface DialogueState {
  turns: DialogueTurn[];
  turn_count: number;
  dialogue_limit_reached: boolean;
  limit_reason?: string;
}

export interface DialogueResponse {
  suggestion_text?: string;
}

export interface DialogueViewProps {
  episode: { phase: string; episode_id?: string };
  dialogueState?: DialogueState;
  dialogueResponse?: DialogueResponse;
  MAX_DIALOGUE_TURNS?: number;
  sendDialogueMessage: (msg: string) => void;
  acceptExercise: () => void;
  rejectExercise: () => void;
  endDialogue: () => void;
}

const ClaimText: React.FC<{ text: string; evidences?: CitationRecord[] }> = ({ text, evidences }) => {
  return (
    <div className="text-white/85 leading-relaxed font-sans text-xs md:text-sm">
      <p>{text}</p>
      {evidences && evidences.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {evidences.map((ev, idx) => (
            <span
              key={ev.citation_id || idx}
              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-[10px] font-mono text-cyan-300"
              title={ev.text}
            >
              <BookOpen className="w-2.5 h-2.5" />
              <span>{ev.source_id || `E${idx + 1}`}</span>
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export const DialogueView: React.FC<DialogueViewProps> = ({
  episode,
  dialogueState = { turns: [], turn_count: 0, dialogue_limit_reached: false },
  dialogueResponse = {},
  MAX_DIALOGUE_TURNS = 5,
  sendDialogueMessage,
  acceptExercise,
  rejectExercise,
  endDialogue,
}) => {
  const [inputText, setInputText] = useState("");

  const isDialoguePhase =
    episode.phase === "DIALOGUE" ||
    episode.phase === "SOCRATIC_DIALOGUE" ||
    episode.phase === "DIALOGUE_LIMIT_REACHED" ||
    episode.phase === "SUGGEST_EXERCISE";

  if (!isDialoguePhase) {
    return null;
  }

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    sendDialogueMessage(text);
    setInputText("");
  };

  const isLimitReached = episode.phase === "DIALOGUE_LIMIT_REACHED" || dialogueState.dialogue_limit_reached;
  const isSuggestExercise = episode.phase === "SUGGEST_EXERCISE";
  const isNormalDialogue = episode.phase === "DIALOGUE" || episode.phase === "SOCRATIC_DIALOGUE";

  return (
    <div className="w-full bg-[#0c0d12]/90 border border-white/[0.08] rounded-2xl p-4 md:p-5 shadow-2xl backdrop-blur-md mb-4 text-white">
      {/* Header del Diálogo Socrático */}
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-white/[0.07]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-cyan-300">
              Diálogo Socrático Guiado
            </h3>
            <p className="text-[11px] text-white/40 font-mono">
              Exploración conceptual sin penalización · Construcción guiada
            </p>
          </div>
        </div>
        <div className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] text-[10px] font-mono text-white/50">
          Turno {dialogueState.turn_count} / {MAX_DIALOGUE_TURNS}
        </div>
      </div>

      {/* Historial de Turnos */}
      {dialogueState.turns && dialogueState.turns.length > 0 && (
        <div className="space-y-3 mb-4 max-h-[360px] overflow-y-auto pr-1">
          {dialogueState.turns.map((turn) => (
            <div key={turn.turn_id} className="space-y-2">
              {/* Mensaje del estudiante */}
              <div className="flex justify-end">
                <div className="max-w-[85%] bg-cyan-950/40 border border-cyan-500/20 rounded-xl rounded-tr-sm p-3 text-cyan-100 text-xs md:text-sm shadow-sm">
                  <div className="text-[10px] uppercase font-mono tracking-wider text-cyan-400/70 mb-1">
                    Vos
                  </div>
                  <p className="leading-relaxed">{turn.student_message}</p>
                </div>
              </div>

              {/* Respuesta del tutor */}
              {turn.presented_response && (
                <div className="flex justify-start">
                  <div className="max-w-[85%] bg-white/[0.03] border border-white/[0.07] rounded-xl rounded-tl-sm p-3 text-white/90 text-xs md:text-sm shadow-sm">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase font-mono tracking-wider text-white/40 mb-1">
                      <MessageSquare className="w-3 h-3 text-cyan-400" />
                      <span>TALOS</span>
                    </div>
                    <ClaimText
                      text={turn.presented_response}
                      evidences={turn.evidence_used}
                    />
                  </div>
                </div>
              )}

              {/* Pregunta socrática */}
              {turn.presented_socratic_question && (
                <div className="bg-amber-950/25 border border-amber-500/25 rounded-xl p-3 text-amber-200/90 text-xs md:text-sm">
                  <div className="flex items-start gap-2">
                    <div className="p-1 rounded bg-amber-500/10 text-amber-400 mt-0.5">
                      <HelpCircle className="w-3.5 h-3.5" />
                    </div>
                    <div>
                      <p className="font-medium text-amber-100">
                        {turn.presented_socratic_question.question_text}
                      </p>
                      <span className="inline-block text-[10px] font-mono text-amber-400/60 mt-1">
                        💡 Razonalo paso a paso. No hay calificación aquí, el objetivo es comprender.
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Input del estudiante durante DIALOGUE normal */}
      {isNormalDialogue && !isLimitReached && (
        <div className="space-y-3 pt-2">
          <div className="relative">
            <textarea
              className="w-full bg-[#13151f] border border-white/10 focus:border-cyan-500/50 rounded-xl p-3 text-xs md:text-sm text-white placeholder-white/30 focus:outline-none transition resize-none font-sans min-h-[70px]"
              placeholder="Preguntá una duda, pedí un ejemplo o profundizá el razonamiento..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage(inputText);
                }
              }}
            />
            <button
              onClick={() => sendMessage(inputText)}
              disabled={!inputText.trim()}
              className="absolute bottom-2.5 right-2.5 px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-30 text-white font-mono text-xs flex items-center gap-1.5 transition shadow-md"
            >
              <span>Enviar</span>
              <Send className="w-3 h-3" />
            </button>
          </div>

          {/* Quick Action Chips */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] font-mono">
            <span className="text-white/30 text-[10px] uppercase tracking-wider mr-1">Atajos:</span>
            <button
              type="button"
              onClick={() => sendMessage("dame un ejemplo práctico")}
              className="px-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-white/70 hover:text-white transition flex items-center gap-1"
            >
              <Sparkles className="w-2.5 h-2.5 text-cyan-400" />
              <span>Dame un ejemplo</span>
            </button>
            <button
              type="button"
              onClick={() => sendMessage("explicá esto de otra forma más intuitiva")}
              className="px-2.5 py-1 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] text-white/70 hover:text-white transition flex items-center gap-1"
            >
              <RotateCcw className="w-2.5 h-2.5 text-amber-400" />
              <span>Explicá de otra forma</span>
            </button>
            <button
              type="button"
              onClick={() => {
                sendMessage("pasá al ejercicio");
                acceptExercise();
              }}
              className="px-2.5 py-1 rounded-full bg-cyan-950/50 hover:bg-cyan-900/60 border border-cyan-500/30 text-cyan-300 transition flex items-center gap-1"
            >
              <span>Ir al ejercicio</span>
              <ArrowRight className="w-2.5 h-2.5" />
            </button>
          </div>
        </div>
      )}

      {/* Límite de diálogo alcanzado */}
      {isLimitReached && (
        <div className="bg-amber-950/20 border border-amber-500/30 rounded-xl p-4 my-2">
          <div className="flex items-start gap-2.5 mb-3">
            <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs md:text-sm font-medium text-amber-200">
                Límite de turnos de diálogo alcanzado
                {dialogueState.limit_reason ? ` (${dialogueState.limit_reason})` : ""}.
              </p>
              <p className="text-xs text-white/60 mt-0.5">
                Para consolidar tu aprendizaje, es momento de poner en práctica lo reflexionado con un ejercicio formal.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-1 font-mono text-xs">
            <button
              onClick={() => acceptExercise()}
              className="px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1.5 transition shadow"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Sí, hacer el ejercicio</span>
            </button>
            <button
              onClick={() => rejectExercise()}
              className="px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] border border-white/10 text-white/80 transition"
            >
              Quiero seguir dialogando
            </button>
            <button
              onClick={() => endDialogue()}
              className="px-3 py-1.5 rounded-lg bg-red-950/40 hover:bg-red-900/50 border border-red-500/30 text-red-300 transition"
            >
              Terminar sesión
            </button>
          </div>
        </div>
      )}

      {/* Sugerencia de Ejercicio */}
      {isSuggestExercise && !isLimitReached && (
        <div className="bg-cyan-950/30 border border-cyan-500/30 rounded-xl p-4 my-2">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-cyan-400" />
            <p className="text-xs md:text-sm font-medium text-cyan-200">
              {dialogueResponse.suggestion_text || "¿Listo para verificar tu comprensión con un ejercicio?"}
            </p>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs mt-3">
            <button
              onClick={() => acceptExercise()}
              className="px-3.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold flex items-center gap-1.5 transition shadow"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Sí, pasar al ejercicio</span>
            </button>
            <button
              onClick={() => rejectExercise()}
              className="px-3 py-1.5 rounded-lg bg-white/[0.06] hover:bg-white/[0.1] border border-white/10 text-white/80 transition"
            >
              Seguir explorando
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
