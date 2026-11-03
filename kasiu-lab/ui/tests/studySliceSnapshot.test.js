// Input: JSON from the fixed backend (R3 snapshot + /next payload), piped on stdin.
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
const payload = JSON.parse(fs.readFileSync(0, 'utf8'));
const notebook = 'a5-synthetic-notebook', kc = 'a5-synthetic-kc';
const session = 'a5-synthetic-session', episode = 'ep_a5-synthetic-session_a5-synthetic-kc';

// Oracle: actions the backend itself declares valid per published phase.
const PHASE_ACTIONS = {
  OPENING_BRIEF: ['START_EXPLANATION', 'REVIEW_PREREQUISITE', 'SELECT_DIFFERENT_KC'],
  EXPLAINING: ['REQUEST_DIALOGUE', 'SKIP_TO_EXERCISE', 'REQUEST_EXAMPLE'],
  DIALOGUE: ['SUBMIT_MESSAGE', 'REQUEST_EXAMPLE', 'REQUEST_REFORMULATION', 'SKIP_TO_EXERCISE', 'ACCEPT_EXERCISE', 'REJECT_EXERCISE'],
  DIALOGUE_LIMIT_REACHED: ['ACCEPT_EXERCISE', 'REJECT_EXERCISE', 'REQUEST_EXERCISE', 'CONTINUE_EXPLORATION'],
  SUGGEST_EXERCISE: ['ACCEPT_EXERCISE', 'REJECT_EXERCISE', 'REQUEST_EXPLANATION'],
  EVALUATING: ['SUBMIT_ANSWER', 'REQUEST_HINT'],
  CLOSED: ['START_NEXT_KC', 'REVIEW_TOPIC'],
};

test('backend snapshot offers only actions admissible for its published phase', () => {
  const snapshot = payload.snapshot;
  assert.ok(PHASE_ACTIONS[snapshot.episode_phase], `unknown phase ${snapshot.episode_phase}`);
  for (const action of snapshot.available_actions) {
    assert.ok(
      PHASE_ACTIONS[snapshot.episode_phase].includes(action),
      `stale action ${action} published for phase ${snapshot.episode_phase}`,
    );
  }
  assert.equal(snapshot.episode_phase, 'EVALUATING');
  assert.deepEqual(snapshot.available_actions, ['SUBMIT_ANSWER', 'REQUEST_HINT']);
  assert.ok(snapshot.session_state_hash);
});

test('StudySliceModal renders the pending exercise with the corrected DTO', async () => {
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

  const dom = new JSDOM('<!doctype html><div id="root"></div>', { url: 'http://a5.invalid/' });
  globalThis.window = dom.window;
  globalThis.document = dom.window.document;
  Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
  globalThis.IS_REACT_ACT_ENVIRONMENT = true;
  window.__TALOS_SYNTHETIC_PROFILE__ = true;
  window.__TALOS_DEFAULT_NOTEBOOK_ID__ = notebook;
  window.__TALOS_STUDENT_ID__ = 'a5-synthetic-student';
  const calls = [];
  const previousFetch = globalThis.fetch;
  globalThis.fetch = window.fetch = async (url) => {
    calls.push(url);
    let data;
    if (url === `/api/pedagogy/notebook/${notebook}/kcs`) {
      data = { notebook_id: notebook, kcs: [{ kc_id: kc, title: 'A5 synthetic KC', unit: 1, priority: 'Media', contextual_status: 'SYNTHETIC', bkt: { p_L: 0.1, attempts: 0 } }] };
    } else if (url === '/api/study/session/open' || url === `/api/study/session/${session}/snapshot`) {
      data = payload.snapshot;
    } else if (url === `/api/pedagogy/episode/${episode}/concept`) {
      data = { status: 'ABSTAINED', packet: null, abstention_reason: 'A5 synthetic abstention', audit_verdict: 'REJECTED_UNSUPPORTED' };
    } else if (url === `/api/pedagogy/episode/${episode}/next`) {
      data = payload.next;
    } else {
      throw new Error(`Forbidden fetch: ${url}`);
    }
    return { ok: true, status: 200, json: async () => structuredClone(data) };
  };
  try {
    const { createRoot } = require('react-dom/client');
    const filename = fileURLToPath(new URL('../src/presentation/features/chat/StudySliceModal.tsx', import.meta.url));
    const { StudySliceModal } = loadSource(filename);
    const root = createRoot(document.getElementById('root'));
    await React.act(async () => root.render(React.createElement(StudySliceModal, {
      isOpen: true, onClose: () => {}, initialNotebookId: notebook,
    })));
    const row = [...document.querySelectorAll('div.group')]
      .find((element) => element.textContent.includes('A5 synthetic KC') && element.textContent.includes('Estudiar'));
    assert.ok(row, 'KC selection must be available');
    await React.act(async () => row.dispatchEvent(new window.MouseEvent('click', { bubbles: true })));
    const text = document.getElementById('root').textContent;
    assert.ok(text.includes(payload.next.exercise.prompt), 'pending exercise must be visible');
    assert.ok(text.includes('Enviar Respuesta'), 'answer control must be visible');
    assert.ok(calls.includes(`/api/pedagogy/episode/${episode}/next`));
    await React.act(async () => root.unmount());
  } finally {
    globalThis.fetch = previousFetch;
    dom.window.close();
  }
});

test('session service propagates stale-state rejection without sending a hash', async () => {
  const filename = fileURLToPath(new URL('../src/services/studySessionService.ts', import.meta.url));
  const modules = new Map();
  function loadSource(file) {
    if (modules.has(file)) return modules.get(file).exports;
    const module = { exports: {} };
    modules.set(file, module);
    const compiled = ts.transpileModule(fs.readFileSync(file, 'utf8'), {
      compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true },
    }).outputText;
    function localRequire(name) {
      if (!name.startsWith('.')) return require(name);
      const base = path.resolve(path.dirname(file), name);
      const resolved = ['.ts', '.tsx', '/index.ts', '/index.tsx']
        .map((suffix) => base + suffix).find((candidate) => fs.existsSync(candidate));
      assert.ok(resolved);
      return loadSource(resolved);
    }
    new Function('require', 'module', 'exports', compiled)(localRequire, module, module.exports);
    return module.exports;
  }
  let sent;
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    sent = JSON.parse(options.body);
    return { ok: false, status: 409, json: async () => ({ detail: 'A5 controlled stale-state rejection' }) };
  };
  try {
    const { studySessionService } = loadSource(filename);
    await assert.rejects(
      studySessionService.executeAction(session, 'REQUEST_DIALOGUE'),
      /A5 controlled stale-state rejection/,
    );
    assert.deepEqual(Object.keys(sent).sort(), ['action', 'payload']);
    assert.ok(!('session_state_hash' in sent));
  } finally {
    globalThis.fetch = previousFetch;
  }
});
