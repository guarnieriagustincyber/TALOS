import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';

const source = await readFile(
  new URL('../src/services/chatService.ts', import.meta.url),
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
const projectionSource = await readFile(new URL('../src/services/auditProjection.ts', import.meta.url), 'utf8');
const projectionModule = { exports: {} };
new Function('module', 'exports', ts.transpileModule(projectionSource, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText)(projectionModule, projectionModule.exports);
const serviceRequire = (specifier) => {
  if (specifier === './auditProjection') return projectionModule.exports;
  if (specifier === '../infrastructure/api/apiClient') return { apiFetch: async () => ({}) };
  if (specifier === '../adapters/chatAdapter') {
    return { adaptBackendChatResponse: (response) => response };
  }
  throw new Error(`Unexpected dependency in chatService.ts: ${specifier}`);
};
new Function('require', 'module', 'exports', compiled)(
  serviceRequire,
  serviceModule,
  serviceModule.exports,
);
const { chatService, createExerciseAttemptId, ExerciseEvaluationError } = serviceModule.exports;

function installSseResponse(events) {
  const previousFetch = globalThis.fetch;
  const stream = new ReadableStream({
    start(controller) {
      const wire = typeof events === 'string'
        ? events
        : events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join('');
      controller.enqueue(new TextEncoder().encode(wire));
      controller.close();
    },
  });
  globalThis.fetch = async () => new Response(stream, {
    headers: { 'content-type': 'text/event-stream' },
  });
  return () => {
    globalThis.fetch = previousFetch;
  };
}

function installFakeTimeouts() {
  const originalSetTimeout = globalThis.setTimeout;
  const originalClearTimeout = globalThis.clearTimeout;
  const scheduled = [];
  globalThis.setTimeout = (callback, delay, ...args) => {
    const timer = { callback, delay, args, cleared: false };
    scheduled.push(timer);
    return timer;
  };
  globalThis.clearTimeout = (timer) => {
    if (timer) timer.cleared = true;
  };
  return {
    activeCount: () => scheduled.filter((timer) => !timer.cleared).length,
    scheduled: () => scheduled,
    fireNext: () => {
      const timer = scheduled.find((candidate) => !candidate.cleared);
      assert.ok(timer, 'expected a pending timeout');
      timer.callback(...timer.args);
    },
    fireScheduled: (index) => scheduled[index].callback(...scheduled[index].args),
    restore: () => {
      globalThis.setTimeout = originalSetTimeout;
      globalThis.clearTimeout = originalClearTimeout;
    },
  };
}

function installPendingSseResponse() {
  const previousFetch = globalThis.fetch;
  let markReadStarted;
  const readStarted = new Promise((resolve) => {
    markReadStarted = resolve;
  });
  globalThis.fetch = async (_url, init) => {
    const body = new ReadableStream({
      start(controller) {
        init.signal.addEventListener(
          'abort',
          () => controller.error(new DOMException('The operation was aborted', 'AbortError')),
          { once: true },
        );
      },
      pull() {
        markReadStarted();
      },
    });
    return new Response(body, { headers: { 'content-type': 'text/event-stream' } });
  };
  return {
    readStarted,
    restore: () => {
      globalThis.fetch = previousFetch;
    },
  };
}

function manifest(abstentionReason = 'NO_EVIDENCE') {
  return {
    event_type: 'evidence_manifest',
    payload: {
      citations: [],
      facet_coverage: {},
      abstained: true,
      abstention_reason: abstentionReason,
    },
  };
}

test('reports a technical audit failure as an operational error, not an academic abstention', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'audit_verdict', payload: { verdict: 'DEFERRED_RETRY' } },
    {
      event_type: 'abstention',
      payload: {
        abstained: true,
        failure_class: 'TECHNICAL',
        abstention_code: 'DEFERRED_RETRY',
        reason: 'TALOS no pudo completar la verificación técnica de la respuesta (S4.4).',
      },
    },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta sintética' }),
    (error) =>
      error.name === 'SseResponseError' &&
      error.message === 'TALOS no pudo completar la verificación técnica de la respuesta (S4.4).',
  );
});

