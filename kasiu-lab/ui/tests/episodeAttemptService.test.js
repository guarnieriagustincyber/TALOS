import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';

const source = await readFile(
  new URL('../src/services/episodeAttemptService.ts', import.meta.url),
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
  () => { throw new Error('episodeAttemptService must not load runtime dependencies'); },
  serviceModule,
  serviceModule.exports,
);
const { episodeAttemptStorageKey, readEpisodeAttemptRecord, writeEpisodeAttemptRecord } = serviceModule.exports;

class MemoryStorage {
  values = new Map();
  getItem(key) { return this.values.get(key) ?? null; }
  setItem(key, value) { this.values.set(key, value); }
}

test('rehydrates an uncertain episode attempt with its exact ID and answer for explicit retry', () => {
  const storage = new MemoryStorage();
  const record = {
    version: 1,
    sessionId: 'session-1',
    episodeId: 'episode-1',
    exerciseId: 'exercise-1',
    current: { attemptId: 'attempt-stable', answer: 'same answer', status: 'submitting' },
    history: [],
  };
  writeEpisodeAttemptRecord(storage, record);

  const restored = readEpisodeAttemptRecord(storage, 'session-1', 'episode-1', 'exercise-1');
  assert.equal(restored.current.status, 'unknown');
  assert.equal(restored.current.attemptId, 'attempt-stable');
  assert.equal(restored.current.answer, 'same answer');
  assert.equal(readEpisodeAttemptRecord(storage, 'session-2', 'episode-1', 'exercise-1'), null);
});

test('episode attempts are isolated by session, episode, and certified exercise identity', () => {
  const first = episodeAttemptStorageKey('session/1', 'episode-1', 'exercise-1');
  const otherSession = episodeAttemptStorageKey('session-2', 'episode-1', 'exercise-1');
  const otherEpisode = episodeAttemptStorageKey('session/1', 'episode-2', 'exercise-1');
  const otherExercise = episodeAttemptStorageKey('session/1', 'episode-1', 'exercise-2');
  assert.equal(new Set([first, otherSession, otherEpisode, otherExercise]).size, 4);
  assert.ok(first.includes('session%2F1'));
});

test('mismatched persisted identities fail closed instead of authorizing another exercise', () => {
  const storage = new MemoryStorage();
  writeEpisodeAttemptRecord(storage, {
    version: 1,
    sessionId: 'session-1',
    episodeId: 'episode-1',
    exerciseId: 'exercise-1',
    current: { attemptId: 'attempt-1', answer: 'answer', status: 'unknown' },
    history: [],
  });
  storage.setItem(episodeAttemptStorageKey('session-1', 'episode-1', 'exercise-2'), JSON.stringify({
    version: 1,
    sessionId: 'session-1',
    episodeId: 'episode-1',
    exerciseId: 'exercise-1',
    current: { attemptId: 'attempt-1', answer: 'answer', status: 'unknown' },
    history: [],
  }));

  assert.throws(
    () => readEpisodeAttemptRecord(storage, 'session-1', 'episode-1', 'exercise-2'),
    /identity|identidad/i,
  );
});
