import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import ts from 'typescript';
import path from 'node:path';

test('Vite dev and preview default to loopback without wildcard CORS or hosts', () => {
  const source = readFileSync(new URL('../vite.config.ts', import.meta.url), 'utf8');
  const compiled = ts.transpileModule(source, { compilerOptions: {
    module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022, esModuleInterop: true,
  } }).outputText;
  const module = { exports: {} };
  new Function('require', 'module', 'exports', '__dirname', compiled)((id) => {
    if (id === 'vite') return { defineConfig: (value) => value };
    if (id === '@vitejs/plugin-react') return () => ({});
    if (id === 'path') return path;
    throw new Error(id);
  }, module, module.exports, '/synthetic/ui');
  const config = module.exports.default;
  assert.equal(config.server.host, '127.0.0.1');
  assert.equal(config.preview.host, '127.0.0.1');
  assert.equal(config.server.strictPort, true);
  assert.equal(config.preview.strictPort, true);
  assert.deepEqual(config.server.allowedHosts, ['localhost', '127.0.0.1']);
  assert.deepEqual(config.server.cors.origin, ['http://localhost:5173', 'http://127.0.0.1:5173']);
  for (const proxy of Object.values(config.server.proxy)) assert.equal(proxy.target, 'http://127.0.0.1:8000');
});
