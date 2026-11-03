import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { after, test } from 'node:test';
import { JSDOM } from 'jsdom';
import React, { act } from 'react';
import ts from 'typescript';

const dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1:5173' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const require = createRequire(import.meta.url);
const { createRoot } = require('react-dom/client');
const icons = new Proxy({}, { get: (_, name) => (props) => React.createElement('span', {
  'aria-hidden': true, 'data-icon': String(name), className: props?.className,
}) });
function load(relativePath, overrides = {}) {
  const module = { exports: {} };
  const compiled = ts.transpileModule(readFileSync(new URL(relativePath, import.meta.url), 'utf8'), { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
  } }).outputText;
  new Function('require', 'module', 'exports', compiled)(
    (id) => id === 'lucide-react' ? icons : id in overrides ? overrides[id] : require(id), module, module.exports,
  );
  return module.exports;
}
const helper = load('../src/services/auditProjection.ts');
const { ContradictionView } = load('../src/presentation/features/views/ContradictionView.tsx');
const { chatService, AuditedResponseError } = load('../src/services/chatService.ts', {
  './auditProjection': helper,
  '../infrastructure/api/apiClient': { apiFetch: async () => ({}) },
  '../adapters/chatAdapter': { adaptBackendChatResponse: (value) => value },
});
const { EvidencePanel } = load('../src/presentation/features/views/EvidencePanel.tsx', {
  './ContradictionView': { ContradictionView }, '../../../services/auditProjection': helper,
  '../../hooks/useSandboxFsm': load('../src/presentation/hooks/useSandboxFsm.ts'),
  '../../../services/chatService': { chatService },
  './CurriculumProgress': { CurriculumProgress: () => null },
});
const text = 'Texto académico sintético. [E1]';
const sha = (value) => createHash('sha256').update(value).digest('hex');
const projection = (overrides = {}) => ({
  audit_id: 'audit-A', request_id: 'req-A', session_id: 'session-A', scope_id: 'nb-A', scope_type: 'notebook',
  notebook_id: 'nb-A', phase: 'conceptual', auditor_verdict: 'APPROVED', decision: 'APPROVED', emission: 'authorized',
  content_sha256: sha(text), content_binding_id: 'binding-A', nli_executed: false, claims: [], ...overrides,
});
async function message(p = projection(), body = text) {
  const audit = await helper.bindMessageAudit(p, body);
  return { id: audit.message_id, text: body, audit, timestamp: 'Synthetic', sender: 'assistant' };
}
const base = { width: 400, isOpen: true, isDragging: false, tab: 'contradicciones', notes: [],
  activeScope: 'Same topic', sessionId: 'session-A', scopeId: 'nb-A', responseKey: 'current',
  consultedSources: [], onResizeStart() {}, onTab() {} };
const tick = () => new Promise((resolve) => setTimeout(resolve, 5));
async function mount(props = {}) {
  const previousFetch = globalThis.fetch;
  const requests = [];
  globalThis.fetch = async (url) => { requests.push(url); throw new Error('Panel must not query reports by session'); };
  const element = document.createElement('div'); document.body.appendChild(element);
  const root = createRoot(element);
  let current = { ...base, ...props };
  async function render(next = {}) {
    current = { ...current, ...next };
    await act(async () => { root.render(React.createElement(EvidencePanel, current)); await tick(); });
    for (let i = 0; i < 20 && !current.responsePending && element.textContent.includes('Consultando información'); i++) await act(tick);
  }
  await render();
  return { element, requests, render, async close() {
    await act(async () => root.unmount()); element.remove(); globalThis.fetch = previousFetch;
    assert.deepEqual(requests, []);
  } };
}
function noApproval(element) { assert.doesNotMatch(element.textContent, /Respuesta aprobada|0 Conflicto|No se registran aserciones|No se detectaron contradicciones/); }
after(() => dom.window.close());

