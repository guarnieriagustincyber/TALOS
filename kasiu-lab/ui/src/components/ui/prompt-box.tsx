"use client";

import React, { useRef, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowUp,
  Plus,
  Square,
  Code2,
  Sparkles,
  BookOpen,
  BrainCircuit,
} from "lucide-react";
import { useClickOutside } from "@/hooks/use-click-outside";
import { cn } from "@/lib/utils";

export interface PromptAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  prefix: string;
}

export interface PromptBoxProps {
  onSend: (message: string) => void;
  placeholder?: string;
  isThinking?: boolean;
  isStreaming?: boolean;
  onStop?: () => void;
  className?: string;
  autoFocus?: boolean;
}

const DEFAULT_ACTIONS: PromptAction[] = [
  {
    id: "practicar",
    label: "Ejercicio Socrático (/practicar)",
    icon: <Code2 className="w-3.5 h-3.5 text-emerald-400" />,
    prefix: "/practicar ",
  },
  {
    id: "explicar",
    label: "Explicar Simple y Conceptual",
    icon: <Sparkles className="w-3.5 h-3.5 text-emerald-400" />,
    prefix: "¿Podrías explicar de manera conceptual y clara ",
  },
  {
    id: "evidencia",
    label: "Citar en el Libro / Corpus",
    icon: <BookOpen className="w-3.5 h-3.5 text-emerald-400" />,
    prefix: "¿En qué capítulo o página exacta del corpus se define ",
  },
  {
    id: "profundizar",
    label: "Profundizar en Detalles Internos",
    icon: <BrainCircuit className="w-3.5 h-3.5 text-emerald-400" />,
    prefix: "Profundicemos en los detalles internos y casos de borde de ",
  },
];

