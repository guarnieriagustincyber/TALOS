# Auditoría de higiene y observabilidad del proyecto

**Fecha:** 2026-09-28
**Modo:** auditoría estática, contención test-only del acceso SQLite y corrida exploratoria de suite global; sin cambios de runtime ni de datos.
**Alcance:** contratos de arquitectura, pruebas/gates, dependencias, integridad Gate 2,
patrones de fallback, medición de benchmark y documentación.
**Límite de evidencia:** el checkout tenía cambios tracked y numerosos artefactos
untracked al momento de la revisión. Los hallazgos describen el snapshot observado;
no atribuyen cambios al último commit ni intentan distinguir deuda histórica de
cambios en curso. No se inspeccionaron exhaustivamente todos los 325 módulos y 443
archivos de test para declarar ausencia de código muerto o fallos.

## Snapshot de preparación observado (no es PRE)

La inspección no destructiva realizada para iniciar la preparación registró:

| Campo | Observación |
|---|---|
| Rama / HEAD | `main` / `ec6012e66b569d610b186c8d1c09f53f7e1dd254` |
| Árbol | 17 archivos tracked modificados, 0 staged, 124 rutas untracked |
| Clasificación de diferencias | Tracked: 7 archivos runtime, 7 de tests, 1 configuración, 1 `pyproject.toml`, 1 plan. Untracked por raíz: `reports/` 67, `tests/` 23, `scripts/` 11, `tmp/` 10, `src/` 9, `docs/` 3 y `config/` 1. Las rutas `reports/`, `scripts/`, `src/diagnostics` y la mayoría de `tests/` corresponden al trabajo BENCH-G2/documentación ya presente; se preservan como entrada preexistente, no como parte automática de Ola 0.5. |
| Herramientas en `.venv` | Python 3.12.3; pytest 9.1.1 |
| Manifiestos | `pyproject.toml` tiene una modificación local que agrega el extra opcional `gate2-diagnostics` con `rapidfuzz>=3.0`; `requirements.lock` no refleja ese extra. No se editó ninguno en esta preparación. |
| Entorno actual | `httpx 0.28.1` y `rapidfuzz 3.14.6` están instalados; esto no demuestra que una instalación limpia los obtenga desde los manifiestos. |
| Entradas protegidas | Golden set `7ac3c707…b337c1`, qrels `68af7033…ed7abc` y knowledge store `fe53f3b4…5b2b1`; las tres rutas están limpias según `git status`. |
| Pruebas | Los dos tests afectados pasaron focalizadamente (`9 passed, 2 warnings`) usando la copia aislada. Luego se ejecutó la suite global exploratoria; el resultado y sus límites están registrados abajo. El inventario inicial por sí solo no es una medición PRE. |

El árbol actual no es limpio y `pyproject.toml` ya está modificado antes de Ola
0.5. Por eso el snapshot no es una autorización para editar A-1/A-2 ni una
baseline atribuible al HEAD. Si el patch de Ola 0.5 va a construirse sobre este
checkout, esa modificación local debe clasificarse como trabajo preexistente y
preservarse; no se debe revertir o incluir automáticamente en el patch.

No se encontró configuración de CI versionada en las rutas convencionales
inspeccionadas (`.github/workflows`, GitLab CI, Azure Pipelines o Jenkins); el
gate observado es local/manual. El `autouse` de `tests/conftest.py` puede
insertar una fuente sintética cuando el módulo define `retrieval_env`; la única
fixture con ese nombre encontrada crea sus bases bajo `tmp_path_factory`, por
lo que esa mutación queda aislada. Esto no demuestra ausencia de otros efectos
laterales de tests y no sustituye su revisión antes del PRE.

### Clasificación inicial propuesta para A-1

El inventario encontró 445 archivos `test_*.py` (módulos, no node IDs), repartidos
en 24 directorios con tests. Se propone este perímetro explícito; es una
clasificación para diseñar el gate, no evidencia de que las suites hayan pasado:

| Clase del gate | Suites / archivos | Tratamiento |
|---|---|---|
| **Required — determinista ordinario** | 414 módulos en `adversarial` (100), `benchmark` (2), `ci` (1), `cli` (1), `context` (3), `contract` (53), `experiments` (2), `hierarchy` (7), `llm` (2), `llm_pool` (6), `memory` (1), `pedagogy` (16), `protected` (2), `retrieval` (5), `security` (7), `session` (1), `storage` (2), `system` (4), `unit` (188), `utils` (1), `web` (10); más los 16 módulos de integración offline. | Incluir en el gate determinista, pero primero aislar los accesos a datos activos identificados abajo. Mantener los tests herméticos requeridos aunque vivan en carpetas `integration` o `adversarial`. |
| **Required — qualification controlada** | `performance` (7 módulos) y `survival` (6 módulos). | No omitir: conservar como etapa de cualificación previa a release, separada del gate rápido por costo/variabilidad de recursos. Revisar umbrales y efectos laterales y registrar hardware/configuración; no usarlos como métrica de producto sin ese contexto. |
| **Optional — entorno externo explícito** | 2 módulos de integración: `test_llm_latency.py` (marca `network`) y `test_study_loop_real_llm.py` (marca `live`). | Opt-in mediante credenciales/red y flags existentes; no convertir el skip por falta de entorno en PASS funcional, y reportar por separado de la suite requerida. |
| **Support-only** | `fixtures` (sin archivos `test_*.py`) y `__pycache__` generado. | No contarlos como suites; conservar fixtures requeridos para las pruebas y excluir bytecode del inventario de certificación. |

