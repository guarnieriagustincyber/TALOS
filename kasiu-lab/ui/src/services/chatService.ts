import { apiFetch } from '../infrastructure/api/apiClient';
import { Citation, ExerciseProposal } from '../presentation/features/views/types';
import { BackendChatResponse, adaptBackendChatResponse } from '../adapters/chatAdapter';
import { AuditProjection, MessageAudit, isAuditProjection, bindMessageAudit } from './auditProjection';

export class AuditedResponseError extends Error {
  constructor(message: string, readonly audit?: MessageAudit) {
    super(message);
    this.name = 'AuditedResponseError';
  }
}

export class QueryAbortedError extends Error {
  constructor(message = 'Consulta abortada por el usuario') {
    super(message);
    this.name = 'QueryAbortedError';
  }
}

export interface ChatQueryRequest {
  query: string;
  notebook_id?: string;
  scope_id?: string;
  scope_type?: 'folder' | 'notebook';
  requested_scope_id?: string;
  session_id?: string;
  recent_turns?: Array<{ role: 'user' | 'assistant'; content: string }>;
}

export interface ExerciseEvaluationRequest {
  exercise_id: string;
  user_answer: string;
  notebook_id: string;
  session_id: string;
  episode_id?: string;
  attempt_id: string;
}

export interface ExerciseEvaluationResponse {
  status: "GRADED" | "UNGRADED";
  exercise_id: string;
  kc_id?: string | null;
  is_correct: boolean | null;
  p_L?: number | null;
  delta_p_L?: number | null;
  remediation?: string | null;
  detail?: string | null;
  was_idempotent_replay?: boolean;
  // H2-A (autorización propietaria 2026-10-21): estado de admisibilidad de la
  // observación emitido por /api/chat/evaluate en la rama de ejercicios
  // generados. Ausente/undefined => evaluación admisible o payload previo
  // (compatibilidad: no se inventa estado de admisibilidad).
  academic_admission?: {
    admissible: boolean;
    reason: string;
  } | null;
  [key: string]: unknown;
}

export class ExerciseEvaluationError extends Error {
  constructor(
    message: string,
    readonly statusCode: number,
    readonly detail: string,
  ) {
    super(message);
    this.name = "ExerciseEvaluationError";
  }
}

export function createExerciseAttemptId(): string {
  const randomUUID = globalThis.crypto?.randomUUID;
  if (typeof randomUUID !== "function") {
    throw new Error("No se pudo crear una identidad estable para el intento.");
  }
  return randomUUID.call(globalThis.crypto);
}

export interface ChatQueryUiModel {
  audit?: MessageAudit;
  reply_text: string;
  evidences: Citation[];
  facet_coverage?: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'>;
  abstained?: boolean;
  abstention_reason?: string | null;
  clarification_requested?: boolean;
  bkt_context?: SseBktContext;
  exercise_proposal?: ExerciseProposal;
  mermaid_diagram?: string | null;
  processing_ms: number;
}

interface SseCitation {
  id?: string;
  citation_id?: string;
  citationId?: string;
  source_id?: string | null;
  sourceId?: string | null;
  document_id?: string | null;
  documentId?: string | null;
  source_title?: string;
  sourceTitle?: string;
  page?: number;
  page_start?: number | null;
  pageStart?: number | null;
  page_end?: number | null;
  pageEnd?: number | null;
  chunk_text?: string;
  chunkText?: string;
  content?: string;
  chunk_id?: string | null;
  chunkId?: string | null;
  relevance_score?: number;
  relevanceScore?: number;
  doc_hash?: string | null;
  docHash?: string | null;
  authority_weight?: number;
  authorityWeight?: number;
  namespace?: string;
  author?: string;
  section?: string;
  epistemic_role?: string;
  epistemicRole?: string;
}

interface SseBktContext {
  kc_id?: string | null;
  context_mode?: string;
  p_L?: number;
  unmet_prerequisites?: string[];
  fallback?: boolean;
}

