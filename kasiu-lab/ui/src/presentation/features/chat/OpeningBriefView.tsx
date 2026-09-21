import React from 'react';
import { BookOpen, Play, RotateCcw, Sparkles } from 'lucide-react';
import { MessageBody } from './MessageBody';

export interface OpeningBriefFactsData {
  notebook_id: string;
  notebook_name: string;
  notebook_purpose: string;
  curriculum_position: {
    unit_or_module: string;
    unit_name: string;
    kcs_in_unit: string[];
    kcs_completed: string[];
    kcs_in_progress: string[];
    kcs_pending: string[];
  };
  eligible_kcs: string[];
  selected_kc: string;
  selected_kc_display_name?: string;
  selected_kc_rationale: string;
  bkt_estimate: number;
  bkt_note: string;
  student_context_note?: string;
  proposed_action: string;
  proposed_action_rationale: string;
}

export interface StudySessionSnapshotData {
  session_id: string;
  notebook_id: string;
  student_id: string;
  session_state_hash: string;
  episode_phase: string;
  current_kc_id: string;
  current_kc_name: string;
  bkt_estimate: number;
  bkt_note: string;
  available_actions: string[];
  opening_brief_facts: OpeningBriefFactsData;
  opening_brief_narrative?: string;
  policy_version: string;
}

interface OpeningBriefViewProps {
  snapshot: StudySessionSnapshotData;
  onExecuteAction: (action: string, payload?: Record<string, any>) => void;
  isLoading?: boolean;
}

export const OpeningBriefView: React.FC<OpeningBriefViewProps> = ({
  snapshot,
  onExecuteAction,
  isLoading = false,
}) => {
  const facts = snapshot.opening_brief_facts;
  const narrative = snapshot.opening_brief_narrative;
  const pos = facts?.curriculum_position;

  return (
    <div className="rounded-[24px] border border-white/[0.1] bg-[#101012] p-6 shadow-2xl mb-6 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.08] pb-4 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-[12px] bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-300">
                Apertura Curricular Soberana
              </span>
              <span className="text-[11px] font-mono text-white/40">
                {snapshot.policy_version}
              </span>
            </div>
            <h2 className="text-base font-bold text-white mt-1">
              {facts?.notebook_name || snapshot.notebook_id}
            </h2>
          </div>
        </div>

        {/* BKT State Box */}
        <div className="text-right font-mono bg-black/40 border border-white/[0.06] rounded-xl px-3 py-1.5">
          <span className="text-[10px] text-white/50 block">Estimación BKT Consultiva</span>
          <span className="text-xs font-bold text-cyan-300">
            P(L) = {(snapshot.bkt_estimate * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {/* Narrative block */}
      {narrative && (
        <div className="mb-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20 p-4 text-sm text-cyan-100/90 leading-relaxed font-sans">
          <div className="flex items-center gap-2 mb-2 text-xs font-mono font-semibold text-cyan-400">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Presentación del Tutor Epistémico</span>
          </div>
          <MessageBody content={narrative} />
        </div>
      )}

      {/* Curriculum Position Facts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4 font-mono text-xs">
        <div className="rounded-xl bg-black/30 border border-white/[0.06] p-3">
          <span className="text-white/40 block mb-1">Módulo Actual</span>
          <span className="text-white font-semibold block">
            {pos?.unit_or_module}: {pos?.unit_name}
          </span>
          <div className="mt-2 text-[11px] text-white/60">
            Completados: <span className="text-emerald-400">{pos?.kcs_completed.length || 0}</span> | 
            En progreso: <span className="text-amber-400">{pos?.kcs_in_progress.length || 0}</span> | 
            Pendientes: <span className="text-white/40">{pos?.kcs_pending.length || 0}</span>
          </div>
        </div>

        <div className="rounded-xl bg-black/30 border border-white/[0.06] p-3">
          <span className="text-white/40 block mb-1">Nodo Pedagógico Seleccionado</span>
          <span className="text-cyan-300 font-semibold block">
            {facts?.selected_kc_display_name || facts?.selected_kc}
          </span>
          <p className="mt-1 text-[11px] text-white/60 font-sans">
            {facts?.selected_kc_rationale}
          </p>
        </div>
      </div>

      {/* Action Prompt */}
      <div className="rounded-xl bg-white/[0.02] border border-white/[0.06] p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <span className="text-xs font-mono text-white/50 block">Propuesta Pedagógica</span>
          <span className="text-sm font-semibold text-white">
            {facts?.proposed_action_rationale || "Iniciar fundamentación conceptual guiada"}
          </span>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {snapshot.available_actions.includes("REVIEW_PREREQUISITE") && (
            <button
              onClick={() => onExecuteAction("REVIEW_PREREQUISITE")}
              disabled={isLoading}
              className="px-3.5 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-white font-mono text-xs flex items-center gap-2 transition disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5 text-amber-400" />
              <span>Repasar Prerequisito</span>
            </button>
          )}

          {snapshot.available_actions.includes("START_EXPLANATION") && (
            <button
              onClick={() => onExecuteAction("START_EXPLANATION")}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-black font-mono font-bold text-xs flex items-center gap-2 shadow-lg shadow-cyan-600/30 transition disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-black" />
              <span>Arrancar Sesión</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
