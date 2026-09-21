import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  CheckSquare,
  ChevronRight,
  FilePlus,
  FileText,
  Folder,
  FolderPlus,
  Hash,
  ListOrdered,
  Loader2,
  Maximize2,
  Network,
  Send,
  UploadCloud,
} from "lucide-react";
import { ActiveEntity, DomainDistributionDto, FolderMessage, FSItem, MindMapNode, NotebookData, NotebookSourcesResponseDto, RoadmapResponse } from "./types";
import { StatusPill } from "./ui-helpers";
import { chatService } from "../../../services/chatService";
import { ReadinessModal } from "./ReadinessModal";
import { ExerciseListView } from "../exercises/ExerciseListView";

const SYSTEM_NAME = "TALOS";

interface PureSvgRoadmapProps {
  nodes: MindMapNode[];
  selectedNodeId: string;
  onSelectNode: (node: MindMapNode) => void;
}

const PureSvgRoadmap: React.FC<PureSvgRoadmapProps> = ({
  nodes,
  selectedNodeId,
  onSelectNode,
}) => {
  return (
    <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5 overflow-hidden">
      <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <Network className="w-4 h-4 text-white/60" />
          <span className="text-xs uppercase tracking-wider text-white/70">
            Grafo Topológico Curricular (Roadmap DAG)
          </span>
        </div>
        <span className="text-[10px] text-white/35">Interactivo · Clic para enfocar</span>
      </div>

      <div className="mt-4 overflow-x-auto k-scroll pb-2">
        <svg viewBox="0 0 880 280" className="w-full min-w-[700px] h-60">
          <defs>
            <marker
              id="roadmap-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto"
            >
              <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="rgba(255,255,255,0.4)" />
            </marker>
          </defs>

          {/* Aristas / Conexiones */}
          {nodes.map((node) =>
            node.connectedTo.map((targetId) => {
              const targetNode = nodes.find((n) => n.id === targetId);
              if (!targetNode) return null;
              return (
                <line
                  key={`${node.id}-${targetId}`}
                  x1={node.x + 60}
                  y1={node.y + 20}
                  x2={targetNode.x + 10}
                  y2={targetNode.y + 20}
                  stroke={node.status === "completed" ? "#10B981" : "rgba(255,255,255,0.18)"}
                  strokeWidth="2"
                  strokeDasharray={node.status === "completed" ? "none" : "4 4"}
                  markerEnd="url(#roadmap-arrow)"
                />
              );
            })
          )}

          {/* Nodos */}
          {nodes.map((node) => {
            const isSelected = selectedNodeId === node.id;
            const isCompleted = node.status === "completed";
            const isCurrent = node.status === "current";

            return (
              <g
                key={node.id}
                onClick={() => onSelectNode(node)}
                className="cursor-pointer group"
              >
                {/* Radar pulse de radio exterior para el nodo en progreso (current) */}
                {isCurrent && (
                  <>
                    <rect
                      x={node.x - 4}
                      y={node.y - 4}
                      width="138"
                      height="52"
                      rx="16"
                      fill="none"
                      stroke="#F59E0B"
                      strokeWidth="1.5"
                      opacity="0.6"
                      strokeDasharray="4 6"
                    >
                      <animate
                        attributeName="stroke-dashoffset"
                        values="0;20"
                        dur="2.5s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.6;0.15;0.6"
                        dur="2.5s"
                        repeatCount="indefinite"
                      />
                    </rect>
                  </>
                )}

                <rect
                  x={node.x}
                  y={node.y}
                  width="130"
                  height="44"
                  rx="12"
                  fill={isSelected ? "#1c1c22" : "#0d0d10"}
                  stroke={
                    isSelected
                      ? "#ffffff"
                      : isCompleted
                      ? "#10B981"
                      : isCurrent
                      ? "#F59E0B"
                      : "rgba(255,255,255,0.12)"
                  }
                  strokeWidth={isSelected ? "2" : isCurrent ? "1.8" : "1.5"}
                  className="transition-all duration-200 group-hover:brightness-125"
                />

                {/* Ondas concéntricas de radar para el pin de telemetría */}
                {isCurrent && (
                  <>
                    <circle
                      cx={node.x + 14}
                      cy={node.y + 22}
                      r="4"
                      fill="none"
                      stroke="#F59E0B"
                      strokeWidth="1.5"
                    >
                      <animate
                        attributeName="r"
                        values="4;16;20"
                        dur="2.2s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.9;0.2;0"
                        dur="2.2s"
                        repeatCount="indefinite"
                      />
                    </circle>
                    <circle
                      cx={node.x + 14}
                      cy={node.y + 22}
                      r="4"
                      fill="none"
                      stroke="#F59E0B"
                      strokeWidth="1"
                    >
                      <animate
                        attributeName="r"
                        values="4;10;15"
                        dur="2.2s"
                        begin="0.7s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.7;0.15;0"
                        dur="2.2s"
                        begin="0.7s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  </>
                )}

                <circle
                  cx={node.x + 14}
                  cy={node.y + 22}
                  r={isCurrent ? "4.5" : "4"}
                  fill={isCompleted ? "#10B981" : isCurrent ? "#F59E0B" : "#555"}
                />
                <text
                  x={node.x + 24}
                  y={node.y + 25}
                  fill="#ffffff"
                  fontSize="10"
                  fontWeight="600"
                  fontFamily="monospace"
                >
                  {node.label.length > 15 ? node.label.slice(0, 14) + "…" : node.label}
                </text>
                <text
                  x={node.x + 24}
                  y={node.y + 36}
                  fill="rgba(255,255,255,0.4)"
                  fontSize="8"
                  fontFamily="monospace"
                >
                  {node.category}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </section>
  );
};


const NotebooksView: React.FC<{
  activeEntity: ActiveEntity;
  fsItems: FSItem[];
  selectedNode: MindMapNode | null;
  onSelectNode: (node: MindMapNode) => void;
  onSelectEntity: (entity: ActiveEntity) => void;
  onOpenChat: () => void;
  onAddMaterial: () => void;
  onCreateFolder: () => void;
  onCreateNotebook: () => void;
}> = ({
  activeEntity,
  fsItems,
  selectedNode,
  onSelectNode,
  onSelectEntity,
  onOpenChat,
  onAddMaterial,
  onCreateFolder,
  onCreateNotebook,
}) => {
  const isFolder = activeEntity.type === "folder";

  // FASE 1: Consumir GET /api/curriculum/roadmap desde backend real con soporte de notebook_id
  const { data: roadmap, isLoading, error } = useQuery<RoadmapResponse>({
    queryKey: ["curriculum-roadmap", activeEntity.id, activeEntity.type],
    queryFn: async () => {
      const url = activeEntity.type === "notebook" && activeEntity.id && activeEntity.id !== "root_global"
        ? `/api/curriculum/roadmap?notebook_id=${encodeURIComponent(activeEntity.id)}`
        : "/api/curriculum/roadmap";
      const res = await fetch(url);
      if (!res.ok) throw new Error("No se pudo cargar el roadmap curricular desde TALOS");
      return res.json();
    },
  });

  // Query dinámica de distribución de dominio doctrinal para el notebook activo
  const { data: domainDistributionData, isLoading: isDomainLoading } = useQuery<DomainDistributionDto>({
    queryKey: ["notebook-domain-distribution", activeEntity.id],
    queryFn: async () => {
      const res = await fetch(`/api/notebook/${encodeURIComponent(activeEntity.id)}/domain-distribution`);
      if (!res.ok) throw new Error("No se pudo cargar la distribución de dominios");
      return res.json();
    },
    enabled: activeEntity.type === "notebook" && activeEntity.id !== "root_global",
  });

  // Query dinámica de fuentes y documentos indexados para el notebook activo
  const { data: notebookSourcesData, isLoading: isSourcesLoading } = useQuery<NotebookSourcesResponseDto>({
    queryKey: ["notebook-sources", activeEntity.id],
    queryFn: async () => {
      const res = await fetch(`/api/notebook/${encodeURIComponent(activeEntity.id)}/sources`);
      if (!res.ok) throw new Error("No se pudo cargar las fuentes del cuaderno");
      return res.json();
    },
    enabled: activeEntity.type === "notebook" && activeEntity.id !== "root_global",
  });

  // Mapear topología DAG a coordenadas y nodos SVG interactivos
  const mindMapNodes = useMemo<MindMapNode[]>(() => {
    if (!roadmap || !roadmap.nodes || roadmap.nodes.length === 0) return [];

    const levelMap = new Map<string, number>();
    roadmap.nodes.forEach((n) => {
      if (n.is_root || n.prerequisites.length === 0) {
        levelMap.set(n.node_id, 0);
      }
    });

    let changed = true;
    let iter = 0;
    while (changed && iter < 10) {
      changed = false;
      iter++;
      roadmap.nodes.forEach((n) => {
        if (n.prerequisites.length > 0) {
          const maxPrereq = Math.max(...n.prerequisites.map((p) => levelMap.get(p) ?? 0));
          const cur = levelMap.get(n.node_id);
          const next = maxPrereq + 1;
          if (cur === undefined || next > cur) {
            levelMap.set(n.node_id, next);
            changed = true;
          }
        }
      });
    }

    const nodesPerLevel = new Map<number, string[]>();
    roadmap.nodes.forEach((n) => {
      const lvl = levelMap.get(n.node_id) ?? 0;
      if (!nodesPerLevel.has(lvl)) nodesPerLevel.set(lvl, []);
      nodesPerLevel.get(lvl)!.push(n.node_id);
    });

    return roadmap.nodes.map((n) => {
      const lvl = levelMap.get(n.node_id) ?? 0;
      const group = nodesPerLevel.get(lvl) || [n.node_id];
      const idxInLvl = group.indexOf(n.node_id);

      const x = 30 + lvl * 200;
      const y = 40 + idxInLvl * 90;

      const outgoing = (roadmap.edges || [])
        .filter((e) => e.from_node === n.node_id)
        .map((e) => e.to_node);

      let status: MindMapNode["status"] = "locked";
      const s = (n.status || "").toUpperCase();
      if (s === "MASTERED" || s === "ASSESSED_PROFICIENT") {
        status = "completed";
      } else if (s === "AVAILABLE" || s === "ACTIVE" || s === "IN_PROGRESS") {
        status = "current";
      } else {
        status = "locked";
      }

      return {
        id: n.node_id,
        label: n.title,
        category: n.node_type || "TOPIC",
        x,
        y,
        status,
        connectedTo: outgoing,
        docRef: `Doc: ${n.node_id}`,
        evalCmd: `:eval ${n.node_id.toLowerCase().replace(/[^a-z0-9]/g, "_")}`,
        description: `Objetivo curricular: ${n.title}. Prerrequisitos: ${
          n.prerequisites.length > 0 ? n.prerequisites.join(", ") : "Ninguno (Raíz)"
        }.`,
      };
    });
  }, [roadmap]);

  const masteredCount = useMemo(() => {
    if (!roadmap?.nodes) return 0;
    return roadmap.nodes.filter(
      (n) =>
        (n.status || "").toUpperCase() === "MASTERED" ||
        (n.status || "").toUpperCase() === "ASSESSED_PROFICIENT"
    ).length;
  }, [roadmap]);

  const totalCount = roadmap?.nodes?.length || 0;
  const progressPct = totalCount > 0 ? Math.round((masteredCount / totalCount) * 100) : 0;

  const dynamicUnits = useMemo(() => {
    if (!roadmap?.nodes) return [];
    return roadmap.nodes.map((n, idx) => {
      const s = (n.status || "").toUpperCase();
      const isDone = s === "MASTERED" || s === "ASSESSED_PROFICIENT";
      const isCur = s === "AVAILABLE" || s === "ACTIVE" || s === "IN_PROGRESS";
      const topicsList = n.subtopics && n.subtopics.length > 0
        ? n.subtopics
        : [
            `Tipo: ${n.node_type || "TOPIC"}`,
            n.is_root ? "Nodo Raíz" : `Prerrequisitos: ${n.prerequisites.join(", ")}`,
          ];
      return {
        number: n.unit ?? (idx + 1),
        title: n.title,
        status: isDone
          ? ("completed" as const)
          : isCur
          ? ("in-progress" as const)
          : ("pending" as const),
        progress: isDone ? 100 : isCur ? 50 : 0,
        topics: topicsList,
      };
    });
  }, [roadmap]);

  const dynamicExercises = useMemo(() => {
    if (!roadmap?.nodes) return [];
    return roadmap.nodes.map((n) => ({
      id: `ex-${n.node_id.toLowerCase().replace(/[^a-z0-9]/g, "-")}`,
      title: `Desafío Práctico: ${n.title}`,
      status: ((n.status || "").toUpperCase() === "MASTERED"
        ? "approved"
        : "pending") as "approved" | "pending",
      desc: `Aserciones evaluadas en Sandbox S6 para ${n.node_id}.`,
    }));
  }, [roadmap]);

  const data = useMemo<NotebookData>(() => {
    return {
      id: activeEntity.id,
      name: activeEntity.name,
      category: roadmap?.title || "Curriculum & Epistemic Roadmap",
      progress: progressPct,
      totalHours: `${totalCount} nodos registrados`,
      units: dynamicUnits,
      mindMapNodes,
      exercises: dynamicExercises,
    };
  }, [activeEntity, roadmap, progressPct, totalCount, dynamicUnits, mindMapNodes, dynamicExercises]);

  const [chatHistories, setChatHistories] = useState<Record<string, FolderMessage[]>>({
    "nb_prog_basica": [
      {
        id: "fc0",
        sender: "assistant",
        text: "Contexto anclado al cuaderno Programación Básica (Fase 0). Consultas aisladas con tutor socrático y aserciones de Python.",
        timestamp: "10:00",
      },
    ],
    "nb_tcp": [
      {
        id: "fc1",
        sender: "assistant",
        text: "Contexto anclado al cuaderno Fundamentos TCP/IP. Consultas se aíslan a este material.",
        timestamp: "09:20",
      },
    ],
    "nb_arq": [
      {
        id: "fc2",
        sender: "assistant",
        text: "Contexto anclado al cuaderno Arquitectura de Computadoras. Consultas sobre Datapath MIPS, latencia AMAT y buses DMA.",
        timestamp: "11:15",
      },
    ],
    "folder_fase0": [
      {
        id: "ff0",
        sender: "assistant",
        text: "Directorio activo: Fase 0 - Ciberseguridad. Materia en curso: Programación Básica (65% completada).",
        timestamp: "09:30",
      },
    ],
    "fadena": [
      {
        id: "ff1",
        sender: "assistant",
        text: "Contexto anclado a la carpeta FADENA (Ciberdefensa). Puedes consultar directivas globales de cátedra o planes de estudio.",
        timestamp: "09:00",
      },
    ],
  });
  const [miniPrompt, setMiniPrompt] = useState("");
  const [readinessTopic, setReadinessTopic] = useState<{ id: string; title: string } | null>(null);

  const currentHistory = chatHistories[activeEntity.id] || [
    {
      id: `default-${activeEntity.id}`,
      sender: "assistant",
      text: isFolder
        ? `Directorio activo: ${activeEntity.name}. Consultas aquí resumen el estado y planificación de las materias contenidas.`
        : `Cuaderno activo: ${activeEntity.name}. Consultas aisladas con hash-lock a sus fuentes y unidades.`,
      timestamp: "Ahora",
    },
  ];

  const [miniChatLoading, setMiniChatLoading] = useState(false);

  const handleSendMiniChat = async () => {
    if (!miniPrompt.trim() || miniChatLoading) return;
    const userText = miniPrompt.trim();
    setMiniPrompt("");

    const newMsg: FolderMessage = {
      id: `u-${Date.now()}`,
      sender: "user",
      text: userText,
      timestamp: "Ahora",
    };

    setChatHistories((prev) => ({
      ...prev,
      [activeEntity.id]: [...(prev[activeEntity.id] || []), newMsg],
    }));

    const isFolderScope = activeEntity.id === "root_global" || activeEntity.type === "root" || activeEntity.type === "folder";
    const targetScopeId = activeEntity.id === "root_global" ? "folder_root" : activeEntity.id;
    const tempReplyId = `a-${Date.now()}`;

    setMiniChatLoading(true);
    try {
      const resp = await chatService.sendQuery(
        {
          query: userText,
          notebook_id: targetScopeId,
          scope_id: targetScopeId,
          scope_type: isFolderScope ? "folder" : "notebook",
          requested_scope_id: activeEntity.name,
        },
        (partialText) => {
          setChatHistories((prev) => {
            const list = prev[activeEntity.id] || [];
            const existingIdx = list.findIndex((m) => m.id === tempReplyId);
            const streamingMsg: FolderMessage = {
              id: tempReplyId,
              sender: "assistant",
              text: partialText,
              timestamp: "Ahora",
            };
            if (existingIdx !== -1) {
              const updated = [...list];
              updated[existingIdx] = streamingMsg;
              return { ...prev, [activeEntity.id]: updated };
            }
            return { ...prev, [activeEntity.id]: [...list, streamingMsg] };
          });
        }
      );

      const replyMsg: FolderMessage = {
        id: tempReplyId,
        sender: "assistant",
        text: resp.reply_text,
        timestamp: "Ahora",
      };

      setChatHistories((prev) => {
        const list = prev[activeEntity.id] || [];
        const existingIdx = list.findIndex((m) => m.id === tempReplyId);
        if (existingIdx !== -1) {
          const updated = [...list];
          updated[existingIdx] = replyMsg;
          return { ...prev, [activeEntity.id]: updated };
        }
        return {
          ...prev,
          [activeEntity.id]: [...list, replyMsg],
        };
      });
    } catch (err: any) {
      console.error("[MiniChat] Error de comunicación:", err);
      const errMsg = err?.message ? String(err.message) : "No fue posible comunicar con el motor soberano TALOS.";
      const errorMsg: FolderMessage = {
        id: `err-${Date.now()}`,
        sender: "assistant",
        text: `⚠️ Error de Enlace: ${errMsg}`,
        timestamp: "Ahora",
      };
      setChatHistories((prev) => ({
        ...prev,
        [activeEntity.id]: [...(prev[activeEntity.id] || []), errorMsg],
      }));
    } finally {
      setMiniChatLoading(false);
    }
  };

  const childFolders = useMemo(
    () => fsItems.filter((i) => i.parentId === activeEntity.id && i.type === "folder"),
    [fsItems, activeEntity.id]
  );
  const childNotebooks = useMemo(
    () => fsItems.filter((i) => i.parentId === activeEntity.id && i.type === "notebook"),
    [fsItems, activeEntity.id]
  );

  return (
    <main className="flex-1 min-w-0 h-full flex overflow-hidden bg-[#0b0b0d] font-mono">
      {/* CONTENIDO DEL CUADERNO O CARPETA */}
      <div className="flex-1 overflow-y-auto k-scroll px-8 py-7 space-y-7">
        <div className="max-w-5xl 2xl:max-w-6xl mx-auto space-y-7">
          
          {/* BANNER DE ERROR O CARGA FAIL-CLOSED */}
          {isLoading && (
            <div className="p-5 rounded-[20px] bg-[#101012] border border-white/[0.08] flex items-center gap-3 text-white/60 text-xs font-mono">
              <Loader2 className="w-4 h-4 animate-spin text-white/40" />
              <span>Cargando topología curricular desde TALOS...</span>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-[18px] bg-red-950/40 border border-red-500/30 flex items-center gap-3 text-red-300 text-xs font-mono">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <div>
                <strong className="block font-semibold">Error de Topología Curricular</strong>
                <span>{(error as Error).message}</span>
              </div>
            </div>
          )}

          {/* CASO A: VISTA DE CARPETA / DIRECTORIO */}
          {isFolder ? (
            <div className="space-y-7 k-fade-in">
              <section className="flex flex-wrap items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
                <div>
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] uppercase tracking-[0.2em] bg-white/[0.04] border border-white/[0.08] text-white/70">
                    <Folder className="w-3.5 h-3.5 text-white/50" />
                    DIRECTORIO CURRICULAR
                  </span>
                  <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-white tracking-tight">
                    {activeEntity.name}
                  </h1>
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    onClick={onCreateNotebook}
                    className="h-10 px-4 rounded-[14px] bg-white text-black text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-white/90 transition shadow-sm"
                  >
                    <FilePlus className="w-4 h-4" />
                    + Cuaderno
                  </button>
                  <button
                    onClick={onCreateFolder}
                    className="h-10 px-4 rounded-[14px] bg-white/[0.05] border border-white/[0.1] text-white text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-white/[0.1] transition"
                  >
                    <FolderPlus className="w-4 h-4" />
                    + Subcarpeta
                  </button>
                </div>
              </section>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5">
                  <span className="block text-[10px] uppercase tracking-wider text-white/35">
                    Cuadernos en este Directorio
                  </span>
                  <strong className="block mt-2 text-2xl tracking-tight text-white">
                    {childNotebooks.length} Materias
                  </strong>
                  <span className="block mt-1 text-xs text-white/40">
                    {childFolders.length} subdirectorios activos
                  </span>
                </div>

                <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5">
                  <span className="block text-[10px] uppercase tracking-wider text-white/35">
                    Tiempo de Cátedra Acumulado
                  </span>
                  <strong className="block mt-2 text-2xl tracking-tight text-white">
                    84 Horas
                  </strong>
                  <span className="block mt-1 text-xs text-white/40">
                    Registradas en ciclo lectivo
                  </span>
                </div>

                <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5">
                  <span className="block text-[10px] uppercase tracking-wider text-white/35">
                    Promedio de Dominio
                  </span>
                  <strong className="block mt-2 text-2xl tracking-tight text-white">
                    76.1%
                  </strong>
                  <div className="mt-2 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                    <div className="h-full bg-white rounded-full" style={{ width: "76.1%" }} />
                  </div>
                </div>
              </div>

              {childFolders.length > 0 && (
                <section className="space-y-3">
                  <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                    <Folder className="w-4 h-4 text-white/50" />
                    <span className="text-xs uppercase tracking-wider font-semibold text-white/70">
                      Subdirectorios Contenidos
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
                    {childFolders.map((f) => (
                      <div
                        key={f.id}
                        onClick={() => onSelectEntity({ id: f.id, name: f.name, type: "folder" })}
                        className="p-4 rounded-[18px] bg-[#12141c] border border-white/[0.08] hover:border-white/30 cursor-pointer transition flex items-center justify-between group"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-white/60 group-hover:text-white transition">
                            <Folder className="w-4 h-4" />
                          </div>
                          <div>
                            <strong className="text-xs text-white block">{f.name}</strong>
                            <span className="text-[10px] text-white/35">Subcarpeta curricular</span>
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-white/30 group-hover:text-white transition" />
                      </div>
                    ))}
                  </div>
                </section>
              )}

              <section className="space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-white/[0.06]">
                  <FileText className="w-4 h-4 text-white/50" />
                  <span className="text-xs uppercase tracking-wider font-semibold text-white/70">
                    Cuadernos y Materias en este Directorio
                  </span>
                </div>

                {childNotebooks.length === 0 ? (
                  <div className="p-8 rounded-[20px] bg-[#101012] border border-dashed border-white/[0.08] text-center text-xs text-white/40">
                    No hay cuadernos registrados en esta carpeta. Haz clic en "+ Cuaderno" para añadir uno.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {childNotebooks.map((nb) => {
                      const cleanName = nb.name.replace(".nb", "");
                      return (
                        <div
                          key={nb.id}
                          className="p-5 rounded-[22px] bg-[#101012] border border-white/[0.08] hover:border-white/30 transition space-y-3 flex flex-col justify-between"
                        >
                          <div>
                            <div className="flex items-center justify-between text-xs">
                              <StatusPill>Roadmap Soberano</StatusPill>
                              <span className="text-[10px] text-white/40">
                                {totalCount} nodos registrados
                              </span>
                            </div>

                            <h3 className="text-sm md:text-base font-bold text-white mt-3 leading-snug">
                              {cleanName}
                            </h3>
                            <p className="text-xs text-white/50 mt-1">
                              {dynamicUnits.length > 0 ? `${dynamicUnits.length} unidades curriculares analizadas.` : "Cuaderno curricular."}
                            </p>
                          </div>

                          <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs">
                            <span className="text-white/60">
                              Dominio: <strong className="text-white">{progressPct}%</strong>
                            </span>

                            <button
                              onClick={() => onSelectEntity({ id: nb.id, name: cleanName, type: "notebook" })}
                              className="px-3 py-1 rounded-xl bg-white text-black font-semibold text-xs hover:bg-white/90 transition shadow-sm"
                            >
                              Abrir Cuaderno →
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>
            </div>
          ) : (
            /* CASO B: VISTA DE CUADERNO / MATERIA TÉCNICA */
            <div className="space-y-7 k-fade-in">
              <section className="flex flex-wrap items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
                <div>
                  <span className="block text-[11px] uppercase tracking-[0.24em] text-white/35">
                    {data.category}
                  </span>
                  <h1 className="mt-2 text-2xl md:text-3xl font-semibold text-white tracking-tight">
                    {data.name}
                  </h1>
                </div>

                <div className="flex items-center gap-3">
                  <span className="inline-flex items-center px-3.5 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-white/[0.05] text-white/80 border border-white/[0.12]">
                    {data.totalHours}
                  </span>

                  <button
                    onClick={onAddMaterial}
                    className="h-10 px-4 rounded-[14px] bg-white text-black text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-white/90 transition shadow-sm"
                  >
                    <UploadCloud className="w-4 h-4" />
                    Material
                  </button>
                </div>
              </section>

              <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5">
                <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-white/60" />
                    <span className="text-xs uppercase tracking-wider text-white/70">
                      Distribución de dominio doctrinal
                    </span>
                  </div>
                  <span className="text-[10px] text-white/35">
                    {domainDistributionData ? `${domainDistributionData.total_chunks} fragmentos indexados` : "métrica analítica"}
                  </span>
                </div>

                {isDomainLoading ? (
                  <div className="h-44 flex items-center justify-center gap-2 text-white/40 text-xs font-mono">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Calculando distribución de fragmentos...</span>
                  </div>
                ) : domainDistributionData && domainDistributionData.distribution.length > 0 ? (
                  <div className="mt-5 flex items-end gap-3 h-44 overflow-x-auto k-scroll pb-2">
                    {domainDistributionData.distribution.map((item, i) => {
                      const colors = ["#f5f5f5", "#dcdcdc", "#bcbcbc", "#999999", "#777777", "#5b5b5b", "#404040"];
                      const tone = colors[i % colors.length];
                      return (
                        <div key={item.kc_id || i} className="h-full flex-1 min-w-[50px] max-w-[90px] flex flex-col items-center justify-end gap-2">
                          <span className="text-[10px] text-white/55 font-mono">{item.percentage}%</span>
                          <div className="w-full max-w-[42px] h-full rounded-t-[13px] bg-black border border-white/[0.06] overflow-hidden flex items-end">
                            <div
                              className="w-full rounded-t-[11px] transition-all duration-500"
                              style={{ height: `${Math.max(item.percentage, 4)}%`, backgroundColor: tone }}
                              title={`${item.kc_display_name}: ${item.chunk_count} chunks (${item.percentage}%) - ${item.unit}`}
                            />
                          </div>
                          <span
                            className="text-[10px] text-white/40 text-center truncate w-full"
                            title={item.kc_display_name}
                          >
                            {item.kc_display_name}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="mt-5 grid grid-cols-7 gap-4 items-end h-44">
                    {[
                      ["Fase 0 Core", 88, "#f5f5f5"],
                      ["ISN Clock", 76, "#dcdcdc"],
                      ["Caché", 64, "#bcbcbc"],
                      ["Crypto", 52, "#999999"],
                      ["RHEL", 44, "#777777"],
                      ["LiME", 34, "#5b5b5b"],
                      ["PKI", 22, "#404040"],
                    ].map(([label, value, tone], i) => (
                      <div key={i} className="h-full flex flex-col items-center justify-end gap-2">
                        <span className="text-[10px] text-white/55">{value}%</span>
                        <div className="w-full max-w-[42px] h-full rounded-t-[13px] bg-black border border-white/[0.06] overflow-hidden flex items-end">
                          <div
                            className="w-full rounded-t-[11px]"
                            style={{ height: `${value}%`, backgroundColor: tone as string }}
                          />
                        </div>
                        <span className="text-[10px] text-white/40 text-center truncate w-full">{label}</span>
                      </div>
                    ))}
                  </div>
                )}
              </section>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  ["Dominio epistémico", `${data.progress}%`, "progreso actual"],
                  ["Aserciones S6", "16 / 18", "Rúbricas Aprobadas"],
                  ["Fuentes indexadas", isSourcesLoading ? "…" : String(notebookSourcesData?.total_sources ?? 0), "Documentos vinculados"],
                ].map(([label, value, meta]) => (
                  <section key={label} className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5">
                    <span className="block text-[10px] uppercase tracking-wider text-white/35">{label}</span>
                    <strong className="block mt-3 text-2xl tracking-tight text-white">{value}</strong>
                    {label === "Dominio epistémico" ? (
                      <div className="mt-3 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                        <div className="h-full bg-white rounded-full" style={{ width: `${data.progress}%` }} />
                      </div>
                    ) : null}
                    <span className="block mt-2 text-xs text-white/35">{meta}</span>
                  </section>
                ))}
              </div>

              <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5">
                <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-white/60" />
                    <span className="text-xs uppercase tracking-wider text-white/70">
                      Fuentes y Materiales Indexados
                    </span>
                  </div>
                  <span className="text-[10px] text-white/35">
                    {notebookSourcesData
                      ? `${notebookSourcesData.total_sources} documento${notebookSourcesData.total_sources === 1 ? "" : "s"} · ${notebookSourcesData.sources.reduce((acc, s) => acc + (s.chunk_count || 0), 0)} fragmentos`
                      : "Verificando knowledge base..."}
                  </span>
                </div>

                {isSourcesLoading ? (
                  <div className="h-32 flex items-center justify-center gap-2 text-white/40 text-xs font-mono">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Recuperando fuentes soberanas...</span>
                  </div>
                ) : notebookSourcesData && notebookSourcesData.sources.length > 0 ? (
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                    {notebookSourcesData.sources.map((src) => (
                      <div
                        key={src.source_id}
                        className="rounded-[16px] bg-black border border-white/[0.08] p-4 flex flex-col gap-2 hover:border-white/25 transition group"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <strong className="block text-xs text-white truncate" title={src.title}>
                              {src.title}
                            </strong>
                            <span className="block mt-0.5 text-[10px] text-white/40 truncate">
                              {src.author}{src.page_count ? ` · ${src.page_count} páginas` : ""}
                            </span>
                          </div>
                          <span className="shrink-0 text-[10px] font-mono px-2 py-0.5 rounded bg-white/[0.05] border border-white/[0.08] text-white/60">
                            {src.chunk_count} chunks
                          </span>
                        </div>
                        <div className="flex items-center justify-between gap-2">
                          <span
                            className="flex items-center gap-1 text-[10px] font-mono text-white/30 truncate"
                            title={src.sha256}
                          >
                            <Hash className="w-3 h-3" />
                            {src.sha256 ? `${src.sha256.slice(0, 16)}…` : "sin digest"}
                          </span>
                          {src.sha256 && (
                            <button
                              onClick={async (e) => {
                                e.stopPropagation();
                                try {
                                  await fetch("/api/sources/open-local", {
                                    method: "POST",
                                    headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ doc_hash: src.sha256 }),
                                  });
                                } catch {
                                  /* noop */
                                }
                              }}
                              className="h-7 px-2.5 rounded-[9px] bg-white/[0.06] border border-white/[0.08] text-white/60 text-[10px] uppercase tracking-wider hover:bg-white hover:text-black transition"
                            >
                              Abrir PDF
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="mt-4 rounded-[16px] border border-dashed border-white/[0.12] p-6 text-center">
                    <p className="text-xs text-white/40">
                      Este cuaderno aún no tiene fuentes indexadas. Usá el botón <strong className="text-white/70">+ Material</strong> para incorporar un PDF canónico.
                    </p>
                  </div>
                )}
              </section>

              <PureSvgRoadmap
                nodes={data.mindMapNodes}
                selectedNodeId={selectedNode?.id ?? ""}
                onSelectNode={onSelectNode}
              />

              {selectedNode && (
                <section className="rounded-[22px] bg-[#101012] border border-white/[0.12] p-5 flex flex-wrap items-center justify-between gap-5 k-fade-in">
                  <div className="max-w-3xl">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusPill active>{selectedNode.category}</StatusPill>
                      <strong className="text-sm text-white">{selectedNode.label}</strong>
                      <StatusPill>{selectedNode.status}</StatusPill>
                    </div>

                    <p className="mt-3 text-xs leading-[1.8] text-white/60">{selectedNode.description}</p>

                    <div className="mt-3 flex flex-wrap gap-4 text-xs text-white/35">
                      <span>DOC: <strong className="text-white/70">{selectedNode.docRef}</strong></span>
                      <span>CMD: <code className="text-white bg-black px-1.5 py-0.5 rounded">{selectedNode.evalCmd}</code></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setReadinessTopic({ id: selectedNode.id, title: selectedNode.label })}
                      className="h-10 px-4 rounded-[14px] bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs font-bold uppercase tracking-wider hover:bg-amber-500/20 transition shadow-sm"
                    >
                      Evaluar Readiness
                    </button>
                    <button
                      onClick={onOpenChat}
                      className="h-10 px-4 rounded-[14px] bg-white text-black text-xs font-bold uppercase tracking-wider hover:bg-white/90 transition shadow-sm"
                    >
                      Lanzar en chat
                    </button>
                  </div>
                </section>
              )}

              <section className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.07]">
                  <div className="flex items-center gap-2">
                    <CheckSquare className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs uppercase tracking-wider font-semibold text-white/80">
                      Ejercicios Prácticos y Auditoría Forense TALOS
                    </span>
                  </div>
                  <span className="text-[10px] text-white/40 font-mono">VSCode Local + Auditor S4.4</span>
                </div>

                <ExerciseListView notebookId={data.id} />
              </section>

              <section className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b border-white/[0.07]">
                  <div className="flex items-center gap-2">
                    <ListOrdered className="w-4 h-4 text-white/60" />
                    <span className="text-xs uppercase tracking-wider text-white/70 font-semibold">
                      Unidades temáticas del programa
                    </span>
                  </div>
                  <span className="text-[10px] text-white/40">Tabla Analítica de Cátedra</span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {data.units.map((unit) => (
                    <div
                      key={unit.number}
                      className="rounded-[22px] bg-[#101012] border border-white/[0.08] p-5 flex flex-col justify-between min-h-[200px]"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-3">
                          <StatusPill>Unidad {unit.number}</StatusPill>
                          <span className="text-[10px] uppercase text-white/35 font-semibold">{unit.status}</span>
                        </div>

                        <h3 className="mt-4 text-sm font-semibold text-white leading-snug">{unit.title}</h3>

                        <ul className="mt-3 space-y-2">
                          {unit.topics.map((topic) => (
                            <li key={topic} className="flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full bg-white/40 mt-1.5 shrink-0" />
                              <span className="text-xs leading-relaxed text-white/50">{topic}</span>
                            </li>
                          ))}
                        </ul>
                      </div>

                      <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between">
                        <span className="text-[10px] uppercase text-white/35">progreso</span>
                        <strong className="text-xs text-white/80">{unit.progress}%</strong>
                      </div>
                    </div>
                  ))}
                </div>

                {/* TABLA ESTRUCTURADA DE UNIDADES Y RÚBRICAS */}
                <div className="rounded-[22px] bg-[#101012] border border-white/[0.08] overflow-hidden">
                  <div className="px-5 py-3.5 border-b border-white/[0.06] flex items-center justify-between bg-white/[0.02]">
                    <span className="text-xs uppercase tracking-wider text-white/70 font-semibold">
                      Desglose Operacional por Unidad
                    </span>
                    <span className="text-[10px] text-white/40 font-mono">
                      Total: {data.units.length} Unidades · Cátedra Oficial
                    </span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-white/[0.06] text-white/40 uppercase tracking-wider text-[9.5px]">
                          <th className="py-3 px-4">Unidad</th>
                          <th className="py-3 px-4">Denominación</th>
                          <th className="py-3 px-4">Tópicos Clave</th>
                          <th className="py-3 px-4">Carga Horaria</th>
                          <th className="py-3 px-4">Dominio</th>
                          <th className="py-3 px-4 text-right">Estado</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-white/[0.04]">
                        {data.units.map((unit, idx) => {
                          const hours = (idx + 1) * 8 + 4;
                          const isDone = unit.progress === 100;
                          return (
                            <tr key={unit.number} className="hover:bg-white/[0.02] transition">
                              <td className="py-3 px-4 font-mono font-bold text-white/80">
                                U-0{unit.number}
                              </td>
                              <td className="py-3 px-4 font-medium text-white max-w-[220px]">
                                {unit.title}
                              </td>
                              <td className="py-3 px-4 text-white/50 text-[11px] max-w-[300px]">
                                <span className="truncate block">
                                  {unit.topics.join(" · ")}
                                </span>
                              </td>
                              <td className="py-3 px-4 font-mono text-white/60">
                                {hours}h est.
                              </td>
                              <td className="py-3 px-4">
                                <div className="flex items-center gap-2">
                                  <div className="w-16 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
                                    <div
                                      className="h-full rounded-full transition-all duration-300"
                                      style={{
                                        width: `${unit.progress}%`,
                                        backgroundColor: isDone ? "#10B981" : "#F59E0B",
                                      }}
                                    />
                                  </div>
                                  <span className="font-mono text-[11px] text-white/70">
                                    {unit.progress}%
                                  </span>
                                </div>
                              </td>
                              <td className="py-3 px-4 text-right">
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] uppercase tracking-wider font-semibold ${
                                    isDone
                                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                      : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                                  }`}
                                >
                                  {unit.status}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              </section>
            </div>
          )}

        </div>
      </div>

      {/* MINI CHAT CONTEXTUAL LATERAL (DIFERENCIADO CARPETA VS CUADERNO) */}
      <aside className="w-[380px] shrink-0 h-full bg-[#0a0a0c] border-l border-white/[0.07] flex flex-col justify-between p-4 select-none">
        <div>
          <div className="pb-3 border-b border-white/[0.07] flex items-center justify-between">
            <div className="min-w-0">
              <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-white/40 font-bold">
                {isFolder ? <Folder className="w-3 h-3 text-white/60" /> : <FileText className="w-3 h-3 text-white/60" />}
                {isFolder ? "Mini Chat de Carpeta" : "Mini Chat de Cuaderno"}
              </span>
              <strong className="block text-xs text-white truncate max-w-[240px] mt-0.5">
                {activeEntity.name}
              </strong>
            </div>

            <button
              onClick={onOpenChat}
              className="p-2 rounded-xl bg-white/[0.04] hover:bg-white hover:text-black transition"
              title="Abrir en Asistente Completo"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="py-4 space-y-3.5 max-h-[calc(100vh-230px)] overflow-y-auto k-scroll pr-1 text-xs">
            {currentHistory.map((m) => (
              <div
                key={m.id}
                className={[
                  "p-3 rounded-[16px] border text-xs leading-relaxed",
                  m.sender === "user"
                    ? "bg-[#16161a] border-white/20 text-white ml-6 text-right"
                    : "bg-[#111113] border-white/[0.08] text-white/80 mr-4",
                ].join(" ")}
              >
                <div className="flex justify-between items-center text-[9px] text-white/30 mb-1">
                  <span>{m.sender === "user" ? "Agustín" : SYSTEM_NAME}</span>
                  <span>{m.timestamp}</span>
                </div>
                <p>{m.text}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="pt-3 border-t border-white/[0.07]">
          <div className="relative flex items-center">
            <input
              type="text"
              value={miniPrompt}
              onChange={(e) => setMiniPrompt(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSendMiniChat();
              }}
              placeholder={isFolder ? `Consultar sobre la carpeta ${activeEntity.name}...` : `Consultar con ${activeEntity.name}...`}
              className="w-full h-10 rounded-[14px] bg-[#111113] border border-white/[0.08] pl-3.5 pr-10 text-xs text-white placeholder:text-white/25 outline-none focus:border-white/30"
            />
            <button
              onClick={handleSendMiniChat}
              className="absolute right-1.5 w-7 h-7 rounded-[10px] bg-white text-black flex items-center justify-center hover:bg-white/90 transition shadow-sm"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </aside>

      {readinessTopic && (
        <ReadinessModal
          isOpen={!!readinessTopic}
          onClose={() => setReadinessTopic(null)}
          topicId={readinessTopic.id}
          topicTitle={readinessTopic.title}
          onStartTopic={() => onOpenChat()}
        />
      )}
    </main>
  );
};


export default NotebooksView;