test('accepts abstention and clarification as distinct terminal pedagogical outcomes', async () => {
  for (const [eventType, reply, code] of [
    ['abstention', 'No hay evidencia suficiente para responder.', 'NO_EVIDENCE'],
    ['clarification', '¿Podés precisar qué concepto querés revisar?', 'NEEDS_CLARIFICATION'],
  ]) {
    const restoreFetch = installSseResponse([
      manifest(code),
      {
        event_type: eventType,
        payload: { abstained: true, reason: reply, abstention_code: code },
      },
    ]);
    try {
      const result = await chatService.sendQuery({ query: 'Consulta de prueba' });
      assert.equal(result.reply_text, reply);
      assert.equal(result.abstained, true);
      assert.equal(result.abstention_reason, code);
      assert.equal(result.clarification_requested, eventType === 'clarification');
    } finally {
      restoreFetch();
    }
  }
});

test('exercise evaluation preserves the certified IDs and exact attempt payload across a retry', async (t) => {
  const previousFetch = globalThis.fetch;
  const requests = [];
  globalThis.fetch = async (url, init) => {
    requests.push({ url, body: JSON.parse(init.body) });
    return new Response(JSON.stringify({
      status: 'GRADED',
      exercise_id: 'exercise-certified-1',
      is_correct: true,
      p_L: 0.6,
      was_idempotent_replay: requests.length === 2,
    }), { status: 200, headers: { 'content-type': 'application/json' } });
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  const request = {
    exercise_id: 'exercise-certified-1',
    user_answer: 'answer preserved exactly',
    notebook_id: 'notebook-synthetic',
    session_id: 'session-synthetic',
    episode_id: 'episode-synthetic',
    attempt_id: 'attempt-stable-1',
  };
  const first = await chatService.evaluateExercise(request);
  const replay = await chatService.evaluateExercise(request);

  assert.equal(first.status, 'GRADED');
  assert.equal(replay.was_idempotent_replay, true);
  assert.equal(requests.length, 2);
  assert.equal(requests[0].url, '/api/chat/evaluate');
  assert.deepEqual(requests[0].body, request);
  assert.deepEqual(requests[1].body, requests[0].body);
});

test('new logical exercise attempts receive distinct stable UUID identities', () => {
  const firstAttempt = createExerciseAttemptId();
  const nextAttempt = createExerciseAttemptId();
  assert.match(firstAttempt, /^[0-9a-f-]{36}$/i);
  assert.match(nextAttempt, /^[0-9a-f-]{36}$/i);
  assert.notEqual(firstAttempt, nextAttempt);
});

test('exercise evaluation surfaces an idempotency conflict without changing its request identity', async (t) => {
  const previousFetch = globalThis.fetch;
  const requestBodies = [];
  globalThis.fetch = async (_url, init) => {
    requestBodies.push(JSON.parse(init.body));
    return new Response(JSON.stringify({ detail: 'attempt_id ya fue usado con otro contenido.' }), {
      status: 409,
      headers: { 'content-type': 'application/json' },
    });
  };
  t.after(() => { globalThis.fetch = previousFetch; });

  const request = {
    exercise_id: 'exercise-certified-1', user_answer: 'first answer',
    notebook_id: 'notebook-synthetic', session_id: 'session-synthetic', attempt_id: 'attempt-fixed',
  };
  await assert.rejects(
    chatService.evaluateExercise(request),
    (error) => error instanceof ExerciseEvaluationError && error.statusCode === 409,
  );
  assert.deepEqual(requestBodies, [request]);
});

test('exercise evaluation retains server UNGRADED as a non-success outcome', async (t) => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({
    status: 'UNGRADED', exercise_id: 'exercise-certified-1', is_correct: null,
    detail: 'Sesión no verificable.',
  }), { status: 200, headers: { 'content-type': 'application/json' } });
  t.after(() => { globalThis.fetch = previousFetch; });

  const result = await chatService.evaluateExercise({
    exercise_id: 'exercise-certified-1', user_answer: 'answer', notebook_id: 'notebook-synthetic',
    session_id: 'session-synthetic', attempt_id: 'attempt-fixed',
  });
  assert.equal(result.status, 'UNGRADED');
  assert.equal(result.is_correct, null);
});