El total de módulos reconcilia: 414 + 16 + 7 + 6 + 2 = 445. En la configuración
pytest está declarado el marcador `slow`, pero la búsqueda no encontró tests que
lo utilicen; no se debe basar el perímetro en ese marcador hasta clasificar sus
consumidores. Las marcas `integration`, `network` y `live` no se deben tratar
como equivalentes: hay integración local hermética que sí debe permanecer en el
conjunto requerido.

Esta clasificación debe convertirse en un manifiesto explícito y una prueba de
cobertura de carpetas/test suites antes de llamar “GLOBAL” al quality gate. Los
dos grupos `performance` y `survival` no se descartan: quedan como fase de
certificación obligatoria controlada. La clasificación por módulo debe refinarse
si un test individual mezcla casos herméticos y externos.

### Aislamiento SQLite y corrida exploratoria de suite global

La búsqueda de efectos laterales identificó dos tests que usan el knowledge
store real desde su ruta versionada, en vez de una copia temporal:

- `tests/retrieval/test_hierarchical_rag.py::test_fadena_so2_pilot_retrieval`
  abre `data/web_state/knowledge_store.db` con `KnowledgeStore`.
- `tests/unit/retrieval/test_symbol_guard.py` construye un `KnowledgeStore` con
  esa misma ruta cuando existe.

El engine estándar ejecuta `PRAGMA journal_mode=WAL` al abrir una conexión
persistente (`src/study_engine/storage/sqlite_engine.py:293–299`). Aunque las
consultas observadas sean de lectura y no se demostró una mutación de filas,
este camino no cumple un contrato de acceso garantizadamente read-only y puede
alterar el modo de journal o crear sidecars WAL. Se clasifican como **bloqueo
PRE A-1**, no como daño ya ocurrido. Se añadió el fixture de sesión
`knowledge_store_test_copy` en `tests/conftest.py`: copia el archivo a pytest
`tmp_path_factory`, verifica SHA-256 del origen y la copia, y rehúsa continuar
si el WAL tiene datos o cambia durante la copia. Ambos tests usan ahora esa
copia; `KnowledgeStore` puede habilitar WAL solo en el archivo temporal.

Verificación focalizada:
`.venv/bin/python -m pytest -q tests/retrieval/test_hierarchical_rag.py::test_fadena_so2_pilot_retrieval tests/unit/retrieval/test_symbol_guard.py`
— **9 passed, 2 warnings**. El hash de `data/web_state/knowledge_store.db`
antes/después coincide con `fe53f3b4…5b2b1`; sus sidecars conservan tamaño y
timestamp. El cambio abarca únicamente harness/tests, no `SQLiteStorageEngine`
ni código de runtime.

El fixture rehúsa copiar si encuentra un WAL no vacío en el origen; no incluye
sidecars en la copia porque para este snapshot un WAL no vacío impide continuar.
Otros tests que referencian la base revisados en esta búsqueda la copian a
`tmp_path`; los tests de golden set consultados solo leen JSON. Esta verificación
estática no descarta otros efectos secundarios en los restantes módulos.

**Estado actualizado:** la acción propuesta de aislar estos dos tests ya está
implementada y validada. Después se ejecutó
`.venv/bin/python -m pytest -q` sobre el checkout observado. Resultado:
**1 failed, 2804 passed, 7 skipped, 146 warnings in 359.12s** (2812 casos
reportados por pytest). La única falla fue
`tests/survival/test_l1_ast_and_immutability.py::test_l1_1_ast_evidence_record_instantiation_sovereignty`;
el test detectó la construcción de un tipo local también llamado
`EvidenceRecord` en `src/study_engine/diagnostics/gate2_evidence_relations.py:285`.
La repetición aislada confirmó el mismo hallazgo (`1 failed in 0.70s`). La
inspección estática clasificó este disparo como **falso positivo semántico
del guard para este caso**. La regla recorre todos los `.py` bajo
`src/study_engine`, omite únicamente `state/ingestion_engine.py` y marca
cualquier llamada cuyo nombre simple sea `EvidenceRecord` (o cuyo atributo
final tenga ese nombre); no resuelve imports, definición ni identidad
cualificada. El módulo de diagnóstico define localmente un `dataclass`
`EvidenceRecord` con campos de pasaje/procedencia (`evidence_id`, `text`,
`source_id`, `document_id`, entre otros), y la línea detectada instancia esa
clase local. El modelo soberano de TALOS, en cambio, está definido en
`state/policy_contracts.py` y representa evidencia de aprendizaje
(`record_id`, `student_id`, `node_id`, `evidence_type`, etc.). El módulo de
diagnóstico no importa ese modelo ni el test demuestra que la instancia llegue
a `EvidenceIngestionEngine` o al ledger. Por tanto, este resultado no evidencia
una fuga de autoridad ni un uso de la clase de runtime; evidencia que el guard
confunde símbolos homónimos de módulos distintos. La regla puede seguir siendo
útil como restricción conservadora, pero su mensaje de “CRITICAL AUTHORITY
LEAK” es más fuerte que lo demostrado por este análisis estático.

