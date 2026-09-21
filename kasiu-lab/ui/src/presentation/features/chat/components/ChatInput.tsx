import React, { useState } from "react";
import {
  ArrowUp,
  Code,
  Square,
  Trash2,
} from "lucide-react";
import { SYSTEM_NAME } from "./shared";

export interface ChatInputProps {
  activeScope: string;
  isThinking: boolean;
  isStreaming: boolean;
  onSend: (text: string) => void;
  onStop?: () => void;
  onClearHistory?: () => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  activeScope,
  isThinking,
  isStreaming,
  onSend,
  onStop,
  onClearHistory,
}) => {
  const [localPrompt, setLocalPrompt] = useState("");
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  // Auto‑resize textarea based on its content
  React.useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const nextH = Math.min(Math.max(el.scrollHeight, 44), 220);
    el.style.height = `${nextH}px`;
  }, [localPrompt]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!isThinking && !isStreaming && localPrompt.trim()) {
        onSend(localPrompt.trim());
        setLocalPrompt("");
      }
    }
  };

  const handleSendClick = () => {
    if (localPrompt.trim()) {
      onSend(localPrompt.trim());
      setLocalPrompt("");
    }
  };

  return (
    <div className="px-4 sm:px-8 md:px-14 lg:px-20 pb-4 sm:pb-6 md:pb-8 pt-2 shrink-0">
      <div className="w-full max-w-[980px] mx-auto">
        <div className="rounded-2xl border border-white/[0.08] bg-[#0d0d10]/95 backdrop-blur-xl p-3 focus-within:border-white/20 transition-all shadow-2xl">
          <textarea
            ref={textareaRef}
            rows={1}
            value={localPrompt}
            onChange={(e) => setLocalPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Pregunta a ${SYSTEM_NAME} sobre ${activeScope} o escribe :eval...`}
            className="w-full resize-none outline-none bg-transparent px-2.5 py-1 font-mono text-xs md:text-sm leading-relaxed text-white placeholder:text-white/25 k-scroll transition-[height] duration-75 min-h-[44px] max-h-[220px]"
          />

          <div className="mt-1.5 pt-2 border-t border-white/[0.05] flex items-center justify-between gap-2">
            <div className="flex items-center gap-1.5 min-w-0">
              <button
                type="button"
                onClick={() => setLocalPrompt("/practicar ")}
                className="h-8 px-3 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] hover:border-white/20 text-white/70 hover:text-white text-[11px] font-mono flex items-center gap-1.5 transition-all duration-150 select-none shrink-0 shadow-xs"
                title="Pedir un ejercicio socrático certificado (/practicar [tema])"
              >
                <Code className="w-3.5 h-3.5 text-white/50 shrink-0" />
                <span>/practicar</span>
              </button>

              {onClearHistory && (
                <button
                  type="button"
                  onClick={onClearHistory}
                  className="h-8 px-2.5 rounded-xl bg-transparent border border-transparent hover:bg-rose-500/10 hover:border-rose-500/20 text-white/40 hover:text-rose-400 text-[11px] font-mono flex items-center gap-1 transition-all duration-150 select-none shrink-0"
                  title="Limpiar conversación (no afecta el progreso cognitivo BKT)"
                >
                  <Trash2 className="w-3 h-3 shrink-0" />
                  <span className="hidden sm:inline">Limpiar chat</span>
                </button>
              )}
            </div>

            {/* Stop button when thinking/streaming, otherwise Send */}
            {isThinking || isStreaming ? (
              <button
                type="button"
                onClick={onStop}
                className="h-8 px-3.5 rounded-xl flex items-center gap-2 transition-all duration-150 text-xs font-mono font-medium select-none shrink-0 bg-rose-500/20 text-rose-300 border border-rose-500/30 hover:bg-rose-500/30 hover:border-rose-500/40 active:scale-95 shadow-sm"
                title="Detener respuesta (Abort)"
              >
                <Square className="w-3 h-3 fill-current animate-pulse" />
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={handleSendClick}
                disabled={!localPrompt.trim()}
                className={[
                  "h-8 px-4 rounded-xl flex items-center gap-2 transition-all duration-150 text-xs font-mono font-semibold select-none shrink-0",
                  localPrompt.trim()
                    ? "bg-white text-black hover:bg-white/90 active:scale-95 shadow-[0_0_16px_rgba(255,255,255,0.18)] hover:shadow-[0_0_20px_rgba(255,255,255,0.28)] cursor-pointer"
                    : "bg-white/[0.03] text-white/20 border border-white/[0.05] cursor-not-allowed opacity-60",
                ].join(" ")}
                title="Enviar mensaje (Enter)"
              >
                <span>Enviar</span>
                <ArrowUp className={`w-3.5 h-3.5 stroke-[2.5] transition-transform duration-150 ${localPrompt.trim() ? "group-hover:-translate-y-0.5" : ""}`} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInput;