test('workspace passes the shared session, actual message, scope and loading state to EvidencePanel', () => {
  const source = readFileSync(new URL('../src/presentation/features/chat/ChatWorkspace.tsx', import.meta.url), 'utf8');
  const ast = ts.createSourceFile('ChatWorkspace.tsx', source, ts.ScriptTarget.ES2022, true, ts.ScriptKind.TSX);
  let panel;
  function visit(node) { if (ts.isJsxSelfClosingElement(node) && node.tagName.getText(ast) === 'EvidencePanel') panel = node; ts.forEachChild(node, visit); }
  visit(ast);
  const attributes = Object.fromEntries(panel.attributes.properties.filter(ts.isJsxAttribute).map((a) => [a.name.getText(ast), a.initializer?.expression?.getText(ast)]));
  assert.equal(attributes.sessionId, 'effectiveChatSessionId');
  assert.ok(attributes.auditMessage && attributes.auditMessages && attributes.scopeId && attributes.responsePending);
  assert.match(source, /session_id: effectiveChatSessionId/);
  const identity = source.match(/const effectiveChatSessionId = ([\s\S]*?);/)[1];
  const select = new Function('activeEntity', 'studySessionSnapshot', 'chatSessionIdRef', `return (${identity});`);
  assert.equal(select({ type: 'notebook', id: 'nb-B' }, { notebook_id: 'nb-A', session_id: 'A' }, { current: 'local' }), null);
  assert.equal(select({ type: 'notebook', id: 'nb-A' }, { notebook_id: 'nb-A', session_id: 'A' }, { current: 'local' }), 'A');
  assert.equal(select({ type: 'folder', id: 'folder-A' }, null, { current: 'local' }), 'local');
});

test('UI-T01: verified approved response shows its exact report, not a session cache', async () => {
  const m = await message(); const view = await mount({ auditMessage: m });
  try { assert.match(view.element.textContent, /Respuesta aprobada dentro del alcance de S4.4/); assert.match(view.element.textContent, /req-A/); assert.match(view.element.textContent, /audit-A/); assert.match(view.element.textContent, /sin claims evaluables/); }
  finally { await view.close(); }
});

for (const [name, original, decision, expected] of [
  ['UI-T02 rejection', 'REJECTED_UNSUPPORTED', 'REJECTED_UNSUPPORTED', /rechazó el contenido/],
  ['UI-T03 inconclusion', 'FLAGGED_UNASSESSED', 'DEFERRED_RETRY', /Evaluación inconclusa/],
]) {
  test(name, async () => {
    const m = await message(projection({ auditor_verdict: original, decision, emission: 'blocked' }), 'Mensaje operativo.');
    const view = await mount({ auditMessage: m });
    try { assert.match(view.element.textContent, expected); assert.match(view.element.textContent, new RegExp(original)); assert.match(view.element.textContent, new RegExp(decision)); assert.match(view.element.textContent, /no al mensaje explicativo/); noApproval(view.element); }
    finally { await view.close(); }
  });
}

test('UI-T04/T08: absent and historical messages remain uncertified without network lookup', async () => {
  const view = await mount();
  try {
    assert.match(view.element.textContent, /No hay un reporte/); noApproval(view.element);
    await view.render({ auditMessage: { id: 'historical', sender: 'assistant', text, timestamp: 'Before FIX-2', claims: [] } });
    assert.match(view.element.textContent, /No hay un reporte/); noApproval(view.element);
  } finally { await view.close(); }
});

test('UI-T05: changing message removes approval immediately; message selector restores only its own report', async () => {
  const first = await message();
  const second = { id: 'old-without-report', text: 'Historical', sender: 'assistant', timestamp: 'Old' };
  const view = await mount({ auditMessage: first, auditMessages: [first, second] });
  try {
    await act(async () => { const select = view.element.querySelector('select'); select.value = second.id; select.dispatchEvent(new dom.window.Event('change', { bubbles: true })); await tick(); });
    assert.match(view.element.textContent, /No hay un reporte/); noApproval(view.element);
    await view.render({ auditMessage: second, responseKey: second.id });
    noApproval(view.element);
  } finally { await view.close(); }
});