test('preserves an error event that supplies only a public reason', async (t) => {
  const publicReason = 'TALOS no pudo completar la respuesta. Reintentá la consulta.';
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const restoreFetch = installSseResponse([
    { event_type: 'error', payload: { reason: publicReason } },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.message === publicReason,
  );
  assert.equal(timers.activeCount(), 0);
});

test('classifies an internal timeout during SSE reading as timeout', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const pendingStream = installPendingSseResponse();
  t.after(pendingStream.restore);

  const request = chatService.sendQuery({ query: 'Consulta sintética' });
  await pendingStream.readStarted;
  timers.fireNext();

  await assert.rejects(
    request,
    (error) =>
      error.name !== 'QueryAbortedError' &&
      error.name !== 'AbortError' &&
      error.message === 'Tiempo de espera agotado (45s sin actividad). El servidor TALOS no respondió.',
  );
  assert.equal(timers.activeCount(), 0);
});

test('accepts progress heartbeat events emitted before completion', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    {
      event_type: 'progress',
      payload: { stage: 'auditing', elapsed_ms: 1200, message: 'La verificación S4.4 sigue en curso.' },
    },
    { event_type: 'audit_verdict', payload: { verdict: 'APPROVED' } },
    { event_type: 'phase_token', payload: { token: 'Respuesta verificada.' } },
    { event_type: 'phase_complete', payload: { completed_phase: 'conceptual' } },
  ]);
  t.after(restoreFetch);

  const activities = [];
  const result = await chatService.sendQuery(
    { query: 'Consulta sintética' },
    undefined,
    undefined,
    (activity) => activities.push(activity),
  );

  assert.equal(result.reply_text, 'Respuesta verificada.');
  assert.equal(activities.length, 1);
  assert.equal(activities[0].stage, 'auditing');
  assert.equal(activities[0].elapsedMs, 1200);
});

test('progress activity resets the inactivity deadline instead of abandoning the request', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const previousFetch = globalThis.fetch;
  let controller;
  const stream = new ReadableStream({ start(c) { controller = c; } });
  globalThis.fetch = async () => new Response(stream, {
    headers: { 'content-type': 'text/event-stream' },
  });
  t.after(() => { globalThis.fetch = previousFetch; });

  const flush = () => new Promise((resolve) => setImmediate(resolve));
  const request = chatService.sendQuery({ query: 'Consulta sintética' });
  await flush();
  await flush();

  const activeInactivity = () => timers.scheduled()
    .filter((timer) => !timer.cleared && timer.delay === 45000).length;
  assert.equal(activeInactivity(), 1);

  controller.enqueue(new TextEncoder().encode(
    'data: {"event_type":"progress","payload":{"stage":"auditing"}}\n\n',
  ));
  await flush();
  await flush();

  // The old inactivity timer was cleared and a fresh one armed; the generous
  // absolute cap remains in place.
  assert.equal(activeInactivity(), 1);
  assert.ok(timers.scheduled().some((timer) => timer.cleared && timer.delay === 45000));
  assert.equal(
    timers.scheduled().filter((timer) => !timer.cleared && timer.delay === 180000).length,
    1,
  );

  controller.enqueue(new TextEncoder().encode(
    'data: {"event_type":"phase_complete","payload":{"completed_phase":"conceptual"}}\n\n',
  ));
  controller.close();

  const result = await request;
  assert.equal(result.reply_text, 'Respuesta generada por TALOS.');
  assert.equal(timers.activeCount(), 0);
});

test('preserves explicit cancellation while an SSE read is pending', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const pendingStream = installPendingSseResponse();
  t.after(pendingStream.restore);
  const externalController = new AbortController();

  const request = chatService.sendQuery(
    { query: 'Consulta sintética' },
    undefined,
    externalController.signal,
  );
  await pendingStream.readStarted;
  externalController.abort();

  await assert.rejects(
    request,
    (error) => error.name === 'QueryAbortedError' &&
      error.message === 'Consulta abortada por el usuario',
  );
  assert.equal(timers.activeCount(), 0);
});

