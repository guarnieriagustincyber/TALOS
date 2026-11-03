# F2A-012 — Expediente canónico de adjudicación técnica y reserva contractual

## 1. Identidad y alcance

- Repositorio: `/media/agustin/Laboratorio/study-engie`
- Rama: `talos-current-audit`
- HEAD: `032339436639d33d310c437c88fe01d94e977449`
- Estado del worktree previo a esta creación: se confirmó la presencia de cambios no relacionados ya existentes en otros archivos del repositorio; no se realizó ninguna modificación de código, configuración, tests ni contrato durante esta creación documental.
- Alcance de este expediente: consolidar el historial, la adjudicación técnica focal, la reserva contractual de C-03d y el estado formal de F2A-012 sin introducir nueva autoridad ni alterar el contrato vigente.
- Autoridad limitada: este expediente es un registro canónico del caso F2A-012; no sustituye ni prevalece sobre contratos, gates de release, roadmap ni criterios de aceptación superiores. Su función es consolidar y preservar la trazabilidad.

## 2. Decisiones humanas registradas

### Decisión 1C
Abrir una adjudicación contractual independiente para determinar si TALOS necesita un estado de deshabilitación de bridge separado de los mecanismos actuales.

### Decisión 2A
Cerrar el alcance técnico focal validado, sin atribuir ese cierre al producto completo ni a gates de release superiores.

### Decisión 3C
Mantener C-03d pendiente; no retirar ni reinterpretar unilateralmente la condición del criterio de aceptación original.

### Decisión 4A
Preservar sin cambios todos los estados canónicos de release enumerados en esta directiva.

### Decisión 5B
Actualizar el documento canónico correspondiente mediante esta directiva independiente.

## 3. Historial documental y precedencia

### 3.1 F2A-012 original

El expediente F2A-012 trató la adjudicación del requisito contractual y la cobertura técnica focal de bridge y autorización, sin introducir nuevos campos de contrato ni estados de habilitación/deshabilitación.

### 3.2 Revisión R1

En la directiva F2A-012-R1 se registró la validación técnica focal de:
- A-01: revalidación de autorización de la caché.
- C-01: insuficiencia de evidencia.
- C-03a: topic no autorizado.
- C-03b: dirección contraria a la permitida.
- C-03c: TTL vencido.
- C-03e: bridge autorizado, control positivo.

La evidencia de esta revisión se presentó como resultado reportado del agente local y no como una ejecución independiente verificada en esta fase documental.

### 3.3 Revisión R2

En F2A-012-R2 se adjudicó la condición C-03d como:
- `NOT PART OF CURRENT CONTRACT — TEST REQUIREMENT UNADJUDICATED`

La conclusión reconoció que el contrato operativo vigente no define un estado independiente de `enabled`, `disabled` ni equivalente.

### 3.4 Revisión R3

En F2A-012-R3 se consolidó la evidencia reportada y se mantuvo la reserva contractual:
- A-01: PASS reportado.
- C-01: PASS reportado.
- C-03a: PASS reportado.
- C-03b: PASS reportado.
- C-03c: PASS reportado.
- C-03d: `NOT PART OF CURRENT CONTRACT — TEST REQUIREMENT UNADJUDICATED`.
- C-03e: PASS reportado.

Se mantuvo el estado de F2A-012 como `PARTIALLY VALIDATED — TECHNICAL CLOSURE PENDING`.

### 3.5 Preservación documental

Este expediente canónico conserva los resultados y decisiones históricas anteriores sin reescribir ni invalidar los documentos de origen. No reemplaza `STEP-24`, `PLAN_MAESTRO_CIERRE_TALOS`, `ROADMAP_V1_5_MASTER`, ni los checkpoints existentes; únicamente consolida la trazabilidad del expediente F2A-012.

## 4. Estado técnico focal registrado

### 4.1 Cierre autorizado del alcance focal

`F2A-012-FOCAL = COMPLETE — FOCAL TECHNICAL SCOPE`

Este cierre se limita exclusivamente a los casos cuya validación fue reportada:

| Caso | Estado reportado |
|---|---|
| A-01 | PASS |
| C-01 | PASS |
| C-03a | PASS |
| C-03b | PASS |
| C-03c | PASS |
| C-03e | PASS |