Como corrección general y separada, el guard ahora resuelve imports del símbolo
protegido (incluidos imports cualificados, `as`, imports relativos y alias
simples) en vez de comparar únicamente el nombre final de la llamada. Se
añadieron regresiones para que los imports/alias del modelo soberano sigan
fallando y una clase local con el mismo nombre —incluido el módulo diagnóstico
Gate 2— pase. El módulo BENCH-G2 permanece intacto. La validación focalizada de
este cambio y del diagnóstico pasó (**28 passed**). La validación de segundo
nivel (`tests/survival`, `tests/contract/test_architecture_boundaries.py` y
`tests/unit/diagnostics/test_gate2_evidence_relations.py`) también pasó:
**87 passed**.

Después pasó la suite global exploratoria:
`.venv/bin/python -m pytest -q` — **2814 passed, 7 skipped, 146 warnings in
374.82s**. Esta corrida posterior no borra ni reescribe la evidencia de la
corrida inicial (**1 failed, 2804 passed, 7 skipped**); demuestra que la nueva
regresión elimina ese fallo en el estado actual. La corrida global sigue siendo
exploratoria sobre checkout dirty, no certificación aprobada ni PRE formal.
BENCH-G2 continúa pausado.

Esta corrida es una **medición exploratoria del checkout dirty**, no una
certificación aprobada ni el PRE formal de un patch A-1/A-2: el perímetro aún no
está formalizado y el árbol contiene cambios de varias líneas. No se ejecutó
benchmark. Antes y después de la validación global se verificaron iguales los
SHA-256 de `golden_set_v2_400.json` (`7ac3c707…b337c1`), sus qrels
(`68af7033…ed7abc`), `golden_set_v2_401.json` (`4442e267…f844857`), sus qrels
(`a76b18d6…87d32e6`), el knowledge store (`fe53f3b4…5b2b1`), los resultados
de benchmark, las telemetrías de supervivencia y el módulo BENCH-G2
`gate2_evidence_relations.py` (`d7ac6085…e270bd60`). No hubo cambios de
contenido en esas rutas. El módulo diagnóstico continúa untracked, como ya
estaba en el snapshot; no se editó. No se modificaron datos históricos ni
salidas versionadas.

### Fuente de verdad propuesta para A-2/A-6

La fuente canónica recomendada es `pyproject.toml`, porque declara metadata del
paquete, dependencias runtime, extras opcionales y de desarrollo en una sola
interfaz estándar. `requirements.lock` debe tratarse como artefacto derivado de
ese manifiesto y regenerarse con el comando/versión de `uv` declarados. `requirements.txt`
no debe ser una segunda autoridad: o se documenta como lista parcial de
bootstrap, o se genera/mantiene de manera verificable si se soporta como ruta de
instalación.

El análisis AST de imports directos encontró `httpx` (en factory, backends y
providers) y `numpy` (incluido en `storage/knowledge_store.py`) usados por
módulos del paquete, pero ninguno aparece en `project.dependencies`; ninguno
está en el lock observado. Ambos están instalados en el `.venv`, lo que explica
por qué esta omisión puede no aparecer en desarrollo. Antes de cerrar A-2 se
requiere confirmar sus superficies soportadas y declararlos como dependencias
directas si forman parte de runtime; luego verificar que el lock refleje esas
dependencias y los extras que su comando afirma incluir. La instalación actual
no sustituye la prueba en un entorno temporal limpio.

## Decisión recomendada y plan ejecutable

### Decisión

La preparación inicial registró el snapshot, inventarió módulos, propuso el
perímetro A-1 y la fuente de verdad A-2/A-6, aisló los dos accesos SQLite
identificados y ejecutó una corrida exploratoria global. La corrida no aprobó:
su único fallo es un falso positivo semántico del guard AST para el dataclass
local de diagnóstico, no evidencia actual de fuga de autoridad. El resultado
original debe conservarse como fallido; esta clasificación estática no lo
reescribe como PASS. Antes de iniciar el patch A-1/A-2, hay que acordar si y
cómo se ajusta el contrato del guard, formalizar el perímetro y fijar el punto
base. BENCH-G2 sigue pausado. La prioridad de Ola 0.5 queda congelada en A-1 y
A-2; los demás hallazgos esperan su propio cambio pequeño.

La razón inmediata es el estado del checkout observado al crear este plan:
rama `main`, `HEAD=ec6012e`, con modificaciones tracked y numerosos archivos
untracked de Gate 2, estabilización, reportes y pruebas. No es el árbol limpio
del baseline histórico `0e57eea`. Ejecutar ahora una suite completa y llamarla
“PRE de Ola 0.5” mezclaría cambios de varias líneas, y puede reescribir salidas
generadas como ya ocurrió en la baseline documentada. No se deben limpiar,
revertir, ocultar (`stash`) ni comprometer esos cambios para resolverlo.

