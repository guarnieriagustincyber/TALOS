import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar as CalendarIcon,
  Check,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Plus,
  Shield,
  Target,
} from "lucide-react";
import { KanbanTask, SpacedRepetitionDueItem } from "./types";
import { INITIAL_KANBAN_TASKS } from "./KanbanView";

export interface CalendarEvent {
  title: string;
  type: "exam" | "lab" | "monk";
  desc: string;
  checklist: { text: string; done: boolean }[];
  isDue?: boolean;
}

export const parseDeadlineDate = (
  deadlineStr: string
): { year: number; month: number; day: number } | null => {
  if (!deadlineStr) return null;
  const str = deadlineStr.trim().toLowerCase();

  // Formato ISO: YYYY-MM-DD
  const isoMatch = str.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
  if (isoMatch) {
    return {
      year: parseInt(isoMatch[1], 10),
      month: parseInt(isoMatch[2], 10) - 1,
      day: parseInt(isoMatch[3], 10),
    };
  }

  // Formato DD/MM/YYYY
  const slashMatch = str.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})$/);
  if (slashMatch) {
    return {
      year: parseInt(slashMatch[3], 10),
      month: parseInt(slashMatch[2], 10) - 1,
      day: parseInt(slashMatch[1], 10),
    };
  }

  // Formato textual en español / inglés: "24 Oct 2026", "28 Octubre 2026", "02 Nov 2026"
  const monthMap: Record<string, number> = {
    ene: 0,
    jan: 0,
    feb: 1,
    mar: 2,
    abr: 3,
    apr: 3,
    may: 4,
    jun: 5,
    jul: 6,
    ago: 7,
    aug: 7,
    sep: 8,
    set: 8,
    oct: 9,
    nov: 10,
    dic: 11,
    dec: 11,
  };

  const textMatch = str.match(/^(\d{1,2})\s+([a-záéíóú]{3,})\s+(\d{4})$/);
  if (textMatch) {
    const day = parseInt(textMatch[1], 10);
    const prefix = textMatch[2].substring(0, 3);
    const m = monthMap[prefix];
    const y = parseInt(textMatch[3], 10);
    if (m !== undefined && !isNaN(day) && !isNaN(y)) {
      return { year: y, month: m, day };
    }
  }

  return null;
};

export interface CalendarViewProps {
  tasks?: KanbanTask[];
  onToggleTaskSubtask?: (taskId: string, subtaskId: string) => void;
  onOpenTopic?: (topic: string) => void;
}

