# TALOS_OPENCODE_TOOLCHAIN_AUDIT.md

**Auditoría read-only del toolchain OpenCode y skills para TALOS**  
Fecha: 2026-10-06  
Rama: `talos-current-audit` | HEAD: `713409f` (2026-10-06 02:41 -0300)  
Directorio: `/media/agustin/Laboratorio/study-engie`

---

## 1. Executive Summary

Auditoría completa del entorno de herramientas utilizado durante la preparación de OpenCode para TALOS. Se inspeccionaron sin modificar: binarios, configuraciones globales y del proyecto, MCP, plugins, skills TALOS, contratos transversales, Graphify, Ponytail, herramientas evaluadas, side effects y seguridad. Hallazgos clave:
- OpenCode CLI 1.18.34 y Desktop 1.18.31 operativos; sesiones de agent crean checkpoints git automáticos bajo `refs/agents/*` (569 refs, .git = 2.3 GB).
- context-mode v1.0.131 conectado y funcional (sirvió esta auditoría); tgrep removido de config con `ModuleNotFoundError` confirmado.
- 6 skills TALOS (`talos-audit`, `talos-evidence`, `talos-isolation`, `talos-pedagogy`, `talos-release`, `talos-testing`) presentes como `SKILL.md` en `.agents/skills/`, sin dependencias externas ni scripts.
- Graphify (`graphifyy` v0.9.77 via uv) instalado; plugin OpenCode en repo pero **sin artefactos en repo** (`graphify-out/` ausente); prueba AST-only en `/tmp/talos-graphify-test/` (1407 fuentes, 18896 nodos, 61250 aristas, 0 tokens LLM).
- Ponytail clonado en `/tmp/ponytail-review` (Hermes no instalado) — evaluación temporal sin integración.
- `.vscode/mcp.json` registra 3 MCPs (Sentry, Context7, Playwright) para VS Code, no para OpenCode.
- `AGENTS.md` untracked, sin literales `V3.1` ni `F-17` requeridos por contrato, con sección `## graphify` autoinyectada (mismo timestamp que plugin).
- `.env` 38 vars (gitignored); `auth.json` 4 proveedores (redactados). Sin secretos expuestos.

**Veredicto:** `AUDIT_COMPLETE — FINDINGS`

---

## 2. Environment Baseline

| Propiedad | Valor |
|-----------|-------|
| hostname | agustin-desktop |
| user | agustin |
| HOME | /home/agustin |
| SHELL | /bin/bash |
| Distro | Linux Mint 22.3 |
| Kernel | 7.0.0-38-generic |
| Arch | x86_64 |
| CPU | AMD Ryzen 5 5600GT (12 cores) |
| RAM | 13 GiB total / 7.3 GiB disponible |
| Python | 3.12.3 (/usr/bin/python3) |
| Git | 2.43.0 (/usr/bin/git) |
| Node | v20.20.2 (/usr/bin/node) |
| npm | 10.8.2 (/usr/bin/npm) |
| npx | 10.8.2 (/usr/bin/npx) |
| VS Code | 1.140.0 (/usr/bin/code) |
| OpenCode CLI | 1.18.34 (/home/agustin/.opencode/bin/opencode) |
| OpenCode Desktop | 1.18.31 (Electron 42.3.3, /opt/OpenCode, proceso activo) |

---

## 3. OpenCode

| Componente | Detalle |
|------------|---------|
| CLI binario | Único: `/home/agustin/.opencode/bin/opencode` |
| Versión CLI | 1.18.34 |
| Desktop binario | `/opt/OpenCode/ai.opencode.desktop` (Electron) |
| Versión Desktop | 1.18.31 (annotation de crashpad) |
| Desktop entries | `/usr/share/applications/ai.opencode.desktop.desktop`, `/usr/share/applications/opencode-desktop.desktop`, `~/.local/share/applications/ai.opencode.desktop.desktop` |
| Storage global | `~/.local/share/opencode/` — `opencode.db` 111 MB, `auth.json` (mode 600, 4 keys), `snapshot/`, `storage/` |
| Duplicados PATH | Ninguno (`type -a opencode` → 1 entrada) |