El snapshot descriptivo y la corrida exploratoria no destructiva están
registrados arriba. Antes de llamar PRE formal a una medición, todavía se debe
formalizar qué suites integran el gate, revisar efectos laterales remanentes,
confirmar el aislamiento de salidas y fijar si se medirá el checkout completo
con sus diferencias actuales o un punto base separado que las preserve. Si no
se puede identificar el estado sin ambigüedad o hay conflicto con
`pyproject.toml`, detenerse antes de editar A-1/A-2 y fijar el punto base con el
usuario. La baseline `0e57eea` y sus resultados históricos se conservan como
evidencia de ese commit, no como PRE de este patch.

### Plan por pasos y criterios de salida

| Paso | Acción | Criterio de salida |
|---|---|---|
| **0 — Congelar contexto PRE** | **Inventario, aislamiento SQLite y validaciones exploratorias completados.** La corrida inicial falló por una colisión nominal del guard AST, clasificada luego como falso positivo semántico; tras la corrección general del guard, pasaron 87 tests de segundo nivel y la suite global exploratoria (2814 passed, 7 skipped). Aún falta formalizar el perímetro y fijar el punto base reproducible. | Punto base reproducible por `HEAD` + inventario de diferencias; hashes protegidos sin cambios; ninguna salida versionada modificada; resultados exploratorios preservados y claramente separados de PRE formal. |
| **1 — A-1: perímetro de certificación** | **Inventario y clasificación propuesta completados, falta formalizarlos.** Registrar el perímetro de la sección anterior como `required`, `optional` o `qualification-required`; la prueba del gate debe fallar ante cualquier directorio/test nuevo sin clasificación. No convertir tests externos en requeridos sin entorno definido. | Prueba del registro: suite nueva desconocida falla; suite requerida sí se ejecuta; omisiones intencionales aparecen con motivo; reporte muestra conteos, skips y fallos por suite. Alinear `scripts/test.sh` y `scripts/quality_gate.py` en sus declaraciones de alcance. |
| **2 — A-2/A-6: manifiestos y lock** | **Decisión de fuente de verdad propuesta arriba, implementación pendiente.** Confirmar imports directos de runtime; declarar `httpx` si las rutas importadoras son parte del paquete soportado. Mantener `pyproject.toml` como fuente canónica y decidir la función de `requirements.txt`. Regenerar `requirements.lock` con el comando/versión acordados y extras declarados. | En un entorno temporal limpio, instalar por el camino soportado, verificar import de CLI/rutas LLM, probar `gate2-diagnostics` sin hacerlo obligatorio para runtime base y comprobar lock/metadata consistentes. No tocar `.venv` de desarrollo ni instalar en el entorno global. |
| **3 — PRE formal del patch** | Las corridas actuales son referencias exploratorias, no PRE aprobado. Una vez formalizados perímetro A-1, entorno A-2 y punto base, repetir tests focalizados y luego el conjunto `required`, aislando salidas. Registrar harness, commit/base, inventario, conteos, skips, warnings, duración y efectos laterales; no introducir cambios de comportamiento de producto. | Evidencia PRE asociada al punto base y al harness exactos. Si aparecen fallos, clasificarlos como baseline/regresión/entorno antes de editar o reportar la limitación; no presentar un subconjunto como global. |
| **4 — Implementar y validar A-1/A-2** | Aplicar los cambios en una rama/patch acotado sobre el punto base acordado. No editar ningún artefacto de BENCH-G2 ni combinar estos cambios con la adjudicación. | Pasan pruebas nuevas de clasificación del gate y validación de instalación limpia; las suites `required` no empeoran respecto de PRE; artefactos versionados y entradas protegidas conservan hashes. |
| **5 — POST y decisión** | Repetir exactamente la matriz PRE sobre el estado POST, comparar resultados y revisar `git diff --check` y los artefactos protegidos. | Informe PRE/POST separado por commit/base y con diferencias explicadas. Solo entonces decidir si A-3/A-4/A-5 entran en otra iteración de Ola 0.5. |

**Condición de pausa:** la preparación y las corridas exploratorias de Paso 0
están registradas y la falla del guard quedó clasificada/corregida; los pasos
restantes no se declaran completados ni autorizan un patch A-1/A-2 hasta fijar
el punto base y completar las precondiciones de PRE formal. BENCH-G2 permanece
pausado y separado. No se acepta ni
canoniza SYN-026…028 por esta decisión; cualquier propuesta de qrel sigue
requiriendo aceptación explícita. Golden sets, qrels históricos, ACL, BKT,
knowledge stores y decisiones canónicas quedan fuera del patch de Ola 0.5.

## Mapa consolidado de gates de estabilización y auditoría

Este mapa consolida el orden y los estados documentados en el
[plan de estabilización](./PLAN_SUITE_FIX_ESTABILIZACION.md) y el
[diagnóstico/plan de continuidad multi-cuaderno](./DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md).
No reemplaza esos planes ni declara aceptado un gate por el mero hecho de que
sus pruebas focalizadas hayan pasado. En particular, “Gate 2” se usa para dos
líneas distintas; aquí se nombran **ESTAB-G2** (perfiles por cuaderno) y
**BENCH-G2** (benchmark/qrels históricos).

### Secuencia de estabilización del producto