test('does not classify an unrelated AbortError as explicit user cancellation', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const previousFetch = globalThis.fetch;
  const stream = new ReadableStream({
    start(controller) {
      controller.error(new DOMException('synthetic transport abort', 'AbortError'));
    },
  });
  globalThis.fetch = async () => new Response(stream, {
    headers: { 'content-type': 'text/event-stream' },
  });
  t.after(() => {
    globalThis.fetch = previousFetch;
  });

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.name === 'Error' &&
      error.message === 'synthetic transport abort',
  );
  assert.equal(timers.activeCount(), 0);
});

test('explicit cancellation wins deterministically when it races with timeout', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const pendingStream = installPendingSseResponse();
  t.after(pendingStream.restore);
  const externalController = new AbortController();

  const request = chatService.sendQuery(
    { query: 'Consulta sintética' },
    undefined,
    externalController.signal,
  );
  await pendingStream.readStarted;
  timers.fireNext();
  externalController.abort();

  await assert.rejects(request, (error) => error.name === 'QueryAbortedError');
  assert.equal(timers.activeCount(), 0);
});

test('fails closed on unknown event types', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'future_event', payload: {} },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.message === 'La respuesta SSE contiene un tipo de evento no reconocido.',
  );
});

test('fails closed on malformed JSON in a data field', async (t) => {
  const restoreFetch = installSseResponse('data: {"event_type":\n\n');
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.message === 'La respuesta SSE contiene un payload de datos inválido.',
  );
});

test('fails closed on an event with a malformed payload shape', async (t) => {
  const restoreFetch = installSseResponse(
    'data: {"event_type":"phase_complete","payload":"not-an-object"}\n\n',
  );
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.message === 'La respuesta SSE contiene un evento con formato inválido.',
  );
});

test('ignores SSE framing fields while parsing data events', async (t) => {
  const restoreFetch = installSseResponse(
    ': heartbeat\nevent: phase_complete\nid: response-1\nretry: 1000\n' +
    'data: {"event_type":"phase_start","payload":{"phase":"conceptual"}}\n\n' +
    'data: {"event_type":"phase_complete","payload":{"completed_phase":"conceptual"}}\n\n',
  );
  t.after(restoreFetch);

  const result = await chatService.sendQuery({ query: 'Consulta de prueba' });
  assert.equal(result.reply_text, 'Respuesta generada por TALOS.');
});

test('returns a completed response and streams progress from the canonical event sequence', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const restoreFetch = installSseResponse([
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    { event_type: 'phase_token', payload: { token: 'Respuesta ' } },
    { event_type: 'phase_token', payload: { token: 'fundamentada.' } },
    {
      event_type: 'evidence_manifest',
      payload: {
        citations: [],
        facet_coverage: {},
        abstained: false,
      },
    },
    {
      event_type: 'phase_complete',
      payload: { completed_phase: 'conceptual' },
    },
  ]);
  t.after(restoreFetch);

  const progress = [];
  const result = await chatService.sendQuery(
    { query: 'Consulta de prueba' },
    (text) => progress.push(text),
  );
  assert.equal(result.reply_text, 'Respuesta fundamentada.');
  assert.equal(result.abstained, false);
  assert.deepEqual(progress, ['Respuesta ', 'Respuesta fundamentada.']);
  assert.equal(timers.activeCount(), 0);
});

