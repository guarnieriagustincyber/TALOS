import assert from 'node:assert/strict';
import { createRequire } from 'node:module';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';

const source = await readFile(
  new URL('../src/presentation/features/chat/ExerciseProposalCard.tsx', import.meta.url),
  'utf8',
);
const compiled = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2022,
    jsx: ts.JsxEmit.ReactJSX,
    esModuleInterop: true,
  },
}).outputText;
const componentModule = { exports: {} };
new Function('require', 'module', 'exports', compiled)(
  createRequire(import.meta.url),
  componentModule,
  componentModule.exports,
);
const { ExerciseProposalCard } = componentModule.exports;

test('renders the received exercise prompt and options without exposing answer metadata', () => {
  const proposal = {
    exercise_id: 'exercise-visible',
    kc_id: 'KC-VISIBLE',
    title: 'Consigna del backend',
    prompt: 'Seleccioná la opción respaldada por el material.',
    type: 'MC',
    options: ['A) Primera opción', 'B) Segunda opción'],
    source: 'generated',
    expected_answer: 'B',
  };

  const markup = renderToStaticMarkup(React.createElement(ExerciseProposalCard, { proposal }));

  assert.match(markup, /Ejercicio propuesto/);
  assert.match(markup, /Consigna del backend/);
  assert.match(markup, /Seleccioná la opción respaldada por el material\./);
  assert.match(markup, /A\) Primera opción/);
  assert.match(markup, /B\) Segunda opción/);
  assert.match(markup, /KC: KC-VISIBLE/);
  assert.doesNotMatch(markup, /expected_answer|>B</);
  assert.match(markup, /Tu respuesta/);
  assert.match(markup, /falta una sesión de estudio persistida/);
});

test('renders a blocked incomplete attempt without offering a new identity or resubmission', () => {
  const proposal = {
    exercise_id: 'exercise-visible', prompt: 'Consigna sintética', type: 'NUMERIC',
  };
  const attempt = {
    attemptId: 'attempt-stable', answer: 'respuesta enviada', status: 'INCOMPLETE',
    message: 'El intento quedó incompleto',
  };
  const markup = renderToStaticMarkup(React.createElement(ExerciseProposalCard, {
    proposal,
    context: { sessionId: 'session-synthetic', notebookId: 'notebook-synthetic', episodeId: 'episode-synthetic' },
    attempt,
    onRetry: () => {},
    onNewAttempt: () => {},
  }));

  assert.match(markup, /attempt-stable/);
  assert.match(markup, /quedó incompleto/);
  assert.doesNotMatch(markup, /Reintentar el mismo intento|Comenzar un intento nuevo|Enviar respuesta/);
});

// --- H2-A (autorización propietaria 2026-10-21): presentación de resultados
// no admisibles. Regla: academic_admission.admissible === false tiene
// precedencia visual sobre is_correct (true o false): estado neutral, sin
// afirmación de corrección o fracaso académico. ---

test('H2-A: pase no admisible (is_correct=true) se presenta como corrección no concluyente', () => {
  const proposal = { exercise_id: 'ex-gen-1', prompt: 'Consigna sintética', type: 'NUMERIC' };
  const attempt = {
    attemptId: 'attempt-h2a-pass', answer: 'x=10 (esperado x=1)', status: 'GRADED',
    result: {
      status: 'GRADED', exercise_id: 'ex-gen-1', is_correct: true,
      academic_admission: { admissible: false, reason: 'state_match: comparación por subcadena no inequívoca' },
    },
  };
  const markup = renderToStaticMarkup(React.createElement(ExerciseProposalCard, {
    proposal, context: { sessionId: 's1', notebookId: 'nb1' }, attempt,
  }));
  assert.match(markup, /Corrección automática no concluyente/);
  assert.match(markup, /no puede\s+acreditar la corrección conceptual/);
  assert.match(markup, /no modifica tu progreso académico/);
  assert.doesNotMatch(markup, /Respuesta correcta\.|Respuesta incorrecta\./);
  assert.doesNotMatch(markup, /text-emerald-300/);
  // No filtrar internals del backend (reason no se renderiza)
  assert.doesNotMatch(markup, /subcadena/);
});

