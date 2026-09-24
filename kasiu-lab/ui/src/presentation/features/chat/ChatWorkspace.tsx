import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  ArrowUp,
  Binary,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Database,
  Eye,
  FileText,
  Folder,
  Loader2,
  Lock,
  MessageCircle,
  Minimize2,
  Network,
  PanelRightOpen,
  Shield,
  Terminal,
  Trash2,
  Upload,
  RefreshCw,
  X,
} from "lucide-react";

import {
  ActiveEntity,
  Citation,
  EvidenceTab,
  FSItem,
  INITIAL_FS,
  KanbanTask,
  Message,
  MindMapNode,
  NoteItem,
  TopView,
} from "../views/types";
import { usePersistentChatHistory } from "../../hooks/usePersistentChatHistory";
import { StudySliceModal } from "./StudySliceModal";
import NotebooksView from "../views/NotebooksView";
import { LibraryView } from "../views/LibraryView";
import { KanbanView, INITIAL_KANBAN_TASKS } from "../views/KanbanView";
import { CalendarView } from "../views/CalendarView";
import { EvidencePanel } from "../views/EvidencePanel";
import StudentProfileView from "../views/StudentProfileView";
import IngestionView from "../views/IngestionView";
import FederationView from "../views/FederationView";
import ThreatIntelView from "../views/ThreatIntelView";
import TelemetryView from "../views/TelemetryView";
import GatesView from "../views/GatesView";
import ConfigView from "../views/ConfigView";
import { chatService, QueryAbortedError } from "../../../services/chatService";
import type { StudySessionSnapshotData } from "./OpeningBriefView";
import { studySessionService } from "../../../services/studySessionService";

import { ChatHeader, TopRail } from "./components/ChatHeader";
import { ChatSidebar, CurriculumRail } from "./components/ChatSidebar";
import { ChatMessages, ClaimText, AbstentionBanner, FacetCoverageBar, DialogueView } from "./components/ChatMessages";
import { ChatInput } from "./components/ChatInput";
import { SYSTEM_NAME, THEME_COLORS, renderItemIcon } from "./components/shared";

export { ChatHeader, TopRail, ChatSidebar, CurriculumRail, ChatMessages, ChatInput, ClaimText, AbstentionBanner, FacetCoverageBar, SYSTEM_NAME, THEME_COLORS, renderItemIcon, DialogueView };

const MONO_STYLES = `
  :root {
    --k-bg: #050505;
    --k-chassis: #0b0b0d;
    --k-surface: #111113;
    --k-surface-2: #151517;
    --k-surface-3: #1b1b1d;
    --k-text: #f5f5f5;
    --k-text-2: #b5b5b5;
    --k-text-3: #777777;
    --k-text-4: #464646;
    --k-line: rgba(255,255,255,.08);
    --k-line-strong: rgba(255,255,255,.14);
  }

  .k-scroll {
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
  }
  .k-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
  .k-scroll::-webkit-scrollbar-track { background: transparent; }
  .k-scroll::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: background-color 0.2s ease, border-color 0.2s ease;
  }
  .k-scroll::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.35);
    border-color: rgba(255, 255, 255, 0.1);
  }
  .k-scroll::-webkit-scrollbar-corner { background: transparent; }

  @keyframes k-fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  .k-fade-in { animation: k-fade-in .15s ease-out; }

  @keyframes k-caret {
    0%, 100% { opacity: 1; }
    50% { opacity: .15; }
  }
  .k-caret { animation: k-caret .8s infinite; }
`;

interface ChatProps {
  messages: Message[];
  activeScope: string;
  isThinking: boolean;
  thinkingStep: string;
  isStreaming: boolean;
  streamedText: string;
  onSend: (text: string) => void;
  onStop?: () => void;
  onEditMessage?: (messageId: string, newContent: string) => void;
  onDeleteMessage?: (messageId: string) => void;
  onClearHistory?: () => void;
  onOpenEvidence: (tab: EvidenceTab, docHash?: string, page?: number, citation?: Citation) => void;
  onOpenCitation?: (citation: Citation) => void;
  onSaveNote: (msgId: string, text: string) => void;
  studySessionSnapshot?: StudySessionSnapshotData | null;
  onExecuteStudyAction?: (action: string, payload?: Record<string, any>) => void;
  isStudyActionLoading?: boolean;
  hasMore?: boolean;
  isLoadingMore?: boolean;
  onLoadMore?: () => void;
}

const ChatView: React.FC<ChatProps> = ({
  messages,
  activeScope,
  isThinking,
  thinkingStep,
  isStreaming,
  streamedText,
  onSend,
  onStop,
  onEditMessage,
  onDeleteMessage,
  onClearHistory,
  onOpenEvidence,
  onOpenCitation,
  onSaveNote,
  studySessionSnapshot,
  onExecuteStudyAction,
  isStudyActionLoading,
  hasMore,
  isLoadingMore,
  onLoadMore,
}) => {
  const memoizedMessages = React.useMemo(() => (
    <ChatMessages
      messages={messages}
      activeScope={activeScope}
      isThinking={isThinking}
      thinkingStep={thinkingStep}
      isStreaming={isStreaming}
      streamedText={streamedText}
      onEditMessage={onEditMessage}
      onDeleteMessage={onDeleteMessage}
      onOpenEvidence={onOpenEvidence}
      onOpenCitation={onOpenCitation}
      onSaveNote={onSaveNote}
      studySessionSnapshot={studySessionSnapshot}
      onExecuteStudyAction={onExecuteStudyAction}
      isStudyActionLoading={isStudyActionLoading}
      hasMore={hasMore}
      isLoadingMore={isLoadingMore}
      onLoadMore={onLoadMore}
      onSend={onSend}
    />
  ), [
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
  ]);

  return (
    <main className="flex-1 min-w-0 h-full bg-[#0b0b0d] flex flex-col overflow-hidden relative">
      {memoizedMessages}
      <ChatInput
        activeScope={activeScope}
        isThinking={isThinking}
        isStreaming={isStreaming}
        onSend={onSend}
        onStop={onStop}
        onClearHistory={onClearHistory}
      />
    </main>
  );
};

/* -------------------------------------------------------------------------- */
/* Componente Principal TALOS Workspace                                       */
/* -------------------------------------------------------------------------- */

