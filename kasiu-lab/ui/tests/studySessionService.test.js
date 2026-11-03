import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';

const source = await readFile(
  new URL('../src/services/studySessionService.ts', import.meta.url),
  'utf8',
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    esModuleInterop: true,
  },
}).outputText;
const serviceModule = { exports: {} };
new Function('require', 'module', 'exports', compiled)(
  () => { throw new Error('studySessionService must not load runtime dependencies'); },
  serviceModule,
  serviceModule.exports,
);
const { studySessionService } = serviceModule.exports;

class MemoryStorage {
  values = new Map();
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, value); }
  removeItem(key) { this.values.delete(key); }
}

function snapshot(sessionId, notebookId = 'notebook-synthetic') {
  return { session_id: sessionId, notebook_id: notebookId, episode_id: 'episode-synthetic' };
}

test('creates once, stores the ID by notebook, and restores the same persisted session', async (t) => {
  const previousFetch = globalThis.fetch;
  const storage = new MemoryStorage();
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url, method: init.method || 'GET', body: init.body ? JSON.parse(init.body) : null });
    if (url === '/api/study/session/open') {
      return new Response(JSON.stringify(snapshot('session-created')),
        { status: 200, headers: { 'content-type': 'application/json' } });
    }
    return new Response(JSON.stringify(snapshot('session-created')),
      { status: 200, headers: { 'content-type': 'application/json' } });
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  const first = await studySessionService.restoreOrOpenSession('notebook-synthetic', 'student-synthetic', storage);
  const second = await studySessionService.restoreOrOpenSession('notebook-synthetic', 'student-synthetic', storage);

  assert.equal(first.disposition, 'CREATED_NEW');
  assert.equal(second.disposition, 'RESTORED_EXISTING');
  assert.equal(first.snapshot.session_id, second.snapshot.session_id);
  assert.equal(calls.filter((call) => call.url === '/api/study/session/open').length, 1);
  assert.match(calls[1].url, /session-created\/snapshot$/);
});

test('only a confirmed 404 retires a missing session ID and reports the replacement visibly', async (t) => {
  const previousFetch = globalThis.fetch;
  const storage = new MemoryStorage();
  storage.setItem('talos_study_session:student-synthetic:notebook-synthetic', 'session-missing');
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push(url);
    if (url.includes('session-missing')) return new Response('{}', { status: 404 });
    if (url === '/api/study/session/open') {
      return new Response(JSON.stringify(snapshot('session-replacement')),
        { status: 200, headers: { 'content-type': 'application/json' } });
    }
    throw new Error(`Unexpected request ${url} ${init.method || 'GET'}`);
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  const result = await studySessionService.restoreOrOpenSession('notebook-synthetic', 'student-synthetic', storage);
  assert.equal(result.disposition, 'PREVIOUS_MISSING_CREATED_NEW');
  assert.equal(result.snapshot.session_id, 'session-replacement');
  assert.equal(storage.getItem('talos_study_session:student-synthetic:notebook-synthetic'), 'session-replacement');
  assert.equal(calls.filter((url) => url === '/api/study/session/open').length, 1);
});

test('a snapshot error other than 404 does not silently create a new session', async (t) => {
  const previousFetch = globalThis.fetch;
  const storage = new MemoryStorage();
  storage.setItem('talos_study_session:student-synthetic:notebook-synthetic', 'session-existing');
  const calls = [];
  globalThis.fetch = async (url) => {
    calls.push(url);
    return new Response('{}', { status: 503 });
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  await assert.rejects(
    studySessionService.restoreOrOpenSession('notebook-synthetic', 'student-synthetic', storage),
    (error) => error.statusCode === 503,
  );
  assert.deepEqual(calls, ['/api/study/session/session-existing/snapshot']);
});

test('concurrent restore requests for the same notebook share one open operation', async (t) => {
  const previousFetch = globalThis.fetch;
  const storage = new MemoryStorage();
  let releaseOpen;
  const openWait = new Promise((resolve) => { releaseOpen = resolve; });
  let openCalls = 0;
  globalThis.fetch = async (url) => {
    if (url !== '/api/study/session/open') throw new Error(`Unexpected request: ${url}`);
    openCalls += 1;
    await openWait;
    return new Response(JSON.stringify(snapshot('session-single-open')),
      { status: 200, headers: { 'content-type': 'application/json' } });
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  const first = studySessionService.restoreOrOpenSession('notebook-synthetic', 'student-synthetic', storage);
  const second = studySessionService.restoreOrOpenSession('notebook-synthetic', 'student-synthetic', storage);
  await Promise.resolve();
  assert.equal(openCalls, 1);
  releaseOpen();
  const results = await Promise.all([first, second]);
  assert.equal(results[0].snapshot.session_id, results[1].snapshot.session_id);
  assert.equal(openCalls, 1);
});

test('keeps session identities isolated by notebook instead of reusing a neighboring session', async (t) => {
  const previousFetch = globalThis.fetch;
  const storage = new MemoryStorage();
  const calls = [];
  globalThis.fetch = async (url, init = {}) => {
    calls.push({ url, body: init.body ? JSON.parse(init.body) : null });
    if (url === '/api/study/session/open') {
      const notebookId = JSON.parse(init.body).notebook_id;
      return new Response(JSON.stringify(snapshot(`session-${notebookId}`, notebookId)),
        { status: 200, headers: { 'content-type': 'application/json' } });
    }
    const sessionId = url.split('/').at(-2);
    const notebookId = sessionId.replace('session-', '');
    return new Response(JSON.stringify(snapshot(sessionId, notebookId)),
      { status: 200, headers: { 'content-type': 'application/json' } });
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  const firstNotebook = await studySessionService.restoreOrOpenSession('notebook-one', 'student-synthetic', storage);
  const secondNotebook = await studySessionService.restoreOrOpenSession('notebook-two', 'student-synthetic', storage);
  const firstRestored = await studySessionService.restoreOrOpenSession('notebook-one', 'student-synthetic', storage);

  assert.equal(firstNotebook.snapshot.session_id, 'session-notebook-one');
  assert.equal(secondNotebook.snapshot.session_id, 'session-notebook-two');
  assert.equal(firstRestored.disposition, 'RESTORED_EXISTING');
  assert.equal(firstRestored.snapshot.session_id, firstNotebook.snapshot.session_id);
  assert.equal(calls.filter((call) => call.url === '/api/study/session/open').length, 2);
});