test('preserves exact source, page, chunk and excerpt provenance from the SSE evidence manifest', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    { event_type: 'audit_verdict', payload: { verdict: 'APPROVED' } },
    { event_type: 'phase_token', payload: { token: 'El búfer [E1] separa productor y consumidor.' } },
    {
      event_type: 'evidence_manifest',
      payload: {
        citations: [{
          citation_id: 'E1', source_id: 'synthetic-source-a', source_title: 'Controlado A',
          document_id: 'synthetic-document-a',
          page_start: 7, page_end: 7, chunk_id: 'chunk-a-1',
          chunk_text: 'El búfer compartido separa productor y consumidor.',
          doc_hash: 'a'.repeat(64), namespace: 'E',
        }],
        facet_coverage: {}, abstained: false,
      },
    },
    { event_type: 'phase_complete', payload: { completed_phase: 'conceptual' } },
  ]);
  t.after(restoreFetch);

  const result = await chatService.sendQuery({ query: '¿Qué hace el búfer compartido?' });
  assert.equal(result.evidences.length, 1);
  assert.equal(result.evidences[0].citationId, 'E1');
  assert.equal(result.evidences[0].sourceId, 'synthetic-source-a');
  assert.equal(result.evidences[0].documentId, 'synthetic-document-a');
  assert.equal(result.evidences[0].pageStart, 7);
  assert.equal(result.evidences[0].pageEnd, 7);
  assert.equal(result.evidences[0].chunkId, 'chunk-a-1');
  assert.equal(result.evidences[0].chunkText, 'El búfer compartido separa productor y consumidor.');
  assert.equal(result.evidences[0].docHash, 'a'.repeat(64));
});

test('accepts the backend exercise proposal before phase completion', async (t) => {
  const exerciseProposal = {
    exercise_id: 'exercise-test',
    kc_id: 'KC-TEST',
    title: 'Ejercicio de práctica',
    prompt: 'Calculá la dirección del elemento i.',
    type: 'EXACT_TEXT',
    options: null,
    source: 'generated',
    source_hash: 'source-hash-from-backend',
  };
  const restoreFetch = installSseResponse([
    {
      event_type: 'phase_start',
      payload: { phase: 'conceptual', max_tokens: 800, code_allowed: false },
    },
    { event_type: 'phase_token', payload: { phase: 'conceptual', token: 'Respuesta final.' } },
    {
      event_type: 'audit_verdict',
      payload: { verdict: 'APPROVED', phase: 'conceptual' },
    },
    {
      event_type: 'evidence_manifest',
      payload: { citations: [], facet_coverage: {}, abstained: false },
    },
    {
      event_type: 'exercise_proposal',
      payload: exerciseProposal,
    },
    {
      event_type: 'phase_complete',
      payload: {
        completed_phase: 'conceptual',
        tokens_produced: 4,
        next_phases: ['pseudocode'],
        code_allowed: false,
        decision: { action: 'answer', message: 'Respuesta final.' },
        bkt_context: { kc_id: 'KC-TEST', context_mode: 'basic', p_L: 0.5 },
      },
    },
  ]);
  t.after(restoreFetch);

  const result = await chatService.sendQuery({ query: 'Consulta de prueba' });
  assert.equal(result.reply_text, 'Respuesta final.');
  assert.equal(result.bkt_context.kc_id, 'KC-TEST');
  assert.deepEqual(result.exercise_proposal, exerciseProposal);
});

test('returns an exercise proposal without generic text when it is the response', async (t) => {
  const exerciseProposal = {
    exercise_id: 'exercise-only',
    kc_id: 'KC-ONLY',
    title: 'Práctica principal',
    prompt: 'Elegí la opción correcta.',
    type: 'MC',
    options: ['A) Primera opción', 'B) Segunda opción'],
  };
  const restoreFetch = installSseResponse([
    {
      event_type: 'evidence_manifest',
      payload: { citations: [], facet_coverage: { exercise: 'KC-ONLY' }, abstained: false },
    },
    { event_type: 'exercise_proposal', payload: exerciseProposal },
    {
      event_type: 'phase_complete',
      payload: { completed_phase: 'conceptual', status: 'EXERCISE_PROPOSED' },
    },
  ]);
  t.after(restoreFetch);

  const result = await chatService.sendQuery({ query: 'Dame un ejercicio' });
  assert.equal(result.reply_text, '');
  assert.deepEqual(result.exercise_proposal, exerciseProposal);
});