| Orden | Gate/fase | Estado según los planes consultados | Evidencia y salida que falta |
|---|---|---|---|
| 0 | **Punto 0 — baseline reproducible** | **Completado como snapshot fechado**, en `main` / `0e57eea`: suite global `2695 passed, 7 skipped`, focalizada `100 passed`; se detectaron y aislaron escrituras de tests a artefactos versionados. | Es evidencia histórica válida para ese commit, no para el checkout actual con cambios locales. Antes de certificar una nueva entrega, repetir la suite en un entorno/salida aislados, registrar commit y resultados y comprobar que no se alteren artefactos versionados. |
| 1 | **Gate 1 — política y protección runtime inicial** | **Completado parcialmente según alcance explícito del plan**: precedencia de solución completa vs. evaluación protegida, nomenclatura `PED-F0…PED-F7` y guarda inicial en chat. Las pruebas focalizadas y una corrida global documentadas llegaron a `2703 passed, 7 skipped`. | La misma política en `TutorPolicy`/Study Loop, continuidad/estado entre workers y detección de paráfrasis no están cerrados. La comprobación textual no es garantía semántica; extenderla requiere contrato y criterio de aceptación propios. |
| 2 | **ESTAB-G2 — aislamiento del perfil por cuaderno** | **Caracterización G2.0 completada; cierre end-to-end no demostrado por esta auditoría.** El plan registra discrepancias entre identidades, catálogos y SQLite local, fallback por subcadena y herencia de contratos/analogías de Fase 0. | Resolver autoridad de identidad curricular; eliminar selección ambigua; fallback neutral o diagnóstico explícito; revisar consumidores reales; demostrar el prompt final en cuadernos soportados y casos desconocidos; tests positivos y negativos contra contaminación curricular. No migrar el estado SQLite local automáticamente. |
| 3 | **Gate C — PED-F5 fuentes, memoria y continuidad** | **Implementación amplia; aceptación abierta** en el plan de continuidad. | Cerrar casos H6 con stores/mocks aislados; probar scope de historial/fuentes/memorias, conflicto entre preferencia persistente y pedido del turno, intentos parciales/ausentes/de otro contexto y no mutación indebida de BKT. No equiparar resolver referencias con memoria de largo plazo. |
| 4 | **Gate D — PED-F6 streaming y fiabilidad** | **Parcial, no aceptado**. | Formalizar estados terminales de SSE/UI (completo, truncado, cancelado, error, abstención/clarificación); exigir terminal exitoso para marcar respuesta completa; probar EOF sin terminal, terminal duplicado y error después de tokens; distinguir error público seguro de detalle interno; probar endpoint a consumidor UI. |
| 5 | **Gate E — PED-F7 evaluación multi-currículo** | **Pendiente**. | Congelar matriz/versiones de currículo × intención × resultado, casos anonimizados y rúbrica; medir por separado respuestas y comportamiento de evaluación. No inferir retención/aprendizaje de una evaluación de respuestas. No usar proveedor real como sustituto de pruebas deterministas. |

El documento de continuidad clasifica PED-F0 como protocolo completado; PED-F1 a
PED-F4 como implementadas y validadas localmente, con límites respecto de
obediencia de proveedor real, contaminación multi-cuaderno y corrección semántica;
PED-F5 con aceptación abierta; PED-F6 parcial/no aceptada; y PED-F7 pendiente.
Las etiquetas “fase” de otros roadmaps no son intercambiables: conservar
`PED-F*`, `Fase 4-eval`, `Fase 4-sec`, `RETR-late-chunking` y
`STUDY-F5-ejercicios` como líneas diferenciadas.

### Track separado: BENCH-G2 — benchmark y adjudicación histórica

Este trabajo es paralelo a ESTAB-G2 y no acepta por sí solo la estabilización
pedagógica. El
[runbook Gate 2](./GATE2_BENCHMARK_SCOPE_RUNBOOK.md) documenta que el inventario
v2.400 encontró 111 consultas en `PENDING_ADJUDICATION`: 42 con qrels históricos
(150 referencias; 149 pendientes individualmente) y 69 sin qrels, que deben
revisarse luego por intención/oráculo y no convertirse automáticamente en
negativas.

| Subgate | Estado observado/documentado | Criterio restante |
|---|---|---|
| Integridad de contrato y ACL | **Implementado y ejecutado en paquetes acotados**: fixture/validador verifican tipos de oráculo, qrels, IDs, chunks y ACL en SQLite read-only; varios paquetes pequeños reportan `release_eligible=true`. | Ese resultado solo aplica al paquete validado. No afirma relevancia semántica, calidad de ranking, recuperación ni abstención end-to-end. |
| Diagnóstico de relaciones de evidencia v0.1 | **Validado como instrumento human-in-the-loop** en micro-lotes y suite adversarial; umbrales no calibrados corpus-wide. | Mantenerlo como señal de triage; no promover/degradar/descartar qrels, decidir independencia ni canonizar. |
| Adjudicación histórica | **En curso y no canónica**. Hay propuestas por consulta/qrel, incluidas SYN-026…028; siguen pendientes de aceptación explícita. | Continuar lotes pequeños revisando intención y cada par query/qrel; preservar qrels históricos, registro de decisiones, ACL y bases. |
| Benchmark real ampliado | **No ejecutado / no aprobado** según el runbook. | Resolver scopes bloqueados, qrels positivos bajo ACL exacta, y decisiones pendientes; luego piloto escalonado en snapshots verificados, con monitoreo térmico y aprobación separada antes de ampliar. No ejecutar directamente el conjunto completo de 420. |