---

## 4. Global Configuration

### `~/.config/opencode/` (63 MB)
- `opencode.jsonc` (188 B): MCP `context-mode` (`npx -y context-mode`, enabled)
- `opencode.jsonc.bak` (301 B): MCP `context-mode` + `tgrep` (`python3 -m tgrep`, enabled) — **configuración histórica con tgrep**
- `package.json`: `@opencode-ai/plugin` 1.18.34
- `node_modules/` (63 MB, deps del plugin)
- `context-mode/sessions/` — estado del MCP

### `~/.opencode/` (240 MB)
- `bin/opencode` (simlink/ejecutable)
- `package.json`: `@opencode-ai/plugin` 1.18.34
- `node_modules/` (240 MB)
- `plugins/` — **vacío**

### `auth.json` (SECRET_PRESENT = YES)
- Ubicación: `~/.local/share/opencode/auth.json`
- Permisos: 600
- Keys: `opencode`, `openrouter`, `nvidia`, `groq` (valores redactados)

---

## 5. TALOS Configuration (repo)

| Path | Contenido |
|------|-----------|
| `.opencode/opencode.json` (105 B) | `"plugin": [".opencode/plugins/graphify.js"]` — **sin MCP** |
| `.opencode/plugins/graphify.js` | 1402 B, sha256 `ca230c9bcd12dce7cba5107e5ec751023bd1c3a34e920b348bf2c7f9d79f0ccd` — hook `tool.execute.before` que prependa recordatorio si existe `graphify-out/graph.json` (hoy inactivo) |
| `.opencode/package.json` | `@opencode-ai/plugin` 1.18.34 |
| `.agents/skills/` | 6 skills TALOS (ver §6) |
| `AGENTS.md` | 36 044 B, sha256 `3df804ed3049fd963aaf5b1d4f2fb19f8ea8b0f15c2124ff36bd274e4066b9bf`, **untracked**, mtime 2026-10-06 14:05:12 |
| `docs/architecture/` | `CROSS-SKILL-CONTRACT-V3.1.md` (5915 B, untracked) + 9 docs más |

---

## 6. Skills TALOS

| Skill | Path | Tamaño | SHA256 (truncado) | H1 Title | Referencias externas |
|-------|------|--------|-------------------|----------|----------------------|
| talos-audit | `.agents/skills/talos-audit/SKILL.md` | 14 225 B | e67333d2f2... | `# TALOS — \`talos-audit\`` | 0 |
| talos-evidence | `.agents/skills/talos-evidence/SKILL.md` | 15 060 B | 28cb95b469... | `# TALOS — \`talos-evidence\`` | 0 |
| talos-isolation | `.agents/skills/talos-isolation/SKILL.md` | 14 157 B | 37d1320c12... | `# TALOS — \`talos-isolation\`` | 0 |
| talos-pedagogy | `.agents/skills/talos-pedagogy/SKILL.md` | 13 142 B | f8c470f200... | `# TALOS — \`talos-pedagogy\`` | 0 |
| talos-release | `.agents/skills/talos-release/SKILL.md` | 13 116 B | a02eb7cff2... | `# TALOS — \`talos-release\`` | 0 |
| talos-testing | `.agents/skills/talos-testing/SKILL.md` | 13 515 B | e9f52cd509... | `# TALOS — \`talos-testing\`` | 0 |

- Cada skill: **un solo archivo `SKILL.md`**, sin scripts, sin archivos auxiliares, sin referencias a MCP/plugins/herramientas externas (`ext-refs: 0`).
- Autoridad declarada: según `SKILL_INTERFACE` interno (Produce/Consume/Puede decidir/No puede decidir).
- Ejecutables por runtime de agente (LLM sigue instrucciones); no requieren toolchain adicional.

---

## 7. Cross-Skill Contract

**Archivo:** `docs/architecture/CROSS-SKILL-CONTRACT-V3.1.md` (5915 B, untracked)

