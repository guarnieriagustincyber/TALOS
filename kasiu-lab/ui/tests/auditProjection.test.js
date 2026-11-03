import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import ts from 'typescript';

function compile(file, require = () => { throw new Error('Unexpected runtime dependency'); }) {
  const module = { exports: {} };
  new Function('require', 'module', 'exports', ts.transpileModule(readFileSync(new URL(file, import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText)(require, module, module.exports);
  return module.exports;
}
const helper = compile('../src/services/auditProjection.ts');
const { chatService, AuditedResponseError } = compile('../src/services/chatService.ts', (id) => {
  if (id === './auditProjection') return helper;
  if (id === '../infrastructure/api/apiClient') return { apiFetch: async () => ({}) };
  if (id === '../adapters/chatAdapter') return { adaptBackendChatResponse: (value) => value };
  throw new Error(id);
});
const text = 'Texto académico sintético. [E1]';
const sha = (value) => createHash('sha256').update(value).digest('hex');
const req = { query: 'synthetic', session_id: 'session-A', scope_id: 'nb-A', scope_type: 'notebook' };
function projection(overrides = {}) {
  return { audit_id: 'audit-A', request_id: 'req-A', session_id: 'session-A', scope_id: 'nb-A', scope_type: 'notebook',
    notebook_id: 'nb-A', phase: 'conceptual', auditor_verdict: 'APPROVED', decision: 'APPROVED', emission: 'authorized',
    content_sha256: sha(text), content_binding_id: 'binding-A', nli_executed: false, claims: [], ...overrides };
}
function events(p = projection(), body = text) {
  return [
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    { event_type: 'audit_verdict', payload: { phase: p.phase, verdict: p.decision, content_sha256: p.content_sha256, content_binding_id: p.content_binding_id, audit_projection: p } },
    ...(p.emission === 'authorized' ? [
      { event_type: 'phase_token', payload: { token: body } }, { event_type: 'phase_complete', payload: {} },
    ] : [{ event_type: 'abstention', payload: { reason: 'Mensaje de abstención sintético.', abstained: true, abstention_code: p.decision } }]),
  ];
}
function wire(items) { return items.map((event) => `data: ${JSON.stringify(event)}\n\n`).join(''); }
function transport(items) { return new Response(wire(items), { headers: { 'content-type': 'text/event-stream' } }); }
async function withEvents(items, run) {
  const previous = globalThis.fetch;
  globalThis.fetch = async () => transport(items);
  try { return await run(); } finally { globalThis.fetch = previous; }
}

test('approved SSE is bound to exact text, message, session, scope and original report', async () => {
  const result = await withEvents(events(), () => chatService.sendQuery(req));
  assert.equal(result.reply_text, text);
  assert.equal(result.audit.projection.request_id, 'req-A');
  assert.equal(result.audit.message_sha256, sha(text));
  const message = { id: result.audit.message_id, text, audit: result.audit };
  assert.equal(await helper.verifyMessageAudit(message, 'session-A', 'nb-A'), true);
  assert.equal(await helper.verifyMessageAudit({ ...message, text: text + ' changed' }, 'session-A', 'nb-A'), false);
  assert.equal(await helper.verifyMessageAudit({ ...message, id: 'another-message' }, 'session-A', 'nb-A'), false);
  assert.equal(await helper.verifyMessageAudit(message, 'session-B', 'nb-A'), false);
  assert.equal(await helper.verifyMessageAudit(message, 'session-A', 'nb-B'), false);
});

test('rejection is attached to the refusal message, not represented as auditing that refusal', async () => {
  const p = projection({ auditor_verdict: 'REJECTED_UNSUPPORTED', decision: 'REJECTED_UNSUPPORTED', emission: 'blocked' });
  const result = await withEvents(events(p), () => chatService.sendQuery(req));
  assert.equal(result.audit.projection.auditor_verdict, 'REJECTED_UNSUPPORTED');
  assert.equal(result.abstained, true);
  assert.notEqual(result.audit.message_sha256, p.content_sha256);
});

test('operational decision preserves original FLAGGED_UNASSESSED after clean terminal framing', async () => {
  const p = projection({ auditor_verdict: 'FLAGGED_UNASSESSED', decision: 'DEFERRED_RETRY', emission: 'blocked' });
  await withEvents(events(p), async () => {
    await assert.rejects(chatService.sendQuery(req), (error) => {
      assert.ok(error instanceof AuditedResponseError);
      assert.equal(error.audit.projection.auditor_verdict, 'FLAGGED_UNASSESSED');
      assert.equal(error.audit.projection.decision, 'DEFERRED_RETRY');
      assert.equal(error.audit.message_sha256, sha(error.message));
      return true;
    });
  });
});

for (const [field, value] of [['session_id', 'session-B'], ['scope_id', 'nb-B'], ['notebook_id', 'nb-B'], ['decision', 'REJECTED_UNSUPPORTED'], ['content_sha256', 'invalid'], ['claims', [{}]]]) {
  test(`incompatible projection ${field} fails closed`, async () => {
    await withEvents(events(projection({ [field]: value })), async () => {
      await assert.rejects(chatService.sendQuery(req));
    });
  });
}

test('altered content does not inherit approval', async () => {
  await withEvents(events(projection(), text + ' ALTERED'), async () => {
    await assert.rejects(chatService.sendQuery(req), /no coincide con su auditoría/);
  });
});

test('audit metadata does not complete a truncated stream', async () => {
  await withEvents(events().slice(0, -1), async () => {
    await assert.rejects(chatService.sendQuery(req), /sin un resultado terminal/);
  });
});

test('empty claims are a present typed report, while old SSE remains uncertified', async () => {
  const current = await withEvents(events(), () => chatService.sendQuery(req));
  assert.deepEqual(current.audit.projection.claims, []);
  const legacy = events(); delete legacy[1].payload.audit_projection;
  const old = await withEvents(legacy, () => chatService.sendQuery(req));
  assert.equal(old.audit, undefined);
});

test('concurrent streams have no shared projection accumulator', async () => {
  const previous = globalThis.fetch;
  globalThis.fetch = async (_, options) => {
    const body = JSON.parse(options.body);
    const b = body.session_id === 'session-B';
    return transport(events(projection({ session_id: body.session_id, request_id: b ? 'req-B' : 'req-A', audit_id: b ? 'audit-B' : 'audit-A', content_binding_id: b ? 'binding-B' : 'binding-A' })));
  };
  try {
    const [a, b] = await Promise.all([chatService.sendQuery(req), chatService.sendQuery({ ...req, session_id: 'session-B' })]);
    assert.equal(a.audit.projection.request_id, 'req-A');
    assert.equal(b.audit.projection.request_id, 'req-B');
    assert.notEqual(a.audit.message_id, b.audit.message_id);
  } finally { globalThis.fetch = previous; }
});

test('a later conflicting audit event invalidates earlier approval', async () => {
  const items = events();
  items.splice(2, 0, { event_type: 'audit_verdict', payload: { verdict: 'REJECTED_UNSUPPORTED' } });
  await withEvents(items, async () => { await assert.rejects(chatService.sendQuery(req)); });
});
