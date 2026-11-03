/** Derived S4.4 metadata received on this response's SSE, not a report lookup. */
export interface AuditProjection {
  audit_id: string;
  request_id: string;
  notebook_id: string;
  session_id: string;
  scope_type: string;
  scope_id: string;
  phase: string;
  auditor_verdict: string;
  decision: string;
  emission: 'authorized' | 'blocked';
  content_sha256: string;
  content_binding_id: string;
  nli_executed: boolean;
  claims: Array<{ claim_index: number; claim_type: string; cited_tags: string[]; nli_verdict: string }>;
}

export interface MessageAudit {
  projection: AuditProjection;
  message_id: string;
  message_sha256: string;
  stream_completed: true;
}

const auditorVerdicts = new Set([
  'APPROVED', 'FLAGGED_UNASSESSED', 'UNVERIFIED_SOURCE', 'REJECTED_UNSUPPORTED',
  'REJECTED_CONTRADICTION', 'REJECTED_ABSTENTION_VIOLATION', 'REJECTED_INJECTION_DETECTED',
  'REJECTED_POLICY_VIOLATION', 'REJECTED_INPUT_MISMATCH',
]);
const claimVerdicts = new Set(['ENTAILED', 'PARTIALLY_SUPPORTED', 'UNSUPPORTED_GENERALIZATION', 'CONTRADICTED', 'NOT_ENTAILED', 'UNASSESSED']);
const claimTypes = new Set(['FACTUAL', 'PEDAGOGICAL', 'QUESTION', 'CONVERSATIONAL', 'STRUCTURAL', 'UNCLASSIFIED']);
const digest = /^[0-9a-f]{64}$/;

export function isAuditProjection(value: unknown): value is AuditProjection {
  if (!value || typeof value !== 'object') return false;
  const p = value as AuditProjection;
  return ['audit_id', 'request_id', 'notebook_id', 'session_id', 'scope_id', 'phase', 'content_binding_id']
    .every((key) => typeof p[key as keyof AuditProjection] === 'string' && String(p[key as keyof AuditProjection]).trim().length > 0)
    && (p.scope_type === 'notebook' || p.scope_type === 'folder')
    && auditorVerdicts.has(p.auditor_verdict)
    && (auditorVerdicts.has(p.decision) || p.decision === 'DEFERRED_RETRY')
    && (p.decision === p.auditor_verdict || (p.auditor_verdict === 'FLAGGED_UNASSESSED' && p.decision === 'DEFERRED_RETRY'))
    && (p.emission === 'authorized' || p.emission === 'blocked')
    && (p.emission === 'authorized') === (p.decision === 'APPROVED')
    && typeof p.content_sha256 === 'string' && digest.test(p.content_sha256)
    && typeof p.nli_executed === 'boolean' && Array.isArray(p.claims)
    && p.claims.every((c) => c && Number.isInteger(c.claim_index) && c.claim_index >= 0
      && claimTypes.has(c.claim_type) && claimVerdicts.has(c.nli_verdict)
      && Array.isArray(c.cited_tags) && c.cited_tags.every((tag) => typeof tag === 'string' && /^E\d+$/.test(tag)))
    && new Set(p.claims.map((c) => c.claim_index)).size === p.claims.length;
}

export async function textDigest(text: string): Promise<string> {
  const bytes = new TextEncoder().encode(text);
  const hash = await globalThis.crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

export async function bindMessageAudit(projection: AuditProjection, text: string): Promise<MessageAudit> {
  const hash = await textDigest(text);
  if (projection.emission === 'authorized' && hash !== projection.content_sha256) {
    throw new Error('El contenido recibido no coincide con su auditoría.');
  }
  return { projection, message_id: globalThis.crypto.randomUUID(), message_sha256: hash, stream_completed: true };
}

export async function verifyMessageAudit(
  message: { id: string; text: string; audit?: MessageAudit }, sessionId: string, scopeId: string,
): Promise<boolean> {
  const audit = message.audit;
  if (!audit || audit.stream_completed !== true || audit.message_id !== message.id
    || !isAuditProjection(audit.projection) || audit.projection.session_id !== sessionId
    || audit.projection.scope_id !== scopeId) return false;
  const hash = await textDigest(message.text);
  return hash === audit.message_sha256
    && (audit.projection.emission !== 'authorized' || hash === audit.projection.content_sha256);
}