export const PromptBox: React.FC<PromptBoxProps> = ({
  onSend,
  placeholder = "Pregunta a TALOS sobre el corpus o escribe un comando...",
  isThinking = false,
  isStreaming = false,
  onStop,
  className,
  autoFocus = false,
}) => {
  const [prompt, setPrompt] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useClickOutside(menuRef, () => setMenuOpen(false));

  // Auto-resize textarea smoothly (min 44px, max 220px)
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const nextH = Math.min(Math.max(el.scrollHeight, 44), 220);
    el.style.height = `${nextH}px`;
  }, [prompt]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSend = () => {
    const trimmed = prompt.trim();
    if (!trimmed || isThinking || isStreaming) return;

    onSend(trimmed);
    setPrompt("");
  };

  const handleSelectAction = (action: PromptAction) => {
    setPrompt((prev) => {
      if (!prev) return action.prefix;
      return `${action.prefix}${prev}`;
    });
    setMenuOpen(false);
    textareaRef.current?.focus();
  };

  const canSend = prompt.trim().length > 0;
  const isBusy = isThinking || isStreaming;

  return (
    <div
      data-slot="card-footer"
      className={cn("w-full p-0", className)}
    >
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="w-full"
      >
        <div
          data-slot="input-group"
          role="group"
          className="group/input-group relative flex w-full min-w-0 flex-col rounded-2xl border border-white/[0.09] bg-[#0c0d12]/95 backdrop-blur-xl transition-[color,box-shadow] duration-200 outline-none focus-within:border-emerald-500/40 focus-within:ring-1 focus-within:ring-emerald-500/30 shadow-2xl"
        >
          {/* Textarea Area */}
          <div className="w-full px-3.5 pt-3 pb-1">
            <textarea
              ref={textareaRef}
              rows={1}
              autoFocus={autoFocus}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="w-full resize-none outline-none bg-transparent font-mono text-xs sm:text-sm leading-relaxed text-white placeholder:text-white/25 k-scroll min-h-[44px] max-h-[220px]"
            />
          </div>

          {/* Input Group Addon / Actions Bar */}
          <div
            role="group"
            data-slot="input-group-addon"
            data-align="block-end"
            className="flex items-center gap-2 px-3 pb-2.5 pt-1 w-full select-none"
          >
            {/* The Plus Button with Dropdown Menu */}
            <div className="relative" ref={menuRef}>
              <button
                type="button"
                data-slot="dropdown-menu-trigger"
                data-variant="outline"
                data-size="icon-sm"
                onClick={() => setMenuOpen((prev) => !prev)}
                className={cn(
                  "size-7 rounded-xl border border-white/[0.07] flex items-center justify-center transition-all cursor-pointer",
                  menuOpen
                    ? "bg-white/[0.12] text-white border-white/20 shadow-xs"
                    : "bg-white/[0.03] text-white/50 hover:bg-white/[0.08] hover:text-white/90 hover:border-white/[0.14]"
                )}
                aria-label="Acciones y prompts socráticos"
                title="Acciones rápidas socráticas"
              >
                <Plus className="w-3.5 h-3.5 stroke-[2]" />
              </button>

              {/* Floating Menu Popover */}
              <AnimatePresence>
                {menuOpen && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.96, y: 6 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.96, y: 6 }}
                    transition={{ duration: 0.12 }}
                    className="absolute bottom-full left-0 mb-2 w-72 rounded-2xl border border-white/[0.08] bg-[#0d0e12]/98 backdrop-blur-2xl p-1.5 shadow-[0_12px_40px_rgba(0,0,0,0.85)] z-50 font-mono text-xs"
                  >
                    <div className="px-2.5 py-1 text-[9.5px] uppercase tracking-wider text-white/35 font-semibold">
                      Comandos Socráticos
                    </div>
                    {DEFAULT_ACTIONS.map((action) => (
                      <button
                        key={action.id}
                        type="button"
                        onClick={() => handleSelectAction(action)}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left text-white/75 hover:text-white hover:bg-white/[0.06] transition-colors cursor-pointer text-xs"
                      >
                        {action.icon}
                        <span className="truncate">{action.label}</span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Quick action inline pills — estéticos, minimalistas y limpios */}
            <button
              type="button"
              onClick={() => handleSelectAction(DEFAULT_ACTIONS[0])}
              className="h-7 px-2.5 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.06] hover:border-emerald-500/30 text-white/55 hover:text-white text-[11px] font-mono flex items-center gap-1.5 transition-all select-none cursor-pointer group"
              title="Pedir ejercicio socrático certified"
            >
              <Code2 className="w-3 h-3 text-emerald-400/80 group-hover:text-emerald-300 transition-colors" />
              <span>/practicar</span>
            </button>

            <button
              type="button"
              onClick={() => handleSelectAction(DEFAULT_ACTIONS[1])}
              className="h-7 px-2.5 rounded-xl border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.06] hover:border-white/15 text-white/55 hover:text-white text-[11px] font-mono hidden sm:flex items-center gap-1.5 transition-all select-none cursor-pointer group"
              title="Explicar simple"
            >
              <Sparkles className="w-3 h-3 text-white/40 group-hover:text-white/70 transition-colors" />
              <span>Explicar</span>
            </button>

            {/* Right side: Send / Stop button */}
            <div className="flex items-center ml-auto">
              <AnimatePresence mode="wait">
                {isBusy ? (
                  <motion.button
                    key="stop"
                    initial={{ scale: 0.85, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.85, opacity: 0 }}
                    type="button"
                    onClick={onStop}
                    className="size-7 rounded-xl bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 flex items-center justify-center transition-all cursor-pointer active:scale-95"
                    title="Detener respuesta (Abort)"
                  >
                    <Square className="w-2.5 h-2.5 fill-current animate-pulse" />
                  </motion.button>
                ) : (
                  <motion.button
                    key="send"
                    whileHover={canSend ? { scale: 1.04 } : {}}
                    whileTap={canSend ? { scale: 0.94 } : {}}
                    type="submit"
                    disabled={!canSend}
                    data-slot="button"
                    data-variant="default"
                    data-size="icon-sm"
                    className={cn(
                      "size-7 rounded-xl flex items-center justify-center transition-all",
                      canSend
                        ? "bg-white text-black hover:bg-emerald-300 shadow-[0_0_12px_rgba(255,255,255,0.2)] cursor-pointer"
                        : "bg-white/[0.03] text-white/20 border border-white/[0.05] cursor-not-allowed"
                    )}
                    aria-label="Send"
                    title="Enviar mensaje (Enter)"
                  >
                    <ArrowUp className="w-3.5 h-3.5 stroke-[2.5]" />
                    <span className="sr-only">Send</span>
                  </motion.button>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export const PromptInputBox = PromptBox;
export default PromptBox;