### Fixes de esta auditoría dentro de la secuencia

Los hallazgos A-1…A-6 de abajo son tareas de higiene y certificación, no nuevos
gates de producto ni autorización para cambiar los datos históricos. Orden
recomendado:

1. **Antes de llamar global a una certificación:** resolver A-1 y fijar el
   perímetro de pruebas; preservar el baseline por commit y aislar salidas.
2. **Antes de afirmar instalación reproducible:** resolver A-2 y A-6 con fuente
   canónica de dependencias, imports directos declarados, lock actualizado y
   prueba de instalación limpia.
3. **Antes de comparar rendimiento:** resolver A-3 para separar throughput
   exitoso de intentos y conservar la tasa de error.
4. **Antes de usar el CLI como indicador de dominio:** resolver A-4, separando
   estado BKT inexistente de errores de lectura/esquema.
5. **Para reducir deriva de operación:** resolver A-5 con un mapa de paquetes
   actual y enlaces verificados.
6. **Luego:** reejecutar las pruebas enfocadas afectadas y una validación global
   con los efectos laterales aislados; registrar nuevo resultado sin reemplazar
   snapshots anteriores.
7. **En paralelo, sin ampliar scope:** continuar ESTAB-G2, Gate C y Gate D según
   sus dependencias; Gate E depende de contratos/aceptación suficientes. BENCH-G2
   continúa por su propio runbook, sin retrieval ampliado hasta aprobar sus
   precondiciones.

La lista no representa fixes implementados: esta auditoría solo registró,
priorizó y ordenó el trabajo pendiente.

### Alcance propuesto: Ola 0.5 — Hygiene / Certification Hardening

Para mantener la intervención pequeña y medible, se recomienda congelar Ola 0.5
en los hallazgos ya observados; no crear otra herramienta ni extender el alcance
a cambios funcionales:

| Prioridad | Ítems | Tratamiento propuesto |
|---|---|---|
| **P1** | A-1 — perímetro real del release gate; A-2 — dependencias directas y lock reproducible | Resolver primero, con tests de clasificación del perímetro e instalación/importación limpia. |
| **P2** | A-3 — separar intentos de throughput exitoso; A-4 — separar BKT ausente de error de lectura; A-5 — corregir el mapa/documentación del proyecto | Cambios pequeños e independientes, cada uno con pruebas o validación focalizada y sin alterar benchmarks históricos. |
| **INFO** | A-6 — definir la autoridad entre `requirements.txt` y `pyproject.toml` | Documentar el propósito; sincronizar solo si `requirements.txt` es una vía de instalación soportada. |

No incluir en Ola 0.5: nuevo import-graph checker, otro validador de evidencia,
detector general de código muerto/configuración, cambio de retrieval, BKT,
EpistemicController, Assessment, Audit ni nuevas dependencias de diagnóstico.
Las herramientas existentes se reutilizan; no se duplican.

La secuencia operativa recomendada es:

1. Mantener BENCH-G2 separado y pausado, conservando propuestas no canónicas
   hasta aceptación explícita; no mezclar esas decisiones con este hardening.
2. Resolver el bloqueo de aislamiento A-1 para los dos tests que abren el
   knowledge store versionado; nunca usar la base activa para PRE.
3. Implementar A-1 y A-2 en un patch de certificación separado, sin tocar
   golden sets, qrels, ACL, bases de conocimiento o decisiones históricas.
4. Abordar A-3…A-5 como cambios focalizados, con pruebas y revisión de sus
   efectos antes de integrarlos al mismo gate.
5. Registrar baseline PRE y resultados POST por commit, con salidas de pruebas
   aisladas; no sustituir snapshots fechados anteriores.
6. Retomar la secuencia de ESTAB-G2 / PED-F5 / PED-F6 y PED-F7 según sus
   precondiciones; BENCH-G2 seguirá su propio runbook y no habilita por sí solo
   retrieval ampliado.

Una siguiente auditoría distinta puede trazar afirmaciones arquitectónicas
concretas a tests ejecutables —por ejemplo, `0 chunks → 0 llamadas al LLM`,
diálogo no verificado → no mutación de BKT, diagnóstico → sin autoridad
canónica, fallo de auditor → fail-closed, `ContextPack` → evidencia válida y
benchmark histórico → inmutabilidad—. Esta revisión no completó esa matriz:
deben comprobarse en los caminos de runtime y en sus pruebas antes de marcarlas
como cubiertas o como brechas.

## Resumen ejecutivo

No se recomienda añadir otro subsistema diagnóstico: ya existen pruebas AST de
fronteras y validadores Gate 2 deterministas. Las oportunidades de mayor valor y
bajo impacto son hacer que el gate llamado “GLOBAL” incluya las suites relevantes,
alinear los manifiestos de instalación y evitar métricas de throughput que cuenten
fallos como solicitudes exitosas.

No se ejecutaron generadores, retrieval, pruebas con servicios externos ni la
suite global. Solo se ejecutaron los dos tests focalizados después de aislar el
SQLite en una copia temporal. No se modificaron datos históricos, qrels, ACL,
golden sets ni knowledge stores.

## Hallazgos priorizados