### Cobertura
Define normalizaciones obligatorias para las 6 skills + AGENTS.md:
- Contradicciones cross-skill → `talos-audit` (§1)
- Tipos canónicos `ISOLATION_VERDICT`, `BOUNDARY_STATUS`, `TEST_EXECUTION_RESULT`, `EVALUATION_RECORD`, `EVIDENCE_REF`, `PROVENANCE_RECORD`, `EVIDENCE_LINEAGE` (§2–4)
- Taxonomía `DATA_ORIGIN`/`PROVENANCE`/`USAGE_ROLE` (§5)
- Estados release `RELEASE_ELIGIBLE*`, `GATE_WAIVED ≠ GATE_SATISFIED`, `UNKNOWN ≠ PASS` (§6)
- F-17 `META-VERIFICATION IS BOUNDED` (§7)
- Regla anti-duplicación (§8)
- Condición de cierre 13 puntos (§10)

### Coherencia con skills
- Skills no duplican el contrato (cumplen §8: definen `PROCEDURE`, `DOMAIN-SPECIFIC CHECKS`, `OUTPUTS`, `LIMITATIONS`, `COMPLETION CRITERIA`).
- Sin dependencias circulares detectadas.
- Sin referencias a herramientas inexistentes en skills.

### AGENTS.md vs Contrato (DOCUMENTED vs ACTUALLY ENFORCED)
| Requisito §7 Contrato | Presente en AGENTS.md literal |
|----------------------|-------------------------------|
| `CROSS-SKILL CONTRACT VERSION = V3.1` | **NO** |
| `F-17: META-VERIFICATION IS BOUNDED` | **NO** (semántica en §3/§11.2/§14.5) |
| `CROSS-SKILL CONTRADICTION → talos-audit owns adjudication` | Sí (§11.2) |
| `GATE_WAIVED ≠ GATE_SATISFIED` | Sí implícito (§14.5 estados; línea 1028 `GATE_WAIVED` existe) |
| `UNKNOWN ≠ PASS` | Sí (§3 tabla conversiones prohibidas) |
| `AGENT_GENERATED ≠ REAL_STUDENT_PERFORMANCE` | Sí (§3/§19.2/§19.3) |
| `TEST_FIXTURE ≠ PRODUCTION_DATA` | Sí (§19.2/§19.3) |

**Hallazgo:** Contrato **DOCUMENTED**; enforcement es conductual (agente sigue SKILL.md). No existe mecanismo técnico de control (registry, gates automatizados). AGENTS.md incorpora semántica pero omite marcadores literales `V3.1`/`F-17`.

---

## 8. context-mode

| Atributo | Valor |
|----------|-------|
| Versión | 1.0.131 (npx cache `16b0a7c005a6df70`) |
| Método instalación | npx (cache local) |
| Registro MCP | `~/.config/opencode/opencode.jsonc` → `"context-mode": { "type": "local", "command": ["npx","-y","context-mode"], "enabled": true }` |
| Estado conexión | **Conectado** — esta sesión usa sus tools (`ctx_batch_execute`, `ctx_doctor`, etc.) |
| Herramientas expuestas | `ctx_execute`, `ctx_batch_execute`, `ctx_search`, `ctx_index`, `ctx_fetch_and_index`, `ctx_execute_file`, `ctx_doctor`, `ctx_stats`, `ctx_upgrade`, `ctx_purge`, `ctx_insight` |
| Dependencias | Node + npx; runtimes: javascript, shell, python, ruby, rust, perl (6/11) |
| tgrep | **Removido** de config vigente; estaba en `opencode.jsonc.bak`. `python3 -c "import tgrep"` → `ModuleNotFoundError: No module named 'tgrep'` **CONFIRMADO** |
| Doctor | Runtimes OK, Server PASS, FTS5 PASS, Hooks scripts PASS, **PreToolUse hook FAIL** (falta `~/.claude/settings.json` — hook específico de Claude Code), Version outdated (1.0.169 disponible) |
| Clasificación | **WORKING** (operativo para OpenCode); tgrep = BROKEN (histórico) |

---

## 9. Graphify