export const CalendarView: React.FC<CalendarViewProps> = ({
  tasks = INITIAL_KANBAN_TASKS,
  onToggleTaskSubtask,
  onOpenTopic,
}) => {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [selectedDay, setSelectedDay] = useState(today.getDate());
  const [manualEvents, setManualEvents] = useState<Record<string, CalendarEvent>>({});

  const [adding, setAdding] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState("");

  // Consumir repasos espaciados reales de E3 SM-2
  const {
    data: dueItems,
    isLoading: loadingDue,
    isError: errorDue,
    error: dueErr,
  } = useQuery<SpacedRepetitionDueItem[]>({
    queryKey: ["studentSpacedRepetitionDue"],
    queryFn: async () => {
      const res = await fetch("/api/student/spaced-repetition/due");
      if (!res.ok) {
        throw new Error(`Error ${res.status} al consultar repasos espaciados: ${res.statusText}`);
      }
      return res.json();
    },
  });

  const months = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
  ];

  const week = ["LUN", "MAR", "MIÉ", "JUE", "VIE", "SÁB", "DOM"];

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const offset = (new Date(year, month, 1).getDay() + 6) % 7;

  const keyFor = (day: number) =>
    `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;

  // Combinar eventos manuales con los calculados por SM-2
  const events = useMemo<Record<string, CalendarEvent>>(() => {
    const combined: Record<string, CalendarEvent> = { ...manualEvents };

    if (dueItems) {
      dueItems.forEach((item) => {
        const d = new Date(item.due_date);
        if (!isNaN(d.getTime())) {
          const k = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
            d.getDate()
          ).padStart(2, "0")}`;
          combined[k] = {
            title: `Repaso SM-2: ${item.topic_title}`,
            type: "monk",
            desc: `Ancla: ${item.anchor_id} · Intervalo: ${item.interval_days}d · EF: ${item.ef} · ${
              item.is_due ? "Vencido (Atención Prioritaria)" : "Programado"
            }`,
            checklist: [
              { text: `Revisar apuntes y aserciones de ${item.topic_title}`, done: false },
              { text: `Ejecutar verificación de anclaje SM-2 en sandbox`, done: false },
            ],
            isDue: item.is_due,
          };
        }
      });
    }

    return combined;
  }, [manualEvents, dueItems]);

  const selectedEvent = events[keyFor(selectedDay)];

  // Agrupar misiones tácticas por día del mes activo
  const missionsByDay = useMemo(() => {
    const map: Record<number, KanbanTask[]> = {};
    tasks.forEach((t) => {
      const parsed = parseDeadlineDate(t.deadline);
      if (parsed && parsed.year === year && parsed.month === month) {
        if (!map[parsed.day]) map[parsed.day] = [];
        map[parsed.day].push(t);
      }
    });
    return map;
  }, [tasks, year, month]);

  const selectedMissions = missionsByDay[selectedDay] || [];

  const changeMonth = (delta: number) => {
    let next = month + delta;
    let nextYear = year;

    if (next < 0) {
      next = 11;
      nextYear--;
    }

    if (next > 11) {
      next = 0;
      nextYear++;
    }

    setMonth(next);
    setYear(nextYear);
    setSelectedDay(1);
  };

  const addEvent = () => {
    if (!newEventTitle.trim()) return;

    setManualEvents((prev) => ({
      ...prev,
      [keyFor(selectedDay)]: {
        title: newEventTitle.trim(),
        type: "lab",
        desc: "Hito registrado manualmente en TALOS.",
        checklist: [{ text: "Preparación inicial", done: false }],
      },
    }));

    setNewEventTitle("");
    setAdding(false);
  };

  const toggleChecklist = (index: number) => {
    if (!selectedEvent) return;

    setManualEvents((prev) => ({
      ...prev,
      [keyFor(selectedDay)]: {
        ...selectedEvent,
        checklist: selectedEvent.checklist.map((item, i) =>
          i === index ? { ...item, done: !item.done } : item
        ),
      },
    }));
  };

  return (
    <main className="flex-1 overflow-y-auto k-scroll bg-[#0b0b0d] px-8 pt-8 pb-10 font-mono">
      <div className="max-w-6xl 2xl:max-w-7xl mx-auto space-y-6">
        {/* ENCABEZADO */}
        <div className="flex flex-wrap items-end justify-between gap-5 pb-5 border-b border-white/[0.08]">
          <div>
            <div className="flex items-center gap-2 py-2 min-h-[2.25rem]">
              <span className="block text-[11px] uppercase tracking-[0.24em] text-white/45 leading-normal">
                temporal layer // sincronización doctrinal & sm-2
              </span>
              <span className="inline-flex items-center text-[9px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 font-mono shrink-0">
                {dueItems ? `${dueItems.length} Anclas SM-2 Activas` : "Cargando SM-2..."}
              </span>
            </div>
            <h1 className="mt-1 text-2xl md:text-3xl font-semibold text-white">
              {months[month]} {year}
            </h1>
            <p className="mt-1 text-xs text-white/40">
              Fechas de repetición espaciada SM-2 y misiones tácticas programadas por fecha límite.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => changeMonth(-1)}
              className="w-10 h-10 rounded-[13px] bg-white/[0.04] border border-white/[0.08] hover:bg-white hover:text-black flex items-center justify-center transition"
              title="Mes anterior"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                const now = new Date();
                setYear(now.getFullYear());
                setMonth(now.getMonth());
                setSelectedDay(now.getDate());
              }}
              className="h-10 px-3.5 rounded-[13px] bg-white/[0.04] border border-white/[0.08] text-xs uppercase tracking-wider text-white/60 hover:text-white transition"
              title="Ir a Hoy"
            >
              Hoy
            </button>
            <button
              onClick={() => changeMonth(1)}
              className="w-10 h-10 rounded-[13px] bg-white/[0.04] border border-white/[0.08] hover:bg-white hover:text-black flex items-center justify-center transition"
              title="Mes siguiente"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* FAIL-CLOSED BANNER SI ERROR EN TELEMETRÍA */}
        {errorDue && (
          <div className="rounded-[18px] bg-rose-950/40 border border-rose-500/30 p-4 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <div className="text-xs text-rose-200">
              <strong className="block font-bold text-rose-300">
                Fallo al recuperar calendario de repetición espaciada:
              </strong>
              {dueErr?.message || "No se pudo sincronizar con /api/student/spaced-repetition/due"}
            </div>
          </div>
        )}

        {/* CONTENEDOR GRID + PANEL LATERAL */}
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_380px] gap-5">
          {/* CALENDARIO MENSUAL */}
          <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5">
            <div className="grid grid-cols-7 gap-2 pb-3 border-b border-white/[0.06]">
              {week.map((day) => (
                <span
                  key={day}
                  className="text-center text-[11px] uppercase tracking-wider text-white/35 font-semibold"
                >
                  {day}
                </span>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-2 mt-3">
              {Array.from({ length: offset }).map((_, index) => (
                <div
                  key={`blank-${index}`}
                  className="h-24 rounded-[14px] bg-black/30"
                />
              ))}

              {Array.from({ length: daysInMonth }).map((_, index) => {
                const day = index + 1;
                const key = keyFor(day);
                const event = events[key];
                const dayMissions = missionsByDay[day] || [];
                const selected = selectedDay === day;

                return (
                  <button
                    key={day}
                    onClick={() => setSelectedDay(day)}
                    className={[
                      "h-24 rounded-[14px] border p-2 text-left flex flex-col justify-between transition overflow-hidden",
                      selected
                        ? "bg-[#1a1a1c] border-amber-400/60 shadow-[0_0_12px_rgba(245,158,11,0.15)]"
                        : "bg-black/25 border-white/[0.05] hover:border-white/[0.14]",
                    ].join(" ")}
                  >
                    <div className="flex items-center justify-between">
                      <span
                        className={[
                          "text-xs font-semibold",
                          selected ? "text-amber-300" : "text-white/45",
                        ].join(" ")}
                      >
                        {day}
                      </span>
                      <div className="flex items-center gap-1">
                        {dayMissions.length > 0 && (
                          <span
                            className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_6px_#F59E0B]"
                            title={`${dayMissions.length} misión(es) asignada(s)`}
                          />
                        )}
                        {event && (
                          <span
                            className={`w-2 h-2 rounded-full ${
                              event.isDue ? "bg-rose-400 shadow-[0_0_6px_#f43f5e]" : "bg-white shadow-[0_0_6px_#fff]"
                            }`}
                            title={event.isDue ? "Repaso SM-2 Vencido" : "Evento programado"}
                          />
                        )}
                      </div>
                    </div>

                    <div className="space-y-1 w-full overflow-hidden">
                      {dayMissions.length > 0 && (
                        <span className="block truncate rounded-[8px] bg-amber-950/80 border border-amber-400/30 px-1.5 py-0.5 text-[8.5px] text-amber-300 font-mono flex items-center gap-1">
                          <Target className="w-2.5 h-2.5 shrink-0 text-amber-400" />
                          <span className="truncate">{dayMissions[0].title}</span>
                          {dayMissions.length > 1 && (
                            <span className="text-[7.5px] text-amber-400/70 font-bold shrink-0">
                              +{dayMissions.length - 1}
                            </span>
                          )}
                        </span>
                      )}

                      {event && (
                        <span
                          className={`block truncate rounded-[8px] border px-1.5 py-0.5 text-[8.5px] ${
                            event.isDue
                              ? "bg-rose-950/60 border-rose-500/30 text-rose-300 font-bold"
                              : "bg-[#151517] border-white/[0.06] text-white/70"
                          }`}
                        >
                          {event.title}
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          {/* PANEL DÍA SELECCIONADO */}
          <section className="rounded-[24px] bg-[#101012] border border-white/[0.08] p-5 flex flex-col">
            <div className="flex items-start justify-between pb-4 border-b border-white/[0.06]">
              <div>
                <span className="block text-[10px] uppercase tracking-wider text-white/35">
                  día seleccionado // inspección
                </span>
                <strong className="block mt-1 text-xl text-white">
                  {selectedDay} {months[month]}
                </strong>
                <span className="text-[10px] text-white/40">
                  {selectedMissions.length} misiones · {selectedEvent ? "1 evento" : "0 eventos"}
                </span>
              </div>

              <button
                onClick={() => setAdding(true)}
                className="w-9 h-9 rounded-[12px] bg-white text-black flex items-center justify-center hover:bg-white/90 transition shadow-sm"
                title="Añadir evento manual"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>

            {adding && (
              <div className="mt-4 rounded-[16px] bg-black border border-white/[0.08] p-3.5 space-y-2">
                <input
                  autoFocus
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                  placeholder="Título del evento"
                  className="w-full h-9 rounded-[10px] bg-[#101012] border border-white/[0.06] px-3 text-xs text-white outline-none"
                />
                <div className="flex justify-end gap-2 pt-1">
                  <button
                    onClick={() => setAdding(false)}
                    className="text-xs text-white/40 hover:text-white px-2 py-1"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={addEvent}
                    className="h-8 px-3 rounded-[10px] bg-white text-black text-xs font-bold"
                  >
                    Guardar
                  </button>
                </div>
              </div>
            )}

            {/* LISTA DE MISIONES Y EVENTOS */}
            <div className="flex-1 pt-4 space-y-4 overflow-y-auto k-scroll max-h-[520px] pr-1">
              {loadingDue && (
                <div className="flex items-center justify-center gap-2 py-4 text-xs text-amber-400">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sincronizando anclas SM-2...</span>
                </div>
              )}

              {/* MISIONES TÁCTICAS VINCULADAS */}
              {selectedMissions.length > 0 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-[10px] uppercase tracking-wider text-amber-400 font-semibold">
                    <span className="flex items-center gap-1.5">
                      <Target className="w-3 h-3 text-amber-400" />
                      Misiones Tácticas (Kanban)
                    </span>
                    <span className="text-white/40">{selectedMissions.length}</span>
                  </div>

                  {selectedMissions.map((mission) => {
                    const statusColor =
                      mission.column === "finalizadas"
                        ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20"
                        : mission.column === "haciendo"
                        ? "text-amber-400 bg-amber-500/10 border-amber-500/20"
                        : "text-zinc-400 bg-white/[0.05] border-white/10";

                    return (
                      <div
                        key={mission.id}
                        className="rounded-[18px] bg-[#141416] border border-white/[0.08] p-4 space-y-3 shadow-sm hover:border-white/20 transition"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span
                              className={`px-2 py-0.5 rounded text-[9.5px] font-mono uppercase font-semibold border ${statusColor}`}
                            >
                              {mission.column}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                              {mission.priority}
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-white/40 truncate max-w-[120px]">
                            #{mission.scope}
                          </span>
                        </div>

                        <div>
                          <h4 className="text-xs font-semibold text-white leading-snug">
                            {mission.title}
                          </h4>
                          {mission.description && (
                            <p className="mt-1 text-[11px] text-white/50 leading-relaxed">
                              {mission.description}
                            </p>
                          )}
                        </div>

                        {/* SUBTAREAS VINCULADAS */}
                        {mission.subtasks && mission.subtasks.length > 0 && (
                          <div className="pt-2 border-t border-white/[0.06] space-y-1.5">
                            <span className="text-[9px] uppercase tracking-wider text-white/35 font-semibold block">
                              Criterios de Verificación ({mission.subtasks.filter((s) => s.done).length}/{mission.subtasks.length})
                            </span>
                            <div className="space-y-1">
                              {mission.subtasks.map((st) => (
                                <button
                                  key={st.id}
                                  type="button"
                                  onClick={() =>
                                    onToggleTaskSubtask?.(mission.id, st.id)
                                  }
                                  className="w-full text-left flex items-start gap-2 text-xs py-0.5 group"
                                >
                                  <span
                                    className={`w-3.5 h-3.5 rounded-[4px] border flex items-center justify-center shrink-0 mt-0.5 transition ${
                                      st.done
                                        ? "bg-amber-400 border-amber-400 text-black"
                                        : "border-white/30 group-hover:border-white/60"
                                    }`}
                                  >
                                    {st.done && (
                                      <Check className="w-2.5 h-2.5 stroke-[3]" />
                                    )}
                                  </span>
                                  <span
                                    className={`leading-tight text-[11px] ${
                                      st.done
                                        ? "line-through text-white/30"
                                        : "text-white/80 group-hover:text-white"
                                    }`}
                                  >
                                    {st.text}
                                  </span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}

              {/* EVENTO DE CALENDARIO / REPASO ESPACIADO SM-2 */}
              {selectedEvent && (
                <div
                  className={`rounded-[18px] border p-4 space-y-3 ${
                    selectedEvent.isDue
                      ? "bg-rose-950/20 border-rose-500/30"
                      : "bg-[#151517] border-white/[0.08]"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`inline-flex items-center px-2.5 py-1 rounded-full font-mono text-[10px] uppercase tracking-wider font-semibold ${
                        selectedEvent.isDue
                          ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                          : "bg-white text-black"
                      }`}
                    >
                      {selectedEvent.isDue ? "SM-2 Vencido" : selectedEvent.type}
                    </span>
                    <span className="text-[10px] text-white/40">Telemetría SM-2</span>
                  </div>
                  <h3 className="text-xs font-semibold text-white">
                    {selectedEvent.title}
                  </h3>
                  <p className="text-[11px] leading-relaxed text-white/50">
                    {selectedEvent.desc}
                  </p>

                  <div className="pt-2.5 border-t border-white/[0.06]">
                    <span className="block text-[10px] uppercase tracking-wider text-white/35 mb-2">
                      Checklist de Consolidación
                    </span>

                    <div className="space-y-1.5">
                      {selectedEvent.checklist.map((item, index) => (
                        <button
                          key={item.text}
                          onClick={() => toggleChecklist(index)}
                          className="w-full text-left flex items-start gap-2 text-xs py-0.5"
                        >
                          <span
                            className={[
                              "w-3.5 h-3.5 rounded-[4px] border flex items-center justify-center shrink-0 mt-0.5 transition",
                              item.done
                                ? "bg-white border-white text-black"
                                : "border-white/30",
                            ].join(" ")}
                          >
                            {item.done && <Check className="w-2.5 h-2.5 stroke-[3]" />}
                          </span>
                          <span
                            className={[
                              "leading-tight text-[11px]",
                              item.done
                                ? "text-white/30 line-through"
                                : "text-white/70",
                            ].join(" ")}
                          >
                            {item.text}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>

                  {onOpenTopic && (
                    <button
                      onClick={() => onOpenTopic(selectedEvent.title)}
                      className="mt-2 text-left text-[10.5px] text-amber-300 hover:text-amber-200 font-semibold flex items-center gap-1 pt-2 border-t border-white/[0.05]"
                    >
                      Iniciar Sesión de Repaso &rarr;
                    </button>
                  )}
                </div>
              )}

              {/* ESTADO VACÍO SI NO HAY NADA */}
              {!selectedEvent && selectedMissions.length === 0 && (
                <div className="h-full min-h-[220px] rounded-[18px] bg-black/25 border border-dashed border-white/[0.08] flex flex-col items-center justify-center text-center px-5">
                  <CalendarIcon className="w-7 h-7 text-white/20" />
                  <p className="mt-3 text-xs text-white/35">
                    Sin eventos críticos ni repeticiones espaciadas para esta fecha.
                  </p>
                </div>
              )}
            </div>

            <div className="mt-4 pt-4 border-t border-white/[0.06] flex items-center justify-between text-xs">
              <span className="text-[10px] uppercase tracking-wider text-white/35 flex items-center gap-1.5">
                <Shield className="w-3 h-3 text-amber-400" />
                TALOS Spaced Repetition
              </span>
              <span className="text-[11px] text-white/60 font-mono">
                Algoritmo SM-2 Activo
              </span>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
};

export default CalendarView;
