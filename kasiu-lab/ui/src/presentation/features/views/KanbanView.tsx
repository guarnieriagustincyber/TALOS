import React, { useMemo, useState } from "react";
import {
  BookOpen,
  Check,
  CheckSquare,
  ChevronDown,
  ChevronRight,
  Clock,
  Edit3,
  Filter,
  Folder,
  Layers,
  Plus,
  Shield,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { FSItem, KanbanTask, TaskColumn, TaskScopeType } from "./types";

export const INITIAL_KANBAN_TASKS: KanbanTask[] = [
  {
    id: "task_001",
    title: "Resolver ejercicio 3.5 del libro",
    description: "Ejercicios de fijación de funciones puras y paso de parámetros.",
    column: "pendiente",
    priority: "P2",
    scope: "Programación Básica",
    scopeType: "notebook",
    deadline: "15 Feb 2026",
    isExpanded: false,
    subtasks: [
      { id: "s-p1", text: "Diseñar firma y docstrings", done: true },
      { id: "s-p2", text: "Implementar asserts de prueba", done: false },
    ],
  },
  {
    id: "task_002",
    title: "Implementar validador de IPv4",
    description: "Parser modular de direcciones IP con separación SRP y testing.",
    column: "haciendo",
    priority: "P1",
    scope: "Programación Básica",
    scopeType: "notebook",
    deadline: "20 Feb 2026",
    isExpanded: true,
    subtasks: [
      { id: "s-p3", text: "Separar octetos con split()", done: true },
      { id: "s-p4", text: "Validar rango 0-255 en cada bloque", done: true },
      { id: "s-p5", text: "Manejo de excepciones con ValueError", done: false },
    ],
  },
  {
    id: "task_003",
    title: "Completar capítulo 2",
    description: "Lectura y asimilación de Estructuras de Control (Spraul).",
    column: "finalizadas",
    priority: "P2",
    scope: "Programación Básica",
    scopeType: "notebook",
    deadline: "Completado",
    isExpanded: false,
    subtasks: [
      { id: "s-p6", text: "Control de flujo secuencial", done: true },
      { id: "s-p7", text: "Bucles while deterministas", done: true },
    ],
  },
  {
    id: "task_004",
    title: "Estudiar punteros (capítulo 5)",
    description: "Mapeo de memoria Heap vs Stack y punteros lógicos.",
    column: "futuro",
    priority: "P3",
    scope: "Programación Básica",
    scopeType: "notebook",
    deadline: "01 Mar 2026",
    isExpanded: false,
    subtasks: [],
  },
  {
    id: "k1",
    title: "Parcial Presencial Arquitectura FADENA",
    description: "Evaluación teórica-práctica sobre jerarquía de memoria, AMAT y microarquitectura.",
    column: "pendiente",
    priority: "P1",
    scope: "FADENA (Ciberdefensa)",
    scopeType: "folder",
    deadline: "24 Oct 2026",
    isExpanded: true,
    subtasks: [
      { id: "s1", text: "Repasar Fetch-Decode-Execute en Datapath", done: true },
      { id: "s2", text: "Dominar fórmula AMAT con penalización L1/L2", done: false },
      { id: "s3", text: "Ejercicios de arbitraje de bus DMA", done: false },
    ],
  },
  {
    id: "k2",
    title: "Prueba de SYN Cookies en Sandbox RHEL 9",
    description: "Validación experimental de mitigación de SYN Flood sin consumo de backlog TCP.",
    column: "haciendo",
    priority: "P1",
    scope: "Fundamentos TCP/IP",
    scopeType: "notebook",
    deadline: "28 Oct 2026",
    isExpanded: true,
    subtasks: [
      { id: "s4", text: "Capturar ráfaga SYN Flood con tcpdump", done: true },
      { id: "s5", text: "Verificar activación en /proc/sys/net/ipv4/tcp_syncookies", done: true },
      { id: "s6", text: "Validar ACK con número de secuencia criptográfico", done: false },
    ],
  },
  {
    id: "k3",
    title: "Validación de Hash-Lock Documental",
    description: "Aseguramiento de integridad criptográfica de fuentes RFC y libros canónicos.",
    column: "finalizadas",
    priority: "P3",
    scope: "TALOS Core",
    scopeType: "general",
    deadline: "Completado",
    isExpanded: false,
    subtasks: [
      { id: "s9", text: "Hash SHA-256 de RFC 793 verificado", done: true },
      { id: "s10", text: "Aserción determinista archivada en vector store", done: true },
    ],
  },
  {
    id: "k4",
    title: "Certificación Final Tramo 1 TCP",
    description: "Examen de consolidación de control de congestión (Reno, Cubic) y ventana deslizante.",
    column: "futuro",
    priority: "P2",
    scope: "Fundamentos TCP/IP",
    scopeType: "notebook",
    deadline: "15 Nov 2026",
    isExpanded: false,
    subtasks: [
      { id: "s11", text: "Simulación de examen cronometrado", done: false },
      { id: "s12", text: "Revisión de anomalías en Wireshark lab", done: false },
    ],
  },
  {
    id: "k5",
    title: "Auditoría de Políticas Air-Gap y Supply Chain",
    description: "Verificación de hermetismo: 0 llamadas CDN y dependencias 100% locales.",
    column: "haciendo",
    priority: "P2",
    scope: "TALOS Core",
    scopeType: "general",
    deadline: "02 Nov 2026",
    isExpanded: false,
    subtasks: [
      { id: "s13", text: "Ejecutar scripts/verify_supply_chain.py", done: true },
      { id: "s14", text: "Validar Content-Security-Policy estricta", done: false },
    ],
  },
  {
    id: "k6",
    title: "Implementación de Decodificador de Instrucciones",
    description: "Laboratorio de decodificación para instrucciones R-type e I-type.",
    column: "pendiente",
    priority: "P2",
    scope: "Arquitectura de Computadoras",
    scopeType: "notebook",
    deadline: "05 Nov 2026",
    isExpanded: false,
    subtasks: [
      { id: "s15", text: "Mapear campos opcode y funct", done: false },
      { id: "s16", text: "Configurar multiplexores de control", done: false },
    ],
  },
];

export interface KanbanViewProps {
  activeScope?: string;
  fsItems?: FSItem[];
  scopes?: string[];
  tasks?: KanbanTask[];
  onUpdateTasks?: (tasks: KanbanTask[]) => void;
  onAskAssistant?: (task: KanbanTask) => void;
}

export const KanbanView: React.FC<KanbanViewProps> = ({
  activeScope,
  fsItems = [],
  scopes,
  tasks: propTasks,
  onUpdateTasks,
  onAskAssistant,
}) => {
  const [internalTasks, setInternalTasks] = useState<KanbanTask[]>(INITIAL_KANBAN_TASKS);
  const tasks = propTasks ?? internalTasks;
  const setTasks = (updater: React.SetStateAction<KanbanTask[]>) => {
    if (onUpdateTasks) {
      const nextTasks = typeof updater === "function" ? updater(tasks) : updater;
      onUpdateTasks(nextTasks);
    } else {
      setInternalTasks(updater);
    }
  };
  const [draggingTaskId, setDraggingTaskId] = useState<string | null>(null);
  const [dragOverColumn, setDragOverColumn] = useState<TaskColumn | null>(null);

  // Filter state: "all" | "general" | "folder:<name>" | "notebook:<name>"
  const [selectedFilter, setSelectedFilter] = useState<string>("all");

  // Creation modal state
  const [isAdding, setIsAdding] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newScopeType, setNewScopeType] = useState<TaskScopeType>("general");
  const [newScope, setNewScope] = useState("TALOS Core");
  const [newPriority, setNewPriority] = useState<"P1" | "P2" | "P3">("P1");
  const [newDeadline, setNewDeadline] = useState("Esta semana");
  const [newSubtask, setNewSubtask] = useState("");
  const [newSubtasks, setNewSubtasks] = useState<string[]>([]);

  // Card editing modal state
  const [editingTask, setEditingTask] = useState<KanbanTask | null>(null);
  const [editSubtaskInput, setEditSubtaskInput] = useState("");

  // Derive folder and notebook lists from fsItems
  const { folderNames, notebookNames } = useMemo(() => {
    const folders: string[] = [];
    const notebooks: string[] = [];

    if (fsItems && fsItems.length > 0) {
      fsItems.forEach((item) => {
        const cleanName = item.name.replace(/\.nb$/, "");
        if (item.type === "folder") {
          folders.push(cleanName);
        } else if (item.type === "notebook") {
          notebooks.push(cleanName);
        }
      });
    }

    // Fallback if fsItems is empty
    if (folders.length === 0) {
      folders.push("FADENA (Ciberdefensa)", "Roadmap Ciberdefensa", "Fase 0 (Core Network)");
    }
    if (notebooks.length === 0) {
      notebooks.push("Fundamentos TCP/IP", "Arquitectura de Computadoras");
    }

    if (scopes && scopes.length > 0) {
      scopes.forEach((s) => {
        if (!notebooks.includes(s) && !folders.includes(s)) {
          notebooks.push(s);
        }
      });
    }

    return { folderNames: Array.from(new Set(folders)), notebookNames: Array.from(new Set(notebooks)) };
  }, [fsItems, scopes]);

  const cleanActiveScope = useMemo(() => {
    return activeScope ? activeScope.replace(/\.nb$/, "") : undefined;
  }, [activeScope]);

  // Columns definition
  const columns: { id: TaskColumn; label: string; accentColor: string; dotColor: string }[] = [
    { id: "pendiente", label: "Pendiente", accentColor: "border-amber-500/30", dotColor: "bg-amber-400" },
    { id: "haciendo", label: "Haciendo", accentColor: "border-amber-400/40", dotColor: "bg-amber-400" },
    { id: "finalizadas", label: "Finalizadas", accentColor: "border-emerald-500/30", dotColor: "bg-emerald-400" },
    { id: "futuro", label: "Futuro", accentColor: "border-purple-500/30", dotColor: "bg-purple-400" },
  ];

  // Filter tasks based on selectedFilter
  const filteredTasks = useMemo(() => {
    if (selectedFilter === "all") return tasks;
    if (selectedFilter === "general") {
      return tasks.filter((t) => t.scopeType === "general" || t.scope.toLowerCase().includes("talos") || t.scope.toLowerCase().includes("general"));
    }
    if (selectedFilter.startsWith("folder:")) {
      const folderTarget = selectedFilter.replace("folder:", "");
      return tasks.filter((t) => t.scope === folderTarget || (t.scopeType === "folder" && t.scope.includes(folderTarget)));
    }
    if (selectedFilter.startsWith("notebook:")) {
      const nbTarget = selectedFilter.replace("notebook:", "");
      return tasks.filter((t) => t.scope === nbTarget || (t.scopeType === "notebook" && t.scope.includes(nbTarget)));
    }
    if (selectedFilter.startsWith("active:")) {
      const target = selectedFilter.replace("active:", "");
      return tasks.filter((t) => t.scope === target || t.scope.includes(target));
    }
    return tasks;
  }, [tasks, selectedFilter]);

  // Open creation modal with appropriate scope preselection
  const openCreateModal = () => {
    if (selectedFilter.startsWith("folder:")) {
      setNewScopeType("folder");
      setNewScope(selectedFilter.replace("folder:", ""));
    } else if (selectedFilter.startsWith("notebook:")) {
      setNewScopeType("notebook");
      setNewScope(selectedFilter.replace("notebook:", ""));
    } else if (cleanActiveScope) {
      const isNotebook = notebookNames.includes(cleanActiveScope);
      setNewScopeType(isNotebook ? "notebook" : "folder");
      setNewScope(cleanActiveScope);
    } else {
      setNewScopeType("general");
      setNewScope("TALOS Core");
    }
    setNewTitle("");
    setNewDescription("");
    setNewPriority("P1");
    setNewDeadline("Esta semana");
    setNewSubtask("");
    setNewSubtasks([]);
    setIsAdding(true);
  };

  const handleCreate = () => {
    if (!newTitle.trim()) return;

    const newTask: KanbanTask = {
      id: `task-${Date.now()}`,
      title: newTitle.trim(),
      description: newDescription.trim() || undefined,
      column: "pendiente",
      priority: newPriority,
      scope: newScope,
      scopeType: newScopeType,
      deadline: newDeadline,
      isExpanded: true,
      subtasks: newSubtasks.map((text, index) => ({
        id: `sub-${Date.now()}-${index}`,
        text,
        done: false,
      })),
    };

    setTasks((prev) => [newTask, ...prev]);
    setIsAdding(false);
  };

  const handleSaveEdit = () => {
    if (!editingTask || !editingTask.title.trim()) return;

    setTasks((prev) =>
      prev.map((task) => (task.id === editingTask.id ? { ...editingTask, title: editingTask.title.trim() } : task))
    );
    setEditingTask(null);
  };

  const toggleSubtask = (taskId: string, subtaskId: string) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId
          ? {
              ...task,
              subtasks: task.subtasks.map((item) =>
                item.id === subtaskId ? { ...item, done: !item.done } : item
              ),
            }
          : task
      )
    );
  };

  const toggleExpand = (taskId: string) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId ? { ...task, isExpanded: !task.isExpanded } : task
      )
    );
  };

  const addSubtaskToExisting = (taskId: string, text: string) => {
    if (!text.trim()) return;
    setTasks((prev) =>
      prev.map((task) =>
        task.id === taskId
          ? {
              ...task,
              subtasks: [
                ...task.subtasks,
                { id: `sub-${Date.now()}`, text: text.trim(), done: false },
              ],
            }
          : task
      )
    );
  };

  const getScopeBadge = (task: KanbanTask) => {
    if (task.scopeType === "folder") {
      return {
        icon: <Folder className="w-3 h-3 text-amber-400" />,
        label: task.scope,
        border: "border-amber-500/20 bg-amber-950/20 text-amber-300",
      };
    }
    if (task.scopeType === "notebook") {
      return {
        icon: <BookOpen className="w-3 h-3 text-amber-400" />,
        label: task.scope,
        border: "border-amber-500/20 bg-amber-500/10 text-amber-300",
      };
    }
    return {
      icon: <Shield className="w-3 h-3 text-emerald-400" />,
      label: task.scope || "General",
      border: "border-emerald-500/20 bg-emerald-950/20 text-emerald-300",
    };
  };

  return (
    <main className="flex-1 min-w-0 h-full overflow-hidden bg-[#0b0b0d] px-6 lg:px-8 py-6 relative font-mono text-xs select-none">
      <div className="h-full flex flex-col max-w-7xl 2xl:max-w-[1700px] mx-auto space-y-4">
        {/* Header bar */}
        <div className="flex flex-col md:flex-row md:items-end justify-between pb-4 border-b border-white/[0.08] shrink-0 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 text-[10px] uppercase tracking-[0.24em] text-white/40 font-bold">
                <Layers className="w-3.5 h-3.5 text-amber-400" />
                Operational Mission Matrix
              </span>
              <span className="px-2 py-0.5 rounded-full bg-white/[0.06] border border-white/[0.08] text-[9px] text-white/50">
                {filteredTasks.length} activas
              </span>
            </div>
            <h1 className="mt-1 text-2xl md:text-3xl font-semibold text-white tracking-tight">
              Misión Táctica y Objetivos
            </h1>
            <p className="mt-1 text-xs text-white/40">
              Control operacional segmentado: misiones globales del sistema, por carpeta curricular o por cuaderno activo.
            </p>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={openCreateModal}
              className="h-9 px-4 rounded-[12px] bg-white text-black text-xs font-bold uppercase tracking-wider flex items-center gap-2 hover:bg-white/90 transition shadow-[0_0_20px_rgba(255,255,255,0.15)]"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              Nueva misión
            </button>
          </div>
        </div>

        {/* Tactical Scope Filter Bar */}
        <div className="flex items-center gap-2 overflow-x-auto k-scroll pb-1 shrink-0 text-[11px]">
          <span className="flex items-center gap-1.5 text-white/30 shrink-0 uppercase tracking-wider text-[10px] mr-1">
            <Filter className="w-3 h-3 text-white/40" />
            Ámbito:
          </span>

          <button
            onClick={() => setSelectedFilter("all")}
            className={`h-7 px-3 rounded-[9px] border transition shrink-0 flex items-center gap-1.5 ${
              selectedFilter === "all"
                ? "bg-white text-black font-semibold border-white"
                : "bg-[#131316] text-white/60 border-white/[0.08] hover:text-white hover:border-white/20"
            }`}
          >
            Todas ({tasks.length})
          </button>

          <button
            onClick={() => setSelectedFilter("general")}
            className={`h-7 px-3 rounded-[9px] border transition shrink-0 flex items-center gap-1.5 ${
              selectedFilter === "general"
                ? "bg-emerald-500/20 text-emerald-300 font-semibold border-emerald-500/40"
                : "bg-[#131316] text-white/60 border-white/[0.08] hover:text-white hover:border-white/20"
            }`}
          >
            <Shield className="w-3 h-3 text-emerald-400" />
            General / Sistema
          </button>

          {/* Active entity quick filter if present */}
          {cleanActiveScope && (
            <button
              onClick={() => setSelectedFilter(`active:${cleanActiveScope}`)}
              className={`h-7 px-3 rounded-[9px] border transition shrink-0 flex items-center gap-1.5 ${
                selectedFilter === `active:${cleanActiveScope}`
                  ? "bg-amber-500/20 text-amber-300 font-semibold border-amber-500/40"
                  : "bg-[#131316] text-amber-400/80 border-amber-500/20 hover:border-amber-400/50"
              }`}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
              Ámbito Activo: {cleanActiveScope}
            </button>
          )}

          {/* Folder dropdown selector */}
          <div className="relative shrink-0">
            <select
              value={selectedFilter.startsWith("folder:") ? selectedFilter : ""}
              onChange={(e) => {
                if (e.target.value) setSelectedFilter(e.target.value);
              }}
              className="h-7 px-2.5 rounded-[9px] bg-[#131316] border border-white/[0.08] text-[11px] text-white/70 hover:text-white hover:border-white/20 outline-none transition"
            >
              <option value="" disabled>
                📁 Filtrar por Carpeta...
              </option>
              {folderNames.map((name) => (
                <option key={name} value={`folder:${name}`}>
                  Carpeta: {name}
                </option>
              ))}
            </select>
          </div>

          {/* Notebook dropdown selector */}
          <div className="relative shrink-0">
            <select
              value={selectedFilter.startsWith("notebook:") ? selectedFilter : ""}
              onChange={(e) => {
                if (e.target.value) setSelectedFilter(e.target.value);
              }}
              className="h-7 px-2.5 rounded-[9px] bg-[#131316] border border-white/[0.08] text-[11px] text-white/70 hover:text-white hover:border-white/20 outline-none transition"
            >
              <option value="" disabled>
                📖 Filtrar por Cuaderno...
              </option>
              {notebookNames.map((name) => (
                <option key={name} value={`notebook:${name}`}>
                  Cuaderno: {name}
                </option>
              ))}
            </select>
          </div>

          {selectedFilter !== "all" && (
            <button
              onClick={() => setSelectedFilter("all")}
              className="h-7 px-2 text-[10px] text-white/40 hover:text-white flex items-center gap-1 transition"
            >
              <X className="w-3 h-3" />
              Limpiar filtro
            </button>
          )}
        </div>

        {/* Kanban Board Columns */}
        <div className="flex-1 overflow-x-auto k-scroll pb-2">
          <div className="grid grid-cols-4 gap-4 min-w-[1060px] h-full">
            {columns.map((column) => {
              const columnTasks = filteredTasks.filter((task) => task.column === column.id);
              const isTarget = dragOverColumn === column.id;

              return (
                <div
                  key={column.id}
                  onDragOver={(e) => {
                    e.preventDefault();
                    setDragOverColumn(column.id);
                  }}
                  onDragLeave={() => setDragOverColumn(null)}
                  onDrop={(e) => {
                    e.preventDefault();
                    const id = e.dataTransfer.getData("text/plain") || draggingTaskId;
                    if (id) {
                      setTasks((prev) =>
                        prev.map((task) =>
                          task.id === id ? { ...task, column: column.id } : task
                        )
                      );
                    }
                    setDraggingTaskId(null);
                    setDragOverColumn(null);
                  }}
                  className={`rounded-[20px] bg-[#101012] border p-3.5 flex flex-col min-h-0 transition duration-150 ${
                    isTarget
                      ? "border-white/40 bg-[#16161a] shadow-[0_0_25px_rgba(255,255,255,0.08)]"
                      : "border-white/[0.07]"
                  }`}
                >
                  {/* Column Header */}
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] shrink-0">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${column.dotColor}`} />
                      <span className="text-xs uppercase tracking-wider font-semibold text-white/80">
                        {column.label}
                      </span>
                    </div>
                    <span className="min-w-5 h-5 px-1.5 rounded-full bg-black/60 border border-white/[0.08] flex items-center justify-center text-[10px] text-white/60">
                      {columnTasks.length}
                    </span>
                  </div>

                  {/* Tasks List */}
                  <div className="flex-1 overflow-y-auto k-scroll space-y-3 pt-3 pr-1">
                    {columnTasks.length === 0 ? (
                      <div className="h-32 border border-dashed border-white/[0.06] rounded-[16px] flex flex-col items-center justify-center text-center p-3 text-white/25">
                        <CheckSquare className="w-5 h-5 mb-1.5 opacity-40" />
                        <span className="text-[10px]">Sin misiones en este estado</span>
                      </div>
                    ) : (
                      columnTasks.map((task) => {
                        const completed = task.subtasks.filter((s) => s.done).length;
                        const total = task.subtasks.length;
                        const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
                        const scopeBadge = getScopeBadge(task);

                        return (
                          <article
                            key={task.id}
                            draggable
                            onDragStart={(e) => {
                              setDraggingTaskId(task.id);
                              e.dataTransfer.setData("text/plain", task.id);
                            }}
                            className={`rounded-[16px] bg-[#141417] border border-white/[0.07] p-3.5 cursor-grab active:cursor-grabbing hover:border-white/[0.18] transition shadow-sm group ${
                              draggingTaskId === task.id ? "opacity-30 border-dashed" : ""
                            }`}
                          >
                            {/* Card Top: Linear-style ID + Priority Badge + Actions */}
                            <div className="flex items-center justify-between gap-2">
                              <div className="flex items-center gap-1.5 min-w-0">
                                <span className="font-mono text-[9px] text-white/40 tracking-wider font-semibold">
                                  #{task.id.slice(-4).toUpperCase()}
                                </span>
                                <span
                                  className={`inline-flex items-center px-1.5 py-0.5 rounded text-[8.5px] font-bold uppercase tracking-wider border ${
                                    task.priority === "P1"
                                      ? "text-red-400 bg-red-950/40 border-red-500/40"
                                      : task.priority === "P2"
                                      ? "text-sky-400 bg-sky-950/40 border-sky-500/40"
                                      : "text-emerald-400 bg-emerald-950/40 border-emerald-500/40"
                                  }`}
                                >
                                  {task.priority === "P1" ? "P1" : task.priority === "P2" ? "P2" : "P3"}
                                </span>
                              </div>

                              <div className="flex items-center gap-1 opacity-60 group-hover:opacity-100 transition">
                                <button
                                  onClick={() => setEditingTask({ ...task })}
                                  title="Modificar misión"
                                  className="w-6 h-6 rounded-[7px] hover:bg-white/[0.08] text-white/50 hover:text-white flex items-center justify-center transition"
                                >
                                  <Edit3 className="w-3 h-3" />
                                </button>
                                <button
                                  onClick={() => toggleExpand(task.id)}
                                  title={task.isExpanded ? "Contraer sub-ítems" : "Expandir sub-ítems"}
                                  className="w-6 h-6 rounded-[7px] hover:bg-white/[0.08] text-white/50 hover:text-white flex items-center justify-center transition"
                                >
                                  {task.isExpanded ? (
                                    <ChevronDown className="w-3.5 h-3.5" />
                                  ) : (
                                    <ChevronRight className="w-3.5 h-3.5" />
                                  )}
                                </button>
                                <button
                                  onClick={() =>
                                    setTasks((prev) => prev.filter((item) => item.id !== task.id))
                                  }
                                  title="Eliminar misión"
                                  className="w-6 h-6 rounded-[7px] hover:bg-red-500/20 text-white/40 hover:text-red-400 flex items-center justify-center transition"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </button>
                              </div>
                            </div>

                            {/* Title */}
                            <h3 className="mt-2.5 text-xs font-semibold leading-snug text-white">
                              {task.title}
                            </h3>

                            {/* Description preview if present */}
                            {task.description && (
                              <p className="mt-1 text-[11px] text-white/45 line-clamp-2 leading-relaxed">
                                {task.description}
                              </p>
                            )}

                            {/* Scope Badge */}
                            <div className="mt-2.5 flex items-center">
                              <span
                                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-[6px] text-[10px] border ${scopeBadge.border}`}
                              >
                                {scopeBadge.icon}
                                <span className="truncate max-w-[180px]">{scopeBadge.label}</span>
                              </span>
                            </div>

                            {/* Checklist Progress */}
                            {total > 0 && (
                              <div className="mt-3">
                                <div className="flex items-center justify-between text-[10px] text-white/40">
                                  <span>Checklist · {completed}/{total}</span>
                                  <strong className="text-white/80">{percent}%</strong>
                                </div>
                                <div className="mt-1 h-1 rounded-full bg-white/[0.08] overflow-hidden">
                                  <div
                                    className={`h-full rounded-full transition-all duration-300 ${
                                      percent === 100
                                        ? "bg-emerald-400"
                                        : percent > 50
                                        ? "bg-amber-400"
                                        : "bg-white/70"
                                    }`}
                                    style={{ width: `${percent}%` }}
                                  />
                                </div>
                               </div>
                             )}

                             {/* Expandable Subtasks Checklist */}
                             {task.isExpanded && (
                               <div className="mt-3 pt-2.5 border-t border-white/[0.06] space-y-1.5">
                                 {task.subtasks.map((subtask) => (
                                   <button
                                     key={subtask.id}
                                     onClick={() => toggleSubtask(task.id, subtask.id)}
                                     className="w-full flex items-start gap-2 text-left py-0.5 group/item"
                                   >
                                     <span
                                       className={`w-3.5 h-3.5 rounded-[4px] border shrink-0 mt-0.5 flex items-center justify-center transition ${
                                         subtask.done
                                           ? "bg-emerald-500 border-emerald-500 text-black"
                                           : "border-white/30 group-hover/item:border-white/60"
                                       }`}
                                     >
                                       {subtask.done && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                                     </span>
                                     <span
                                       className={`text-[11px] leading-snug transition ${
                                         subtask.done
                                           ? "text-white/30 line-through"
                                           : "text-white/75 group-hover/item:text-white"
                                       }`}
                                     >
                                       {subtask.text}
                                     </span>
                                   </button>
                                 ))}

                                 <div className="pt-1.5">
                                   <input
                                     type="text"
                                     placeholder="+ Añadir sub-ítem..."
                                     onKeyDown={(e) => {
                                       if (e.key === "Enter") {
                                         const val = (e.target as HTMLInputElement).value.trim();
                                         if (val) {
                                           addSubtaskToExisting(task.id, val);
                                           (e.target as HTMLInputElement).value = "";
                                         }
                                       }
                                     }}
                                     className="w-full h-7 px-2 rounded-[7px] bg-black/60 border border-white/[0.08] text-[10px] text-white placeholder:text-white/25 outline-none focus:border-white/30"
                                   />
                                 </div>
                               </div>
                             )}

                             {/* Footer info: deadline & direct assistant action */}
                             <div className="mt-3 pt-2.5 border-t border-white/[0.06] flex items-center justify-between text-[10px] text-white/40">
                               <div className="flex items-center gap-1 font-mono text-[10px] text-white/50">
                                 <Clock className="w-3 h-3 text-white/30" />
                                 <span>{task.deadline}</span>
                               </div>

                               {onAskAssistant && (
                                 <button
                                   type="button"
                                   onClick={(e) => {
                                     e.stopPropagation();
                                     onAskAssistant(task);
                                   }}
                                   className="px-2 py-0.5 rounded-[6px] bg-white/[0.04] border border-white/[0.08] hover:bg-emerald-500/20 hover:border-emerald-500/40 text-white/60 hover:text-emerald-300 transition text-[9.5px] font-mono flex items-center gap-1 shadow-xs"
                                   title="Iniciar sesión en el asistente para resolver esta misión"
                                 >
                                   <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
                                   <span>Resolver</span>
                                 </button>
                               )}
                             </div>
                           </article>
                         );
                       })
                     )}
                   </div>
                 </div>
               );
             })}
            </div>
          </div>
        </div>

        {/* MODAL CREAR NUEVA MISIÓN */}
        {isAdding && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-150">
            <div className="w-full max-w-xl rounded-[22px] bg-[#101012] border border-white/[0.12] p-6 shadow-[0_25px_90px_rgba(0,0,0,0.85)] space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/[0.07]">
                <div className="flex items-center gap-2">
                  <CheckSquare className="w-4 h-4 text-amber-400" />
                  <span className="text-xs font-semibold uppercase tracking-wider text-white">
                    Registrar Misión Táctica
                  </span>
                </div>
                <button
                  onClick={() => setIsAdding(false)}
                  className="w-7 h-7 rounded-[8px] bg-white/[0.04] hover:bg-white hover:text-black flex items-center justify-center transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3.5">
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-white/40">
                    Título de la misión
                  </label>
                 <input
                   autoFocus
                   value={newTitle}
                   onChange={(e) => setNewTitle(e.target.value)}
                   placeholder="Ej. Análisis de Handshake TCP en Wireshark"
                   className="mt-1 w-full h-10 rounded-[11px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30"
                 />
               </div>

               <div>
                 <label className="block text-[10px] uppercase tracking-wider text-white/40">
                   Descripción operacional (Opcional)
                 </label>
                 <textarea
                   value={newDescription}
                   onChange={(e) => setNewDescription(e.target.value)}
                   rows={2}
                   placeholder="Detalle o consignas específicas de la misión..."
                   className="mt-1 w-full rounded-[11px] bg-black border border-white/[0.08] p-3 text-xs text-white outline-none focus:border-white/30 resize-none"
                 />
               </div>

               {/* Scope Selector: General vs Carpeta vs Cuaderno */}
               <div>
                 <label className="block text-[10px] uppercase tracking-wider text-white/40 mb-1.5">
                   Ámbito de la misión
                 </label>
                 <div className="grid grid-cols-3 gap-2">
                   <button
                     type="button"
                     onClick={() => {
                       setNewScopeType("general");
                       setNewScope("TALOS Core");
                     }}
                     className={`h-8 rounded-[9px] text-[11px] font-medium border flex items-center justify-center gap-1.5 transition ${
                       newScopeType === "general"
                         ? "bg-emerald-950/50 text-emerald-300 border-emerald-500/40"
                         : "bg-black border-white/[0.08] text-white/40 hover:text-white"
                     }`}
                   >
                     <Shield className="w-3 h-3" />
                     General
                   </button>
                   <button
                     type="button"
                     onClick={() => {
                       setNewScopeType("folder");
                       if (folderNames[0]) setNewScope(folderNames[0]);
                     }}
                     className={`h-8 rounded-[9px] text-[11px] font-medium border flex items-center justify-center gap-1.5 transition ${
                       newScopeType === "folder"
                         ? "bg-amber-950/50 text-amber-300 border-amber-500/40"
                         : "bg-black border-white/[0.08] text-white/40 hover:text-white"
                     }`}
                   >
                     <Folder className="w-3 h-3" />
                     Por Carpeta
                   </button>
                   <button
                     type="button"
                     onClick={() => {
                       setNewScopeType("notebook");
                       if (notebookNames[0]) setNewScope(notebookNames[0]);
                     }}
                     className={`h-8 rounded-[9px] text-[11px] font-medium border flex items-center justify-center gap-1.5 transition ${
                       newScopeType === "notebook"
                         ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                         : "bg-black border-white/[0.08] text-white/40 hover:text-white"
                     }`}
                   >
                     <BookOpen className="w-3 h-3" />
                     Por Cuaderno
                   </button>
                 </div>

                 {/* Sub-selector based on scope type */}
                 {newScopeType === "folder" && (
                   <select
                     value={newScope}
                     onChange={(e) => setNewScope(e.target.value)}
                     className="mt-2 w-full h-9 rounded-[10px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none"
                   >
                     {folderNames.map((name) => (
                       <option key={name} value={name}>
                         📁 {name}
                       </option>
                     ))}
                   </select>
                 )}

                 {newScopeType === "notebook" && (
                   <select
                     value={newScope}
                     onChange={(e) => setNewScope(e.target.value)}
                     className="mt-2 w-full h-9 rounded-[10px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none"
                   >
                     {notebookNames.map((name) => (
                       <option key={name} value={name}>
                         📖 {name}
                       </option>
                     ))}
                   </select>
                 )}
               </div>

               {/* Priority and Deadline */}
               <div className="grid grid-cols-2 gap-3">
                 <div>
                   <label className="block text-[10px] uppercase tracking-wider text-white/40">
                     Prioridad Semántica
                   </label>
                   <div className="grid grid-cols-3 gap-1.5 mt-1.5">
                     {(["P1", "P2", "P3"] as const).map((priority) => (
                       <button
                         key={priority}
                         type="button"
                         onClick={() => setNewPriority(priority)}
                         className={`h-8 rounded-[9px] text-[10px] font-bold border transition ${
                           newPriority === priority
                             ? priority === "P1"
                               ? "bg-red-950/60 text-red-300 border-red-500/50"
                               : priority === "P2"
                               ? "bg-sky-950/60 text-sky-300 border-sky-500/50"
                               : "bg-emerald-950/60 text-emerald-300 border-emerald-500/50"
                             : "bg-black border-white/[0.08] text-white/40 hover:text-white"
                         }`}
                       >
                         {priority}
                       </button>
                     ))}
                   </div>
                 </div>

                 <div>
                   <label className="block text-[10px] uppercase tracking-wider text-white/40">
                     Plazo / Deadline
                   </label>
                   <input
                     value={newDeadline}
                     onChange={(e) => setNewDeadline(e.target.value)}
                     className="mt-1.5 w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30"
                   />
                 </div>
               </div>

               {/* Initial Checklist */}
               <div>
                 <label className="block text-[10px] uppercase tracking-wider text-white/40">
                   Checklist Inicial
                 </label>
                 <div className="mt-1 flex gap-2">
                   <input
                     value={newSubtask}
                     onChange={(e) => setNewSubtask(e.target.value)}
                     onKeyDown={(e) => {
                       if (e.key === "Enter" && newSubtask.trim()) {
                         e.preventDefault();
                         setNewSubtasks((prev) => [...prev, newSubtask.trim()]);
                         setNewSubtask("");
                       }
                     }}
                     placeholder="Escribe un sub-ítem y pulsa Enter"
                     className="flex-1 h-8 rounded-[9px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30"
                   />
                   <button
                     type="button"
                     onClick={() => {
                       if (!newSubtask.trim()) return;
                       setNewSubtasks((prev) => [...prev, newSubtask.trim()]);
                       setNewSubtask("");
                     }}
                     className="h-8 px-3 rounded-[9px] bg-white/[0.06] border border-white/[0.08] text-[11px] text-white/70 hover:text-white transition"
                   >
                     Añadir
                   </button>
                 </div>

                 {newSubtasks.length > 0 && (
                   <div className="mt-2 space-y-1 max-h-24 overflow-y-auto k-scroll">
                     {newSubtasks.map((item, index) => (
                       <div
                         key={`${item}-${index}`}
                         className="rounded-[8px] bg-black border border-white/[0.06] px-2.5 py-1.5 flex items-center justify-between"
                       >
                         <span className="text-[11px] text-white/70">{item}</span>
                         <button
                           type="button"
                           onClick={() =>
                             setNewSubtasks((prev) => prev.filter((_, i) => i !== index))
                           }
                           className="text-white/30 hover:text-white"
                         >
                           <X className="w-3 h-3" />
                         </button>
                       </div>
                     ))}
                   </div>
                 )}
               </div>
             </div>

             <div className="pt-3 border-t border-white/[0.07] flex justify-end gap-2">
               <button
                 type="button"
                 onClick={() => setIsAdding(false)}
                 className="h-9 px-4 rounded-[10px] bg-white/[0.04] text-white/50 hover:text-white transition text-xs"
               >
                 Descartar
               </button>
               <button
                 type="button"
                 onClick={handleCreate}
                 className="h-9 px-4 rounded-[10px] bg-white text-black font-bold text-xs hover:bg-white/90 transition shadow-sm"
               >
                 Registrar misión
               </button>
             </div>
           </div>
         </div>
       )}

       {/* MODAL MODIFICAR MISIÓN */}
       {editingTask && (
         <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-150">
           <div className="w-full max-w-xl rounded-[22px] bg-[#101012] border border-white/[0.12] p-6 shadow-[0_25px_90px_rgba(0,0,0,0.85)] space-y-4">
             <div className="flex items-center justify-between pb-3 border-b border-white/[0.07]">
               <div className="flex items-center gap-2">
                 <Edit3 className="w-4 h-4 text-amber-400" />
                 <span className="text-xs font-semibold uppercase tracking-wider text-white">
                   Modificar Misión Táctica
                 </span>
               </div>
              <button
                onClick={() => setEditingTask(null)}
                className="w-7 h-7 rounded-[8px] bg-white/[0.04] hover:bg-white hover:text-black flex items-center justify-center transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3.5">
              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40">
                  Título
                </label>
                <input
                  value={editingTask.title}
                  onChange={(e) => setEditingTask({ ...editingTask, title: e.target.value })}
                  className="mt-1 w-full h-10 rounded-[11px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30"
                />
              </div>

              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40">
                  Descripción operacional
                </label>
                <textarea
                  value={editingTask.description || ""}
                  onChange={(e) => setEditingTask({ ...editingTask, description: e.target.value })}
                  rows={2}
                  className="mt-1 w-full rounded-[11px] bg-black border border-white/[0.08] p-3 text-xs text-white outline-none focus:border-white/30 resize-none"
                />
              </div>

              {/* Column Status and Priority */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-white/40">
                    Estado / Columna
                  </label>
                  <select
                    value={editingTask.column}
                    onChange={(e) =>
                      setEditingTask({ ...editingTask, column: e.target.value as TaskColumn })
                    }
                    className="mt-1 w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-2.5 text-xs text-white outline-none"
                  >
                    <option value="pendiente">Pendiente</option>
                    <option value="haciendo">Haciendo</option>
                    <option value="finalizadas">Finalizadas</option>
                    <option value="futuro">Futuro</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[10px] uppercase tracking-wider text-white/40">
                    Prioridad
                  </label>
                  <div className="grid grid-cols-3 gap-1.5 mt-1">
                    {(["P1", "P2", "P3"] as const).map((p) => (
                      <button
                        key={p}
                        type="button"
                        onClick={() => setEditingTask({ ...editingTask, priority: p })}
                        className={`h-8 rounded-[8px] text-[10px] font-bold border transition ${
                          editingTask.priority === p
                            ? p === "P1"
                              ? "bg-red-950/60 text-red-300 border-red-500/50"
                              : p === "P2"
                              ? "bg-sky-950/60 text-sky-300 border-sky-500/50"
                              : "bg-emerald-950/60 text-emerald-300 border-emerald-500/50"
                            : "bg-black border-white/[0.08] text-white/40 hover:text-white"
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Scope reassignment */}
              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40">
                  Ámbito Asignado
                </label>
                <div className="grid grid-cols-3 gap-2 mt-1">
                  <select
                    value={editingTask.scopeType || "general"}
                    onChange={(e) => {
                      const st = e.target.value as TaskScopeType;
                      setEditingTask({
                        ...editingTask,
                        scopeType: st,
                        scope:
                          st === "general"
                            ? "TALOS Core"
                            : st === "folder"
                            ? folderNames[0] || "General"
                            : notebookNames[0] || "General",
                      });
                    }}
                    className="h-8 rounded-[9px] bg-black border border-white/[0.08] px-2 text-[11px] text-white outline-none"
                  >
                    <option value="general">General</option>
                    <option value="folder">Carpeta</option>
                    <option value="notebook">Cuaderno</option>
                  </select>

                  <div className="col-span-2">
                    {editingTask.scopeType === "folder" ? (
                      <select
                        value={editingTask.scope}
                        onChange={(e) => setEditingTask({ ...editingTask, scope: e.target.value })}
                        className="w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-2 text-[11px] text-white outline-none"
                      >
                        {folderNames.map((f) => (
                          <option key={f} value={f}>
                            📁 {f}
                          </option>
                        ))}
                      </select>
                    ) : editingTask.scopeType === "notebook" ? (
                      <select
                        value={editingTask.scope}
                        onChange={(e) => setEditingTask({ ...editingTask, scope: e.target.value })}
                        className="w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-2 text-[11px] text-white outline-none"
                      >
                        {notebookNames.map((nb) => (
                          <option key={nb} value={nb}>
                            📖 {nb}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <input
                        value={editingTask.scope}
                        onChange={(e) => setEditingTask({ ...editingTask, scope: e.target.value })}
                        className="w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-2.5 text-[11px] text-white outline-none"
                        placeholder="TALOS Core / General"
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Deadline */}
              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40">
                  Plazo / Deadline
                </label>
                <input
                  value={editingTask.deadline}
                  onChange={(e) => setEditingTask({ ...editingTask, deadline: e.target.value })}
                  className="mt-1 w-full h-8 rounded-[9px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30"
                />
              </div>

              {/* Checklist editor */}
              <div>
                <label className="block text-[10px] uppercase tracking-wider text-white/40">
                  Checklist ({editingTask.subtasks.filter((s) => s.done).length}/{editingTask.subtasks.length} completados)
                </label>
                <div className="mt-1 flex gap-2">
                  <input
                    value={editSubtaskInput}
                    onChange={(e) => setEditSubtaskInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && editSubtaskInput.trim()) {
                        e.preventDefault();
                        setEditingTask({
                          ...editingTask,
                          subtasks: [
                            ...editingTask.subtasks,
                            { id: `sub-${Date.now()}`, text: editSubtaskInput.trim(), done: false },
                          ],
                        });
                        setEditSubtaskInput("");
                      }
                    }}
                    placeholder="+ Añadir sub-ítem..."
                    className="flex-1 h-8 rounded-[9px] bg-black border border-white/[0.08] px-3 text-xs text-white outline-none focus:border-white/30"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      if (!editSubtaskInput.trim()) return;
                      setEditingTask({
                        ...editingTask,
                        subtasks: [
                          ...editingTask.subtasks,
                          { id: `sub-${Date.now()}`, text: editSubtaskInput.trim(), done: false },
                        ],
                      });
                      setEditSubtaskInput("");
                    }}
                    className="h-8 px-3 rounded-[9px] bg-white/[0.06] border border-white/[0.08] text-[11px] text-white/70 hover:text-white transition"
                  >
                    Añadir
                  </button>
                </div>

                <div className="mt-2 space-y-1 max-h-28 overflow-y-auto k-scroll">
                  {editingTask.subtasks.map((sub, index) => (
                    <div
                      key={sub.id}
                      className="rounded-[8px] bg-black border border-white/[0.06] px-2.5 py-1.5 flex items-center justify-between gap-2"
                    >
                      <button
                        type="button"
                        onClick={() => {
                          setEditingTask({
                            ...editingTask,
                            subtasks: editingTask.subtasks.map((s) =>
                              s.id === sub.id ? { ...s, done: !s.done } : s
                            ),
                          });
                        }}
                        className="flex items-center gap-2 text-left flex-1 min-w-0"
                      >
                        <span
                          className={`w-3.5 h-3.5 rounded-[4px] border shrink-0 flex items-center justify-center ${
                            sub.done ? "bg-emerald-500 border-emerald-500 text-black" : "border-white/30"
                          }`}
                        >
                          {sub.done && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                        </span>
                        <span
                          className={`text-[11px] truncate ${
                            sub.done ? "text-white/30 line-through" : "text-white/80"
                          }`}
                        >
                          {sub.text}
                        </span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setEditingTask({
                            ...editingTask,
                            subtasks: editingTask.subtasks.filter((_, i) => i !== index),
                          });
                        }}
                        className="text-white/30 hover:text-red-400 transition"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-white/[0.07] flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setEditingTask(null)}
                className="h-9 px-4 rounded-[10px] bg-white/[0.04] text-white/50 hover:text-white transition text-xs"
              >
                Cancelar
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                className="h-9 px-4 rounded-[10px] bg-white text-black font-bold text-xs hover:bg-white/90 transition shadow-sm"
              >
                Guardar cambios
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};

export default KanbanView;
