import React, { useEffect, useRef, useState } from "react";
import {
  Activity,
  BookOpen,
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
  ZoomIn,
} from "lucide-react";
import { ActiveEntity, TopView } from "../../views/types";
import { SYSTEM_NAME, THEME_COLORS, renderItemIcon } from "./shared";

export interface ChatHeaderProps {
  currentView: TopView;
  p1Open: boolean;
  p3Open: boolean;
  activeEntity: ActiveEntity;
  fontScale: "standard" | "comfort" | "large";
  backendOnline?: boolean | null;
  isZenMode?: boolean;
  onToggleZenMode?: () => void;
  onChangeFontScale: (scale: "standard" | "comfort" | "large") => void;
  onView: (view: TopView) => void;
  onToggleP1: () => void;
  onToggleP3: () => void;
  onOpenStudySlice?: () => void;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  currentView,
  p1Open,
  p3Open,
  activeEntity,
  fontScale,
  backendOnline,
  isZenMode,
  onToggleZenMode,
  onChangeFontScale,
  onView,
  onToggleP1,
  onToggleP3,
  onOpenStudySlice,
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

  return (
    <header className="px-3 pt-2 shrink-0 relative z-40 w-full max-w-full box-border">
      <div className="h-14 rounded-2xl bg-[#0c0c0e]/90 backdrop-blur-xl border border-white/[0.08] shadow-lg relative w-full box-border">
        <div className="h-full flex items-center justify-between px-3 md:px-4 gap-2 min-w-0">
          <div className="flex items-center gap-2 md:gap-2.5">
            <button
              onClick={onToggleP1}
              className={[
                "w-8 h-8 rounded-xl border flex items-center justify-center transition select-none shrink-0",
                p1Open
                  ? "bg-white/[0.1] text-white border-white/[0.16] shadow-sm"
                  : "bg-white/[0.02] text-white/50 border-white/[0.06] hover:text-white hover:bg-white/[0.06] hover:border-white/[0.12]",
              ].join(" ")}
              title={p1Open ? "Ocultar Árbol (Ctrl+1)" : "Mostrar Árbol (Ctrl+1)"}
            >
              {p1Open ? <PanelLeftClose className="w-3.5 h-3.5" /> : <PanelLeftOpen className="w-3.5 h-3.5" />}
            </button>

            <div
              className="h-8 px-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center gap-2 shrink-0 select-none"
              title={
                backendOnline
                  ? "Servidor TALOS conectado (API activa)"
                  : backendOnline === false
                  ? "Servidor desconectado (Modo local)"
                  : "Comprobando conexión..."
              }
            >
              <span className="text-xs font-mono font-bold tracking-[0.18em] text-white">
                {SYSTEM_NAME}
              </span>
              <span
                className={`w-2 h-2 rounded-full shrink-0 ${
                  backendOnline
                    ? "bg-emerald-400 shadow-[0_0_6px_#34d399] animate-pulse"
                    : backendOnline === false
                    ? "bg-rose-500 shadow-[0_0_6px_#f43f5e]"
                    : "bg-amber-400 shadow-[0_0_6px_#fbbf24] animate-pulse"
                }`}
              />
            </div>

            <div className="flex items-center gap-1 ml-0.5 overflow-x-auto no-scrollbar">
              {coreNav.map((item) => {
                const Icon = item.icon;
                const active = currentView === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onView(item.id)}
                    className={[
                      "h-8 px-2.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-mono tracking-wide shrink-0",
                      active
                        ? "bg-white/[0.1] text-white border border-white/[0.14] font-semibold shadow-xs"
                        : "text-white/45 border border-transparent hover:text-white hover:bg-white/[0.04]",
                    ].join(" ")}
                  >
                    <Icon className="w-3.5 h-3.5 opacity-80 shrink-0" />
                    <span>{item.label}</span>
                  </button>
                );
              })}

              {/* BOTON MODO ESTUDIO VERTICAL SLICE */}
              {onOpenStudySlice && (
                <button
                  type="button"
                  onClick={onOpenStudySlice}
                  className="h-8 px-2.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-mono tracking-wide bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 hover:bg-emerald-500/20 font-medium shrink-0"
                  title="Abrir Vertical Slice de Estudio (KCs + Explicación + Ejercicio real + BKT)"
                >
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Estudiar</span>
                </button>
              )}
            </div>

            {/* DROPDOWN ARQUITECTURA (FUERA DEL CONTENEDOR CON OVERFLOW) */}
            <div className="relative shrink-0 z-50" ref={infraMenuRef}>
              <button
                type="button"
                onClick={() => setInfraMenuOpen(!infraMenuOpen)}
                className={[
                  "h-8 px-2.5 rounded-lg flex items-center gap-1.5 transition-all text-xs font-mono tracking-wide shrink-0",
                  activeInfraItem
                    ? "bg-white/[0.1] text-white border border-white/[0.14] font-semibold shadow-xs"
                    : "text-white/45 border border-transparent hover:text-white hover:bg-white/[0.04]",
                ].join(" ")}
                title="Herramientas de Arquitectura, Auditoría y Gates"
              >
                <Layers className="w-3.5 h-3.5 opacity-80 shrink-0" />
                <span>Arquitectura</span>
                <ChevronDown className={`w-3 h-3 ml-0.5 opacity-50 transition-transform ${infraMenuOpen ? "rotate-180" : ""}`} />
              </button>

              {infraMenuOpen && (
                <div className="absolute left-0 top-full mt-2 w-48 rounded-xl bg-[#121215] border border-white/[0.12] shadow-2xl p-1.5 z-50 k-fade-in font-mono backdrop-blur-xl">
                  <div className="px-2.5 py-1 text-[9px] text-white/35 uppercase tracking-widest border-b border-white/[0.06] mb-1 font-semibold">
                    Capas CAL / E4 / E5
                  </div>
                  {infraNav.map((item) => {
                    const Icon = item.icon;
                    const active = currentView === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => {
                          onView(item.id);
                          setInfraMenuOpen(false);
                        }}
                        className={[
                          "w-full h-8 px-2.5 rounded-lg flex items-center gap-2 text-xs transition text-left",
                          active
                            ? "bg-white/[0.1] text-white font-medium"
                            : "text-white/60 hover:text-white hover:bg-white/[0.05]",
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
          </div>

          <div className="flex items-center gap-2 min-w-0">
            {(() => {
              const activeColorConfig = THEME_COLORS[activeEntity.color || "amber"] || THEME_COLORS.amber;
              return (
                <div
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border transition min-w-0 max-w-[200px] sm:max-w-[260px] md:max-w-[340px] ${activeColorConfig.bg} ${activeColorConfig.border}`}
                  title={activeEntity.name}
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full shrink-0 ${activeColorConfig.dot}`}
                  />
                  <div className="flex items-center gap-1.5 truncate min-w-0">
                    <span className={`${activeColorConfig.text} shrink-0`}>
                      {renderItemIcon(activeEntity.icon, activeEntity.type === "folder", false, "w-3.5 h-3.5")}
                    </span>
                    <span className="text-xs font-mono font-medium text-white/90 truncate">
                      {activeEntity.name}
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {/* CONTROL DE LECTURA / ZOOM — COLAPSABLE */}
            {(() => {
              const [zoomOpen, setZoomOpen] = React.useState(false);
              const zoomRef = React.useRef<HTMLDivElement>(null);

              React.useEffect(() => {
                if (!zoomOpen) return;
                const close = (e: MouseEvent) => {
                  if (zoomRef.current && !zoomRef.current.contains(e.target as Node)) {
                    setZoomOpen(false);
                  }
                };
                document.addEventListener("mousedown", close);
                return () => document.removeEventListener("mousedown", close);
              }, [zoomOpen]);

              const label = fontScale === "standard" ? "100%" : fontScale === "comfort" ? "112%" : "125%";

              return (
                <div ref={zoomRef} className="relative hidden sm:block">
                  <button
                    type="button"
                    onClick={() => setZoomOpen((v) => !v)}
                    className={`h-8 w-8 rounded-lg border flex items-center justify-center transition select-none ${
                      zoomOpen
                        ? "bg-white/[0.1] text-white border-white/[0.16]"
                        : "bg-white/[0.02] text-white/50 border-white/[0.06] hover:text-white/80 hover:bg-white/[0.05]"
                    }`}
                    title={`Zoom de texto: ${label}`}
                  >
                    <ZoomIn className="w-3.5 h-3.5" />
                  </button>

                  {zoomOpen && (
                    <div className="absolute right-0 top-full mt-2 z-50 bg-[#121215] border border-white/[0.1] rounded-xl p-1.5 shadow-2xl k-fade-in min-w-[140px]">
                      <div className="text-[10px] uppercase font-mono text-white/35 px-2 pb-1 tracking-wider font-semibold">
                        Zoom texto
                      </div>
                      {([
                        { scale: "standard" as const, label: "100%", desc: "Estándar" },
                        { scale: "comfort" as const, label: "112%", desc: "Confort" },
                        { scale: "large" as const, label: "125%", desc: "Amplio" },
                      ]).map((opt) => {
                        const active = fontScale === opt.scale;
                        return (
                          <button
                            key={opt.scale}
                            type="button"
                            onClick={() => {
                              onChangeFontScale(opt.scale);
                              setZoomOpen(false);
                            }}
                            className={`w-full flex items-center justify-between gap-3 px-2 py-1.5 rounded-lg text-xs font-mono transition ${
                              active
                                ? "bg-white/[0.1] text-white font-semibold"
                                : "text-white/60 hover:text-white hover:bg-white/[0.04]"
                            }`}
                          >
                            <span>{opt.desc}</span>
                            <span className={`text-[10px] ${active ? "text-white/80" : "text-white/30"}`}>{opt.label}</span>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })()}

            {/* MODO ZEN (PANTALLA LIMPIA) */}
            {currentView === "chat" && (
              <button
                onClick={onToggleZenMode}
                className={[
                  "h-8 px-2.5 rounded-lg border flex items-center gap-1.5 transition text-xs font-mono select-none shrink-0",
                  isZenMode
                    ? "bg-white/[0.1] text-white border-white/[0.16] font-medium"
                    : "bg-white/[0.02] text-white/50 border-white/[0.06] hover:text-white/80 hover:bg-white/[0.05]",
                ].join(" ")}
                title={isZenMode ? "Salir de Modo Zen (Ctrl+Z o Esc)" : "Modo Zen: Chat limpio sin distracciones (Ctrl+Z)"}
              >
                {isZenMode ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                <span className="hidden xl:inline text-[11px]">Zen</span>
              </button>
            )}

            {currentView === "chat" && (
              <button
                onClick={onToggleP3}
                className={[
                  "h-8 px-2.5 rounded-lg border flex items-center gap-1.5 transition text-xs font-mono select-none shrink-0",
                  p3Open
                    ? "bg-white/[0.1] text-white border-white/[0.16] font-medium"
                    : "bg-white/[0.02] text-white/50 border-white/[0.06] hover:text-white/80 hover:bg-white/[0.05]",
                ].join(" ")}
                title={p3Open ? "Ocultar Evidencia (Ctrl+3)" : "Mostrar Evidencia (Ctrl+3)"}
              >
                {p3Open ? <PanelRightClose className="w-3.5 h-3.5" /> : <PanelRightOpen className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline text-[11px]">Evidencia</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export const TopRail = ChatHeader;
export default ChatHeader;