Se registra también la ejecución reportada de la batería de pruebas:

```bash
. .venv/bin/activate && python -m pytest -q \
  tests/unit/audit/test_generation_adapter.py \
  tests/unit/web/test_f5_context_containment.py \
  tests/integration/test_socratic_dialogue.py \
  tests/adversarial/federation/test_red_team_e4.py
```

Resultado informado: `38 passed, 2 warnings`.

Importante: este documento no afirma que la batería haya sido ejecutada de nuevo en esta fase. Lo registrado es la evidencia reportada por el agente local y la historia documental del caso. La ejecución independiente no se asume ni se presenta como nueva prueba.

### 4.2 Alcance no cubierto por este cierre

La autorización documental de este expediente no transforma el estado técnico focal en cierre del producto ni de los gates de release. El alcance focal es un cierre de expediente y no una certificación de producto.

## 5. Reserva contractual obligatoria: C-03d

La adjudicación contractual final sustituye la condición pendiente previa por la determinación del contrato vigente.

`C-03d = CLOSED — NOT APPLICABLE TO CURRENT CONTRACT`

Clasificación final:

`NOT APPLICABLE TO CURRENT CONTRACT — CONTRACTUAL ADJUDICATION CLOSED`

### 5.1 Fundamento contractual

La inspección contractual de solo lectura confirma que el contrato vigente de `CrossNotebookBridge` no exige un estado de habilitación independiente `enabled`/`disabled` ni un estado administrativo equivalente para cumplir la autorización actual.

Los mecanismos observados actuales son:
- presencia o ausencia de la entrada en la allowlist;
- expiración por TTL;
- restricciones de topic;
- dirección autorizada.

No existe una fuente contractual o normativa aprobada que imponga un campo independiente para deshabilitar un bridge. La ausencia de ese campo no constituye un defecto del contrato vigente. La autorización se expresa por autorización efectiva y revocación semántica ya presentes en la allowlist y en la vigencia temporal, sin necesidad de un estado administrativo distinto.

### 5.2 Tratamiento de la decisión humana anterior

La decisión humana anterior dejó C-03d pendiente como estado histórico. Esta adjudicación contractual final no borra ese historial, pero sí reemplaza la condición pendiente por la determinación contractual vigente:

- la condición quedó pendiente en la etapa anterior;
- la inspección contractual actual demuestra que la exigencia no es un requisito aplicable al contrato vigente;
- la resolución final se aplica solo a C-03d y no modifica los resultados de los otros casos del expediente.

### 5.3 Exclusiones y limitaciones

1. No se marca C-03d como `PASS`.
2. No se declara un defecto de implementación demostrado.
3. No se añade `enabled`, `disabled` ni un campo equivalente.
4. La presente adjudicación no altera contratos, gates superiores ni estados de release.
5. Cualquier requisito futuro de estado de habilitación independiente requerirá una decisión contractual separada, con caso de uso explícito, justificación y aprobación humana.

## 6. Estado global de F2A-012

El expediente separa explícitamente dos niveles:

### A. Alcance técnico focal
`COMPLETE — FOCAL TECHNICAL SCOPE`

### B. Criterio original completo
`CLOSED FOR C-03d — NOT APPLICABLE TO CURRENT CONTRACT`

Esto preserva la distinción entre:
- cierre técnico del alcance focal validado; y
- cierre contractual de la condición pendiente C-03d, al constatar que no forma parte del contrato vigente.

La resolución final no declara F2A-012 completamente cerrado como producto ni como cierre de gates superiores. La decisión aplica específicamente a C-03d y no altera los resultados técnicos reportados para A-01, C-01 ni C-03a/b/c/e.

## 7. Estados de release invariantes

Estos estados se conservan sin cambios:

- `PRODUCT COMPLETE`: no demostrado.
- `P1.2.B06-RUN`: `BLOCKED`.
- `P1.2`: `FAIL / DIAGNOSTIC — NOT_CLOSED`.
- Certificación TALOS V1.5: no emitida.
- B — cambio de scope y continuidad de permisos: diferido.
- TALOS V1.0-elite: históricamente congelado y certificado; fuera del alcance de esta intervención.

## 8. Restricciones de edición y operación