| Atributo | Valor |
|----------|-------|
| Paquete | `graphifyy` v0.9.77 (PyPI, doble 'y') |
| Instalación | `uv tool install graphifyy` (uv 0.12.23) |
| Binarios | `~/.local/bin/graphify`, `~/.local/bin/graphify-mcp` |
| Plugin OpenCode | `.opencode/plugins/graphify.js` (registrado en `.opencode/opencode.json`) |
| Artefactos en repo | **NINGUNO** — `graphify-out/` **no existe** en repo (`find` sin resultados) |
| Artefactos fuera de repo | `/tmp/talos-graphify-test/graphify-out/` (56 MB, mtime 2026-10-06 13:28) |
| — graph.json | 28.8 MB, keys: `nodes` (18896), `edges` (61250), `hyperedges` (0), `input_tokens`=0, `output_tokens`=0, `extracted_sources`=1407 |
| — manifest.json | 1406 claves (archivos procesados) |
| — GRAPH_REPORT.md / wiki | **Ausentes** |
| Números declarados vs reales | 1407 archivos (extracted_sources ✅), 18896 nodos ✅, 61250 aristas ✅, **0 tokens LLM** ✅ (AST-only) |
| Sección en AGENTS.md | Autoinyectada (líneas 1986–1997), mismo timestamp que plugin (14:05:12) |
| Dependencia de código TALOS | **NINGUNA** — `grep -rIl graphify src tests benchmark` → vacío |
| Clasificación | **EVALUATED_ONLY** (plugin SIDE_EFFECT en config; sin artefactos ni dependencia de producto) |

---

## 10. Ponytail

| Atributo | Valor |
|----------|-------|
| Ubicación | `/tmp/ponytail-review/` (git repo, 29 entradas) |
| Origen | `https://github.com/DietrichGebert/ponytail.git` |
| Objetivo | Plugin para **Hermes** (gateway/agent) — `hermes plugins enable ponytail` |
| Hermes instalado | **NO** (`command -v hermes` → no encontrado) |
| Integración OpenCode | `opencode.json` vacío placeholder; sin hooks/plugins activos |
| Archivos notables | `after-install.md`, `AGENTS.md` (2.5 KB), `.claude-plugin/`, `.clinerules/`, `skills/`, `hooks/`, `commands/` |
| Clasificación | **EVALUATED_ONLY + SIDE_EFFECT_ONLY** (artefacto temporal en `/tmp`, sin función actual) |

---

## 11. Herramientas Evaluadas

| Herramienta | Instalado | Configurado | Conectado | Operativo | Usado por TALOS | Estado |
|-------------|-----------|-------------|-----------|-----------|-----------------|--------|
| OpenCode CLI | ✅ | ✅ | ✅ | ✅ | Tooling | CANONICAL |
| OpenCode Desktop | ✅ | ✅ | ✅ | ✅ | Tooling | CANONICAL |
| context-mode (MCP) | ✅ (npx) | ✅ (global) | ✅ | ✅ | Auditoría (esta sesión) | OPERATIONAL |
| Graphify (CLI+MCP) | ✅ (uv) | ✅ (plugin repo) | ❌ | ❌ (sin graphify-out en repo) | No | EVALUATED_ONLY |
| tgrep (MCP histórico) | ❌ | ⚠️ (solo .bak) | ❌ | ❌ | No | BROKEN |
| Ponytail | ⚠️ (/tmp clone) | ❌ | ❌ | ❌ | No | EVALUATED_ONLY + SIDE_EFFECT_ONLY |
| VS Code MCPs (3) | ✅ (npx cache) | ✅ (.vscode/mcp.json) | ⚠️ (VS Code scope) | ⚠️ | No (VS Code) | OPTIONAL |
| CodeQL | ❌ | ❌ | ❌ | ❌ | No | UNKNOWN |
| Playwright | ✅ (.venv 1.63.0) | ✅ (venv + VS Code MCP) | ✅ (browsers cached) | ✅ | No | PARTIAL (package OK; browser binarios presentes) |
| Repomix | ✅ (npm global 1.14.0) | ❌ | ❌ | ✅ | No | OPTIONAL |
| Aider | ✅ (.venv 0.86.2) | ❌ | ❌ | ✅ | No | OPTIONAL |
| Ruff | ✅ (.venv 0.16.10) | ⚠️ (no en pyproject) | ❌ | ✅ | No | OPTIONAL |
| Pyright | ✅ (.venv 1.1.414) | ⚠️ (no en pyproject) | ❌ | ✅ | No | OPTIONAL |
| pytest | ✅ (.venv 9.1.1) | ✅ (pyproject dev) | ✅ (testpaths=tests) | ✅ | **Sí** (runner tests) | CANONICAL |
| pre-commit | ❌ | ❌ | ❌ | ❌ | No | REJECTED |
| Semgrep | ✅ (.venv 1.179.0) | ⚠️ (no en pyproject) | ❌ | ✅ | No | OPTIONAL |
| Bandit | ✅ (.venv 1.9.4) | ⚠️ (no en pyproject) | ❌ | ✅ | No | OPTIONAL |
| pip-audit | ✅ (.venv) | ⚠️ (no en pyproject) | ❌ | ✅ | No | OPTIONAL |
| Gitleaks | ✅ (/usr/local/bin 8.30.0) | ❌ | ❌ | ✅ | No | OPTIONAL |
| GitHub Actions | ❌ | ❌ | ❌ | ❌ | No | REJECTED (no workflows) |
| Mem0 / Claude-Mem | ❌ | ❌ | ❌ | ❌ | No | UNKNOWN |
| CrewAI / AutoGen | ❌ | ❌ | ❌ | ❌ | No | UNKNOWN |
| Husky | ❌ | ❌ | ❌ | ❌ | No | REJECTED |

