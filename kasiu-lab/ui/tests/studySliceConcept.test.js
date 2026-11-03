// Input: JSON from test_a4_public_concept.frontend_scenarios(), streamed on stdin.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';

const require = createRequire(import.meta.url);
const React = require('react');
const ts = require('typescript');
const { JSDOM } = require('jsdom');
const scenarios = JSON.parse(fs.readFileSync(0, 'utf8'));
assert.deepEqual(Object.keys(scenarios).sort(), ['approved', 'extra', 'inconclusive', 'rejected']);
const modules = new Map();

function loadSource(filename) {
  if (modules.has(filename)) return modules.get(filename).exports;
  const module = { exports: {} };
  modules.set(filename, module);
  const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true,
    },
  }).outputText;
  function localRequire(name) {
    // Decorative icons only; hooks, component logic, services and rendering are real.
    if (name === 'lucide-react') return new Proxy({}, { get: () => () => null });
    if (!name.startsWith('.')) return require(name);
    const base = path.resolve(path.dirname(filename), name);
    const resolved = ['.ts', '.tsx', '/index.ts', '/index.tsx']
      .map((suffix) => base + suffix).find((candidate) => fs.existsSync(candidate));
    assert.ok(resolved, `Unresolved source import: ${name}`);
    return loadSource(resolved);
  }
  new Function('require', 'module', 'exports', compiled)(localRequire, module, module.exports);
  return module.exports;
}

for (const [scenario, payload] of Object.entries(scenarios)) {
  for (const omitOptional of scenario === 'approved' ? [false, true] : [false]) {
    test(`StudySliceModal: backend ${scenario}, omit optional=${omitOptional}`, async () => {
      const approved = payload.status === 'PRESENTABLE';
      const publicPayload = structuredClone(payload);
      if (omitOptional) {
        for (const field of ['formalization', 'implementation_guidance', 'pitfalls', 'reasoning_guidance']) {
          delete publicPayload.packet[field];
        }
      }
      const notebook = 'a4-synthetic-notebook', kc = 'a4-synthetic-kc';
      const session = 'a4-synthetic-session', episode = 'a4-synthetic-episode';
      const dom = new JSDOM('<!doctype html><div id="root"></div>', { url: 'http://a4.invalid/' });
      globalThis.window = dom.window;
      globalThis.document = dom.window.document;
      Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
      globalThis.IS_REACT_ACT_ENVIRONMENT = true;
      window.__TALOS_SYNTHETIC_PROFILE__ = true;
      window.__TALOS_DEFAULT_NOTEBOOK_ID__ = notebook;
      window.__TALOS_STUDENT_ID__ = 'a4-synthetic-student';
      const calls = [];
      const previousFetch = globalThis.fetch;
      globalThis.fetch = window.fetch = async (url) => {
        calls.push(url);
        let data;
        if (url === `/api/pedagogy/notebook/${notebook}/kcs`) {
          data = { notebook_id: notebook, name: 'A4 synthetic notebook', kcs: [{
            kc_id: kc, title: 'A4 synthetic KC', unit: 1, priority: 'Media',
            contextual_status: 'SYNTHETIC', bkt: { p_L: 0.1, attempts: 0 },
          }] };
        } else if (url === '/api/study/session/open') {
          data = { session_id: session, notebook_id: notebook, current_kc_id: kc,
            episode_id: episode, episode_phase: 'EXPLAINING', available_actions: [] };
        } else if (url === `/api/pedagogy/episode/${episode}/concept`) {
          data = publicPayload;
        } else if (url === `/api/pedagogy/episode/${episode}/next`) {
          data = { intervention_type: 'NO_QUALIFIABLE_EXERCISE' };
        } else {
          throw new Error(`Forbidden fetch: ${url}`);
        }
        return { ok: true, status: 200, json: async () => structuredClone(data) };
      };
      const { createRoot } = require('react-dom/client');
      const filename = fileURLToPath(new URL('../src/presentation/features/chat/StudySliceModal.tsx', import.meta.url));
      const { StudySliceModal } = loadSource(filename);
      const root = createRoot(document.getElementById('root'));
      try {
        await React.act(async () => root.render(React.createElement(StudySliceModal, {
          isOpen: true, onClose: () => {}, initialNotebookId: notebook,
        })));
        const row = [...document.querySelectorAll('div.group')]
          .find((element) => element.textContent.includes('A4 synthetic KC') && element.textContent.includes('Estudiar'));
        assert.ok(row, 'Actual KC selection must be available');
        await React.act(async () => row.dispatchEvent(new window.MouseEvent('click', { bubbles: true })));
        const text = document.getElementById('root').textContent;
        assert.equal(text.includes('S4.4: APPROVED'), approved);
        assert.equal(text.includes('A4_CORE'), approved);
        assert.equal(text.includes('A4_MODEL'), approved);
        if (approved) {
          assert.ok(text.includes(payload.packet.core_concept));
          assert.ok(text.includes(payload.packet.mental_model));
        } else {
          // /next may replace the abstention message; it must never expose a concept.
          assert.ok(document.querySelector('[role="alert"]'));
          assert.ok(!text.includes('Explicación Integrada Multifuente'));
        }
        for (const marker of ['A4_OBJECTIVE', 'A4_REASONING', 'A4_FORMAL', 'A4_IMPL', 'A4_PITFALL', 'Errores Frecuentes y Puntos Críticos:']) {
          assert.ok(!text.includes(marker), `Unverified content/fallback exposed: ${marker}`);
        }
        assert.ok(calls.includes(`/api/pedagogy/episode/${episode}/concept`));
      } finally {
        await React.act(async () => root.unmount());
        globalThis.fetch = previousFetch;
        dom.window.close();
      }
    });
  }
}