const INITIAL_CHAT_BY_SCOPE: Record<string, Message[]> = {
  "nb_prog_basica": [
    {
      id: "p1-1",
      sender: "user",
      text: "¿Cómo se asignan y gestionan las variables en la memoria RAM en Python?",
      timestamp: "Hace 5 días",
      isSaved: true,
    },
    {
      id: "p1-2",
      sender: "assistant",
      text: [
        "### Gestión de Memoria en CPython: Heap y Punteros [E1]",
        "",
        "En Python, las variables **no almacenan valores directamente** en posiciones de memoria fijas, sino **referencias a objetos** alojados en el *Heap*:",
        "",
        "* **Identidad (`id`):** Dirección de memoria del objeto.",
        "* **Tipo (`type`):** Metadatos inmutables asignados al instanciar.",
        "* **Contador de Referencias (`ob_refcnt`):** Entero que registra cuántos punteros activos apuntan al objeto.",
        "",
        "> **Garbage Collector CPython:** Cuando el contador satisface $ob\\_refcnt = 0$, la memoria se libera de forma inmediata y determinista. Para referencias cíclicas complejas, actúa el recolector generacional cíclico.",
      ].join("\n"),
      timestamp: "Hace 5 días",
      isSaved: true,
    },
    {
      id: "p1-3",
      sender: "user",
      text: "¿Cuál es la diferencia entre evaluar condiciones anidadas frente a if/elif/else secuencial?",
      timestamp: "Hace 3 días",
      isSaved: true,
    },
    {
      id: "p1-4",
      sender: "assistant",
      text: [
        "### Estructuras de Control: Secuencial vs. Anidamiento Profundo",
        "",
        "La estructura `if / elif / else` evalúa expresiones booleanas de forma secuencial y determinista de arriba hacia abajo:",
        "",
        "1. **Cortocircuito (*Short-Circuit*):** En cuanto una condición evalúa a `True`, se bifurca inmediatamente y se omiten las ramas subsiguientes.",
        "2. **Complejidad Ciclomática:** El anidamiento profundo multiplica las ramas de ejecución ($M = E - N + 2P$), dificultando las pruebas unitarias y el análisis estático.",
      ].join("\n"),
      timestamp: "Hace 3 días",
      isSaved: true,
    },
    {
      id: "p1-5",
      sender: "user",
      text: "Estoy diseñando una función para parsear IPs. ¿Cómo debo modularizarla según Clean Code?",
      timestamp: "Ayer",
      isSaved: true,
    },
    {
      id: "p1-6",
      sender: "assistant",
      text: [
        "### Principio de Responsabilidad Única (SRP) en Parseo de Redes [E1]",
        "",
        "Aplica el principio de **Responsabilidad Única (SRP)**: una función debe encargarse de un único aspecto computacional. Desacoplamos la extracción de octetos de la validación matemática de rango:",
        "",
        "```python",
        "def parse_ipv4(ip_str: str) -> tuple[int, ...]:",
        '    """Valida y parsea una dirección IPv4 canónica en octetos numéricos.',
        "    ",
        "    Raises:",
        '        ValueError: Si la dirección no contiene 4 octetos en el rango [0, 255].',
        '    """',
        '    octets = ip_str.strip().split(".")',
        "    if len(octets) != 4:",
        '        raise ValueError("Dirección IPv4 inválida: requiere exactamente 4 octetos")',
        "    ",
        "    parsed = tuple(int(oct) for oct in octets if oct.isdigit())",
        "    if len(parsed) != 4 or any(not (0 <= octet <= 255) for octet in parsed):",
        '        raise ValueError("Octeto fuera de rango probabilístico [0, 255]")',
        "    return parsed",
        "```",
        "",
        "**Garantías Arquitectónicas:**",
        "* **Determinismo:** Retorno inmutable mediante tupla `tuple[int, ...]`. ",
        "* **Invariante Matemática:** Cada octeto satisface estrictamente $0 \\le octet \\le 255$.",
        "* **Aislamiento de Excepciones:** Emisión de `ValueError` sin estados globales corruptos.",
      ].join("\n"),
      timestamp: "Ayer",
      isSaved: true,
    },
  ],
  "nb_tcp": [
    {
      id: "tcp-1",
      sender: "assistant",
      text: [
        "### Establecimiento de Conexión TCP: Three-Way Handshake [E1]",
        "",
        `Centro de Operaciones **${SYSTEM_NAME}** listo. Contexto activo: **Fundamentos TCP/IP** (Capa de Transporte L4).`,
        "",
        "El protocolo TCP (RFC 793 / RFC 6528) sincroniza los números de secuencia mediante un handshake determinista de tres fases:",
        "",
        "1. **SYN (Host A $\\to$ Host B):** El cliente selecciona un número de secuencia inicial ($ISN_A$) generado pseudoaleatoriamente:",
        "$$ISN_A = (Clock\\_Counter \\pmod{2^{32}}) + \\mathcal{H}(IP_s, IP_d, Port_s, Port_d, Secret)$$",
        "",
        "2. **SYN-ACK (Host B $\\to$ Host A):** El servidor acusa recibo incrementando el acuse $ACK = ISN_A + 1$ y emite su propio número de secuencia inicial $ISN_B$ [E2].",
        "",
        "3. **ACK (Host A $\\to$ Host B):** El cliente confirma con $ACK = ISN_B + 1$. La sesión queda formalmente en estado `ESTABLISHED`.",
        "",
        "> **Directiva de Ciberdefensa RFC 6528:** La aleatorización estricta de $ISN$ neutraliza vectores de ataque de predicción de secuencia (*TCP Sequence Prediction Attacks*) e inyección a ciegas de paquetes RST/FIN.",
      ].join("\n"),
      timestamp: "09:15",
      isSaved: false,
    },
  ],
  "nb_arq": [
    {
      id: "arq-1",
      sender: "assistant",
      text: [
        "### Microarquitectura: Jerarquía de Caché & Ecuación AMAT [E1]",
        "",
        `Centro de Operaciones **${SYSTEM_NAME}** listo. Contexto activo: **Arquitectura de Computadoras** (Cátedra FADENA).`,
        "",
        "El rendimiento temporal de la jerarquía de memoria se cuantifica analíticamente mediante la ecuación canónica de **Tiempo de Acceso Medio a Memoria (AMAT)**:",
        "",
        "$$AMAT = T_{hit} + (MR_{L1} \\times MP_{L1})$$",
        "",
        "Para una arquitectura multinivel con memoria caché L1 y L2 desacoplada:",
        "",
        "$$AMAT = T_{L1} + MR_{L1} \\times \\left( T_{L2} + MR_{L2} \\times MP_{L2} \\right)$$",
        "",
        "Donde:",
        "* **$T_{hit}$ / $T_{L1}$:** Latencia del ciclo de reloj de acierto en la caché L1.",
        "* **$MR$ (*Miss Rate*):** Tasa de fallos probabilística ($0 \\le MR \\le 1$).",
        "* **$MP$ (*Miss Penalty*):** Penalización de ciclos hacia el bus principal o DRAM.",
        "",
        "```python",
        "def calculate_amat(t_l1: float, mr_l1: float, t_l2: float, mr_l2: float, mp_l2: float) -> float:",
        '    """Calcula el AMAT multinivel en ciclos de reloj de CPU."""',
        "    penalty_l2 = t_l2 + (mr_l2 * mp_l2)",
        "    return t_l1 + (mr_l1 * penalty_l2)",
        "```",
      ].join("\n"),
      timestamp: "10:30",
      isSaved: false,
    },
  ],
  "folder_fase0": [
    {
      id: "f0-1",
      sender: "assistant",
      text: [
        "### Directorio Activo: Fase 0 — Fundamentos de Ciberseguridad",
        "",
        "* **Cuaderno activo:** `Programación Básica` (65% completado).",
        "* **Módulos sincronizados:** Tipos de datos, estructuras de control, funciones puras y manejo de excepciones.",
        "* **Tutor Socrático:** Listo para consultas doctrinales y revisión de código estático.",
      ].join("\n"),
      timestamp: "Hoy",
      isSaved: false,
    },
  ],
  "fadena": [
    {
      id: "fad-1",
      sender: "assistant",
      text: [
        "### Entorno Curricular: FADENA (Ciberdefensa)",
        "",
        "* **Carrera:** Ciberdefensa — 1er Año Curricular.",
        "* **Cuaderno vinculado:** `Arquitectura de Computadoras.nb`.",
        "* **Directivas Habilitadas:** Consultas transversales de cátedra, resolución analítica de exámenes y cronograma doctrinal.",
      ].join("\n"),
      timestamp: "Hoy",
      isSaved: false,
    },
  ],
};