**Leyenda estados:** `CANONICAL` = parte del flujo canónico; `OPERATIONAL` = funcional y usado; `OPTIONAL` = instalado/operativo pero no requerido; `EVALUATED_ONLY` = probado/evaluado sin integración; `REJECTED` = descartado/ausente intencionalmente; `PARTIAL` = funcionalidad parcial; `BROKEN` = roto/no funciona; `UNKNOWN` = sin evidencia de decisión; `SIDE_EFFECT_ONLY` = solo efecto secundario.

---

## 12. Dependencies Matrix

| Componente | TALOS requiere | OpenCode requiere | Opcional | Realmente usado |
|------------|----------------|-------------------|----------|-----------------|
| OpenCode CLI | ❌ | — | ✅ | ✅ (tooling) |
| OpenCode Desktop | ❌ | — | ✅ | ✅ (tooling) |
| context-mode | ❌ | ✅ (MCP activo) | ✅ | ✅ (esta auditoría) |
| Graphify | ❌ | ❌ | ✅ | ❌ (plugin inactivo) |
| Ponytail | ❌ | ❌ | ❌ | ❌ |
| Skills TALOS | ✅ (normativa) | ❌ | ❌ | ✅ (agent runtime) |
| MCP context-mode | ❌ | ✅ | ✅ | ✅ |
| pytest | ✅ (tests) | ❌ | ❌ | ✅ |
| .venv dev tools | ⚠️ (parcial) | ❌ | ✅ | ⚠️ (solo pytest en pyproject) |

> "Inferir 'required' desde documentación solamente" → **no se hizo**. Solo pytest y skills son dependencias reales de TALOS.

---

## 13. MCP Inventory

| Nombre | Ubicación | Transporte | Comando | Estado | Uso real | TALOS depende |
|--------|-----------|------------|---------|--------|----------|---------------|
| context-mode | `~/.config/opencode/opencode.jsonc` | stdio (npx) | `npx -y context-mode` | **CONNECTED** | Sí (esta sesión) | No |
| tgrep (histórico) | `~/.config/opencode/opencode.jsonc.bak` | stdio (python) | `python3 -m tgrep` | **REMOVIDO/BROKEN** | No | No |
| graphify-mcp | `~/.local/bin/graphify-mcp` | stdio | `graphify-mcp` | **UNREGISTERED** | No | No |
| sentry-mcp | `.vscode/mcp.json` | stdio (npx) | `npx @sentry/mcp-server@0.42.0` | CONFIGURED (VS Code) | No | No |
| context7 | `.vscode/mcp.json` | stdio (npx) | `npx @upstash/context7-mcp@4.1.1` | CONFIGURED (VS Code) | No | No |
| playwright-mcp | `.vscode/mcp.json` | stdio (npx) | `npx @playwright/mcp@latest` | CONFIGURED (VS Code) | No | No |

