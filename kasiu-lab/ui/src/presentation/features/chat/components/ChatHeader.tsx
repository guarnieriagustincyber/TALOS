import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  BookOpen,
  Brain,
  Calendar as CalendarIcon,
  CheckSquare,
  ChevronDown,
  Database,
  FolderTree,
  GraduationCap,
  Layers,
  Maximize2,
  MessageSquare,
  Minimize2,
  Network,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Settings,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { ActiveEntity, TopView } from "../../views/types";
import { SYSTEM_NAME } from "./shared";

export interface ChatHeaderProps {
  currentView: TopView;
  p1Open: boolean;
  p3Open: boolean;
  activeEntity?: ActiveEntity;
  fontScale?: "standard" | "comfort" | "large";
  backendOnline?: boolean | null;
  isZenMode?: boolean;
  onToggleZenMode?: () => void;
  onChangeFontScale?: (scale: "standard" | "comfort" | "large") => void;
  onView: (view: TopView) => void;
  onToggleP1: () => void;
  onToggleP3: () => void;
  onOpenStudySlice?: () => void;
  onOpenCognitiveProfile?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  currentView,
  p1Open,
  p3Open,
  backendOnline,
  isZenMode,
  onToggleZenMode,
  onView,
  onToggleP1,
  onToggleP3,
  onOpenStudySlice,
  onOpenCognitiveProfile,
}) => {
  const [infraMenuOpen, setInfraMenuOpen] = useState(false);
  const infraMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (infraMenuRef.current && !infraMenuRef.current.contains(event.target as Node)) {
        setInfraMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const coreNav = [
    { id: "chat" as TopView, icon: MessageSquare, label: "Asistente" },
    { id: "arbol" as TopView, icon: FolderTree, label: "Cuadernos" },
    { id: "libros" as TopView, icon: BookOpen, label: "Biblioteca" },
    { id: "estudiante" as TopView, icon: GraduationCap, label: "Estudiante" },
    { id: "tareas" as TopView, icon: CheckSquare, label: "Misión" },
    { id: "agenda" as TopView, icon: CalendarIcon, label: "Agenda" },
  ];

  const infraNav = [
    { id: "ingesta" as TopView, icon: Database, label: "Ingesta CAL" },
    { id: "federacion" as TopView, icon: Network, label: "Federación" },
    { id: "threatintel" as TopView, icon: ShieldAlert, label: "Threat Intel" },
    { id: "telemetria" as TopView, icon: Activity, label: "Telemetría" },
    { id: "gates" as TopView, icon: ShieldCheck, label: "Gates" },
    { id: "config" as TopView, icon: Settings, label: "Configuración" },
  ];

  const activeInfraItem = infraNav.find((i) => i.id === currentView);

  // En modo chat, la nav central incluye todos los elementos integrados
  const isChatView = currentView === "chat";

  return (
    <header className="h-12 border-b border-white/[0.06] bg-[#0c0c0e]/95 backdrop-blur-xl shrink-0 relative z-40 w-full flex items-center px-3 gap-2 select-none box-border">

      {/* ZONA IZQUIERDA: Toggle Árbol + Brand */}
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={onToggleP1}
          className={[
            "w-7 h-7 rounded-lg border flex items-center justify-center transition select-none shrink-0 cursor-pointer",
            p1Open
              ? "bg-white/[0.08] text-white border-white/[0.12]"
              : "text-white/30 border-white/[0.05] hover:text-white/60 hover:bg-white/[0.04]",
          ].join(" ")}
          title={p1Open ? "Ocultar Árbol (Ctrl+1)" : "Mostrar Árbol (Ctrl+1)"}
        >
          {p1Open ? <PanelLeftClose className="w-3.5 h-3.5" /> : <PanelLeftOpen className="w-3.5 h-3.5" />}
        </button>

        <div
          className="h-7 px-2.5 rounded-lg bg-white/[0.02] border border-white/[0.05] flex items-center gap-1.5 shrink-0"
          title={
            backendOnline
              ? "Servidor TALOS conectado"
              : backendOnline === false
              ? "Servidor desconectado"
              : "Comprobando..."
          }
        >
          <span className="text-[11px] font-mono font-bold tracking-[0.16em] text-white/80">
            {SYSTEM_NAME}
          </span>
          <span
            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
              backendOnline
                ? "bg-emerald-400 shadow-[0_0_5px_#34d399] animate-pulse"
                : backendOnline === false
                ? "bg-rose-500"
                : "bg-amber-400 animate-pulse"
            }`}
          />
        </div>
      </div>

      {/* ZONA CENTRAL: Todo el nav integrado y centrado */}
      <nav className="flex-1 flex items-center justify-center min-w-0">
        <div className="inline-flex items-center gap-0.5 bg-black/40 border border-white/[0.07] p-0.5 rounded-xl backdrop-blur-md shadow-inner shrink-0 relative">

          {/* Tabs principales */}
          {coreNav.map((item) => {
            const Icon = item.icon;
            const active = currentView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onView(item.id)}
                className={[
                  "relative h-7 px-2.5 rounded-lg flex items-center justify-center gap-1.5 text-[11px] font-mono tracking-wide shrink-0 cursor-pointer select-none transition-colors",
                  active
                    ? "text-white font-medium"
                    : "text-white/40 hover:text-white/70 hover:bg-white/[0.03]",
                ].join(" ")}
                title={item.label}
              >
                {active && (
                  <motion.div
                    layoutId="active-folder-tab"
                    className="absolute inset-0 bg-white/[0.08] border border-white/[0.12] rounded-lg shadow-sm"
                    transition={{ type: "spring", bounce: 0.12, duration: 0.3 }}
                  />
                )}
                <Icon className={`relative z-10 w-3.5 h-3.5 shrink-0 ${active ? "opacity-100 text-emerald-400" : "opacity-50"}`} />
                <span className="relative z-10 truncate hidden sm:inline">{item.label}</span>
              </button>
            );
          })}

          {/* Separador sutil */}
          <div className="w-px h-4 bg-white/[0.08] mx-0.5 shrink-0" />

          {/* Arquitectura dropdown — integrado en la nav central */}
          <div className="relative shrink-0 z-50" ref={infraMenuRef}>
            <button
              type="button"
              onClick={() => setInfraMenuOpen(!infraMenuOpen)}
              className={[
                "relative h-7 px-2 rounded-lg flex items-center gap-1 text-[11px] font-mono shrink-0 cursor-pointer select-none transition-colors",
                activeInfraItem
                  ? "text-white font-medium bg-white/[0.08] border border-white/[0.12]"
                  : "text-white/40 hover:text-white/70 hover:bg-white/[0.03]",
              ].join(" ")}
              title="Arquitectura / Infraestructura"
            >
              <Layers className="w-3.5 h-3.5 shrink-0 opacity-80" />
              <ChevronDown className={`w-2.5 h-2.5 opacity-40 transition-transform ${infraMenuOpen ? "rotate-180" : ""}`} />
            </button>

            {infraMenuOpen && (
              <div className="absolute top-full mt-2 left-1/2 -translate-x-1/2 w-48 rounded-xl bg-[#121215] border border-white/[0.14] shadow-[0_16px_40px_rgba(0,0,0,0.8)] p-1.5 z-[100] k-fade-in font-mono backdrop-blur-2xl">
                <div className="px-2.5 py-1 text-[9px] text-white/30 uppercase tracking-widest border-b border-white/[0.06] mb-1 font-semibold">
                  CAL / E4 / E5
                </div>
                {infraNav.map((item) => {
                  const Icon = item.icon;
                  const active = currentView === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => { onView(item.id); setInfraMenuOpen(false); }}
                      className={[
                        "w-full h-7 px-2.5 rounded-lg flex items-center gap-2 text-[11px] transition text-left cursor-pointer",
                        active ? "bg-white/[0.1] text-white font-medium" : "text-white/55 hover:text-white hover:bg-white/[0.05]",
                      ].join(" ")}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0 opacity-70" />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Perfil Cognitivo — integrado en nav central */}
          {onOpenCognitiveProfile && (
            <>
              <div className="w-px h-4 bg-white/[0.08] mx-0.5 shrink-0" />
              <button
                type="button"
                onClick={onOpenCognitiveProfile}
                className="relative h-7 px-2 rounded-lg flex items-center gap-1.5 text-[11px] font-mono shrink-0 cursor-pointer select-none transition-colors text-white/40 hover:text-white/70 hover:bg-white/[0.03]"
                title="Perfil Cognitivo BKT"
              >
                <Brain className="w-3.5 h-3.5 shrink-0 opacity-80" />
              </button>
            </>
          )}

          {/* Estudiar — integrado en nav central */}
          {onOpenStudySlice && (
            <button
              type="button"
              onClick={onOpenStudySlice}
              className="relative h-7 px-2 rounded-lg flex items-center gap-1.5 text-[11px] font-mono shrink-0 cursor-pointer select-none transition-colors text-emerald-400/50 hover:text-emerald-300 hover:bg-emerald-500/[0.06]"
              title="Estudiar (Vertical Slice)"
            >
              <Sparkles className="w-3.5 h-3.5 shrink-0" />
            </button>
          )}
        </div>
      </nav>

      {/* ZONA DERECHA: Solo iconos sutiles para Zen y Evidencia */}
      <div className="flex items-center gap-1 shrink-0">
        {/* Zen — ultra-sutil, solo icono */}
        {isChatView && (
          <button
            onClick={onToggleZenMode}
            className={[
              "w-7 h-7 rounded-lg border flex items-center justify-center transition cursor-pointer shrink-0",
              isZenMode
                ? "bg-white/[0.08] text-white border-white/[0.12]"
                : "text-white/25 border-transparent hover:text-white/50 hover:border-white/[0.06]",
            ].join(" ")}
            title={isZenMode ? "Salir de Modo Zen (Esc)" : "Modo Zen (Ctrl+Z)"}
          >
            {isZenMode ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        )}

        {/* Evidencia — solo icono */}
        {isChatView && (
          <button
            onClick={onToggleP3}
            className={[
              "w-7 h-7 rounded-lg border flex items-center justify-center transition cursor-pointer shrink-0",
              p3Open
                ? "bg-white/[0.08] text-white border-white/[0.12]"
                : "text-white/25 border-transparent hover:text-white/50 hover:border-white/[0.06]",
            ].join(" ")}
            title={p3Open ? "Ocultar Evidencia (Ctrl+3)" : "Mostrar Evidencia (Ctrl+3)"}
          >
            {p3Open ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
          </button>
        )}
      </div>
    </header>
  );
};


export const TopRail = ChatHeader;
export default ChatHeader;

