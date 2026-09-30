import { apiFetch } from '../infrastructure/api/apiClient';
import { Citation } from '../presentation/features/views/types';
import { BackendChatResponse, adaptBackendChatResponse } from '../adapters/chatAdapter';

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

export interface ChatQueryUiModel {
  reply_text: string;
  evidences: Citation[];
  facet_coverage?: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'>;
  abstained?: boolean;
  abstention_reason?: string | null;
  bkt_context?: SseBktContext;
  mermaid_diagram?: string | null;
  processing_ms: number;
}

interface SseCitation {
  id?: string;
  citation_id?: string;
  citationId?: string;
  source_id?: string | null;
  sourceId?: string | null;
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
  'evidence_manifest',
  'phase_complete',
  'truncated',
  'error',
  'citation_audit',
  'exercise_proposal',
  'stream_aborted',
] as const;

type SseEventType = typeof SSE_EVENT_TYPES[number];

interface SseEvent {
  event_type: SseEventType;
  payload?: SseEventPayload;
}

function isSseEventType(value: string): value is SseEventType {
  return SSE_EVENT_TYPES.some((eventType) => eventType === value);
}

class SseResponseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SseResponseError';
  }
}

function parseSseEvent(raw: string): SseEvent | null {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return null;
  }

  if (typeof parsed !== 'object' || parsed === null || !('event_type' in parsed)) return null;
  const candidate = parsed as { event_type?: unknown; payload?: unknown };
  if (typeof candidate.event_type !== 'string' || !isSseEventType(candidate.event_type)) {
    return null;
  }

  const payload = candidate.payload;
  return {
    event_type: candidate.event_type,
    payload: typeof payload === 'object' && payload !== null
      ? payload as SseEventPayload
      : undefined,
  };
}

export const chatService = {
  async sendQuery(
    req: ChatQueryRequest,
    onProgress?: (streamedText: string) => void,
    externalSignal?: AbortSignal
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

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 45000);

    // Si hay señal externa, enlazarla para disparar abort en el controller interno
    if (externalSignal) {
      if (externalSignal.aborted) {
        clearTimeout(timeoutId);
        throw new QueryAbortedError();
      }
      externalSignal.addEventListener('abort', () => controller.abort(), { once: true });
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
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (externalSignal?.aborted || (err.name === 'AbortError' && externalSignal)) {
        throw new QueryAbortedError('Consulta abortada por el usuario');
      }
      if (err.name === 'AbortError') {
        throw new Error("Tiempo de espera agotado (45s). El servidor TALOS no respondió.");
      }
      throw err;
    }

    if (!response.ok) {
      clearTimeout(timeoutId);
      const errorText = await response.text();
      throw new Error(`[API ERROR ${response.status}] ${errorText}`);
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('text/event-stream')) {
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullText = '';
      let done = false;
      let buffer = '';
      let lastPhaseCompleted = false;

      let capturedCitations: Citation[] = [];
      let capturedFacetCoverage: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'> = {};
      let capturedAbstained: boolean = false;
      let capturedAbstentionReason: string | null = null;
      let capturedBktContext: SseBktContext | undefined;

      try {
        while (!done && reader) {
          try {
            const { value, done: streamDone } = await reader.read();
            done = streamDone;
            if (value) {
              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split('\n');
              buffer = lines.pop() || '';
              for (const line of lines) {
                const trimmed = line.trim();
                if (trimmed.startsWith('data: ')) {
                  const eventData = parseSseEvent(trimmed.slice(6));
                  if (!eventData) continue;
                  const eventPayload = eventData.payload;

                  if (eventData.event_type === 'phase_start') {
                    lastPhaseCompleted = false;
                  } else if (eventData.event_type === 'phase_token') {
                    lastPhaseCompleted = false;
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
                    lastPhaseCompleted = true;
                    if (eventPayload?.decision?.message && !fullText) {
                      fullText = eventPayload.decision.message;
                    }
                    if (eventPayload?.bkt_context) {
                      capturedBktContext = normalizeBktContext(eventPayload.bkt_context);
                    }
                  } else if (eventData.event_type === 'truncated') {
                    const message = eventPayload?.message;
                    throw new SseResponseError(
                      typeof message === 'string' && message.trim()
                        ? message
                        : 'La respuesta quedó truncada antes de completarse.'
                    );
                  } else if (eventData.event_type === 'error') {
                    const errorMessage = eventPayload?.message || eventPayload?.detail || eventPayload?.error;
                    throw new SseResponseError(typeof errorMessage === 'string' && errorMessage.trim()
                      ? errorMessage
                      : 'Ocurrió un error en el servidor.');
                  } else if (
                    eventData.event_type === 'citation_audit' ||
                    eventData.event_type === 'exercise_proposal'
                  ) {
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
            // Si la señal externa fue disparada, propagar QueryAbortedError
            if (externalSignal?.aborted) {
              throw new QueryAbortedError('Consulta abortada por el usuario');
            }
            // If the stream was interrupted (e.g. abort, client disconnect, connection close)
            // but we already captured text, exit the loop cleanly rather than failing the message
            if (readErr?.name === 'AbortError' || String(readErr?.message).includes('aborted')) {
              break;
            }
            if (fullText.trim()) {
              break;
            }
            throw readErr;
          }
        }
      } finally {
        clearTimeout(timeoutId);
      }

      if (!lastPhaseCompleted) {
        throw new SseResponseError(
          'La respuesta SSE terminó antes de completarse.'
        );
      }

      const t1 = performance.now();
      return {
        reply_text: fullText || 'Respuesta generada por TALOS.',
        evidences: capturedCitations,
        facet_coverage: capturedFacetCoverage,
        abstained: capturedAbstained,
        abstention_reason: capturedAbstentionReason,
        bkt_context: capturedBktContext,
        mermaid_diagram: null,
        processing_ms: Math.round(t1 - t0),
      };
    }

    const raw = (await response.json()) as BackendChatResponse & {
      bkt_context?: SseBktContext | null;
    };
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