**npx caches (evidencia de ejecución previa):** `create-vite`, `context-mode@1.0.131`, `@upstash/context7-mcp@4.1.1`, `@playwright/mcp@0.0.83`, `@sentry/mcp-server@0.42.0`. Solo `context-mode` registrado en OpenCode actual.

---

## 14. Plugins

| Plugin | Origen | Scope | Función | Estado |
|--------|--------|-------|---------|--------|
| `@opencode-ai/plugin` 1.18.34 | npm | Global (`~/.config/opencode` + `~/.opencode` + repo `.opencode`) | Core plugin OpenCode | CANONICAL |
| `graphify.js` | Repo local (1402 B) | Repo `.opencode/plugins/` | Hook `tool.execute.before` → echo recordatorio si `graphify-out/graph.json` existe | CONFIGURED / INERT (condición falsa) |

VS Code extensions: `code --list-extensions` → **ninguna** de `continue|cline|roo|copilot|codeql|graphify|opencode|aider|semgrep`.

---

## 15. Hooks y Automatización

| Tipo | Hallazgo |
|------|----------|
| Git hooks (`.git/hooks/`) | **Ninguno activo** (solo `.sample`) |
| Husky | No instalado / sin `.husky/` |
| OpenCode hooks | Plugin `graphify.js` → `tool.execute.before` (único) |
| Agent checkpoints | **569 refs** bajo `refs/agents/<uuid>/checkpoints/turn/N` creados automáticamente por OpenCode Desktop/CLI (commit `c0b4f8e` 2026-10-06 12:55 incluye `.agents/`, `AGENTS.md`, `.env.example`, etc.) — **modifica .git automáticamente** |
| Cron / systemd user | Ninguno relacionado |
| Servicios persistentes | OpenCode Desktop corriendo (4 procesos) |
| `.vscode/mcp.json` | 3 MCPs (promptString secrets) — workspace VS Code |

**Riesgo:** Checkpoints de agente escriben commits y refs en `.git` sin intervención del usuario (side effect documentado).

---

## 16. Seguridad

| Elemento | Hallazgo |
|----------|----------|
| `~/.local/share/opencode/auth.json` | **SECRET_PRESENT = YES** — 4 keys (opencode, openrouter, nvidia, groq), mode 600, valores redactados |
| `.env` (repo) | **SECRET_PRESENT = YES** — 38 vars (OPENAI, ANTHROPIC, GROQ, GEMINI, NVIDIA, CEREBRAS, SAMBANOVA, CLOUDFLARE, XKIRO, OLLAMA, etc.), gitignored (línea 26 `.gitignore`: `.env`) |
| `.env.example` | 13 keys (plantilla, sin valores) |
| Patrones secretos en config dirs | Solo falsos positivos en `node_modules/effect` (nombres de variables tipo `apiKey`) — **sin secretos reales** |
| `~/.claude/settings.json` | **AUSENTE** (causa FAIL hook PreToolUse context-mode) |
| Secretos en código | No detectados (grep de patrones `sk-`, `ghp_`, `AIza`, `BEGIN PRIVATE KEY` → solo node_modules) |

---

## 17. Reproducibilidad