test('H2-A: fallo no admisible (is_correct=false) tampoco afirma fracaso académico', () => {
  const proposal = { exercise_id: 'ex-gen-2', prompt: 'Consigna sintética', type: 'NUMERIC' };
  const attempt = {
    attemptId: 'attempt-h2a-fail', answer: 'respuesta faltante de keywords', status: 'GRADED',
    result: {
      status: 'GRADED', exercise_id: 'ex-gen-2', is_correct: false,
      academic_admission: { admissible: false, reason: 'keyword_coverage: cobertura léxica estructural' },
    },
  };
  const markup = renderToStaticMarkup(React.createElement(ExerciseProposalCard, {
    proposal, context: { sessionId: 's1', notebookId: 'nb1' }, attempt,
  }));
  assert.match(markup, /Corrección automática no concluyente/);
  assert.doesNotMatch(markup, /Respuesta correcta\.|Respuesta incorrecta\./);
});

test('H2-A: certificado/admisible conserva el feedback legítimo (verde/ámbar)', () => {
  const proposal = { exercise_id: 'ex-cert-1', prompt: 'Consigna sintética', type: 'NUMERIC' };
  const ok = {
    attemptId: 'a-ok', answer: '1012', status: 'GRADED',
    result: { status: 'GRADED', exercise_id: 'ex-cert-1', is_correct: true, delta_p_L: 0.7 },
  };
  const markupOk = renderToStaticMarkup(React.createElement(ExerciseProposalCard, {
    proposal, context: { sessionId: 's1', notebookId: 'nb1' }, attempt: ok,
  }));
  assert.match(markupOk, /Respuesta correcta\./);
  assert.doesNotMatch(markupOk, /no concluyente/);
});

test('H2-A: payload legado sin academic_admission mantiene compatibilidad', () => {
  const proposal = { exercise_id: 'ex-cert-2', prompt: 'Consigna sintética', type: 'NUMERIC' };
  const legacyFail = {
    attemptId: 'a-legacy', answer: '999', status: 'GRADED',
    result: { status: 'GRADED', exercise_id: 'ex-cert-2', is_correct: false },
  };
  const markup = renderToStaticMarkup(React.createElement(ExerciseProposalCard, {
    proposal, context: { sessionId: 's1', notebookId: 'nb1' }, attempt: legacyFail,
  }));
  assert.match(markup, /Respuesta incorrecta\./);
  assert.doesNotMatch(markup, /no concluyente/);
});

test('H2-A: historial de intentos no admisible muestra estado neutral', () => {
  const proposal = { exercise_id: 'ex-gen-3', prompt: 'Consigna sintética', type: 'NUMERIC' };
  const attempt = {
    attemptId: 'a-hist-now', answer: 'respuesta', status: 'GRADED',
    result: {
      status: 'GRADED', exercise_id: 'ex-gen-3', is_correct: true,
      academic_admission: { admissible: false, reason: 'bug_class: alias por subcadena' },
    },
  };
  const history = [
    { attemptId: 'a-hist-old', answer: 'anterior', status: 'GRADED',
      result: { status: 'GRADED', exercise_id: 'ex-gen-3', is_correct: false,
        academic_admission: { admissible: false, reason: 'contenido no admisible' } } },
  ];
  const markup = renderToStaticMarkup(React.createElement(ExerciseProposalCard, {
    proposal, context: { sessionId: 's1', notebookId: 'nb1' }, attempt, attemptHistory: history,
  }));
  assert.match(markup, /No concluyente \(sin efecto académico\)/);
  assert.doesNotMatch(markup, />"?Correcto<|>Correcto</);
});