| ID | Prioridad | Área | Hallazgo y evidencia | Siguiente paso acotado |
|---|---|---|---|---|
| A-1 | **P1** | Tests / release gate | `scripts/quality_gate.py` ejecuta solo `tests/unit`, `tests/contract`, `tests/adversarial`, `tests/protected` y `tests/integration` (líneas 22–28). El árbol actual contiene, entre otras, `tests/security`, `tests/system`, `tests/survival`, `tests/web`, `tests/pedagogy`, `tests/session`, `tests/storage`, `tests/llm` y `tests/ci`, que ese gate no incluye. El script `scripts/test.sh` invoca `pytest tests/`, por lo que el alcance de ambos comandos no coincide. | Definir una sola lista explícita y completa de suites certificables, o hacer que el gate ejecute `pytest tests/` con exclusiones documentadas. Añadir una prueba que detecte directorios de tests nuevos no incorporados al gate. |
| A-2 | **P1** | Dependencias / instalación | `httpx` es importado directamente por varios módulos LLM/reranker y `numpy` por `storage/knowledge_store.py` y retrieval, pero ninguno se declara en `pyproject.toml:15–38` ni aparece en `requirements.lock`. Ambos están instalados en el entorno actual, por lo que eso no verifica una instalación limpia. Además, el lock afirma `--all-extras` pero no contiene `rapidfuzz`, declarado en `pyproject.toml:29–31`. | Confirmar el soporte runtime de las rutas; declarar las dependencias directas; regenerar el lock desde el manifiesto actualizado con todos los extras; probar instalación/importación limpia. |
| A-3 | **P2** | Benchmark / observabilidad | En `scripts/benchmark_gate2_retrieval.py:147–166`, las excepciones se cuentan en `errors` y sus latencias se excluyen, pero `qps` se calcula como `request_count / duration`. Si hay errores, el valor representa intentos por segundo, no solicitudes exitosas por segundo. El reporte sí expone el número de errores; no es una falla silenciosa. | Reportar por separado `attempt_qps` y `successful_qps`, o calcular `qps` con el número de operaciones completadas correctamente. Conservar el contador y la tasa de errores. |
| A-4 | **P2** | Fail-open / CLI | `src/study_engine/cli.py:435–447` hace una consulta SQLite read-only para el estado BKT y devuelve `{}` ante cualquier `Exception`. El llamador (`cli.py:493–505`) interpreta ausencias como `not_started`; por ello, una tabla ausente, una base corrupta o un error de esquema puede presentarse igual que la ausencia legítima de estados BKT. | Mantener la base inexistente como caso opcional si ese es el contrato, pero propagar o notificar errores de lectura/esquema en vez de representar todos como `{}`. Añadir pruebas separadas para DB ausente y esquema inválido. |
| A-5 | **P2** | Documentación / onboarding | El árbol del proyecto en `README.md:5–53` no representa el paquete actual: omite áreas presentes como `student`, `session`, `state`, `web`, `federation`, `diagnostics` y `curriculum`, y lista directorios que no aparecen en el inventario actual, como `src/study_engine/tester`. Esto puede llevar a navegación y onboarding incorrectos. | Sustituir el árbol manual por uno actualizado y acotado o documentar los paquetes reales de primer nivel; verificar también los enlaces del README. |
| A-6 | **INFO** | Dependencias / fuente de verdad | `requirements.txt:1–3` solo incluye `pydantic`, `pytest` y `pytest-cov`, mientras `pyproject.toml` declara más dependencias de runtime y herramientas de desarrollo. No queda claro en los archivos inspeccionados si `requirements.txt` es intencionalmente parcial o una vía de instalación soportada. | Aclarar en README cuál manifiesto es canónico. Si se soporta instalar desde `requirements.txt`, sincronizarlo o separar explícitamente requisitos runtime y de desarrollo. |

No se confirmó ningún hallazgo P0 ni vulnerabilidad explotable en esta revisión de
higiene. La revisión no fue una auditoría de seguridad.

## Evaluación por área

### A. Arquitectura y contratos

**Fortaleza verificada:** `tests/contract/test_architecture_boundaries.py`
implementa comprobaciones estáticas de imports mediante AST para varias fronteras
(incluyendo retrieval, state, execution, assessment y curriculum). No hace falta
crear ahora otro import-graph checker paralelo.

**Oportunidad:** incorporar las fronteras nuevas o no cubiertas a la matriz existente
solo cuando un contrato concreto las justifique. No se infiere una violación de
arquitectura por la mera existencia de dependencias entre carpetas.

### B. Código muerto y configuración

La revisión estática no basta para afirmar que un módulo o una configuración están
muertos: el uso dinámico, entry points, imports condicionales y scripts pueden no
aparecer en una búsqueda simple. No se recomienda borrado automático. Un detector
de imports/configuración sin uso queda como oportunidad exploratoria, no como
hallazgo confirmado.

### C. Dependencias

Aplican A-2 y A-6. Además de la divergencia entre manifiestos, la ausencia de una
dependencia importada directamente es distinta de una dependencia transitiva:
el paquete debe declarar sus imports directos, sin depender de que otra biblioteca
los instale incidentalmente. La presencia de RapidFuzz como extra opcional sí
respeta el límite deseado de no incorporarlo al conjunto de runtime normal; el
problema es la falta de coherencia del lock observado.

