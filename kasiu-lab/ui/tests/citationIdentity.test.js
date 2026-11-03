import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { test } from 'node:test';
import ts from 'typescript';

const source = await readFile(
  new URL('../src/presentation/features/chat/citationIdentity.ts', import.meta.url),
  'utf8',
);
const compiled = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const module = { exports: {} };
new Function('module', 'exports', compiled)(module, module.exports);
const { resolveCitationByTag } = module.exports;

test('binds only the exact namespaced citation identity, never ordinal position', () => {
  const evidence = [
    { citationId: 'E2', namespace: 'E', sourceId: 'doc-two' },
    { citationId: 'TF1', namespace: 'TF', sourceId: 'threat-feed' },
    { citationId: 'E1', namespace: 'E', sourceId: 'doc-one' },
  ];
  assert.equal(resolveCitationByTag('E1', evidence)?.sourceId, 'doc-one');
  assert.equal(resolveCitationByTag('TF1', evidence)?.sourceId, 'threat-feed');
  assert.equal(resolveCitationByTag('E3', evidence), undefined);
  assert.equal(resolveCitationByTag('1', evidence), undefined);
  assert.equal(resolveCitationByTag('LAB1', evidence), undefined);
});

test('rejects a manifest record whose namespace contradicts its identity', () => {
  assert.equal(
    resolveCitationByTag('E1', [{ citationId: 'E1', namespace: 'TF', sourceId: 'wrong' }]),
    undefined,
  );
});