export const ChatWorkspace: React.FC = () => {
  const [currentView, setCurrentView] = useState<TopView>("chat");
  const [fontScale, setFontScale] = useState<"standard" | "comfort" | "large">("comfort");
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [isStudySliceOpen, setIsStudySliceOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    const backendOnlineRef = { current: null as boolean | null };
    const checkHealth = async () => {
      try {
        const res = await fetch("/api/health");
        if (mounted && res.ok !== backendOnlineRef.current) {
          backendOnlineRef.current = res.ok;
          setBackendOnline(res.ok);
        }
        // Register heartbeat with backend (fire-and-forget)
        fetch("/api/system/heartbeat", { method: "POST" }).catch(() => {});
      } catch {
        if (mounted && backendOnlineRef.current !== false) {
          backendOnlineRef.current = false;
          setBackendOnline(false);
        }
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);

    // Notify backend to shut down when the window or tab is closed
    const handleUnload = () => {
      navigator.sendBeacon("/api/system/shutdown");
    };
    window.addEventListener("beforeunload", handleUnload);

    return () => {
      mounted = false;
      clearInterval(interval);
      window.removeEventListener("beforeunload", handleUnload);
    };
  }, []);

  const [activeEntity, setActiveEntity] = useState<ActiveEntity>({
    id: "fase0-soc",
    name: "Programación y Pensamiento Algorítmico",
    type: "notebook",
  });

  const [studySessionSnapshot, setStudySessionSnapshot] = useState<StudySessionSnapshotData | null>(null);
  const [isStudyActionLoading, setIsStudyActionLoading] = useState(false);
  const lastOpenedNotebookRef = React.useRef<string | null>(null);

  // Carga o sincroniza la sesión de estudio al seleccionar un cuaderno (Directiva Final v2)
  useEffect(() => {
    let active = true;
    if (activeEntity.type === "notebook" && activeEntity.id && activeEntity.id !== "root_global") {
      // Deduplicar: no re-abrir si el notebook no cambió
      if (lastOpenedNotebookRef.current === activeEntity.id) return;
      lastOpenedNotebookRef.current = activeEntity.id;
      studySessionService.openSession(activeEntity.id, "agustin")
        .then((snap) => {
          if (active) setStudySessionSnapshot(snap);
        })
        .catch((err) => {
          console.warn("No se pudo iniciar sesión de estudio soberana para", activeEntity.id, err);
          if (active) setStudySessionSnapshot(null);
        });
    } else {
      lastOpenedNotebookRef.current = null;
      setStudySessionSnapshot(null);
    }
    return () => {
      active = false;
    };
  }, [activeEntity.id, activeEntity.type]);

  const handleExecuteStudyAction = async (action: string, payload?: Record<string, any>) => {
    if (!studySessionSnapshot || isStudyActionLoading) return;
    setIsStudyActionLoading(true);
    try {
      const nextSnap = await studySessionService.executeAction(studySessionSnapshot.session_id, action, payload);
      setStudySessionSnapshot(nextSnap);
    } catch (err: any) {
      console.error("Error al ejecutar acción de estudio:", err);
    } finally {
      setIsStudyActionLoading(false);
    }
  };


  const fallbackMessages = useMemo(() => {
    return INITIAL_CHAT_BY_SCOPE[activeEntity.id] ?? [
      {
        id: `m-default-${activeEntity.id}`,
        sender: "assistant",
        text: activeEntity.type === "folder"
          ? `Directorio activo: ${activeEntity.name}. Las consultas aquí resumen el estado y avance de los cuadernos contenidos.`
          : `Centro de Operaciones ${SYSTEM_NAME} listo. Contexto activo: ${activeEntity.name}. Consultas aisladas con verificación estricta a sus fuentes autorizadas.`,
        timestamp: "Ahora",
        isSaved: false,
      },
    ];
  }, [activeEntity.id, activeEntity.name, activeEntity.type]);

  const {
    messages,
    hasMore,
    isLoadingMore,
    loadMore,
    setMessages,
    editMessage,
    deleteMessage,
    clearHistory,
  } = usePersistentChatHistory(activeEntity.id, fallbackMessages);

  const lastAssistantEvidences = useMemo(() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].sender === "assistant" && messages[i].evidences && messages[i].evidences!.length > 0) {
        return messages[i].evidences!;
      }
    }
    return [];
  }, [messages]);

  const abortControllerRef = useRef<AbortController | null>(null);

  const [isThinking, setIsThinking] = useState(false);
  const [thinkingStep, setThinkingStep] = useState(
    "Analizando consulta..."
  );

  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedText, setStreamedText] = useState("");

  const [isP1Open, setIsP1Open] = useState(true);
  const [isP3Open, setIsP3Open] = useState(true);
  const [isZenMode, setIsZenMode] = useState(false);
  const prevP1OpenRef = useRef(true);

  // Modal para limpiar toda la conversación
  const [showClearConfirmModal, setShowClearConfirmModal] = useState(false);

  const handleStop = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  const toggleZenMode = () => {
    setIsZenMode((prev) => {
      if (!prev) {
        prevP1OpenRef.current = isP1Open;
        setIsP1Open(false);
      } else {
        setIsP1Open(prevP1OpenRef.current);
      }
      return !prev;
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        toggleZenMode();
      } else if (e.key === "Escape" && isZenMode) {
        e.preventDefault();
        toggleZenMode();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isZenMode, isP1Open]);

  const [p1Width, setP1Width] = useState(310);
  const [p3Width, setP3Width] = useState(400);

  const [draggingP1, setDraggingP1] = useState(false);
  const [draggingP3, setDraggingP3] = useState(false);

  const [p3Tab, setP3Tab] = useState<EvidenceTab>("progreso");
  const [savedNotes, setSavedNotes] = useState<NoteItem[]>([
    {
      id: "n1",
      title: "Memoria RAM y Variables",
      text: "Las variables son contenedores de datos en memoria RAM. Cada variable tiene un nombre, un tipo y un valor.",
      date: "Hace 5 días",
      scope: "Programación Básica",
    },
    {
      id: "n2",
      title: "Estructuras de Decisión",
      text: "if/elif/else = estructura de decisión secuencial. Siempre evaluar de arriba hacia abajo para evitar complejidad ciclomática.",
      date: "Hace 3 días",
      scope: "Programación Básica",
    },
    {
      id: "n3",
      title: "Clean Code en Funciones",
      text: "Las funciones deben tener UN solo propósito (Clean Code). Si hace más de una cosa, dividirla.",
      date: "Ayer",
      scope: "Programación Básica",
    },
    {
      id: "n4",
      title: "Variables Globales vs Parámetros",
      text: "Evitar variables globales. Usar parámetros y return para comunicación desacoplada entre funciones.",
      date: "Ayer",
      scope: "Programación Básica",
    },
    {
      id: "n5",
      title: "Documentación con Docstrings",
      text: "Siempre documentar con docstrings. Explicar QUÉ hace la función, no CÓMO lo hace internamente.",
      date: "Hoy, 10:15",
      scope: "Programación Básica",
    },
    {
      id: "n6",
      title: "Regla de ISN (RFC 793)",
      text: "El reloj del ISN avanza periódicamente (~4µs) y se utiliza como base para evitar colisiones en conexiones concurrentes o estados TIME_WAIT residuales.",
      date: "Hoy, 09:20",
      scope: "Fundamentos TCP/IP",
    },
    {
      id: "n7",
      title: "Mitigación SYN Cookies",
      text: "En Linux Kernel 5.x / RHEL 9, sysctl net.ipv4.tcp_syncookies = 1 codifica el ISN del servidor mediante un hash criptográfico de las 4-tuplas sin asignar estructura TCB en la memoria del kernel.",
      date: "Hoy, 09:45",
      scope: "Fundamentos TCP/IP",
    },
    {
      id: "n8",
      title: "Cálculo de Latencia AMAT",
      text: "AMAT = Hit Time + (Miss Rate × Miss Penalty). En arquitecturas jerárquicas multinivel: AMAT = L1_Hit + L1_Miss_Rate × (L2_Hit + L2_Miss_Rate × RAM_Latency).",
      date: "Ayer, 18:10",
      scope: "Arquitectura de Computadoras",
    },
  ]);

  const handleDeleteNote = (id: string) => {
    setSavedNotes((prev) => prev.filter((n) => n.id !== id));
  };

  const handleAddDirectNote = (newNote: { title: string; text: string; scope: string }) => {
    setSavedNotes((prev) => [
      {
        id: `note-${Date.now()}`,
        title: newNote.title || `Nota · ${newNote.text.slice(0, 28)}…`,
        text: newNote.text,
        date: "Recién anclada",
        scope: newNote.scope || activeEntity.name,
      },
      ...prev,
    ]);
  };

  const [kanbanTasks, setKanbanTasks] = useState<KanbanTask[]>(INITIAL_KANBAN_TASKS);

  const handleToggleTaskSubtask = (taskId: string, subtaskId: string) => {
    setKanbanTasks((prev) =>
      prev.map((t) => {
        if (t.id !== taskId) return t;
        return {
          ...t,
          subtasks: t.subtasks.map((st) =>
            st.id === subtaskId ? { ...st, done: !st.done } : st
          ),
        };
      })
    );
  };

  const [selectedMindNode, setSelectedMindNode] = useState<MindMapNode | null>(null);

  const [fsItems, setFsItems] = useState<FSItem[]>(INITIAL_FS);
  const [draggedItemId, setDraggedItemId] = useState<string | null>(null);

  const [creationModal, setCreationModal] = useState<"folder" | "notebook" | null>(null);
  const [editingItem, setEditingItem] = useState<FSItem | null>(null);
  const [editName, setEditName] = useState("");
  const [editIcon, setEditIcon] = useState("folder");
  const [editColor, setEditColor] = useState("amber");
  const [newItemName, setNewItemName] = useState("");

  /* Stepper de creación de cuaderno */
  const [creationStep, setCreationStep] = useState(1);
  const [uploadedRoadmap, setUploadedRoadmap] = useState<string | null>(null);
  const [uploadedProgram, setUploadedProgram] = useState<string | null>(null);
  const [ingestMessages, setIngestMessages] = useState<{ sender: "user" | "system"; text: string }[]>([]);
  const [ingestPrompt, setIngestPrompt] = useState("");
  const [previewUnits, setPreviewUnits] = useState<{ num: number; title: string; topics: string[] }[]>([]);

  const resetCreationStepper = () => {
    setCreationStep(1);
    setNewItemName("");
    setUploadedRoadmap(null);
    setUploadedProgram(null);
    setIngestMessages([]);
    setIngestPrompt("");
    setPreviewUnits([]);
  };

  const [isAddingMaterial, setIsAddingMaterial] = useState(false);
  const [materialFileObj, setMaterialFileObj] = useState<File | null>(null);
  const [isUploadingMaterial, setIsUploadingMaterial] = useState(false);
  const [materialUploadError, setMaterialUploadError] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const [materialTitle, setMaterialTitle] = useState("");
  const [isSyncingFolder, setIsSyncingFolder] = useState(false);
  const [syncFeedback, setSyncFeedback] = useState<string | null>(null);

  // Referencias para limpieza de timers (Prevención de Memory Leaks)
  const streamIntervalRef = useRef<number | null>(null);
  const thinkingTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (streamIntervalRef.current) window.clearInterval(streamIntervalRef.current);
      if (thinkingTimeoutRef.current) window.clearTimeout(thinkingTimeoutRef.current);
    };
  }, []);

  /* ------------------------------------------------------------------------
     Atajos Tácticos Globales (Ctrl+1: P1, Ctrl+3: P3, Esc: Modales)
  ------------------------------------------------------------------------ */

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape cierra modales activos
      if (e.key === "Escape") {
        if (creationModal) {
          e.preventDefault();
          setCreationModal(null);
          return;
        }
        if (isAddingMaterial) {
          e.preventDefault();
          setIsAddingMaterial(false);
          return;
        }
      }

      // Atajos con Ctrl o Meta (Cmd)
      if (e.ctrlKey || e.metaKey) {
        if (e.key === "1") {
          e.preventDefault();
          setIsP1Open((prev) => !prev);
        } else if (e.key === "3") {
          e.preventDefault();
          setIsP3Open((prev) => !prev);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [creationModal, isAddingMaterial]);

  /* ------------------------------------------------------------------------
     Splitters
  ------------------------------------------------------------------------ */

  const startP1Resize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setDraggingP1(true);
  }, []);

  const startP3Resize = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setDraggingP3(true);
  }, []);

  useEffect(() => {
    const move = (e: MouseEvent) => {
      if (draggingP1) {
        const next = e.clientX - 12;
        if (next >= 250 && next <= 540) setP1Width(next);
      }

      if (draggingP3) {
        const next = window.innerWidth - e.clientX - 12;
        if (next >= 300 && next <= 680) setP3Width(next);
      }
    };

    const up = () => {
      setDraggingP1(false);
      setDraggingP3(false);
    };

    // Exit early if no drag is active to avoid attaching global listeners
    if (!draggingP1 && !draggingP3) {
      return;
    }
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
    window.addEventListener("mousemove", move);
    window.addEventListener("mouseup", up);
    return () => {
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", move);
      window.removeEventListener("mouseup", up);
    };
  }, [draggingP1, draggingP3]);

  /* ------------------------------------------------------------------------
     Tree Drag & Drop
  ------------------------------------------------------------------------ */

  const handleTreeDragStart = (e: React.DragEvent, id: string) => {
    e.stopPropagation();
    setDraggedItemId(id);
    e.dataTransfer.setData("text/plain", id);
  };

  const handleTreeDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleTreeDrop = (
    e: React.DragEvent,
    targetFolderId: string | null
  ) => {
    e.preventDefault();
    e.stopPropagation();

    const id = e.dataTransfer.getData("text/plain") || draggedItemId;
    if (!id || id === targetFolderId) return;

    setFsItems((prev) =>
      prev.map((item) =>
        item.id === id ? { ...item, parentId: targetFolderId } : item
      )
    );

    setDraggedItemId(null);
  };

  const handleConfirmCreation = () => {
    if (!newItemName.trim() || !creationModal) return;

    const name = newItemName.trim();
    const isNotebook = creationModal === "notebook";
    const itemId = `${isNotebook ? "nb" : "folder"}-${Date.now()}`;
    const cleanName = isNotebook ? (name.endsWith(".nb") ? name : `${name}.nb`) : name;

    setFsItems((prev) => [
      ...prev,
      {
        id: itemId,
        name: cleanName,
        type: isNotebook ? "notebook" : "folder",
        parentId: null,
      },
    ]);

    if (isNotebook) {
      const displayName = cleanName.replace(".nb", "");
      setActiveEntity({ id: itemId, name: displayName, type: "notebook" });
    } else {
      setActiveEntity({ id: itemId, name: name, type: "folder" });
    }

    resetCreationStepper();
    setCreationModal(null);
  };

  /* ------------------------------------------------------------------------
     Chat Send con Conexión Real al Backend y Limpieza de Timers
  ------------------------------------------------------------------------ */

  const handleSend = useCallback(async (rawText: string) => {
    const userText = rawText.trim();
    if (!userText || isThinking || isStreaming) return;

    setMessages((prev) => [
      ...prev,
      {
        id: `u-${Date.now()}`,
        sender: "user",
        text: userText,
        timestamp: "Ahora",
      },
    ]);

    setIsThinking(true);
    setThinkingStep("Consultando fuentes curriculares...");

    // Crear AbortController para permitir cancelación con botón Stop
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      // Conexión real a endpoint FastAPI /api/chat/query
      const isFolderOrRoot = activeEntity.id === "root_global" || activeEntity.type === "root" || activeEntity.type === "folder";
      const apiResponse = await chatService.sendQuery(
        {
          query: userText,
          notebook_id: activeEntity.id === "root_global" ? "folder_root" : activeEntity.id,
          scope_id: activeEntity.id === "root_global" ? "folder_root" : activeEntity.id,
          scope_type: isFolderOrRoot ? "folder" : "notebook",
          requested_scope_id: activeEntity.name,
        },
        (partialText) => {
          setIsThinking(false);
          setIsStreaming(true);
          setStreamedText(partialText);
        },
        controller.signal
      );

      const responseText = apiResponse.reply_text;

      setIsThinking(false);
      setIsStreaming(false);
      setStreamedText("");
      abortControllerRef.current = null;

      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          sender: "assistant",
          text: responseText,
          timestamp: "Ahora",
          isSaved: false,
          evidences: apiResponse.evidences,
          facetCoverage: apiResponse.facet_coverage,
          abstained: apiResponse.abstained,
          abstentionReason: apiResponse.abstention_reason,
        },
      ]);
    } catch (error: any) {
      setIsThinking(false);
      setIsStreaming(false);
      setStreamedText("");
      abortControllerRef.current = null;

      if (error instanceof QueryAbortedError || error?.name === "AbortError" || error?.name === "QueryAbortedError") {
        setMessages((prev) => [
          ...prev,
          {
            id: `aborted-${Date.now()}`,
            sender: "assistant",
            text: "⏹ Consulta abortada.",
            timestamp: "Ahora",
          },
        ]);
        return;
      }

      console.error("Error de comunicación con TALOS:", error);
      const errMsg = error?.message ? String(error.message) : "No fue posible comunicar con el motor soberano TALOS.";
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: `⚠️ Error de Comunicación: ${errMsg}`,
          timestamp: "Ahora",
          errorState: true,
        },
      ]);
    }
  }, [isThinking, isStreaming, activeEntity, setMessages]);

  const handleSaveNote = (messageId: string, text: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.id === messageId ? { ...m, isSaved: !m.isSaved } : m
      )
    );

    setSavedNotes((prev) => [
      {
        id: `note-${Date.now()}`,
        title: `Aserción · ${text.slice(0, 32)}…`,
        text,
        date: "Recién anclada",
        scope: activeEntity.name,
      },
      ...prev,
    ]);
  };

  const [evidenceDocHash, setEvidenceDocHash] = useState<string | undefined>();
  const [evidencePage, setEvidencePage] = useState<number | undefined>();
  const [activeCitation, setActiveCitation] = useState<Citation | null>(null);

  const openEvidence = (
    tab: EvidenceTab,
    docHash?: string,
    page?: number,
    citation?: Citation
  ) => {
    setIsP3Open(true);
    setP3Tab(tab);
    if (docHash) setEvidenceDocHash(docHash);
    if (page) setEvidencePage(page);
    if (citation) setActiveCitation(citation);
    setCurrentView("chat");
  };

  const handleOpenCitation = (citation: Citation) => {
    setActiveCitation(citation);
    openEvidence(
      "evidencia",
      citation.docHash || undefined,
      citation.page || undefined,
      citation
    );
  };

  const handleSelectEntity = (entity: ActiveEntity) => {
    setActiveEntity(entity);
  };

  return (
    <div data-font-scale={fontScale} className="h-screen w-screen bg-[#050505] text-[#f5f5f5] overflow-hidden p-1 sm:p-2 md:p-3 font-sans antialiased">
      <style>{MONO_STYLES}</style>

      <div className="relative h-full w-full overflow-hidden rounded-2xl md:rounded-[28px] border border-white/[0.08] bg-[#0b0b0d] shadow-[0_35px_110px_rgba(0,0,0,.65)] flex flex-col">
        
        {/* MODO ZEN FLOATING CONTROLS — ULTRA SUTIL Y NO INVASIVO */}
        {isZenMode && (
          <div className="absolute top-3 left-1/2 -translate-x-1/2 z-50 k-fade-in flex items-center gap-1.5 opacity-40 hover:opacity-100 transition-opacity duration-300">
            <button
              onClick={toggleZenMode}
              className="h-7 px-2.5 rounded-full bg-[#121215]/80 border border-white/[0.08] text-white/50 hover:text-white text-[11px] font-mono flex items-center gap-1.5 shadow-lg backdrop-blur-md transition hover:bg-white/[0.08]"
              title="Salir de Modo Zen (Esc o Ctrl+Z)"
            >
              <Minimize2 className="w-3 h-3 text-white/60" />
              <span>Modo Zen (Esc)</span>
            </button>
            <button
              onClick={() => setIsP3Open((v) => !v)}
              className="h-7 px-2.5 rounded-full bg-[#121215]/80 border border-white/[0.08] text-white/50 hover:text-white text-[11px] font-mono flex items-center gap-1.5 shadow-lg backdrop-blur-md transition hover:bg-white/[0.08]"
              title={isP3Open ? "Ocultar Evidencia (Ctrl+3)" : "Mostrar Evidencia (Ctrl+3)"}
            >
              <PanelRightOpen className="w-3 h-3 text-white/60" />
              <span>{isP3Open ? "Ocultar Evidencia" : "Evidencia"}</span>
            </button>
          </div>
        )}

        {/* TOP RAIL */}
        {!isZenMode && (
          <TopRail
            currentView={currentView}
            p1Open={isP1Open}
            p3Open={isP3Open}
            activeEntity={activeEntity}
            fontScale={fontScale}
            backendOnline={backendOnline}
            isZenMode={isZenMode}
            onToggleZenMode={toggleZenMode}
            onChangeFontScale={setFontScale}
            onView={setCurrentView}
            onToggleP1={() => setIsP1Open((v) => !v)}
            onToggleP3={() => setIsP3Open((v) => !v)}
            onOpenStudySlice={() => setIsStudySliceOpen(true)}
          />
        )}

        {/* ESPACIO DE TRABAJO */}
        <div className="flex-1 min-h-0 flex overflow-hidden">
          
          {/* ASISTENTE (CHAT) */}
          {currentView === "chat" && (
            <>
              <CurriculumRail
                width={p1Width}
                isOpen={isP1Open}
                isDragging={draggingP1}
                activeEntity={activeEntity}
                fsItems={fsItems}
                draggedItemId={draggedItemId}
                onResizeStart={startP1Resize}
                onSelectEntity={handleSelectEntity}
                onDragStart={handleTreeDragStart}
                onDragOver={handleTreeDragOver}
                onDrop={handleTreeDrop}
                onCreateFolder={() => setCreationModal("folder")}
                onCreateNotebook={() => setCreationModal("notebook")}
                onEditEntity={(item) => {
                  setEditingItem(item);
                  setEditName(item.name.replace(".nb", ""));
                  setEditIcon(item.icon || (item.type === "folder" ? "folder" : "book"));
                  setEditColor(item.color || "amber");
                }}
              />

              <ChatView
                messages={messages}
                activeScope={activeEntity.name}
                isThinking={isThinking}
                thinkingStep={thinkingStep}
                isStreaming={isStreaming}
                streamedText={streamedText}
                onSend={handleSend}
                onStop={handleStop}
                onEditMessage={editMessage}
                onDeleteMessage={deleteMessage}
                onClearHistory={() => setShowClearConfirmModal(true)}
                onOpenEvidence={openEvidence}
                onOpenCitation={handleOpenCitation}
                onSaveNote={handleSaveNote}
                studySessionSnapshot={studySessionSnapshot}
                onExecuteStudyAction={handleExecuteStudyAction}
                isStudyActionLoading={isStudyActionLoading}
                hasMore={hasMore}
                isLoadingMore={isLoadingMore}
                onLoadMore={loadMore}
              />

              <EvidencePanel
                width={p3Width}
                isOpen={isP3Open}
                isDragging={draggingP3}
                tab={p3Tab}
                notes={savedNotes}
                activeScope={activeEntity.name}
                docHash={evidenceDocHash}
                initialPage={evidencePage}
                activeCitation={activeCitation}
                consultedSources={lastAssistantEvidences}
                onSelectCitation={(cit) => {
                  setActiveCitation(cit);
                  if (cit) {
                    if (cit.docHash) setEvidenceDocHash(cit.docHash);
                    if (cit.page || cit.pageStart) setEvidencePage(cit.page || cit.pageStart || 1);
                  }
                }}
                notebookId={activeEntity.type === "notebook" ? activeEntity.id : "fadena-lenguajes"}
                onAskTopic={(topic) => {
                   handleSend(`Explícame los conceptos fundamentales de: ${topic}`);
                }}
                onResizeStart={startP3Resize}
                onTab={setP3Tab}
                onDeleteNote={handleDeleteNote}
                onAddNote={handleAddDirectNote}
              />
            </>
          )}

          {/* CUADERNOS (CARPETA vs CUADERNO + MINI CHAT) */}
          {currentView === "arbol" && (
            <>
              <CurriculumRail
                width={p1Width}
                isOpen={isP1Open}
                isDragging={draggingP1}
                activeEntity={activeEntity}
                fsItems={fsItems}
                draggedItemId={draggedItemId}
                onResizeStart={startP1Resize}
                onSelectEntity={handleSelectEntity}
                onDragStart={handleTreeDragStart}
                onDragOver={handleTreeDragOver}
                onDrop={handleTreeDrop}
                onCreateFolder={() => setCreationModal("folder")}
                onCreateNotebook={() => setCreationModal("notebook")}
                onEditEntity={(item) => {
                  setEditingItem(item);
                  setEditName(item.name.replace(".nb", ""));
                  setEditIcon(item.icon || (item.type === "folder" ? "folder" : "book"));
                  setEditColor(item.color || "amber");
                }}
              />

              <NotebooksView
                activeEntity={activeEntity}
                fsItems={fsItems}
                selectedNode={selectedMindNode}
                onSelectNode={setSelectedMindNode}
                onSelectEntity={handleSelectEntity}
                onOpenChat={() => setCurrentView("chat")}
                onAddMaterial={() => setIsAddingMaterial(true)}
                onCreateFolder={() => setCreationModal("folder")}
                onCreateNotebook={() => setCreationModal("notebook")}
              />
            </>
          )}

          {currentView === "libros" && (
            <LibraryView
              onOpen={() => {
                setCurrentView("chat");
                setIsP3Open(true);
                setP3Tab("pagina");
              }}
            />
          )}

          {currentView === "ingesta" && (
            <IngestionView />
          )}

          {currentView === "federacion" && (
            <FederationView />
          )}

          {currentView === "threatintel" && (
            <ThreatIntelView />
          )}

          {currentView === "telemetria" && (
            <TelemetryView />
          )}

          {currentView === "gates" && (
            <GatesView />
          )}

          {currentView === "config" && (
            <ConfigView />
          )}

          {currentView === "tareas" && (
            <KanbanView
              activeScope={activeEntity.name}
              fsItems={fsItems}
              tasks={kanbanTasks}
              onUpdateTasks={setKanbanTasks}
              onAskAssistant={(task) => {
                setCurrentView("chat");
                handleSend(`Ayúdame a resolver la misión: "${task.title}". Contexto de la tarea: ${task.description || "Sin descripción adicional"}`);
              }}
            />
          )}

          {currentView === "agenda" && (
            <CalendarView
              tasks={kanbanTasks}
              onToggleTaskSubtask={handleToggleTaskSubtask}
            />
          )}

          {currentView === "estudiante" && (
            <StudentProfileView
              onOpenChatWithTopic={(topic) => {
                setCurrentView("chat");
                handleSend(`Quiero repasar y profundizar el tema: "${topic}". Explícame los fundamentos y evaluemos mi comprensión.`);
              }}
            />
          )}
        </div>


        {/* MODAL PERSONALIZAR ELEMENTO (NOMBRE, ICONO Y COLOR) */}
        {editingItem && (
          <div
            onClick={(e) => {
              if (e.target === e.currentTarget) setEditingItem(null);
            }}
            className="absolute inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-5 k-fade-in font-mono select-none"
          >
            <div className="w-full max-w-md rounded-[24px] bg-[#101012] border border-white/[0.12] p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.07]">
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase tracking-wider text-white font-semibold">
                    Personalizar {editingItem.type === "folder" ? "Carpeta" : "Cuaderno"}
                  </span>
                </div>
                <button
                  onClick={() => setEditingItem(null)}
                  className="w-7 h-7 rounded-[8px] bg-white/[0.04] hover:bg-white hover:text-black flex items-center justify-center transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40 mb-1">
                  Nombre del Elemento
                </label>
                <input
                  autoFocus
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full h-10 rounded-[11px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30 font-mono"
                />
              </div>

              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40 mb-1.5">
                  Color Táctico de Identidad
                </label>
                <div className="grid grid-cols-6 gap-2">
                  {[
                    { id: "amber", label: "Ámbar", bg: "bg-amber-400" },
                    { id: "emerald", label: "Esmeralda", bg: "bg-emerald-400" },
                    { id: "purple", label: "Púrpura", bg: "bg-purple-400" },
                    { id: "blue", label: "Cielo", bg: "bg-sky-400" },
                    { id: "rose", label: "Rosa", bg: "bg-rose-400" },
                    { id: "zinc", label: "Titanio", bg: "bg-zinc-200" },
                  ].map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setEditColor(c.id)}
                      className={`h-9 rounded-[10px] border flex flex-col items-center justify-center gap-1 transition ${
                        editColor === c.id
                          ? "border-white bg-white/[0.12] shadow-sm"
                          : "border-white/[0.06] bg-black/40 hover:border-white/20"
                      }`}
                    >
                      <span className={`w-3.5 h-3.5 rounded-full ${c.bg}`} />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40 mb-1.5">
                  Iconografía Especializada
                </label>
                <div className="grid grid-cols-5 gap-2">
                  {[
                    { id: "folder", icon: Folder, label: "Carpeta" },
                    { id: "book", icon: BookOpen, label: "Libro" },
                    { id: "terminal", icon: Terminal, label: "CLI" },
                    { id: "shield", icon: Shield, label: "Escudo" },
                    { id: "cpu", icon: Cpu, label: "CPU" },
                    { id: "network", icon: Network, label: "Red" },
                    { id: "database", icon: Database, label: "DB" },
                    { id: "binary", icon: Binary, label: "Binario" },
                    { id: "lock", icon: Lock, label: "Seguridad" },
                    { id: "file", icon: FileText, label: "Archivo" },
                  ].map((ic) => {
                    const IconComp = ic.icon;
                    return (
                      <button
                        key={ic.id}
                        type="button"
                        onClick={() => setEditIcon(ic.id)}
                        className={`h-10 rounded-[10px] border flex flex-col items-center justify-center gap-1 transition ${
                          editIcon === ic.id
                            ? "border-white bg-white text-black font-bold shadow-sm"
                            : "border-white/[0.06] bg-black/40 text-white/60 hover:text-white hover:border-white/20"
                        }`}
                        title={ic.label}
                      >
                        <IconComp className="w-4 h-4" />
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-3 border-t border-white/[0.07] flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditingItem(null)}
                  className="h-9 px-4 rounded-[10px] bg-white/[0.04] text-white/50 hover:text-white transition text-xs"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    if (!editingItem || !editName.trim()) return;
                    const finalName = editingItem.type === "notebook"
                      ? (editName.endsWith(".nb") ? editName : `${editName}.nb`)
                      : editName;

                    setFsItems((prev) =>
                      prev.map((it) =>
                        it.id === editingItem.id
                          ? { ...it, name: finalName, icon: editIcon, color: editColor }
                          : it
                      )
                    );

                    // Si es la entidad activa, sincronizar context bar
                    if (activeEntity.id === editingItem.id) {
                      setActiveEntity((prev) => ({
                        ...prev,
                        name: editName,
                        icon: editIcon,
                        color: editColor,
                      }));
                    }

                    setEditingItem(null);
                  }}
                  className="h-9 px-4 rounded-[10px] bg-white text-black font-bold text-xs hover:bg-white/90 transition shadow-sm"
                >
                  Guardar configuración
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL CREAR CARPETA O CUADERNO (STEPPER) */}
        {creationModal && (
          <div
            onClick={(e) => {
              if (e.target === e.currentTarget) {
                resetCreationStepper();
                setCreationModal(null);
              }
            }}
            className="absolute inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-5 k-fade-in"
          >
            {creationModal === "folder" ? (
              /* ── CARPETA: Modal simple ── */
              <div className="w-full max-w-md rounded-[22px] bg-[#101012] border border-white/[0.10] p-5 shadow-2xl font-mono">
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                  <span className="text-xs uppercase tracking-wider text-white/70 font-semibold">
                    Nueva Carpeta
                  </span>
                  <button
                    onClick={() => { resetCreationStepper(); setCreationModal(null); }}
                    className="w-8 h-8 rounded-[10px] bg-white/[0.04] hover:bg-white hover:text-black flex items-center justify-center transition"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <input
                  autoFocus
                  value={newItemName}
                  onChange={(e) => setNewItemName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter") handleConfirmCreation(); }}
                  placeholder="Nombre de la carpeta..."
                  className="mt-4 w-full h-11 rounded-[13px] bg-black border border-white/[0.08] px-3.5 text-xs text-white outline-none focus:border-white/30"
                />
                <div className="mt-4 flex justify-end gap-2 text-xs">
                  <button
                    onClick={() => { resetCreationStepper(); setCreationModal(null); }}
                    className="h-9 px-3.5 rounded-[11px] bg-white/[0.04] text-white/40 hover:text-white"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleConfirmCreation}
                    className="h-9 px-4 rounded-[11px] bg-white text-black font-bold hover:bg-white/90 transition shadow-sm"
                  >
                    Crear
                  </button>
                </div>
              </div>
            ) : (
              /* ── CUADERNO: Stepper de 3 pasos ── */
              <div className={`w-full rounded-[22px] bg-[#101012] border border-white/[0.10] p-5 shadow-2xl font-mono ${creationStep === 3 ? "max-w-4xl" : "max-w-lg"}`}>
                {/* Header con stepper */}
                <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                  <div className="flex items-center gap-3">
                    <span className="text-xs uppercase tracking-wider text-white/70 font-semibold">
                      Nuevo Cuaderno
                    </span>
                    <div className="flex items-center gap-1">
                      {[1, 2, 3].map((s) => (
                        <div
                          key={s}
                          className={`w-6 h-1.5 rounded-full transition ${
                            s === creationStep
                              ? "bg-amber-400"
                              : s < creationStep
                              ? "bg-amber-400/40"
                              : "bg-white/10"
                          }`}
                        />
                      ))}
                    </div>
                    <span className="text-[10px] text-white/30 font-mono">
                      {creationStep}/3
                    </span>
                  </div>
                  <button
                    onClick={() => { resetCreationStepper(); setCreationModal(null); }}
                    className="w-8 h-8 rounded-[10px] bg-white/[0.04] hover:bg-white hover:text-black flex items-center justify-center transition"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* PASO 1: Nombre */}
                {creationStep === 1 && (
                  <div className="mt-4 space-y-4">
                    <div>
                      <label className="block text-[10px] uppercase tracking-wider text-white/40 mb-1.5">
                        Nombre del Cuaderno
                      </label>
                      <input
                        autoFocus
                        value={newItemName}
                        onChange={(e) => setNewItemName(e.target.value)}
                        onKeyDown={(e) => { if (e.key === "Enter" && newItemName.trim()) setCreationStep(2); }}
                        placeholder="Ej: Fundamentos de Redes..."
                        className="w-full h-11 rounded-[13px] bg-black border border-white/[0.08] px-3.5 text-xs text-white outline-none focus:border-white/30"
                      />
                    </div>
                    <div className="flex justify-end gap-2 text-xs">
                      <button
                        onClick={() => { resetCreationStepper(); setCreationModal(null); }}
                        className="h-9 px-3.5 rounded-[11px] bg-white/[0.04] text-white/40 hover:text-white"
                      >
                        Cancelar
                      </button>
                      <button
                        disabled={!newItemName.trim()}
                        onClick={() => setCreationStep(2)}
                        className="h-9 px-4 rounded-[11px] bg-white text-black font-bold hover:bg-white/90 transition shadow-sm disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5"
                      >
                        Siguiente
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                )}

                {/* PASO 2: Subir Roadmap y Programa */}
                {creationStep === 2 && (
                  <div className="mt-4 space-y-4">
                    <p className="text-xs text-white/50">
                      Subí el roadmap y/o el programa de la materia para que TALOS pueda mapear automáticamente las unidades, temas y nodos de dominio.
                    </p>

                    <div className="grid grid-cols-2 gap-3">
                      {/* Upload Roadmap */}
                      <label className="cursor-pointer group">
                        <input
                          type="file"
                          accept=".pdf,.png,.jpg,.jpeg"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) setUploadedRoadmap(file.name);
                          }}
                        />
                        <div className={`h-28 rounded-[14px] border-2 border-dashed flex flex-col items-center justify-center gap-2 transition ${
                          uploadedRoadmap
                            ? "border-amber-400/50 bg-amber-500/5"
                            : "border-white/10 hover:border-white/25 bg-white/[0.02]"
                        }`}>
                          {uploadedRoadmap ? (
                            <>
                              <FileText className="w-5 h-5 text-amber-400" />
                              <span className="text-[10px] text-amber-300 font-medium truncate max-w-[140px] px-2">{uploadedRoadmap}</span>
                              <span className="text-[9px] text-white/30">ROADMAP CARGADO</span>
                            </>
                          ) : (
                            <>
                              <Upload className="w-5 h-5 text-white/30 group-hover:text-white/50" />
                              <span className="text-[10px] text-white/40 uppercase tracking-wider font-semibold">Roadmap</span>
                              <span className="text-[9px] text-white/25">PDF o Imagen</span>
                            </>
                          )}
                        </div>
                      </label>

                      {/* Upload Programa */}
                      <label className="cursor-pointer group">
                        <input
                          type="file"
                          accept=".pdf,.doc,.docx"
                          className="hidden"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) setUploadedProgram(file.name);
                          }}
                        />
                        <div className={`h-28 rounded-[14px] border-2 border-dashed flex flex-col items-center justify-center gap-2 transition ${
                          uploadedProgram
                            ? "border-emerald-400/50 bg-emerald-500/5"
                            : "border-white/10 hover:border-white/25 bg-white/[0.02]"
                        }`}>
                          {uploadedProgram ? (
                            <>
                              <FileText className="w-5 h-5 text-emerald-400" />
                              <span className="text-[10px] text-emerald-300 font-medium truncate max-w-[140px] px-2">{uploadedProgram}</span>
                              <span className="text-[9px] text-white/30">PROGRAMA CARGADO</span>
                            </>
                          ) : (
                            <>
                              <Upload className="w-5 h-5 text-white/30 group-hover:text-white/50" />
                              <span className="text-[10px] text-white/40 uppercase tracking-wider font-semibold">Programa</span>
                              <span className="text-[9px] text-white/25">PDF / DOCX</span>
                            </>
                          )}
                        </div>
                      </label>
                    </div>

                    <div className="flex justify-between gap-2 text-xs">
                      <button
                        onClick={() => setCreationStep(1)}
                        className="h-9 px-3.5 rounded-[11px] bg-white/[0.04] text-white/40 hover:text-white flex items-center gap-1.5"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        Atrás
                      </button>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            // Crear sin archivos — creación rápida
                            handleConfirmCreation();
                          }}
                          className="h-9 px-3.5 rounded-[11px] bg-white/[0.04] text-white/50 hover:text-white"
                        >
                          Crear sin fuentes
                        </button>
                        <button
                          onClick={() => {
                            // Generar preview simulado basado en los archivos cargados
                            const simulatedUnits = [
                              { num: 1, title: "Fundamentos y Conceptos Introductorios", topics: ["Terminología Base", "Marco Teórico", "Objetivos del Tramo"] },
                              { num: 2, title: "Desarrollo Temático Principal", topics: ["Análisis de Estructuras", "Casos Prácticos", "Evaluación Formativa"] },
                              { num: 3, title: "Profundización y Aplicaciones", topics: ["Integración de Conceptos", "Laboratorio Práctico", "Resolución de Problemas"] },
                              { num: 4, title: "Evaluación y Certificación", topics: ["Repaso General", "Examen Parcial", "Trabajo Práctico Final"] },
                            ];
                            setPreviewUnits(simulatedUnits);
                            setIngestMessages([
                              { sender: "system", text: `Se procesaron ${uploadedRoadmap ? "el roadmap" : ""}${uploadedRoadmap && uploadedProgram ? " y " : ""}${uploadedProgram ? "el programa" : ""} para "${newItemName}". Se detectaron ${simulatedUnits.length} unidades temáticas. Podés ajustar el mapeo a continuación.` },
                            ]);
                            setCreationStep(3);
                          }}
                          disabled={!uploadedRoadmap && !uploadedProgram}
                          className="h-9 px-4 rounded-[11px] bg-white text-black font-bold hover:bg-white/90 transition shadow-sm disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1.5"
                        >
                          Procesar
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {/* PASO 3: Chat de Ajuste + Preview del Roadmap */}
                {creationStep === 3 && (
                  <div className="mt-4 space-y-3">
                    <div className="flex gap-3" style={{ height: "380px" }}>
                      {/* Panel izquierdo: Chat de ajuste */}
                      <div className="flex-1 min-w-0 flex flex-col rounded-[14px] border border-white/[0.08] bg-black/40 overflow-hidden">
                        <div className="px-3 py-2 border-b border-white/[0.06] flex items-center gap-2 shrink-0">
                          <MessageCircle className="w-3.5 h-3.5 text-amber-400" />
                          <span className="text-[10px] uppercase tracking-wider text-white/40 font-semibold">
                            Ajustar Ingesta
                          </span>
                        </div>
                        <div className="flex-1 overflow-y-auto k-scroll px-3 py-3 space-y-2.5">
                          {ingestMessages.map((msg, i) => (
                            <div
                              key={i}
                              className={`text-xs leading-relaxed rounded-[10px] px-3 py-2 max-w-[90%] ${
                                msg.sender === "user"
                                  ? "bg-white/[0.08] text-white ml-auto"
                                  : "bg-amber-500/10 text-amber-200/80 border border-amber-500/15"
                              }`}
                            >
                              {msg.text}
                            </div>
                          ))}
                        </div>
                        <div className="px-3 py-2 border-t border-white/[0.06] flex gap-2 shrink-0">
                          <input
                            value={ingestPrompt}
                            onChange={(e) => setIngestPrompt(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && ingestPrompt.trim()) {
                                const userMsg = ingestPrompt.trim();
                                setIngestMessages((prev) => [
                                  ...prev,
                                  { sender: "user", text: userMsg },
                                ]);
                                setIngestPrompt("");
                                // Simular respuesta del sistema
                                setTimeout(() => {
                                  setIngestMessages((prev) => [
                                    ...prev,
                                    { sender: "system", text: `Entendido. Se ajustó el mapeo según tu indicación: "${userMsg}". La preview se actualizó.` },
                                  ]);
                                }, 500);
                              }
                            }}
                            placeholder="Ej: Agrupá las unidades 3 y 4..."
                            className="flex-1 h-8 rounded-[9px] bg-black border border-white/[0.08] px-2.5 text-[11px] text-white outline-none focus:border-white/25"
                          />
                          <button
                            onClick={() => {
                              if (ingestPrompt.trim()) {
                                const userMsg = ingestPrompt.trim();
                                setIngestMessages((prev) => [
                                  ...prev,
                                  { sender: "user", text: userMsg },
                                ]);
                                setIngestPrompt("");
                                setTimeout(() => {
                                  setIngestMessages((prev) => [
                                    ...prev,
                                    { sender: "system", text: `Ajuste aplicado: "${userMsg}". Preview actualizado.` },
                                  ]);
                                }, 500);
                              }
                            }}
                            className="w-8 h-8 rounded-[9px] bg-white/[0.06] hover:bg-white hover:text-black flex items-center justify-center transition shrink-0"
                          >
                            <ArrowUp className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>

                      {/* Panel derecho: Preview del Roadmap */}
                      <div className="flex-1 min-w-0 flex flex-col rounded-[14px] border border-white/[0.08] bg-black/40 overflow-hidden">
                        <div className="px-3 py-2 border-b border-white/[0.06] flex items-center gap-2 shrink-0">
                          <Eye className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-[10px] uppercase tracking-wider text-white/40 font-semibold">
                            Preview Roadmap
                          </span>
                        </div>
                        <div className="flex-1 overflow-y-auto k-scroll px-3 py-3 space-y-2">
                          {previewUnits.map((unit) => (
                            <div
                              key={unit.num}
                              className="rounded-[10px] border border-white/[0.08] bg-white/[0.02] p-3"
                            >
                              <div className="flex items-center gap-2 mb-1.5">
                                <span className="text-[10px] font-mono font-bold text-amber-400/80 bg-amber-500/10 px-1.5 py-0.5 rounded">
                                  U{unit.num}
                                </span>
                                <span className="text-xs text-white/80 font-medium truncate">
                                  {unit.title}
                                </span>
                              </div>
                              <div className="flex flex-wrap gap-1">
                                {unit.topics.map((t, ti) => (
                                  <span
                                    key={ti}
                                    className="text-[10px] px-1.5 py-0.5 rounded bg-white/[0.04] text-white/40 border border-white/[0.06]"
                                  >
                                    {t}
                                  </span>
                                ))}
                              </div>
                              {/* Mini progress bar */}
                              <div className="mt-2 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                                <div
                                  className="h-full rounded-full bg-amber-400/30"
                                  style={{ width: unit.num === 1 ? "10%" : "0%" }}
                                />
                              </div>
                            </div>
                          ))}

                          {previewUnits.length === 0 && (
                            <div className="flex items-center justify-center h-full text-xs text-white/25">
                              Sin datos de preview
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex justify-between gap-2 text-xs pt-1">
                      <button
                        onClick={() => setCreationStep(2)}
                        className="h-9 px-3.5 rounded-[11px] bg-white/[0.04] text-white/40 hover:text-white flex items-center gap-1.5"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        Atrás
                      </button>
                      <button
                        onClick={handleConfirmCreation}
                        className="h-9 px-5 rounded-[11px] bg-white text-black font-bold hover:bg-white/90 transition shadow-sm flex items-center gap-1.5"
                      >
                        Confirmar Ingesta
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* MODAL AGREGAR MATERIAL */}
        {isAddingMaterial && (
          <div
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsAddingMaterial(false);
            }}
            className="absolute inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-5 font-mono k-fade-in"
          >
            <div className="w-full max-w-2xl rounded-[24px] bg-[#101012] border border-white/[0.10] p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.06]">
                <div>
                  <span className="block text-[10px] uppercase tracking-wider text-white/40">
                    Source layer
                  </span>
                  <strong className="block mt-1 text-sm text-white">
                    Incorporar material · {activeEntity.name}
                  </strong>
                </div>

                <button
                  onClick={() => setIsAddingMaterial(false)}
                  className="w-8 h-8 rounded-[10px] bg-white/[0.04] hover:bg-white hover:text-black flex items-center justify-center transition"
                  title="Cerrar (Esc)"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3.5 mt-2">
                <input
                  value={materialTitle}
                  onChange={(e) => setMaterialTitle(e.target.value)}
                  placeholder="Título del documento / RFC..."
                  className="h-11 rounded-[13px] bg-black border border-white/[0.08] px-3.5 text-xs text-white outline-none focus:border-white/30"
                />
                <label
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const f = e.dataTransfer.files?.[0];
                    if (f && f.name.toLowerCase().endsWith(".pdf")) {
                      setMaterialFileObj(f);
                      setMaterialUploadError(null);
                      if (!materialTitle.trim()) setMaterialTitle(f.name.replace(/\.pdf$/i, ""));
                    } else {
                      setMaterialUploadError("Solo se admiten archivos PDF.");
                    }
                  }}
                  className="h-11 rounded-[13px] bg-black border border-dashed border-white/[0.15] px-3.5 text-xs text-white/50 flex items-center cursor-pointer hover:border-white/35 hover:text-white transition truncate"
                >
                  <span className="truncate">{materialFileObj ? materialFileObj.name : "Arrastrá o seleccioná un PDF…"}</span>
                  <input
                    type="file"
                    accept="application/pdf,.pdf"
                    className="hidden"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f) {
                        setMaterialFileObj(f);
                        setMaterialUploadError(null);
                        if (!materialTitle.trim()) setMaterialTitle(f.name.replace(/\.pdf$/i, ""));
                      }
                    }}
                  />
                </label>
              </div>

              {materialUploadError && (
                <p className="text-[11px] text-rose-400">{materialUploadError}</p>
              )}

              {/* OPCIÓN B: SINCRONIZAR DESDE CARPETA LOCAL DEL PROYECTO */}
              <div className="p-3.5 rounded-[16px] bg-black/40 border border-white/[0.07] space-y-2">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs text-white/90 font-semibold block">
                      ¿Copia manual en la carpeta del proyecto?
                    </span>
                    <span className="text-[11px] text-white/40 block">
                      Podés colocar los apuntes y libros en <code className="text-amber-300 text-[10.5px]">data/sources/{activeEntity.id}/</code> (o transversal en <code className="text-amber-300 text-[10.5px]">data/sources/general/</code>)
                    </span>
                  </div>
                  <button
                    type="button"
                    disabled={isSyncingFolder || isUploadingMaterial}
                    onClick={async () => {
                      setIsSyncingFolder(true);
                      setSyncFeedback(null);
                      setMaterialUploadError(null);
                      try {
                        const res = await fetch(`/api/notebook/${encodeURIComponent(activeEntity.id)}/sync-sources-folder`, {
                          method: "POST",
                        });
                        if (!res.ok) {
                          const err = await res.json().catch(() => ({}));
                          throw new Error(err.detail || `HTTP ${res.status}`);
                        }
                        const data = await res.json();
                        setSyncFeedback(data.message || `Sincronizados ${data.linked_count} libros.`);
                        await Promise.all([
                          queryClient.invalidateQueries({ queryKey: ["notebook-sources", activeEntity.id] }),
                          queryClient.invalidateQueries({ queryKey: ["notebook-domain-distribution", activeEntity.id] }),
                        ]);
                      } catch (err: any) {
                        setMaterialUploadError(err?.message || "Error al sincronizar fuentes de la carpeta.");
                      } finally {
                        setIsSyncingFolder(false);
                      }
                    }}
                    className="h-8 px-3.5 rounded-xl bg-white/[0.06] border border-white/[0.12] hover:bg-white/[0.12] text-xs text-white/90 hover:text-white flex items-center justify-center gap-1.5 transition shrink-0 disabled:opacity-40"
                  >
                    {isSyncingFolder ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                        <span>Sincronizando...</span>
                      </>
                    ) : (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Sincronizar carpeta local</span>
                      </>
                    )}
                  </button>
                </div>
                {syncFeedback && (
                  <p className="text-[11px] text-emerald-400 font-medium">{syncFeedback}</p>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-center justify-between">
                <span className="text-[10px] uppercase tracking-wider text-white/30">
                  SHA-256 Digest provenance check
                </span>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsAddingMaterial(false)}
                    className="h-10 px-4 rounded-[12px] bg-white/[0.04] text-white/40 text-xs hover:text-white transition"
                  >
                    Cancelar
                  </button>
                  <button
                    disabled={!materialFileObj || isUploadingMaterial}
                    onClick={async () => {
                      if (!materialFileObj || isUploadingMaterial) return;
                      setIsUploadingMaterial(true);
                      setMaterialUploadError(null);
                      try {
                        const fd = new FormData();
                        fd.append("file", materialFileObj);
                        if (materialTitle.trim()) fd.append("title", materialTitle.trim());
                        const uploadUrl = `/api/notebook/${encodeURIComponent(activeEntity.id)}/upload-source`;
                        const res = await fetch(uploadUrl, { method: "POST", body: fd });
                        if (!res.ok) {
                          const err = await res.json().catch(() => ({}));
                          throw new Error(err.detail || `HTTP ${res.status}`);
                        }
                        const data = await res.json();
                        await Promise.all([
                          queryClient.invalidateQueries({ queryKey: ["notebook-sources", activeEntity.id] }),
                          queryClient.invalidateQueries({ queryKey: ["notebook-domain-distribution", activeEntity.id] }),
                        ]);
                        setIsAddingMaterial(false);
                        setMaterialFileObj(null);
                        setMaterialTitle("");
                        console.info(`Material indexado: ${data.chunk_count} fragmentos (SHA-256 ${String(data.doc_hash).slice(0, 12)}…)`);
                      } catch (err: any) {
                        setMaterialUploadError(err?.message || "Falló la indexación del material.");
                      } finally {
                        setIsUploadingMaterial(false);
                      }
                    }}
                    className="h-10 px-5 rounded-[12px] bg-white text-black text-xs font-bold hover:bg-white/90 transition shadow-sm disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    {isUploadingMaterial ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Indexando…
                      </>
                    ) : (
                      "Indexar material"
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* MODAL DE CONFIRMACIÓN: LIMPIAR CONVERSACIÓN */}
        {showClearConfirmModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 k-fade-in font-mono">
            <div className="w-full max-w-md rounded-[20px] bg-[#141417] border border-white/[0.12] p-6 shadow-[0_16px_50px_rgba(0,0,0,0.5)] space-y-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-[10px] bg-rose-500/10 border border-rose-500/30 text-rose-400 flex items-center justify-center shrink-0">
                  <Trash2 className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">¿Limpiar conversación del cuaderno?</h3>
                  <span className="text-[11px] text-white/40">Cuaderno: {activeEntity.name}</span>
                </div>
              </div>
              <div className="p-3 rounded-[12px] bg-white/[0.03] border border-white/[0.06] text-xs text-white/70 space-y-2">
                <p>
                  Esta acción eliminará el historial de mensajes de la pantalla y de tu almacenamiento local (localStorage).
                </p>
                <p className="text-cyan-400/90 text-[11px]">
                  ℹ️ <strong>El progreso cognitivo (BKT / dominios de conocimiento) NO se verá afectado</strong>, ya que se almacena y audita soberanamente en el backend.
                </p>
              </div>
              <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-white/[0.06]">
                <button
                  type="button"
                  onClick={() => setShowClearConfirmModal(false)}
                  className="h-8 px-3 rounded-[10px] bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-white/60 hover:text-white text-xs transition"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    clearHistory();
                    setShowClearConfirmModal(false);
                  }}
                  className="h-8 px-3.5 rounded-[10px] bg-rose-500/20 border border-rose-500/40 hover:bg-rose-500/30 text-rose-300 text-xs font-semibold transition"
                >
                  Limpiar historial
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL VERTICAL SLICE DE ESTUDIO (48H) */}
        <StudySliceModal
          isOpen={isStudySliceOpen}
          onClose={() => setIsStudySliceOpen(false)}
          initialNotebookId={activeEntity.id}
        />

      </div>
    </div>
  );
};

export default ChatWorkspace;