function normalizeBktContext(context?: SseBktContext | null): SseBktContext | undefined {
  if (!context) return undefined;
  return {
    kc_id: context.kc_id ?? null,
    context_mode: context.context_mode,
    p_L: typeof context.p_L === 'number' ? context.p_L : undefined,
    unmet_prerequisites: Array.isArray(context.unmet_prerequisites)
      ? context.unmet_prerequisites.filter((item): item is string => typeof item === 'string')
      : undefined,
    fallback: typeof context.fallback === 'boolean' ? context.fallback : undefined,
  };
}

interface SseEventPayload {
  token?: string;
  citations?: SseCitation[];
  facet_coverage?: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'>;
  abstained?: boolean;
  abstention_reason?: string | null;
  bkt_context?: SseBktContext;
  decision?: { message?: string };
  message?: string;
  detail?: string;
  error?: string;
  valid_citations?: string[];
  invalid_citations?: string[];
  citation_count?: number;
  stripped_from_stream?: string[];
  [key: string]: unknown;
}

const SSE_EVENT_TYPES = [
  'phase_start',
  'phase_token',
  'progress',
  'guard_blocked',
  'truncated',
  'audit_verdict',
  'evidence_manifest',
  'phase_complete',
  'abstention',
  'clarification',
  'error',
  'citation_audit',
  'exercise_proposal',
  'stream_aborted',
] as const;

type SseEventType = typeof SSE_EVENT_TYPES[number];

// Operational verdicts are not academic abstentions.  They are surfaced as
// technical errors so the student is not told that evidence is missing when the
// provider (or the auditor) simply failed.
const TECHNICAL_ABSTENTION_CODES = new Set([
  'DEFERRED_RETRY',
  'REJECTED_AUDIT_ERROR',
  'AUDITOR_UNAVAILABLE',
  'AUDIT_RESULT_MISSING',
  'REJECTED_INPUT_MISMATCH',
]);

interface SseEvent {
  event_type: SseEventType;
  payload?: SseEventPayload;
}

function isSseEventType(value: string): value is SseEventType {
  return SSE_EVENT_TYPES.some((eventType) => eventType === value);
}

function isExerciseProposal(payload: SseEventPayload | undefined): payload is SseEventPayload & ExerciseProposal {
  return Boolean(
    payload &&
    typeof payload.exercise_id === 'string' &&
    typeof payload.prompt === 'string' &&
    (payload.kc_id === undefined || payload.kc_id === null || typeof payload.kc_id === 'string') &&
    (payload.title === undefined || typeof payload.title === 'string') &&
    (payload.type === undefined || payload.type === null || typeof payload.type === 'string') &&
    (payload.options === undefined ||
      payload.options === null ||
      (Array.isArray(payload.options) && payload.options.every((option) => typeof option === 'string')))
  );
}

class SseResponseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SseResponseError';
  }
}

function parseSseEvent(raw: string): SseEvent {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    throw new SseResponseError('La respuesta SSE contiene un payload de datos inválido.');
  }

  if (typeof parsed !== 'object' || parsed === null || !('event_type' in parsed)) {
    throw new SseResponseError('La respuesta SSE contiene un evento con formato inválido.');
  }
  const candidate = parsed as { event_type?: unknown; payload?: unknown };
  if (typeof candidate.event_type !== 'string') {
    throw new SseResponseError('La respuesta SSE contiene un evento con formato inválido.');
  }
  if (!isSseEventType(candidate.event_type)) {
    throw new SseResponseError('La respuesta SSE contiene un tipo de evento no reconocido.');
  }
  if (
    candidate.payload !== undefined &&
    (typeof candidate.payload !== 'object' || candidate.payload === null || Array.isArray(candidate.payload))
  ) {
    throw new SseResponseError('La respuesta SSE contiene un evento con formato inválido.');
  }

  const payload = candidate.payload;
  return {
    event_type: candidate.event_type,
    payload: payload as SseEventPayload | undefined,
  };
}