| Componente | Reproducible | Evidencia |
|------------|--------------|-----------|
| Python deps (prod) | ✅ | `pyproject.toml` (pydantic, fastapi, uvicorn, numpy, pymupdf, etc.) |
| Python deps (dev) | ⚠️ PARCIAL | `pyproject.toml` declara `pytest, pytest-cov, black, flake8, mypy`; **falta** `ruff, pyright, semgrep, bandit, pip-audit, playwright, aider` (instalados manualmente en .venv) |
| Lockfile | ✅ | `requirements.lock` (90 KB, 2024-09-29) — pinned |
| Node deps global (opencode plugin) | ⚠️ | `package-lock.json` en `~/.config/opencode` y `~/.opencode` (sin lock global npm) |
| Graphify | ⚠️ | `uv tool list` muestra `graphifyy v0.9.77` (pinned por uv) |
| Repomix | ⚠️ | npm global `repomix@1.14.0` (sin lock) |
| VS Code MCPs | ⚠️ | `.vscode/mcp.json` pinea sentry@0.42.0, context7@4.1.1; playwright@latest **sin pin** |
| OpenCode binarios | ❌ | Instalador propietario (sin versión declarada en repo) |
| uv | ✅ | `uv 0.12.23` (binario en ~/.local/bin) |

---

## 18. Integridad TALOS

