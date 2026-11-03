import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { after, test } from 'node:test';
import { JSDOM } from 'jsdom';
import React, { act } from 'react';
import ts from 'typescript';

// Real hook in JSDOM with real localStorage; no network, no backend.
const dom = new JSDOM('<html><body></body></html>', { url: 'http://127.0.0.1:5173' });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
globalThis.localStorage = dom.window.localStorage;
globalThis.HTMLElement = dom.window.HTMLElement;
globalThis.IS_REACT_ACT_ENVIRONMENT = true;
const require = createRequire(import.meta.url);
const { createRoot } = require('react-dom/client');
function load(file, overrides = {}) {
  const module = { exports: {} };
  new Function('require', 'module', 'exports', ts.transpileModule(readFileSync(new URL(file, import.meta.url), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
  }).outputText)((id) => id in overrides ? overrides[id] : require(id), module, module.exports);
  return module.exports;
}
const { usePersistentChatHistory } = load('../src/presentation/hooks/usePersistentChatHistory.ts', {
  '../features/views/types': {},
});
const audit = { projection: { audit_id: 'audit-A' }, message_id: 'm1', message_sha256: '0'.repeat(64), stream_completed: true };
function Probe({ onReady }) {
  const api = usePersistentChatHistory('scope-synthetic');
  onReady(api);
  return null;
}
const tick = () => new Promise((resolve) => setTimeout(resolve, 0));
after(() => dom.window.close());

test('persisted history is not an authenticated replay: audit never survives storage', async () => {
  dom.window.localStorage.clear();
  const element = document.createElement('div');
  document.body.appendChild(element);
  const root = createRoot(element);
  let api;
  await act(async () => { root.render(React.createElement(Probe, { onReady: (value) => { api = value; } })); await tick(); });
  await act(async () => {
    api.setMessages([{ id: 'm1', sender: 'assistant', text: 'Texto sintético.', timestamp: 'Ahora', audit }]);
    await tick();
  });
  const stored = JSON.parse(dom.window.localStorage.getItem('talos_chat_history_scope-synthetic'));
  assert.equal(stored[0].audit, undefined);
  assert.equal(stored[0].text, 'Texto sintético.');
  await act(async () => { root.unmount(); });

  const reloadRoot = createRoot(element);
  let reloaded;
  await act(async () => { reloadRoot.render(React.createElement(Probe, { onReady: (value) => { reloaded = value; } })); await tick(); });
  await act(tick);
  assert.equal(reloaded.messages.length, 1);
  assert.equal(reloaded.messages[0].text, 'Texto sintético.');
  assert.equal(reloaded.messages[0].audit, undefined);
  await act(async () => { reloadRoot.unmount(); });
  element.remove();
});