export const chatService = {
  async evaluateExercise(req: ExerciseEvaluationRequest): Promise<ExerciseEvaluationResponse> {
    const response = await fetch('/api/chat/evaluate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    const payload = await response.json().catch(() => ({})) as Record<string, unknown>;
    if (!response.ok) {
      const detail = typeof payload.detail === 'string'
        ? payload.detail
        : `La evaluación no pudo completarse (HTTP ${response.status}).`;
      throw new ExerciseEvaluationError(detail, response.status, detail);
    }
    if (
      payload.status !== 'GRADED' && payload.status !== 'UNGRADED' ||
      payload.exercise_id !== req.exercise_id ||
      (payload.status === 'GRADED' && typeof payload.is_correct !== 'boolean')
    ) {
      throw new Error('La respuesta de evaluación no coincide con el ejercicio solicitado.');
    }
    return payload as unknown as ExerciseEvaluationResponse;
  },

  async sendQuery(
    req: ChatQueryRequest,
    onProgress?: (streamedText: string) => void,
    externalSignal?: AbortSignal,
    onActivity?: (activity: { stage?: string; message?: string; elapsedMs?: number }) => void
  ): Promise<ChatQueryUiModel> {
    const t0 = performance.now();

    const isFolder = req.scope_type === 'folder' ||
      req.notebook_id === 'root_global' ||
      req.scope_id === 'root_global' ||
      req.notebook_id === 'folder_root' ||
      req.scope_id === 'folder_root';

    const normalizedScopeId = (req.scope_id === 'root_global' || req.notebook_id === 'root_global')
      ? 'folder_root'
      : (req.scope_id || req.notebook_id || 'default_nb');

    const payload = {
      query: req.query,
      prompt: req.query,
      notebook_id: normalizedScopeId,
      scope_id: normalizedScopeId,
      scope_type: isFolder ? 'folder' : (req.scope_type || 'notebook'),
      requested_scope_id: req.requested_scope_id || null,
      session_id: req.session_id || null,
      recent_turns: req.recent_turns || null,
    };

    // A legitimate request is never abandoned merely because the auditor is
    // still working.  The timeout is inactivity-based: any SSE byte (including
    // progress/heartbeat events) resets it.  A generous absolute cap prevents
    // an indefinitely open connection.
    const INACTIVITY_TIMEOUT_MS = 45000;
    const ABSOLUTE_TIMEOUT_MS = 180000;

    const controller = new AbortController();
    let abortCause: 'explicit' | 'timeout' | 'idle_timeout' | null = null;
    let requestSettled = false;
    let inactivityId: ReturnType<typeof setTimeout> | undefined;
    let absoluteId: ReturnType<typeof setTimeout> | undefined;
    const clearRequestTimers = () => {
      if (inactivityId !== undefined) clearTimeout(inactivityId);
      if (absoluteId !== undefined) clearTimeout(absoluteId);
      inactivityId = undefined;
      absoluteId = undefined;
    };
    const cleanupRequest = () => {
      requestSettled = true;
      clearRequestTimers();
      externalSignal?.removeEventListener('abort', abortFromUser);
    };
    const toRequestError = (error: unknown): unknown => {
      if (abortCause === 'explicit') {
        return new QueryAbortedError('Consulta abortada por el usuario');
      }
      if (abortCause === 'idle_timeout') {
        return new Error('Tiempo de espera agotado (45s sin actividad). El servidor TALOS no respondió.');
      }
      if (abortCause === 'timeout') {
        return new Error('Tiempo de espera agotado (180s). El servidor TALOS no completó la respuesta.');
      }
      if (
        typeof error === 'object' &&
        error !== null &&
        'name' in error &&
        error.name === 'AbortError'
      ) {
        return new Error(error instanceof Error ? error.message : 'La conexión con TALOS se interrumpió.');
      }
      return error;
    };
    const armInactivityTimeout = () => {
      if (requestSettled) return;
      if (inactivityId !== undefined) clearTimeout(inactivityId);
      inactivityId = setTimeout(() => {
        if (requestSettled || abortCause === 'explicit') return;
        abortCause = 'idle_timeout';
        controller.abort();
      }, INACTIVITY_TIMEOUT_MS);
    };
    const abortFromUser = () => {
      if (requestSettled) return;
      abortCause = 'explicit';
      clearRequestTimers();
      controller.abort();
    };
    armInactivityTimeout();
    absoluteId = setTimeout(() => {
      if (requestSettled || abortCause === 'explicit') return;
      abortCause = 'timeout';
      controller.abort();
    }, ABSOLUTE_TIMEOUT_MS);

    // Si hay señal externa, enlazarla para disparar abort en el controller interno
    if (externalSignal) {
      if (externalSignal.aborted) {
        cleanupRequest();
        throw new QueryAbortedError();
      }
      externalSignal.addEventListener('abort', abortFromUser, { once: true });
    }

    let response: Response;
    try {
      response = await fetch('/api/chat/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });
      if (abortCause) throw toRequestError(new Error());
    } catch (err: any) {
      cleanupRequest();
      throw toRequestError(err);
    }

    if (!response.ok) {
      cleanupRequest();
      let errorText: string;
      try {
        errorText = await response.text();
      } catch (error) {
        throw toRequestError(error);
      }
      throw new Error(`[API ERROR ${response.status}] ${errorText}`);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('text/event-stream')) {
      let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;
      try {
        reader = response.body?.getReader();
      } catch (error) {
        cleanupRequest();
        throw toRequestError(error);
      }
      const decoder = new TextDecoder();
      let fullText = '';
      let done = false;
      let buffer = '';
      let phaseCompleted = false;
      let terminalOutcome: 'abstention' | 'clarification' | null = null;

      let capturedCitations: Citation[] = [];
      let capturedFacetCoverage: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'> = {};
      let capturedAbstained: boolean = false;
      let capturedAbstentionReason: string | null = null;
      let capturedClarificationRequested = false;
      let capturedBktContext: SseBktContext | undefined;
      let capturedExerciseProposal: ExerciseProposal | undefined;
      let capturedAudit: AuditProjection | undefined;
      let technicalReason: string | undefined;

      try {
        while (!done && reader) {
          try {
            const { value, done: streamDone } = await reader.read();
            if (abortCause) throw toRequestError(new Error());
            done = streamDone;
            if (value) {
              buffer += decoder.decode(value, { stream: true });
              // Any received bytes -- including progress heartbeats emitted
              // while S4.4 is still auditing -- prove the server is alive.
              armInactivityTimeout();
            }
            if (streamDone) {
              buffer += decoder.decode();
            }
            if (value) {
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';
              for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('data:')) {
                  const eventData = parseSseEvent(trimmed.slice(5).replace(/^ /, ''));
                  const eventPayload = eventData.payload;

                  if (terminalOutcome) {
                    throw new SseResponseError(
                      'La respuesta SSE incluyó eventos después de su resultado terminal.'
                    );
                  }
                  if (phaseCompleted && eventData.event_type === 'phase_complete') {
                    throw new SseResponseError(
                      'La respuesta SSE incluyó más de un cierre de fase.'
                    );
                  }
                  if (phaseCompleted) {
                    throw new SseResponseError(
                      'La respuesta SSE incluyó un evento no permitido después del cierre de fase.'
                    );
                  }

                  if (eventData.event_type === 'phase_start') {
                    phaseCompleted = false;
                  } else if (eventData.event_type === 'phase_token') {
                    fullText += eventPayload?.token || '';
                    onProgress?.(fullText);
                  } else if (eventData.event_type === 'evidence_manifest') {
                    if (Array.isArray(eventPayload?.citations)) {
                      capturedCitations = eventPayload.citations.map((citation) => {
                        const sourceId = citation.source_id || citation.sourceId || null;
                        const citationId = citation.citation_id || citation.id || citation.citationId || '';
                        const namespace = citation.namespace === 'TF' || citation.namespace === 'LAB'
                          ? citation.namespace
                          : 'E';
                        return {
                          id: citation.id || citation.citation_id || citation.citationId,
                          citationId,
                          sourceId,
                          source_id: sourceId,
                          documentId: citation.document_id || citation.documentId || null,
                          document_id: citation.document_id || citation.documentId || null,
                          sourceTitle: citation.source_title || citation.sourceTitle || undefined,
                          source_title: citation.source_title || citation.sourceTitle || undefined,
                          page: citation.page ?? citation.page_start ?? citation.pageStart ?? undefined,
                          pageStart: citation.page ?? citation.page_start ?? citation.pageStart ?? undefined,
                          pageEnd: citation.page_end ?? citation.pageEnd ?? null,
                          chunkText: citation.chunk_text || citation.chunkText || citation.content || '',
                          chunk_text: citation.chunk_text || citation.chunkText || citation.content || '',
                          chunkId: citation.chunk_id || citation.chunkId || null,
                          relevanceScore: citation.relevance_score ?? citation.relevanceScore ?? undefined,
                          relevance_score: citation.relevance_score ?? citation.relevanceScore ?? undefined,
                          docHash: citation.doc_hash || citation.docHash || null,
                          authorityWeight: citation.authority_weight ?? citation.authorityWeight ?? 1.0,
                          namespace,
                          author: citation.author,
                          section: citation.section,
                          epistemicRole: citation.epistemic_role || citation.epistemicRole,
                          epistemic_role: citation.epistemic_role || citation.epistemicRole,
                        };
                      });
                    }
                    if (eventPayload?.facet_coverage) {
                      capturedFacetCoverage = eventPayload.facet_coverage;
                    }
                    if (typeof eventPayload?.abstained === 'boolean') {
                      capturedAbstained = eventPayload.abstained;
                    }
                    if (eventPayload?.abstention_reason) {
                      capturedAbstentionReason = eventPayload.abstention_reason;
                    }
                  } else if (eventData.event_type === 'phase_complete') {
                    phaseCompleted = true;
                    if (eventPayload?.decision?.message && !fullText) {
                      fullText = eventPayload.decision.message;
                    }
                    if (eventPayload?.bkt_context) {
                      capturedBktContext = normalizeBktContext(eventPayload.bkt_context);
                    }
                  } else if (
                    eventData.event_type === 'abstention' ||
                    eventData.event_type === 'clarification'
                  ) {
                    const outcomePayload = eventPayload || {};
                    const reason = outcomePayload.reason;
                    if (typeof reason !== 'string' || !reason.trim()) {
                      throw new SseResponseError(
                        eventData.event_type === 'clarification'
                          ? 'TALOS solicitó una aclaración, pero no proporcionó el mensaje necesario.'
                          : 'TALOS se abstuvo de responder, pero no proporcionó el motivo.'
                      );
                    }
                    const abstentionCode = typeof outcomePayload.abstention_code === 'string'
                      ? outcomePayload.abstention_code
                      : '';
                    if (
                      eventData.event_type === 'abstention' &&
                      (outcomePayload.failure_class === 'TECHNICAL' ||
                        TECHNICAL_ABSTENTION_CODES.has(abstentionCode))
                    ) {
                      // Preserve the failure, but confirm clean terminal framing before attaching audit metadata.
                      technicalReason = reason;
                    }
                    fullText = reason;
                    capturedAbstained = typeof outcomePayload.abstained === 'boolean'
                      ? outcomePayload.abstained
                      : eventData.event_type === 'abstention';
                    capturedClarificationRequested = eventData.event_type === 'clarification';
                    if (
                      !capturedAbstentionReason &&
                      typeof outcomePayload.abstention_code === 'string'
                    ) {
                      capturedAbstentionReason = outcomePayload.abstention_code;
                    }
                    terminalOutcome = eventData.event_type;
                  } else if (eventData.event_type === 'truncated') {
                    const message = eventPayload?.message;
                    throw new SseResponseError(
                      typeof message === 'string' && message.trim()
                        ? message
                        : 'La respuesta quedó truncada antes de completarse.'
                    );
                  } else if (eventData.event_type === 'error') {
                    const errorMessage = eventPayload?.message ||
                      eventPayload?.detail ||
                      eventPayload?.reason ||
                      eventPayload?.error;
                    throw new SseResponseError(typeof errorMessage === 'string' && errorMessage.trim()
                      ? errorMessage
                      : 'Ocurrió un error en el servidor.');
                  } else if (eventData.event_type === 'exercise_proposal') {
                    if (!isExerciseProposal(eventPayload)) {
                      throw new SseResponseError('La propuesta de ejercicio SSE tiene un formato inválido.');
                    }
                    capturedExerciseProposal = eventPayload;
                  } else if (eventData.event_type === 'progress') {
                    const stage = typeof eventPayload?.stage === 'string'
                      ? eventPayload.stage
                      : undefined;
                    const message = typeof eventPayload?.message === 'string'
                      ? eventPayload.message
                      : undefined;
                    const elapsedMs = typeof eventPayload?.elapsed_ms === 'number'
                      ? eventPayload.elapsed_ms
                      : undefined;
                    onActivity?.({ stage, message, elapsedMs });
                    console.debug('Evento SSE progress:', eventPayload);
                  } else if (eventData.event_type === 'audit_verdict' && eventPayload?.audit_projection !== undefined) {
                    const projection = eventPayload.audit_projection;
                    if (capturedAudit || fullText || !isAuditProjection(projection)
                      || projection.session_id !== req.session_id
                      || projection.scope_id !== normalizedScopeId || projection.scope_type !== payload.scope_type
                      || (projection.scope_type === 'notebook' && projection.notebook_id !== normalizedScopeId)
                      || projection.phase !== eventPayload.phase
                      || projection.content_binding_id !== eventPayload.content_binding_id
                      || projection.content_sha256 !== eventPayload.content_sha256
                      || projection.decision !== eventPayload.verdict) {
                      throw new SseResponseError('La proyección de auditoría no corresponde a esta invocación.');
                    }
                    capturedAudit = projection;
                  } else if (
                    eventData.event_type === 'citation_audit' ||
                    eventData.event_type === 'guard_blocked' ||
                    eventData.event_type === 'audit_verdict'
                  ) {
                    if (eventData.event_type === 'audit_verdict' && capturedAudit) {
                      throw new SseResponseError('La respuesta contiene decisiones de auditoría incompatibles.');
                    }
                    console.debug(`Evento SSE ${eventData.event_type}:`, eventPayload);
                  } else if (eventData.event_type === 'stream_aborted') {
                    const message = eventPayload?.message;
                    throw new SseResponseError(
                      typeof message === 'string' && message.trim()
                        ? message
                        : 'La generación se interrumpió antes de completarse.'
                    );
                  }
                }
              }
            }
          } catch (readErr: any) {
            if (readErr instanceof SseResponseError) throw readErr;
            throw toRequestError(readErr);
          }
        }
      } finally {
        cleanupRequest();
      }

      if (buffer.trimStart().startsWith('data:')) {
        throw new SseResponseError(
          'El stream SSE terminó con un evento de datos incompleto.'
        );
      }

      if (!terminalOutcome && !phaseCompleted) {
        throw new SseResponseError(
          'La respuesta SSE terminó sin un resultado terminal válido.'
        );
      }

      if (capturedAudit && ((capturedAudit.emission === 'authorized' && (!phaseCompleted || capturedAbstained))
        || (capturedAudit.emission === 'blocked' && (!terminalOutcome || phaseCompleted)))) {
        throw new SseResponseError('La auditoría no corresponde al resultado terminal.');
      }
      const replyText = fullText || (capturedExerciseProposal ? '' : 'Respuesta generada por TALOS.');
      const audit = capturedAudit ? await bindMessageAudit(capturedAudit, replyText) : undefined;
      if (technicalReason) {
        if (audit) throw new AuditedResponseError(technicalReason, audit);
        throw new SseResponseError(technicalReason);
      }

      const t1 = performance.now();
      return {
        reply_text: replyText,
        audit,
        evidences: capturedCitations,
        facet_coverage: capturedFacetCoverage,
        abstained: capturedAbstained,
        abstention_reason: capturedAbstentionReason,
        clarification_requested: capturedClarificationRequested,
        bkt_context: capturedBktContext,
        exercise_proposal: capturedExerciseProposal,
        mermaid_diagram: null,
        processing_ms: Math.round(t1 - t0),
      };
    }

    let raw: BackendChatResponse & { bkt_context?: SseBktContext | null };
    try {
      raw = (await response.json()) as BackendChatResponse & {
        bkt_context?: SseBktContext | null;
      };
      if (abortCause) throw toRequestError(new Error());
    } catch (error) {
      throw toRequestError(error);
    } finally {
      cleanupRequest();
    }
    const t1 = performance.now();
    const adapted = adaptBackendChatResponse(raw);

    const convertedCitations: Citation[] = adapted.evidences.map((e) => ({
      citationId: e.evidence_id,
      sourceId: e.citations[0]?.source_title || null,
      docHash: e.citations[0]?.source_hash?.includes(':')
        ? e.citations[0]?.source_hash.split(':')[1]
        : e.citations[0]?.source_hash || null,
      pageStart: e.citations[0]?.location?.page_number ?? null,
      pageEnd: e.citations[0]?.location?.page_number ?? null,
      chunkId: e.evidence_id,
      authorityWeight: e.verification_score ?? 1.0,
      namespace: 'E',
      sourceTitle: e.citations[0]?.source_title,
      source_title: e.citations[0]?.source_title,
    }));

    return {
      reply_text: adapted.reply_text,
      evidences: convertedCitations,
      abstained: adapted.abstained,
      abstention_reason: adapted.abstention_reason,
      bkt_context: normalizeBktContext(raw.bkt_context),
      mermaid_diagram: adapted.mermaid_diagram,
      processing_ms: Math.round(t1 - t0),
    };
  },

  async openLocalSource(sourceHash: string): Promise<{ status: string; message: string }> {
    // Si viene en formato algorithm:digest, extraer digest
    const doc_hash = sourceHash.includes(':') ? sourceHash.split(':')[1] : sourceHash;
    return apiFetch<{ status: string; message: string }>('/api/sources/open-local', {
      method: 'POST',
      body: JSON.stringify({ doc_hash }),
    });
  },

  getPageRenderUrl(
    sourceHash: string,
    pageNumber: number = 1,
    options?: { highlight?: string; bbox?: string; dpi?: number }
  ): string {
    const doc_hash = sourceHash.includes(':') ? sourceHash.split(':')[1] : sourceHash;
    const params = new URLSearchParams({ page: String(pageNumber) });
    if (options?.highlight) {
      params.append('highlight', options.highlight);
    }
    if (options?.bbox) {
      params.append('bbox', options.bbox);
    }
    if (options?.dpi) {
      params.append('dpi', String(options.dpi));
    }
    return `/api/sources/${doc_hash}/page-render?${params.toString()}`;
  },
};
