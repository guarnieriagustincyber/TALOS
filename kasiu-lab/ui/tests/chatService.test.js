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
const serviceRequire = (specifier) => {
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
const { chatService } = serviceModule.exports;

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

test('preserves an error event that supplies only a public reason', async (t) => {
  const publicReason = 'TALOS no pudo completar la respuesta. Reintentá la consulta.';
  const restoreFetch = installSseResponse([
    { event_type: 'error', payload: { reason: publicReason } },
  ]);
  t.after(restoreFetch);

  await assert.rejects(
    chatService.sendQuery({ query: 'Consulta de prueba' }),
    (error) => error.message === publicReason,
  );
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
});

test('accepts the backend exercise proposal before phase completion', async (t) => {
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
      payload: {
        exercise_id: 'exercise-test',
        kc_id: 'KC-TEST',
        exercise_type: 'practice',
      },
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
    /synthetic connection failure/,
  );
});
