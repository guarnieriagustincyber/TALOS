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
}

export interface ChatQueryUiModel {
  reply_text: string;
  evidences: Citation[];
  facet_coverage?: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'>;
  abstained?: boolean;
  abstention_reason?: string | null;
  mermaid_diagram?: string | null;
  processing_ms: number;
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

      let capturedCitations: Citation[] = [];
      let capturedFacetCoverage: Record<string, 'SUFFICIENT' | 'PARTIAL' | 'MISSING'> = {};
      let capturedAbstained: boolean = false;
      let capturedAbstentionReason: string | null = null;

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
                  try {
                    const eventData = JSON.parse(trimmed.slice(6));
                    if (eventData.event_type === 'phase_token') {
                      fullText += eventData.payload?.token || '';
                      if (onProgress) {
                        onProgress(fullText);
                      }
                    } else if (eventData.event_type === 'evidence_manifest') {
                      if (Array.isArray(eventData.payload?.citations)) {
                        capturedCitations = eventData.payload.citations.map((c: any) => ({
                          id: c.id || c.citation_id || c.citationId,
                          citationId: c.citation_id || c.id || c.citationId,
                          sourceId: c.source_id || c.sourceId || null,
                          source_id: c.source_id || c.sourceId || null,
                          sourceTitle: c.source_title || c.sourceTitle || c.source_id || "Documento Canónico",
                          source_title: c.source_title || c.sourceTitle || c.source_id || "Documento Canónico",
                          page: c.page ?? c.page_start ?? c.pageStart ?? 1,
                          pageStart: c.page ?? c.page_start ?? c.pageStart ?? 1,
                          pageEnd: c.page_end ?? c.pageEnd ?? null,
                          chunkText: c.chunk_text || c.chunkText || c.content || "",
                          chunk_text: c.chunk_text || c.chunkText || c.content || "",
                          chunkId: c.chunk_id || c.chunkId || null,
                          relevanceScore: c.relevance_score ?? c.relevanceScore ?? 0.85,
                          relevance_score: c.relevance_score ?? c.relevanceScore ?? 0.85,
                          docHash: c.doc_hash || c.docHash || null,
                          authorityWeight: c.authority_weight ?? c.authorityWeight ?? 1.0,
                          namespace: c.namespace || 'E',
                        }));
                      }
                      if (eventData.payload?.facet_coverage) {
                        capturedFacetCoverage = eventData.payload.facet_coverage;
                      }
                      if (typeof eventData.payload?.abstained === 'boolean') {
                        capturedAbstained = eventData.payload.abstained;
                      }
                      if (eventData.payload?.abstention_reason) {
                        capturedAbstentionReason = eventData.payload.abstention_reason;
                      }
                    } else if (eventData.event_type === 'phase_complete') {
                      if (eventData.payload?.decision?.message && !fullText) {
                        fullText = eventData.payload.decision.message;
                      }
                    } else if (eventData.event_type === 'error') {
                      if (!fullText) {
                        fullText = `⚠️ Error en respuesta: ${eventData.payload?.error || 'Ocurrió un error en el servidor.'}`;
                      }
                    }
                  } catch {
                    // Ignore partial JSON parse errors
                  }
                }
              }
            }
          } catch (readErr: any) {
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

      const t1 = performance.now();
      return {
        reply_text: fullText || 'Respuesta generada por TALOS.',
        evidences: capturedCitations,
        facet_coverage: capturedFacetCoverage,
        abstained: capturedAbstained,
        abstention_reason: capturedAbstentionReason,
        mermaid_diagram: null,
        processing_ms: Math.round(t1 - t0),
      };
    }

    const raw = (await response.json()) as BackendChatResponse;
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
    }));

    return {
      reply_text: adapted.reply_text,
      evidences: convertedCitations,
      abstained: adapted.abstained,
      abstention_reason: adapted.abstention_reason,
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