No se modificó:
- código;
- tests;
- configuración;
- `bridge_registry.py`;
- `bridges.allowlist.json`;
- bases de datos, corpus, índices, snapshots, modelos ni estado del estudiante;
- plan maestro, roadmap, checkpoints existentes ni otros expedientes.

No se ejecutaron operaciones destructivas de Git, no se cambiaron ramas, ni se crearon commits.

La única operación autorizada por esta directiva fue la creación de este expediente canónico en la ruta indicada, siempre que el path estuviera libre y compatible con la estructura documental existente.

## 9. Verificación final del expediente

Se verificaron estas condiciones antes de la creación:
- rama: `talos-current-audit`;
- HEAD: `032339436639d33d310c437c88fe01d94e977449`;
- directorio `docs/expedientes/`: no existía;
- archivo objetivo: no existía.

Se confirma que este expediente nuevo se creó en la ruta:
- `docs/expedientes/F2A-012-EXPEDIENTE-CANONICO.md`

La creación documental se limitó a este archivo y no alteró otros archivos del repositorio.

## 10. Adjudicación contractual final de C-03d

**Identificador:** `F2A-012-C03D-CONTRACT-ADJUDICATION-01`

### 10.1 Fuentes inspeccionadas

- `src/study_engine/federation/bridge_registry.py`
- `config/bridges.allowlist.json`
- `docs/expedientes/F2A-012-EXPEDIENTE-CANONICO.md`
- antecedentes documentales de la etapa R1/R2/R3 del expediente F2A-012

### 10.2 Evidencia contractual relevante

El contrato vigente observado en `CrossNotebookBridge` contiene los campos:
- `bridge_id`
- `source_notebook`
- `target_notebook`
- `topic_allowlist`
- `direction`
- `ttl_days`
- `created_at`
- `reviewer`
- `provenance_tag`

El comportamiento actual de autorización y revocación observado en `BridgeRegistry` se basa en:
- presencia o ausencia en la allowlist;
- verificaciones de dirección;
- topic permitido;
- expiración por TTL;
- rechazo cerrado ante ausencia de autorización.

No se observó un campo `enabled`, `disabled` ni un estado administrativo equivalente en el modelo contractual vigente ni en la allowlist effective.

### 10.3 Resultado A aplicado

Se aplica el Resultado A de la directiva de adjudicación contractual final:

`C-03d = CLOSED — NOT APPLICABLE TO CURRENT CONTRACT`

Clasificación final:

`NOT APPLICABLE TO CURRENT CONTRACT — CONTRACTUAL ADJUDICATION CLOSED`

Esto significa que la obligación que C-03d parecía exigir no es una obligación aplicable al contrato vigente. El contrato actual ya expresa la autorización, la revocación y la denegación mediante la allowlist, la dirección, los topics permitidos y la expiración por TTL. No se requiere un campo `enabled` adicional para satisfacer la semántica contractual efectiva del bridge vigente.

### 10.4 Tratamiento de la decisión humana anterior

La decisión humana previa quedó registrada como un estado pendiente, como corresponde a una adjudicación anterior no cerrada. Esta decisión contractual final no borra ese historial, pero lo sustituye para el estado actual del requisito C-03d. La nueva adjudicación aplica únicamente a C-03d y no modifica los resultados de los demás casos del expediente.

### 10.5 Efecto preciso sobre el criterio original

La exigencia C-03d queda resuelta como no aplicable al contrato vigente. No se marca como `PASS`, no se transforma en una deuda demostrada, y no se modifica la implementación ni la semántica del contrato vigente.

La resolución final no certifica el producto ni cierra gates superiores. Su alcance es exclusivamente contractual sobre la condición C-03d.

## 11. Conclusión

Este expediente canónico consolida:
- el resultado focal reportado;
- la adjudicación contractual final de C-03d;
- la separación entre cierre técnico focal y cierre contractual del requisito pendiente;
- la preservación de los estados de release invariantes;
- la ausencia de cualquier afirmación sobre producto completo, cierre total de F2A-012 ni certificación TALOS V1.5.

La cuestión de una posible habilitación/deshabilitación explícita de bridge queda resuelta para el contrato vigente como no aplicable, sin introducir ningún campo `enabled`, sin modificar la implementación ni la semántica de `CrossNotebookBridge` y sin ampliar la autoridad del expediente más allá de C-03d.
