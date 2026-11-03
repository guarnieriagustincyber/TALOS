import React, { FormEvent, useState } from "react";
import type {
  ExerciseAttemptState,
  ExerciseEvaluationContext,
  ExerciseProposal,
} from "../views/types";

// H2-A (autorización propietaria 2026-10-21): el backend emite
// `academic_admission` en la rama de ejercicios generados de
// /api/chat/evaluate. Se describe localmente sin ampliar el contrato
// compartido; ausencia del campo => comportamiento legado (compatibilidad).
type AttemptResultWithAdmission = NonNullable<ExerciseAttemptState["result"]> & {
  academic_admission?: {
    admissible: boolean;
    reason: string;
  } | null;
};

function isNonAdmissibleAttempt(result: unknown): boolean {
  const admission = (result as AttemptResultWithAdmission | undefined)?.academic_admission;
  return admission?.admissible === false;
}

interface ExerciseProposalCardProps {
  proposal: ExerciseProposal;
  context?: ExerciseEvaluationContext;
  attempt?: ExerciseAttemptState;
  attemptHistory?: ExerciseAttemptState[];
  evaluationError?: string;
  onSubmit?: (answer: string) => void;
  onRetry?: () => void;
  onNewAttempt?: () => void;
}

export const ExerciseProposalCard: React.FC<ExerciseProposalCardProps> = ({
  proposal,
  context,
  attempt,
  attemptHistory = [],
  evaluationError,
  onSubmit,
  onRetry,
  onNewAttempt,
}) => {
  const [answer, setAnswer] = useState("");
  const canEvaluate = Boolean(context?.sessionId && onSubmit);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (answer.trim() && canEvaluate && !attempt) onSubmit?.(answer.trim());
  };

  return (
    <section
      aria-label="Ejercicio propuesto"
      className="mt-4 rounded-xl border border-sky-500/25 bg-sky-950/20 p-4 space-y-3"
    >
      <div className="flex flex-wrap items-center gap-2 font-mono text-[10px] uppercase tracking-wider text-sky-300">
        <span>Ejercicio propuesto</span>
        {proposal.type && <span className="text-white/50">Formato: {proposal.type}</span>}
        {proposal.kc_id && <span className="text-white/50">KC: {proposal.kc_id}</span>}
      </div>
      {proposal.title && proposal.title !== proposal.prompt && (
        <h3 className="text-sm font-semibold text-white">{proposal.title}</h3>
      )}
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-white/85">{proposal.prompt}</p>
      {proposal.options && proposal.options.length > 0 && (
        <ol className="list-inside list-[upper-alpha] space-y-1 pt-1 text-sm text-white/75">
          {proposal.options.map((option, index) => (
            <li key={`${index}-${option}`}>{option}</li>
          ))}
        </ol>
      )}

      {evaluationError && <p role="alert" className="text-xs text-rose-200">{evaluationError}</p>}

      {!attempt && (
        <form onSubmit={submit} className="space-y-2">
          <label className="block text-xs text-white/65" htmlFor={`answer-${proposal.exercise_id}`}>
            Tu respuesta
          </label>
          <textarea
            id={`answer-${proposal.exercise_id}`}
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            maxLength={2000}
            rows={3}
            disabled={!canEvaluate}
            className="w-full rounded-lg border border-white/10 bg-black/30 p-2 text-sm text-white disabled:opacity-50"
          />
          {!canEvaluate && (
            <p role="status" className="text-xs text-amber-300">
              No se puede evaluar: falta una sesión de estudio persistida para esta propuesta.
            </p>
          )}
          <button
            type="submit"
            disabled={!canEvaluate || !answer.trim()}
            className="rounded-lg bg-sky-500/20 px-3 py-2 text-xs font-semibold text-sky-200 disabled:opacity-40"
          >
            Enviar respuesta
          </button>
        </form>
      )}

      {attempt && (
        <div aria-live="polite" className="rounded-lg border border-white/10 bg-black/25 p-3 text-sm text-white/80">
          <p className="text-xs text-white/45">Intento {attempt.attemptId}</p>
          <p className="mt-1 whitespace-pre-wrap">Respuesta: {attempt.answer}</p>
          {attempt.status === "SUBMITTING" && <p role="status" className="mt-2">Evaluando en el servidor…</p>}
          {attempt.status === "UNKNOWN" && (
            <div className="mt-2 space-y-2">
              <p role="alert">No se conoce si el servidor completó el intento. Reintentar conservará la misma identidad y respuesta.</p>
              <button type="button" onClick={onRetry} className="rounded-lg bg-amber-500/15 px-3 py-2 text-xs text-amber-200">Reintentar el mismo intento</button>
            </div>
          )}
          {attempt.status === "INCOMPLETE" && (
            <p role="alert" className="mt-2 text-amber-200">El intento quedó incompleto y el servidor bloqueó su repetición. No se creará otra identidad automáticamente.</p>
          )}
          {attempt.status === "CONFLICT" && (
            <p role="alert" className="mt-2 text-rose-200">Conflicto de identidad: {attempt.message || "el servidor rechazó el intento"}. No se reenvió con otra identidad.</p>
          )}
          {attempt.status === "UNGRADED" && (
            <p role="alert" className="mt-2 text-amber-200">No evaluado: {attempt.result?.detail || "el servidor no pudo verificar el ejercicio"}</p>
          )}
          {attempt.status === "GRADED" && (
            <div className="mt-2 space-y-2">
              {isNonAdmissibleAttempt(attempt.result) ? (
                <p role="status" className="text-white/70">
                  Corrección automática no concluyente: el corrector no puede
                  acreditar la corrección conceptual de esta respuesta, y la
                  observación no modifica tu progreso académico.
                </p>
              ) : (
                <p className={attempt.result?.is_correct ? "text-emerald-300" : "text-amber-200"}>
                  {attempt.result?.is_correct ? "Respuesta correcta." : "Respuesta incorrecta."}
                </p>
              )}
              {attempt.result?.feedback && <p>{attempt.result.feedback}</p>}
              {attempt.result?.remediation && <p>{attempt.result.remediation}</p>}
              {attempt.result?.was_idempotent_replay && <p className="text-xs text-sky-200">Resultado recuperado del mismo intento; no se aplicó una evaluación nueva.</p>}
              <button type="button" onClick={onNewAttempt} className="rounded-lg bg-white/10 px-3 py-2 text-xs text-white">Comenzar un intento nuevo</button>
            </div>
          )}
        </div>
      )}
      {attemptHistory.length > 0 && (
        <details className="rounded-lg border border-white/10 bg-black/20 p-3 text-xs text-white/65">
          <summary className="cursor-pointer">Intentos anteriores ({attemptHistory.length})</summary>
          <ol className="mt-2 list-inside list-decimal space-y-1">
            {attemptHistory.map((previous) => (
              <li key={previous.attemptId}>
                {previous.status === "GRADED"
                  ? (isNonAdmissibleAttempt(previous.result)
                      ? "No concluyente (sin efecto académico)"
                      : previous.result?.is_correct ? "Correcto" : "Incorrecto")
                  : previous.status === "UNGRADED" ? "No evaluado" : "Estado no concluyente"}
                {previous.result?.feedback ? ` — ${previous.result.feedback}` : ""}
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
};