test('UI-T06: same topic with another session or scope cannot reuse approval', async () => {
  const view = await mount({ auditMessage: await message() });
  try {
    await view.render({ sessionId: 'session-B' }); noApproval(view.element); assert.match(view.element.textContent, /No se pudo verificar/);
    await view.render({ sessionId: 'session-A', scopeId: 'nb-B' }); noApproval(view.element);
    await view.render({ sessionId: null }); assert.match(view.element.textContent, /No hay una sesión/); noApproval(view.element);
  } finally { await view.close(); }
});

test('UI-T07: altered content, different message ID and invalid report cannot inherit approval', async () => {
  const m = await message(); const view = await mount({ auditMessage: m });
  try {
    for (const changed of [{ ...m, text: m.text + ' ALTERED' }, { ...m, id: 'another' }, { ...m, audit: { ...m.audit, projection: { ...m.audit.projection, audit_id: '' } } }]) {
      await view.render({ auditMessage: changed }); noApproval(view.element); assert.match(view.element.textContent, /No se pudo verificar/);
    }
  } finally { await view.close(); }
});

test('UI-T09: in-flight or failed transport has no completed verification', async () => {
  const view = await mount({ auditMessage: await message(), responsePending: true });
  try {
    assert.match(view.element.textContent, /Consultando información/); noApproval(view.element);
    await view.render({ responsePending: false, auditMessage: { id: 'transport-error', text: 'Error', sender: 'assistant', errorState: true } });
    assert.match(view.element.textContent, /No se pudo verificar/); noApproval(view.element);
  } finally { await view.close(); }
});

test('claim metadata is shown faithfully without inventing two-source contradictions or rationale', async () => {
  const m = await message(projection({ auditor_verdict: 'REJECTED_CONTRADICTION', decision: 'REJECTED_CONTRADICTION', emission: 'blocked',
    claims: [{ claim_index: 3, claim_type: 'FACTUAL', cited_tags: ['E1'], nli_verdict: 'CONTRADICTED' }] }), 'Abstención.');
  const view = await mount({ auditMessage: m });
  try { assert.match(view.element.textContent, /Claim 4/); assert.match(view.element.textContent, /CONTRADICTED/); assert.match(view.element.textContent, /Citas: E1/); assert.match(view.element.textContent, /afirmación contradicha/); noApproval(view.element); }
  finally { await view.close(); }
});

const wires = process.env.TALOS_AUDIT_WIRES_STDIN ? JSON.parse(readFileSync(0, 'utf8')) : null;
test('UI-T10: real backend controlled SSE → real client parser → real React panel', { skip: !wires }, async () => {
  for (const fixture of wires) {
    const previous = globalThis.fetch;
    globalThis.fetch = async () => new Response(fixture.events.map((e) => `data: ${JSON.stringify(e)}\n\n`).join(''), { headers: { 'content-type': 'text/event-stream' } });
    let m;
    try {
      const result = await chatService.sendQuery({ query: 'tabla de rutas', session_id: 'session-A', scope_type: 'notebook', scope_id: 'nb-synthetic' });
      m = { id: result.audit?.message_id || 'no-report', text: result.reply_text, audit: result.audit, timestamp: 'Synthetic', sender: 'assistant' };
    } catch (error) {
      assert.ok(error instanceof AuditedResponseError);
      m = { id: error.audit?.message_id || 'error', text: error.message, audit: error.audit, errorState: true, timestamp: 'Synthetic', sender: 'assistant' };
    } finally { globalThis.fetch = previous; }
    const view = await mount({ scopeId: 'nb-synthetic', auditMessage: m });
    try {
      if (fixture.expected === 'APPROVED') assert.match(view.element.textContent, /Respuesta aprobada/);
      else { noApproval(view.element); assert.match(view.element.textContent, fixture.expected === 'REJECTED_UNSUPPORTED' ? /rechazó el contenido/ : /Evaluación inconclusa/); }
    } finally { await view.close(); }
  }
});