test('rejects malformed exercise proposals instead of fabricating a display payload', async (t) => {
  const restoreFetch = installSseResponse([
    {
      event_type: 'exercise_proposal',
      payload: { exercise_id: 'missing-prompt' },
    },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Dame un ejercicio' }),
    (error) => error.message === 'La propuesta de ejercicio SSE tiene un formato inválido.',
  );
});

test('fails closed when EOF arrives without a terminal outcome', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    { event_type: 'phase_token', payload: { token: 'Respuesta parcial.' } },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    /sin un resultado terminal válido/,
  );
});

test('fails closed on an incomplete trailing data frame after a terminal event', async (t) => {
  const restoreFetch = installSseResponse(
    'data: {"event_type":"phase_complete","payload":{"completed_phase":"conceptual"}}\n\n' +
    'data: {"event_type":"phase_start","payload":{"phase":"next"}}',
  );
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.message === 'El stream SSE terminó con un evento de datos incompleto.',
  );
});

test('rejects truncation even when the backend later closes the phase', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    { event_type: 'phase_token', payload: { token: 'Respuesta parcial.' } },
    {
      event_type: 'truncated',
      payload: { message: 'La respuesta quedó truncada por límite de tokens.' },
    },
    { event_type: 'phase_complete', payload: { completed_phase: 'conceptual' } },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    /La respuesta quedó truncada por límite de tokens/,
  );
});

test('rejects duplicate terminal events', async (t) => {
  const restoreFetch = installSseResponse([
    { event_type: 'phase_start', payload: { phase: 'conceptual' } },
    { event_type: 'phase_complete', payload: { completed_phase: 'conceptual' } },
    { event_type: 'phase_complete', payload: { completed_phase: 'conceptual' } },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    /más de un cierre de fase/,
  );
});

test('rejects an error event after phase completion', async (t) => {
  for (const event of [
    { event_type: 'error', payload: { reason: 'Falló el cierre de la respuesta.' } },
    { event_type: 'truncated', payload: { message: 'Respuesta truncada.' } },
    { event_type: 'stream_aborted', payload: { message: 'Stream interrumpido.' } },
    {
      event_type: 'exercise_proposal',
      payload: { exercise_id: 'late-exercise' },
    },
  ]) {
    const restoreFetch = installSseResponse([
      { event_type: 'phase_start', payload: { phase: 'conceptual' } },
      { event_type: 'phase_complete', payload: { completed_phase: 'conceptual' } },
      event,
    ]);

    try {
      await assert.rejects(
        chatService.sendQuery({ query: 'Consulta de prueba' }),
        /evento no permitido después del cierre de fase/,
      );
    } finally {
      restoreFetch();
    }
  }
});

test('does not accept a completed phase when the stream errors before clean EOF', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const previousFetch = globalThis.fetch;
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(
        'data: {"event_type":"phase_start","payload":{"phase":"conceptual"}}\n\n' +
        'data: {"event_type":"phase_complete","payload":{"completed_phase":"conceptual"}}\n\n',
      ));
      controller.error(new Error('synthetic connection failure'));
    },
  });
  globalThis.fetch = async () => new Response(stream, {
    headers: { 'content-type': 'text/event-stream' },
  });
  t.after(() => {
    globalThis.fetch = previousFetch;
  });

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.name !== 'QueryAbortedError' &&
      error.message === 'synthetic connection failure',
  );
  assert.equal(timers.activeCount(), 0);
});

test('does not abort a completed request when its cleared timeout callback runs late', async (t) => {
  const timers = installFakeTimeouts();
  t.after(timers.restore);
  const previousFetch = globalThis.fetch;
  let requestSignal;
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(new TextEncoder().encode(
        'data: {"event_type":"phase_complete","payload":{"completed_phase":"conceptual"}}\n\n',
      ));
      controller.close();
    },
  });
  globalThis.fetch = async (_url, init) => {
    requestSignal = init.signal;
    return new Response(stream, { headers: { 'content-type': 'text/event-stream' } });
  };
  t.after(() => {
    globalThis.fetch = previousFetch;
  });

  const result = await chatService.sendQuery({ query: 'Consulta de prueba' });
  assert.equal(result.reply_text, 'Respuesta generada por TALOS.');
  assert.equal(timers.activeCount(), 0);
  timers.fireScheduled(0);
  assert.equal(requestSignal.aborted, false);
});
