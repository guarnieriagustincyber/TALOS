# Checkpoint 053 — gate de autoridad de baseline spec

Fecha: 2026-10-01
Repositorio: `guarnieriagustincyber/TALOS`
HEAD de inicio: `f81134fc2293916210d53c8065f3a0049e52b0b4`

## 1. Decisión del gate

**Opción seleccionada: C — mantener autoridad irresuelta.**

`BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED`

`STOP_REASON = UNRESOLVED_PROVENANCE`

La selección de C es la decisión operativa explícita de este gate humano:
ninguna de las dos copias se utilizará como autoridad normativa mientras no
haya una instrucción que elija una autoridad operativa o evidencia nueva que
la demuestre. Se conserva el estado de parada de 051/052; no se elige por
tracking, ubicación, fecha, tamaño, completitud aparente ni similitud.

## 2. Evidencia resumida de 051/052

- `docs/A_PRE_0_BASELINE_SPEC.md` tiene SHA-256
  `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c`;
  actualmente está untracked y no está en el tree de HEAD.
- `files/A_PRE_0_BASELINE_SPEC.md` tiene SHA-256
  `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0`;
  está tracked en `main`.
- Los archivos son byte y semánticamente distintos. El primero se presenta
  como `SPECIFIED`; el segundo como `NOT READY` y añade secciones materiales
  de readiness, ledger, predicate, crosswalk y adjudicaciones.
- El ledger atribuye al path externo
  `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md` el hash
  SHA-256 `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4`
  y registra `present_in_qualified_overlay=false`.
- 052 no recuperó el artefacto `f058…` en la historia Git/local documental
  examinada; ninguna copia actual coincide con ese hash.

Estos hechos explican por qué el gate no puede cerrar provenance por sí
mismo; no prueban cuál copia debe ser autoridad.

## 3. Opciones consideradas

### Opción A — autoridad operativa de `files/`

Declarar la copia tracked en `files/` referencia operativa futura, sin
afirmar que sea históricamente idéntica al artefacto `f058…`.

Contrato si se seleccionara:

```text
BASELINE_SPEC_AUTHORITY = CANONICAL_FILES_COPY
AUTHORITY_REASON = HUMAN_OPERATIONAL_DECISION
HISTORICAL_IDENTITY_WITH_F058 = NOT_ESTABLISHED
```

No seleccionada en este gate.

### Opción B — autoridad operativa de `docs/`

Declarar la copia presente en `docs/` referencia operativa futura, sin
convertirla en tracked ni afirmar que sea históricamente idéntica al artefacto
`f058…`.

Contrato si se seleccionara:

```text
BASELINE_SPEC_AUTHORITY = CANONICAL_DOCS_COPY
AUTHORITY_REASON = HUMAN_OPERATIONAL_DECISION
HISTORICAL_IDENTITY_WITH_F058 = NOT_ESTABLISHED
```

No seleccionada en este gate.

### Opción C — mantener autoridad irresuelta

No utilizar ninguna copia como autoridad normativa, conservar
`STOP_REASON = UNRESOLVED_PROVENANCE` y dejar 048 bloqueado. Esta opción no
afirma autoridad operativa futura para `docs/` ni para `files/`.

## 4. Justificación explícita y límites históricos

La razón del gate es **no transformar el expediente de provenance en una
elección por conveniencia**: 052 demuestra dos textos locales distintos y un
tercer hash externo no recuperado, pero no aporta una declaración humana
previa que seleccione una referencia operativa entre A y B. Ante la ausencia
de esa instrucción, se registra C como decisión conservadora explícita de
este gate. Es una decisión de manejo actual, no una conclusión sobre la
intención histórica de los autores.

No se afirma:

- que `files/` sea históricamente canónica porque esté tracked;
- que `docs/` sea históricamente canónica por estar bajo `docs/`;
- que cualquiera de las copias sea más correcta por fecha, tamaño o
  contenido;
- que las dos copias sean duplicados;
- que alguna copia represente, derive de o sea históricamente idéntica al
  artefacto de SHA `f058…`;
- que `f058…` fuera recuperado o que su contenido haya sido reconstruido.

La situación de `f058…` permanece:

```text
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
HISTORICAL_IDENTITY_WITH_F058 = NOT_ESTABLISHED
```

La segunda variable se registra como límite del expediente, no como
declaración de identidad de una copia seleccionada (no se seleccionó A ni B).

## 5. Efecto sobre 048 y estados A-PRE

La autoridad continúa irresuelta; por tanto, la reconciliación 048 **no puede
reanudarse**. Se requiere una decisión humana posterior que elija A o B como
autoridad operativa futura, o provenance nueva y verificable. Este checkpoint
no realiza trabajo de 048.

| Estado | Valor preservado |
|---|---|
| A-PRE-0 | `NOT_READY`; `predicate_result=false` |
| A-PRE-1 | `NOT_AUTHORIZED / NOT_EXECUTED` |
| Inventory | `frozen=false` |
| Disposiciones globales | 385/385 `UNKNOWN` |
| Reconciliación 048 | Bloqueada por `UNRESOLVED_PROVENANCE` |
| Ejecución dinámica | Ninguna |

## 6. Restricciones y verificación

Esta tarea sólo registra la decisión. No se modificaron ninguna baseline
spec, manifest, ledger, `requirements.lock`, inventario ni disposición. No se
copió, borró, reparó o convirtió en tracked ninguna spec. No se ejecutaron
TALOS, FastAPI, workloads, probes, benchmarks ni actividad dinámica; tampoco
se accedió a VM, DB, corpus o modelos.

Hashes de estado inicial y final requeridos:

| Artefacto | SHA-256 inicial = final |
|---|---|
| Manifest | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Spec `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Spec `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |

Verificación post-escritura:

- JSON manifest y ledger: válido.
- Filas / nombres únicos / números únicos: 385 / 385 / 385.
- Disposiciones globales `UNKNOWN`: 385.
- `git diff --check`: pasado.
- Cambios canónicos: ninguno.