### D. Configuración

No se encontró evidencia suficiente para etiquetar flags o configuraciones
específicas como obsoletas. La forma segura de continuar sería comparar
declaraciones con consumidores y documentar excepciones dinámicas antes de
proponer eliminaciones.

### E. Integridad de evidencia

**Control existente verificado:** `src/study_engine/diagnostics/gate2_segment_validation.py`
valida estructura, referencias qrel/chunk, pertenencia a ACL y hashes; abre la base
en modo `ro`, no ejecuta retrieval y declara límites semánticos explícitos
(líneas 48–80 y 86–91, 169–185). Esto cubre una parte importante de la propuesta
de `evidence_integrity_check`; no recomiendo duplicarla.

Este control no es una adjudicación semántica ni una validación de ranking. Esa
distinción está documentada y debe mantenerse.

### F. Higiene de benchmark

El validador de segmentos Gate 2 ya informa hashes y elegibilidad separadamente de
la validación estructural. El runbook también requiere hashes, ACL, resultados por
tipo de oráculo y cuidado con las bases activas. La discrepancia QPS descrita en
A-3 es el único defecto concreto encontrado en la medición revisada.

### G. Fallbacks y fallos

Aplica A-4. También existen `except Exception` en `student/readiness_probe.py:44–49`
y `student/laguna_detector.py:42–50`, donde un resolver de prerrequisitos fallido
activa un mapa local o termina sin resultado. Pueden ser fallbacks deliberados; no
se clasifican aquí como defectos confirmados porque la semántica esperada cuando
falla el resolver necesita una decisión de producto y revisión de sus llamadores.
La recomendación es cubrir explícitamente resolver exitoso, error y fallback,
incluyendo trazabilidad del fallback si afecta una decisión pedagógica.

### H. Observabilidad de runtime

El benchmark de retrieval ya informa errores y latencias, y el runbook de Gate 2
exige monitorizar CPU, memoria, temperatura y throttling durante pilotos en el
hardware objetivo. No se recomienda duplicar sensores térmicos en el runner sin
una necesidad operativa demostrada. A-3 mejora la interpretación de los datos que
ya se generan.

### I. Cobertura de tests

Aplica A-1. Además, la prueba AST de arquitectura demuestra que ciertos contratos
transversales ya tienen protección ejecutable. La cantidad de archivos de test o
el número histórico de tests no se toma como sustituto de cobertura contractual.

### J. Deriva documental

Aplica A-5. Los documentos de certificación contienen resultados fechados; otro
documento de continuidad advierte explícitamente que las cifras anteriores son
snapshots y no evidencia del estado actual. Por eso no se interpretan las cifras
históricas de tests como una afirmación vigente ni se recomienda reescribirlas sin
mantener su fecha y perímetro.

### K. Próximas oportunidades de bajo impacto

1. Corregir primero la cobertura declarada por el release gate (A-1).
2. Alinear dependencias directas, extras y lock reproducible (A-2, A-6).
3. Corregir la semántica de QPS y mantener visibles los fallos (A-3).
4. Hacer explícito el error de lectura BKT frente al estado realmente ausente (A-4).
5. Actualizar el mapa del repositorio en README (A-5).
6. Después de esos cambios, considerar un reporte automático de capacidades
   implementación → contrato/test → gate; esta auditoría no trazó exhaustivamente
   cada promesa de `CAPABILITIES.md` hasta su ruta de runtime.

## Decisiones de alcance

- No se cambiaron dependencias ni se regeneró el lock.
- Los dos tests focalizados de SQLite pasaron tras aislarlos (9 passed,
  2 warnings); la validación de segundo nivel pasó (87 passed).
- La suite global exploratoria falló inicialmente por el falso positivo AST y
  pasó después de corregir el guard: 2814 passed, 7 skipped, 146 warnings.
  Ninguna de estas corridas se declara PRE formal y no se ejecutó benchmark.
- Se cambió únicamente el harness/test para que esos tests utilicen una copia
  temporal del knowledge store; no se cambió runtime ni datos históricos.
- No se editaron golden sets, qrels, decisiones, ACL ni bases de conocimiento.
- Los hallazgos son oportunidades priorizadas; requieren confirmación antes de
  implementar cambios de comportamiento.

## Punto de reanudación

El código y este informe del endurecimiento del harness/guard están guardados
en Git. El commit de este checkpoint es `08c1dae` (rama `main`). El commit
incluye este informe, el aislamiento SQLite test-only y la regresión/fix del
guard AST; no incluye el resto de cambios locales preexistentes del checkout.
Esos cambios permanecen deliberadamente en el árbol de trabajo y no deben
limpiarse ni descartarse como parte de la reanudación.

**Estado para continuar:** BENCH-G2 sigue pausado; los datos históricos siguen
protegidos; la exploratoria global pasó, pero no es PRE formal. El siguiente
trabajo es cerrar el punto base reproducible y formalizar el perímetro A-1
(clasificación `required` / `optional` / `qualification-required`); A-2 y el
patch A-1/A-2 esperan esas precondiciones. Antes de cualquier patch, revisar el
estado completo del árbol y conservar todas las modificaciones locales.