| Check | Resultado |
|-------|-----------|
| `git status --porcelain` | 4 líneas untracked: `.agents/`, `.opencode/`, `AGENTS.md`, `docs/architecture/` |
| Tracked modifications | **NINGUNA** |
| HEAD | `713409f792b9774aae65bf90a7fc0ab296638453` (2026-10-06 02:41:43 -0300) "audit: publish current TALOS state" |
| Branch | `talos-current-audit` |
| Stash | Vacío |
| Untracked dirs sizes | `.agents/` 128 KB, `.opencode/` 63 MB, `docs/architecture/` 12 KB |
| Commit extraño `c0b4f8e` | Agent checkpoint (refs/agents/*), no en branch actual |
| `.git` size | 2.3 GB (inflado por 569 checkpoints de agente) |

**Auditoría no modificó** código, tests, corpus, BD, modelos, checkpoints, reports, gates, docs canónicas. Solo se crea este reporte (nuevo untracked).

---

## 19. Final Matrix (resumen §20)

| Herramienta | Instalado | Configurado | Conectado | Operativo | Usado por TALOS | Dependencia | Estado |
|-------------|-----------|-------------|-----------|-----------|-----------------|-------------|--------|
| OpenCode CLI | ✅ | ✅ | ✅ | ✅ | Tooling | ❌ | CANONICAL |
| OpenCode Desktop | ✅ | ✅ | ✅ | ✅ | Tooling | ❌ | CANONICAL |
| context-mode MCP | ✅ | ✅ | ✅ | ✅ | Auditoría | ❌ | OPERATIONAL |
| Graphify CLI/MCP | ✅ | ✅ (plugin) | ❌ | ❌ | ❌ | ❌ | EVALUATED_ONLY |
| tgrep MCP | ❌ | ⚠️ (.bak) | ❌ | ❌ | ❌ | ❌ | BROKEN |
| Ponytail | ⚠️ (/tmp) | ❌ | ❌ | ❌ | ❌ | ❌ | EVALUATED_ONLY + SIDE_EFFECT_ONLY |
| Skills TALOS (6) | ✅ | ✅ | — | ✅ (instrucciones) | ✅ (normativa) | ✅ | CANONICAL |
| AGENTS.md | ✅ (repo) | ✅ | — | ✅ | ✅ | ✅ | CANONICAL (untracked) |
| Cross-Skill Contract | ✅ | ✅ | — | ✅ (doc) | ✅ | ✅ | CANONICAL (untracked) |
| VS Code MCPs (3) | ✅ | ✅ (.vscode) | ⚠️ (VS Code) | ⚠️ | ❌ | ❌ | OPTIONAL |
| pytest | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | CANONICAL |
| ruff/pyright/semgrep/bandit/pip-audit/playwright/aider/black/mypy/flake8 | ✅ (.venv) | ⚠️ (parcial pyproject) | ✅ | ✅ | ❌ | ❌ | OPTIONAL |
| gitleaks | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | OPTIONAL |
| repomix | ✅ (npm global) | ❌ | ❌ | ✅ | ❌ | ❌ | OPTIONAL |
| CodeQL / pre-commit / Husky / GitHub Actions / Mem0 / CrewAI / AutoGen | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | REJECTED / UNKNOWN |

---

## 20. Findings (Hallazgos)

1. **tgrep MCP roto/removido** — configurado en `opencode.jsonc.bak`, módulo Python ausente (`ModuleNotFoundError` reproducido). Dejado como basura histórica.
2. **Graphify sin artefactos en repo** — plugin configurado y sección AGENTS.md inyectada, pero `graphify-out/` no existe en working tree; única ejecución comprobada en `/tmp/talos-graphify-test/` (hoy 13:28).
3. **AGENTS.md untracked y sin marcadores V3.1/F-17 literales** — semántica del contrato presente pero marcadores explícitos ausentes.
4. **OpenCode agent checkpoints** — 569 refs `refs/agents/*` creados automáticamente (2.3 GB en `.git`); side effect no documentado que modifica `.git`.
5. **Desktop vs CLI version skew** — Desktop 1.18.31 vs CLI 1.18.34.
5. **VS Code MCPs** — 3 MCPs registrados solo en workspace VS Code (Sentry, Context7, Playwright), no en OpenCode; secrets via `promptString`.
6. **Herramientas dev fuera de pyproject** — ruff, pyright, semgrep, bandit, pip-audit, playwright, aider instalados en `.venv` sin declararse en `pyproject.toml` `[dev]`.
7. **`/home/agustin/AGENTS.md` NO EXISTE** — hipótesis de side effect de Graphify **refutada**.
8. **requirements.lock existe** (90 KB) pero pyproject dice "use requirements.lock" — lock presente, bien.
9. **CROSS-SKILL-CONTRACT-V3.1.md untracked** — igual que skills y AGENTS.md; capa normativa no versionada.
10. **Auth tokens en auth.json y .env** — presentes y gitignored correctamente; sin exposición.

---

## 21. Cleanup Candidates (candidatos a limpieza)

| Artefacto | Ubicación | Tipo | Acción sugerida |
|-----------|-----------|------|-----------------|
| Graphify test run | `/tmp/talos-graphify-test/` | SIDE_EFFECT | Eliminar (56 MB) |
| Ponytail review clone | `/tmp/ponytail-review/` | SIDE_EFFECT | Eliminar |
| opencode.jsonc.bak (con tgrep) | `~/.config/opencode/opencode.jsonc.bak` | HISTÓRICO | Archivar/eliminar |
| npx caches antiguos | `~/.npm/_npx/*` (5 dirs) | CACHE | `npx clear-cache` o borrar manual |
| `~/.claude/{backups,context-mode,sessions}` | `~/.claude/` | SIDE_EFFECT (hooks Claude) | Eliminar si no se usa Claude Code |
| `graphify.js` plugin + sección AGENTS.md | Repo `.opencode/plugins/` + AGENTS.md líneas 1986–1997 | CONFIGURACIÓN INERTE | Eliminar si Graphify se descarta |
| `.opencode/node_modules` (63 MB) + `~/.opencode/node_modules` (240 MB) | Directorios locales | CACHE RECREABLE | `rm -rf`; se regeneran con `opencode plugin install` |
| Agent checkpoints refs | `refs/agents/*` (569) | SIDE_EFFECT AUTOMÁTICO | Evaluar política de retención; `git for-each-ref --format='delete %(refname)' refs/agents/*` si no se necesitan |

---

## 22. Open Questions (preguntas abiertas)

1. ¿CodeQL fue descartado explícitamente o solo no instalado? (estado UNKNOWN)
2. ¿Por qué se removió tgrep del config? ¿Hay plan de reemplazo?
3. ¿Las skills y AGENTS.md deben commitearse en `main` o permanecer en branch de auditoría?
4. ¿El version skew Desktop 1.18.31 / CLI 1.18.34 es intencional?
5. ¿Los checkpoints de agente (`refs/agents/*`) son feature deseada o fuga de almacenamiento?
6. ¿Se piensa usar Graphify en flujo TALOS (ej. gates) o era solo evaluación?
7. ¿`pyproject.toml` dev deps deben actualizarse para incluir ruff/pyright/semgrep/bandit/pip-audit/playwright/aider?

---

## 23. Final Verdict

**AUDIT_COMPLETE — FINDINGS**