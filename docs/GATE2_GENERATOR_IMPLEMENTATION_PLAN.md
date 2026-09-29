# Plan de implementación del generador Gate 2

**Fecha:** 2026-09-28  
**Estado:** fases A-C implementadas; preparación de snapshots y propuestas
deterministas implementadas; piloto real mínimo inconcluso; qrels positivos de
`GS2-VULN-004` adjudicados con aprobación del usuario y paquete reducido
v2.402-pilot1-adjudicated generado. La adjudicación del benchmark completo y
la evaluación end-to-end siguen pendientes.
**Alcance:** generar una nueva versión del dataset y sus qrels a partir de
snapshots verificables, preservando v2.400/v2.401 y sin modificar la ACL
activa.

## 1. Motivo de la etapa liviana

La verificación recién completada no pretendía medir Recall, MRR, latencia ni
calidad semántica. Validó únicamente el contrato que debe impedir que un
generador publique datos inconsistentes:

- IDs duplicados, faltantes o desconocidos;
- qrels ausentes para consultas positivas;
- qrels positivos en OOD globales o negativas por scope;
- chunks inexistentes o fuera de la ACL declarada;
- cambios de scope sin decisión curricular;
- conteos de metadata que no coinciden con los registros;
- respuestas vacías tratadas erróneamente como éxito positivo.

Hacer retrieval sobre las bases reales antes de cerrar esas invariantes habría
consumido CPU y memoria para producir qrels que todavía no podrían
considerarse válidos. La etapa liviana reduce el riesgo y deja el retrieval
real como una operación posterior, acotada y auditable.

## 2. Resultado esperado

El generador producirá en un directorio de salida nuevo, nunca sobre
`data/eval/` histórico:

1. `gate2_<version>.dataset.json`;
2. `gate2_<version>.qrels.json`;
3. `gate2_<version>.decisions.json`;
4. `gate2_<version>.manifest.json`;
5. `gate2_<version>.integrity.json`;
6. opcionalmente, un reporte de propuestas pendientes de revisión humana.

La versión no debe llamarse `v2.401` ni sobrescribir archivos existentes. Se
usará una nueva etiqueta, por ejemplo `v2.402-scope-contract` o la versión
que se acuerde al iniciar la implementación.

## 3. Entradas permitidas

### 3.1 Evidencia histórica, solo lectura

- `data/eval/golden_set_v2_400.json`;
- `data/eval/qrels/golden_set_v2_400.qrels.json`;
- `data/eval/golden_set_v2_401.json`;
- `data/eval/qrels/golden_set_v2_401.qrels.json`;
- sus archivos `.meta.json`;
- `config/notebook_identity_decisions.json`;
- `config/notebook_kc_catalog.json`;
- `config/notebook_source_roles.json`.

Estos archivos sirven para comparación, trazabilidad y propuesta de
decisiones. No se deben copiar “a ciegas” para publicar una nueva versión.

### 3.2 Configuración de ejecución

El CLI del generador debe recibir explícitamente:

- ruta de dataset histórico de entrada;
- ruta de qrels históricos de entrada;
- manifiesto de decisiones curriculares;
- ACL por scope;
- ruta del snapshot de knowledge store;
- ruta del snapshot del vector store cuando se habilite retrieval;
- directorio de salida vacío o inexistente;
- versión nueva;
- modo de ejecución: `fixture`, `proposal` o `generate`.

No se usarán rutas activas como destino. El modo `fixture` no debe abrir
ninguna base SQLite.

## 4. Modelo de datos de la nueva versión

Cada registro debe normalizarse a esta forma conceptual:

```json
{
  "query_id": "GS2-...",
  "query": "texto",
  "scope": "notebook-id",
  "oracle_type": "positive_in_scope",
  "kc_ids": ["..."],
  "previous_scope": "scope-anterior",
  "scope_decision_id": "decision-...",
  "qrels_status": "pending|approved|rejected",
  "qrels_provenance": "historical|fixture|retrieval_proposal|human_verified",
  "reviewer": null,
  "notes": "..."
}
```

Reglas:

- `positive_in_scope`: qrels no vacíos y cada chunk pertenece a la ACL de
  `scope`;
- `ood_global`: qrels vacíos, sin scope temático positivo alternativo;
- `negative_by_scope`: el tema puede existir en el corpus general, pero está
  fuera del scope declarado; qrels vacíos y decisión curricular explícita;
- consultas ambiguas: `qrels_status=blocked`, no se publican como aprobadas;
- un cambio de scope siempre requiere `scope_decision_id`, evidencia y
  revisor;
- no se inferirá una decisión por título, categoría, KC o similitud lexical.

Los qrels conservarán grados enteros positivos, pero la asignación de grados
propuesta por retrieval será siempre `retrieval_proposal` hasta revisión
humana. El generador no debe presentar candidatos automáticos como verdad
canónica.

## 5. Fases de implementación

### Fase A — CLI y carga segura

1. Crear `scripts/generate_gate2_benchmark.py`.
2. Implementar carga JSON con errores explícitos y validación de tipos.
3. Resolver rutas absolutas y rechazar:
   - entrada inexistente;
   - destino dentro de `data/eval/` histórico;
   - destino igual a una entrada;
   - versión ya existente;
   - archivos de salida preexistentes sin `--force` explícito.
4. Calcular SHA-256 de todas las entradas antes de procesarlas.
5. Escribir primero en un directorio temporal y publicar mediante renombre
   atómico solo después de pasar todas las validaciones.

### Fase B — Normalización y decisiones

1. Leer v2.400 y v2.401 como fuentes separadas.
2. Construir el índice `query_id -> registro histórico`.
3. Detectar cambios de scope, cambios de tipo de oráculo, qrels heredados y
   consultas nuevas.
4. Exigir una decisión explícita para las 70 consultas con cambio de scope y
   para las 20 consultas de depuración.
5. Mantener estados `pending` o `blocked` cuando falte revisión; no
   convertirlos automáticamente en positivas.
6. Validar que las decisiones usen únicamente IDs de notebook conocidos por el
   manifiesto de scopes.
7. Generar `decisions.json` con:
   - query ID;
   - scope anterior y nuevo;
   - tipo de oráculo;
   - KC;
   - evidencia de decisión;
   - revisor;
   - timestamp;
   - estado.

### Fase C — Clasificación explícita de oráculos

1. Mapear categorías históricas a los tres tipos únicamente con reglas
   declaradas.
2. Rechazar la promoción automática de una abstención histórica a OOD global.
3. Clasificar como `negative_by_scope` solo los casos con evidencia de que el
   objetivo existe fuera del scope, pero no en su ACL.
4. Dejar bloqueadas las consultas cuya pertenencia curricular no pueda
   distinguirse.
5. Validar el dataset normalizado con
   `validate_gate2_contract`.
6. Derivar metadata de los registros finales:
   - total de consultas;
   - totales por tipo;
   - totales por scope;
   - consultas con qrels;
   - pendientes/bloqueadas.

### Fase D — Propuestas de qrels sobre snapshot

Esta fase requiere aprobación explícita después de completar A-C.

1. Crear copias consistentes de `knowledge_store.db` y
   `vector_store.db` en un directorio temporal local.
2. Registrar hashes y tamaño de las copias.
3. Abrir las copias en modo lectura para la generación; nunca las bases
   activas.
4. Pasar siempre `notebook_id` y la lista de `source_ids` autorizados al
   retrieval.
5. Usar una consulta por vez, `top_k <= 5`, sin concurrencia ni reranker
   pesado en el primer piloto.
6. Para cada positiva:
   - recuperar candidatos solo dentro de su ACL;
   - verificar que cada chunk exista;
   - guardar candidatos y scores como propuesta;
   - no publicar como `approved` sin revisión.
7. Para OOD y negativas por scope:
   - no generar qrels positivos;
   - guardar únicamente el resultado de la prueba de abstención/aislamiento;
   - separar el informe de recuperación del qrels.
8. Detener si aparece throttling, temperatura no segura, error de integridad,
   memoria insuficiente o escritura inesperada.

### Fase E — Integridad y publicación

1. Ejecutar validación estructural del dataset y qrels.
2. Ejecutar validación de ACL por cada chunk.
3. Comprobar correspondencia exacta entre query IDs y qrels.
4. Comprobar que los conteos declarados coincidan con los derivados.
5. Comprobar que las consultas positivas aprobadas tengan qrels no vacíos.
6. Comprobar que OOD/negativas aprobadas tengan qrels vacíos.
7. Comparar SHA-256 pre/post de las bases activas.
8. Escribir `manifest.json` con:
   - versión;
   - commit;
   - comandos;
   - hashes de entradas y snapshots;
   - configuración;
   - modelo/embedding si se usó;
   - límites de retrieval;
   - estado térmico/capacidad si hubo piloto.
9. Publicar solo si todos los checks pasan; si no, conservar el diagnóstico
   temporal y marcar la ejecución como inconclusa.

## 6. Diseño de pruebas

### Unitarias, sin SQLite real

Fixtures mínimos deben cubrir:

- una positiva válida;
- un OOD global;
- una negativa por scope;
- qrels faltantes y desconocidos;
- chunk inexistente;
- chunk de otra ACL;
- scope desconocido;
- cambio sin decisión;
- metadata inconsistente;
- positiva con respuesta vacía;
- OOD con candidatos;
- negativa con citas;
- IDs duplicados.

### Integración con snapshots sintéticos

Crear SQLite temporal con dos notebooks, dos ACL y tres chunks. Verificar que
el generador:

- use solo la copia;
- no escriba en la base de entrada;
- rechace un qrel cruzado;
- produzca hashes reproducibles;
- limpie o preserve el directorio temporal según el modo solicitado.

### No incluido en esta etapa

- benchmark completo de 420 consultas;
- comparación TALOS/NotebookLM;
- regeneración masiva de embeddings;
- ejecución concurrente;
- poda o modificación de ACL;
- publicación de qrels automáticos como golden truth.

## 7. Orden exacto de ejecución

1. Implementar A-C y ampliar fixtures unitarios.
2. Ejecutar pruebas focalizadas y `compileall`.
3. Ejecutar el generador en modo `fixture` únicamente.
4. Revisar el `integrity.json` y el manifiesto.
5. Obtener aprobación para D.
6. Preparar snapshots y comprobar hashes.
7. Ejecutar un piloto mínimo en serie, con una positiva por scope, una
   negativa por scope y un OOD global.
8. Revisar temperatura, RSS, latencia y fuentes.
9. Solo si el piloto es estable, ampliar gradualmente.
10. Mantener el benchmark inconcluso si falla cualquier criterio del runbook.

## 8. Criterios de aceptación

El generador se considera listo para piloto cuando:

- no modifica ningún archivo histórico ni ACL activa;
- produce una nueva versión reproducible;
- todas las consultas tienen exactamente un tipo de oráculo;
- toda positiva aprobada tiene qrels no vacíos;
- todo OOD/negativa aprobada tiene qrels vacíos;
- no hay chunks inexistentes o fuera de ACL;
- todas las decisiones de scope están registradas;
- metadata y conteos se derivan y reconcilian automáticamente;
- los fixtures y las pruebas focalizadas pasan;
- el manifiesto permite reconstruir la ejecución.

El generador **no** autoriza por sí mismo la poda de ACL. Esa decisión queda
fuera de este plan y requiere resultados de calidad y capacidad del piloto.

## 9. Estado de implementación — 2026-09-28

Se implementó [generate_gate2_benchmark.py](../scripts/generate_gate2_benchmark.py)
con:

- modos `fixture`, `proposal` y `generate`, dejando estos dos últimos
  explícitamente bloqueados hasta la fase de snapshots;
- carga JSON con errores explícitos y hashes SHA-256 de entradas;
- rechazo de versión histórica `v2.401`, destinos existentes y destinos bajo
  `data/eval/`;
- publicación atómica en un directorio nuevo;
- normalización de registros y qrels;
- decisiones obligatorias por consulta;
- bloqueo de consultas sin decisión, sin promoverlas a golden truth;
- clasificación explícita de los tres tipos de oráculo;
- descarte de qrels para consultas no aprobadas, OOD o negativas;
- metadata derivada de los registros normalizados;
- manifiesto que indica que no se ejecutó retrieval.

Las pruebas de [test_gate2_generator.py](../tests/unit/retrieval/test_gate2_generator.py)
cubren generación fixture, decisiones faltantes, cambios de scope sin
`scope_decision_id`, protección de históricos y directorios de salida.
Validación ejecutada:

```text
.venv/bin/pytest -q tests/unit/retrieval/test_gate2_oracle.py \
  tests/unit/retrieval/test_gate2_generator.py \
  tests/unit/diagnostics/test_notebook_reconciliation.py
21 passed
```

También pasaron `compileall`, el smoke del CLI y `git diff --check`. No se
abrieron las bases reales, no se ejecutó retrieval y no se generaron artefactos
versionados desde v2.400/v2.401.

## 10. Siguiente paso inmediato

Se implementó [gate2_snapshots.py](../src/study_engine/diagnostics/gate2_snapshots.py)
con copia SQLite read-only, hashes SHA-256 de origen y snapshot, lectura de ACL
desde la copia y detección de cambios en las bases fuente. Las pruebas de
[test_gate2_snapshots.py](../tests/unit/diagnostics/test_gate2_snapshots.py)
usan bases sintéticas y verifican que las fuentes no se muten.

Validación adicional:

```text
.venv/bin/pytest -q tests/unit/diagnostics/test_gate2_snapshots.py \
  tests/unit/retrieval/test_gate2_generator.py \
  tests/unit/retrieval/test_gate2_oracle.py
15 passed
```

El siguiente paso es integrar un runner de piloto que consuma las decisiones
curriculares aprobadas y reporte métricas separadas. No ejecutar todavía contra
`data/web_state` ni modificar ACL o golden sets históricos.

### Implementación de propuestas sobre snapshots sintéticos — 2026-09-28

Se implementó
[gate2_proposals.py](../src/study_engine/diagnostics/gate2_proposals.py).
`generate_qrel_proposals` recibe un `Gate2Dataset`, una ruta de snapshot y un
retriever inyectable. Ejecuta los tres tipos de consulta aprobados para probar
la recuperación dentro del scope, pero solo las positivas pueden producir
qrels. OOD globales y negativas por scope conservan qrels vacíos; sus
candidatos se reportan como diagnóstico y no como evidencia relevante. Las
consultas no aprobadas se omiten y quedan como `decision_pending`.

La función:

- deriva `source_ids` desde `notebook_sources` en el snapshot read-only;
- ejecuta secuencialmente, con el `top_k` limitado a 1..5;
- verifica que cada candidato tenga score finito, chunk existente y source
  autorizado;
- rechaza duplicados, candidatos fuera de ACL y respuestas mayores que
  `top_k`;
- conserva el score de retrieval y propone grado provisional 1 (candidato sin
  relevancia graduada) para revisión humana; no convierte directamente scores
  de retrieval en relevancia;
- devuelve `qrels_provenance=retrieval_proposal` y `approved=false`;
- no modifica el dataset, el snapshot ni ninguna base fuente.

Las pruebas de
[test_gate2_proposals.py](../tests/unit/diagnostics/test_gate2_proposals.py)
usan un snapshot SQLite sintético y cubren aislamiento, chunks inexistentes,
`top_k` excesivo, ejecución solo de positivas y ausencia de aprobación
automática.

Validación de esta iteración:

```text
.venv/bin/pytest -q tests/unit/diagnostics/test_gate2_proposals.py \
  tests/unit/diagnostics/test_gate2_snapshots.py \
  tests/unit/retrieval/test_gate2_oracle.py \
  tests/unit/retrieval/test_gate2_generator.py
19 passed
```

No se ejecutó el retriever contra `data/web_state`, no se abrieron las bases
activas y no se modificaron ACL ni golden sets históricos.

### Integración CLI de snapshots — 2026-09-28

El modo `proposal` de
[generate_gate2_benchmark.py](../scripts/generate_gate2_benchmark.py) quedó
integrado con un retriever FTS secuencial sobre el snapshot. Las observaciones
de OOD/negativas y los candidatos se guardan en un archivo separado del qrels;
ninguna consulta no aprobada se envía a retrieval. Por seguridad:

- exige `--knowledge-db`, `--vector-db` y `--allow-retrieval`;
- rechaza `--top-k` fuera de 1..5;
- crea snapshots antes de abrir `KnowledgeStore`;
- deriva la ACL desde el snapshot;
- procesa una consulta por vez;
- limpia el directorio temporal y cierra el store al finalizar;
- deja `generate` bloqueado para una ejecución aprobada posterior.

La integración fue probada únicamente con fixtures y con el caso de
consentimiento explícito ausente. No se ejecutó el CLI en `data/web_state`.
Pruebas focalizadas de esta iteración:

```text
.venv/bin/pytest -q tests/unit/retrieval/test_gate2_generator_cli.py \
  tests/unit/retrieval/test_gate2_generator_snapshot_integration.py \
  tests/unit/diagnostics/test_gate2_proposals.py \
  tests/unit/diagnostics/test_gate2_snapshots.py \
  tests/unit/retrieval/test_gate2_generator.py \
  tests/unit/retrieval/test_gate2_oracle.py
21 passed
```

El piloto real continúa pendiente de decisiones curriculares aprobadas y de
verificación térmica en el equipo destino.

#### Piloto real mínimo v2.402-pilot1 — 2026-09-28

Con autorización del usuario se seleccionó una negativa por scope sustentada
en evidencia local. La consulta **“¿Cómo funciona Round Robin y cómo influye
la duración del quantum en la planificación de procesos?”** se evaluó en
`fadena-lenguajes`: FTS5 devolvió 0 chunks bajo esa ACL para
`"Round Robin" AND quantum`, mientras que en `fadena-so2` devolvió 24 chunks,
incluidos extractos explícitos de planificación Round Robin y time quantum de
`src_stallings_os_internals_7ed`. La ACL de `fadena-lenguajes` no incluye esa
fuente. El primer candidato recuperado en el scope objetivo fue un pasaje
general de Joyanes sobre procesos y colas de prioridad, sin Round Robin ni
quantum: falso positivo léxico, no fuga de una fuente ajena.

El piloto ejecutó tres consultas en serie, `top_k=1`, sobre snapshots
temporales, usando FTS:

| Tipo | Query ID | Scope | Candidatos | Ausencia requerida |
|---|---|---|---:|---|
| Positiva | `GS2-VULN-004` | `NB-CYBERSECURITY-V1` | 1 | No |
| OOD global | `GS2-OOD-001` | `NB-SEC-01-C-PTR` | 1 | Sí, falló |
| Negativa por scope | `G2-PILOT-NEG-001` | `fadena-lenguajes` | 1 | Sí, falló |

La positiva produjo como propuesta
`Computer_Security_Stallings_3rd_Ed.pdf:p427:c0000`, cuyo texto describe una
race condition. No coincide con los dos chunks del qrels histórico, por lo
que el nuevo candidato queda pendiente de adjudicación; no se considera
validado como qrel.

La OOD recuperó un pasaje de Joyanes sobre la comunidad informática mundial y
la planificación curricular; no responde a la pregunta del Mundial. Es otro
falso positivo léxico y hace fallar el criterio estricto de cero candidatos.
No se generaron respuestas ni citas, por lo que el piloto no mide abstención
generativa ni precisión de citas.

**Resultado: inconcluso.** Los negativos producen 0/2 ausencias de candidatos
y la positiva requiere revisión del qrel propuesto. No hubo candidatos fuera
de la ACL según el validador de propuestas. Latencias: positiva 80.41 ms, OOD
32.94 ms, negativa por scope 27.81 ms. RSS peak 62.2 MiB; CPU user/system
3.082/2.144 s. El proceso tardó 20.26 s incluyendo snapshots. Temperatura
CPU máxima 72.9 °C (baseline 72.9 °C), GPU máxima 54 °C (baseline 54 °C),
load máximo 3.65; no se alcanzaron los umbrales de parada. Los hashes
SHA-256 de ambas bases activas coinciden antes/después y los snapshots
temporales se limpiaron.

Artefactos: [reporte del piloto](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.pilot-report.json),
observaciones de retrieval y propuestas en el mismo directorio. El resultado
no justifica cambios de ACL. Próximo paso: inspeccionar el falso positivo
lexical (con una política de relevancia/abstención separada del filtro ACL),
revisar el qrel positivo y repetir solo después de un cambio acotado con
pruebas; mantener intactas las bases y golden sets históricos.

#### Auditoría offline de candidatos y qrels — 2026-09-28

Se añadió `topic_anchors` al contrato de consulta y al normalizador del
generador para que el dataset publicado conserve los anclajes de auditoría.
La prueba de normalización verifica este campo. En la auditoría del piloto se
usaron anclajes específicos para la OOD (“final del Mundial”, “Mundial de
México 1986”, Argentina y Alemania), de modo que la mención genérica de
“mundial” en un pasaje sobre informática no cuente como soporte temático.

`scripts/audit_gate2_pilot_candidates.py` inspeccionó el dataset y las
observaciones existentes contra la base de conocimiento en modo SQLite
read-only; no ejecutó retrieval. El reporte
`gate2_v2.402-pilot1.candidate-audit.json` concluye:

- La positiva `GS2-VULN-004` tiene un candidato recuperado tópico
  (`Computer_Security_Stallings_3rd_Ed.pdf:p427:c0000`) y un qrel histórico
  tópico (`chk_0aa9aa4cc0b2_428_1`), ambos con evidencia de “race condition”.
  El otro qrel histórico (`chk_07e0f6d0fb24_58_1`) no coincide con las anclas.
- La OOD `GS2-OOD-001` conserva un candidato recuperado, pero no coincide con
  las anclas específicas; sigue siendo un falso positivo retrieval-level.
- La negativa `G2-PILOT-NEG-001` conserva un candidato sin Round Robin ni
  quantum, también un falso positivo retrieval-level. No se encontraron
  candidatos fuera de ACL.

Las recomendaciones iniciales de mantener/agregar/retirar qrels fueron solo
señales para adjudicación humana: no se alteraron qrels históricos ni ACL. Las
pruebas unitarias cubren también que una palabra amplia como “mundial” no haga
coincidir una consulta OOD más específica.

Se completó una pasada técnica de un solo revisor en el formulario
[gate2_v2.402-pilot1.qrel-adjudication.json](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-adjudication.json).
El resultado excluye el pasaje de checksum, clasifica el pasaje de lockfile
como evidencia parcial (grado 2) y el ejemplo de archivo temporal como
evidencia directa (grado 3). El usuario aceptó los tres juicios y la rúbrica
semántica; la
[propuesta de pertenencia a qrels](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-membership-proposal.json)
registra esa aceptación y su limitación de revisor único.

La inspección de los scripts generadores v2.400/v2.401 muestra que las notas
3/2/1 se asignaban por posición de retrieval, no por relevancia semántica.
No se usan aquellas notas como rúbrica semántica; la escala aprobada para
v2.402 es distinta y explícita. La revisión fue realizada por un único
asistente de IA, no ciega ni independiente; la aprobación del usuario está
registrada. No se modificaron datos históricos ni ACL.

#### Publicación del paquete de piloto adjudicado — 2026-09-28

Se creó el paquete
[v2.402-pilot1-adjudicated](../reports/gate2_pilot_v2_402_adjudicated/),
derivado del piloto de tres consultas, con la decisión aceptada de
`GS2-VULN-004`: Spraul excluido; Stallings/lockfile grado 2; Stallings
check-then-create grado 3. Los qrels de OOD y negativa por scope permanecen
vacíos. La fuente de verdad de la aceptación, rúbrica y firma de usuario es
[el registro de adjudicación](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-membership-proposal.json);
la entrada explícita de qrels y decisiones también queda en el directorio del
piloto.

Se generó con `--mode fixture`; el manifiesto registra `retrieval.executed:
false`. El contrato validó tres IDs, un qrel positivo, scopes y conteos
derivados. Una verificación de solo lectura contra SQLite confirmó que los dos
chunks publicados existen y están autorizados en `NB-CYBERSECURITY-V1`.
El normalizador conserva `qrels_provenance=human_verified` únicamente si la
decisión está aprobada y contiene revisor y evidencia; se añadieron pruebas
para ambas condiciones. Validación: 31 pruebas focalizadas Gate 2 pasaron;
Black, compileall y `git diff --check` pasaron. La suite completa de 420
consultas, nuevas adjudicaciones qrel y evaluación end-to-end de
abstención/citas siguen fuera de este paquete.

#### Gate offline segmentado — 2026-09-28

Se implementaron
[`gate2_segment_validation.py`](../src/study_engine/diagnostics/gate2_segment_validation.py)
y el CLI [`validate_gate2_segments.py`](../scripts/validate_gate2_segments.py).
Validan IDs, forma de qrels, grados 1..3, existencia de chunks y ACL usando
SQLite read-only; el reporte agrupa por `scope × oracle_type` e incluye hashes.
Solo consulta IDs referenciados: no ejecuta retrieval, embeddings ni escaneo
global.

Las pruebas sintéticas cubren segmentación, ausencia de escrituras, qrel
cross-scope y grado fuera de rango. La ejecución sobre
`v2.402-pilot1-adjudicated` produjo
[PASS estructural](../reports/gate2_pilot_v2_402_adjudicated/gate2_v2.402-pilot1-adjudicated.segment-validation.json):
3 segmentos válidos, dos qrels para la positiva, qrels vacíos para OOD y
negativa.

Próxima etapa: componer un segmento positivo adicional por scope con consultas
y qrels adjudicados bajo la rúbrica aprobada; validar cada paquete offline y
detener ante IDs incompletos, ACL incorrecta o grado inválido. Solo tras ese
gate proponer un piloto retrieval por scope, en serie y sobre snapshots, con
`top_k` 1..5 y guardia térmica. No lanzar los 420 casos ni generación/LLM en
esta etapa.

### Diagnósticos de oráculos negativos — 2026-09-28

Se amplió el piloto para ejecutar retrieval de consultas OOD globales y
negativas por scope únicamente cuando su decisión está aprobada. Sus qrels
permanecen vacíos; `observations.json` informa candidatos y si la ausencia de
candidatos se cumple. Esto es un diagnóstico del retriever, no evaluación
end-to-end de citas o abstención generativa; no se ejecuta un LLM ni se
inventan citas.

Una decisión no aprobada no se envía al retriever. Para positivas aprobadas,
los qrels candidatos usan grado provisional 1 y el score/rank originales se
guardan por separado para revisión humana; el score no se convierte
automáticamente en grado de relevancia.

Verificación posterior a la ampliación:

```text
.venv/bin/pytest -q tests/unit/diagnostics/test_gate2_proposals.py \
  tests/unit/diagnostics/test_gate2_snapshots.py \
  tests/unit/retrieval/test_gate2_generator_snapshot_integration.py \
  tests/unit/retrieval/test_gate2_generator_cli.py \
  tests/unit/retrieval/test_gate2_oracle.py \
  tests/unit/retrieval/test_gate2_generator.py \
  tests/unit/retrieval/test_select_gate2_pilot.py
24 passed
```

`compileall`, Black con `--target-version py312` y `git diff --check`
pasaron. No se ejecutó retrieval con bases reales; el piloto sigue bloqueado
hasta que existan decisiones curriculares aprobadas.

Las positivas aprobadas producen entradas qrels provisionales con grado 1,
mientras que el score de retrieval y rango se guardan como campos separados
marcados `pending_human_review`. No se asignan grados de relevancia basados
automáticamente en una escala de score arbitraria.

### Preflight del piloto real — 2026-09-28

El piloto no se inició. La comprobación de entradas no encontró ningún
dataset/qrels/manifiesto `gate2_*` normalizado con decisiones curriculares,
por lo que no existe una consulta positiva aprobada que pueda ejecutarse sin
inventar scope u oráculo. Las bases
`data/web_state/knowledge_store.db` y `data/web_state/vector_store.db` están
presentes, pero no se usaron.

También se observó una inconsistencia intermitente al invocar directamente el
CLI con `.venv/bin/python`: el smoke reportó `ModuleNotFoundError` para
`pydantic`, mientras que las pruebas focalizadas del mismo entorno pasan y
`pip` muestra el paquete instalado. Esto debe resolverse antes del piloto para
no confundir un fallo de entorno con un fallo de retrieval.

Resultado: **piloto inconcluso, sin retrieval ejecutado**, sin modificaciones
en bases activas, ACL o golden sets, y sin impacto térmico atribuible a esta
operación. Siguiente acción obligatoria: preparar/revisar el dataset Gate 2
normalizado y estabilizar la invocación del CLI; luego seleccionar una
positiva aprobada, una negativa por scope y una OOD global para el piloto.

Para preparar esa revisión sin inventar decisiones se añadió
[preflight_gate2_pilot.py](../scripts/preflight_gate2_pilot.py). El preflight
solo lee dataset/qrels históricos, comprueba cobertura exacta de IDs, calcula
hashes y genera una plantilla con todas las decisiones en estado `blocked`.
No abre SQLite, no asigna scope ni `oracle_type`, y no habilita retrieval.
La invocación del generador debe usar explícitamente `PYTHONPATH=src`:

```text
PYTHONPATH=src .venv/bin/python scripts/generate_gate2_benchmark.py --help
```

Después de completar y revisar la plantilla, el piloto debe usar únicamente
un conjunto reducido con una positiva aprobada, una negativa por scope y una
OOD global, siempre con `--allow-retrieval --top-k 1`.

La plantilla inicial quedó generada en
`tmp/gate2_review_decisions_v2_402.json` a partir de v2.400: **400 consultas,
400 entradas qrels, 0 faltantes y 0 desconocidas**, todas en estado
`blocked_pending_curricular_review`. Es un artefacto de revisión, no un
dataset publicable ni una autorización de retrieval.

La selección auditable de candidatos quedó en
`tmp/gate2_pilot_selection_v2_402.json`. Identifica:

- positiva candidata: `GS2-VULN-004`, scope histórico
  `NB-CYBERSECURITY-V1`, con 2 qrels;
- OOD candidata: `GS2-OOD-001`, scope histórico `NB-SEC-01-C-PTR`, con qrels
  vacíos;
- negativa candidata: `GS2-VULN-001`, scope histórico
  `NB-CYBERSECURITY-V1`, pero **bloqueada** porque su abstención histórica no
  prueba que el tema exista fuera de la ACL.

El reporte queda `blocked_pending_negative_scope_review` y
`pilot_authorized=false`. No se ejecutó retrieval. Para autorizarlo falta
registrar evidencia curricular de la tercera consulta y convertir las tres
decisiones en un dataset Gate 2 versionado.

### Selección de segmentos positivos por scope — 2026-09-28

Se preparó
[v2.402-positive-segments-review](../reports/gate2_positive_segments_v2_402/)
desde v2.400/qrels en modo local y read-only, sin retrieval. Se eligieron dos
casos seguros y con pasajes verificables: `GS2-VULN-018` en SEC-01 (Deadlock)
y `GS2-VULN-007` en `fadena-so2` (mitigaciones defensivas de overflow). Sus
qrels fueron revisados contra contenido local y su ACL exacta. Se proponen
qrels grado 2 para ambos: el extracto Deadlock ejemplifica interbloqueo pero
no enumera las cuatro condiciones; el de no-execute cubre mitigación en stack
y heap, pero no toda la comparación solicitada. Se mantienen como
`adjudication_proposal`, pendientes de aceptación, no como `human_verified`.

El gate estructural/ACL produjo `status=passed` para cinco consultas y cuatro
combinaciones scope-oráculo, pero `release_eligible=false` hasta adjudicar los
dos qrels. El reporte está en
[`gate2_v2.402-positive-segments-review.validation.json`](../reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-review.validation.json).
Los otros scopes se bloquearon, no se rellenaron artificialmente:
`fadena-lenguajes` tiene qrels que apuntan a atributos GNU C, no al syscall
`clone`; `fadena-teleco` hereda qrels de overflow aunque pregunta vida útil,
contigüidad y velocidad; `fadena-std` no tiene qrels positivos; y la única
otra positiva cyber solicita shellcode ejecutable, así que no se usa para
ampliar el set.

Siguiente puerta: el usuario revisa los dos qrels candidatos y la exclusión
del duplicado parcial de Coffman. Hasta esa aceptación, no son elegibles para
retrieval. Después, generar paquete aprobable y correr de nuevo el validador;
luego elegir un scope piloto y comprobar readiness térmica antes de ejecutar
retrieval.

### Publicación de segmentos positivos adjudicados — 2026-09-28

El usuario aceptó las dos adjudicaciones sin cambios y confirmó la rúbrica
semántica: `GS2-VULN-018` conserva `chk_92876e0f2bc2_425_1` con grado 2 y
excluye el duplicado; `GS2-VULN-007` conserva `chk_0aa9aa4cc0b2_385_1` con
grado 2 y excluye los otros cuatro candidatos. Se regeneró el paquete
[v2.402-positive-segments-adjudicated](../reports/gate2_positive_segments_v2_402_adjudicated/)
en modo `fixture`; el manifiesto registra `retrieval.executed=false`.

La validación
[segmentada](../reports/gate2_positive_segments_v2_402_adjudicated/gate2_v2.402-positive-segments-adjudicated.segment-validation.json)
pasó estructura y ACL (`release_eligible=true`, cero decisiones pendientes).
Las cinco consultas quedaron repartidas en tres positivas con cuatro qrels
grado 2/3, una OOD global sin qrels y una negativa por scope sin qrels. La
comprobación usó SQLite read-only sobre `data/web_state/knowledge_store.db`;
su hash coincide con el piloto anterior. No se modificaron ACL ni golden sets
históricos.

La batería focalizada de contrato, generador, CLI, snapshot y validador pasó:
**22 passed**. El siguiente paso es revisar los scopes bloqueados (`fadena-
lenguajes`, `fadena-teleco` y `fadena-std`) y seleccionar evidencia positiva
semánticamente válida, empezando por inspección local read-only. No ampliar
retrieval ni ejecutar el benchmark completo todavía.

#### Auditoría de evidencia de scopes pendientes — 2026-09-28

Se completó la inspección de los tres scopes en SQLite read-only, sin ejecutar
el pipeline de retrieval. El
[reporte](../reports/gate2_scope_evidence_audit_2026-09-28.md) conserva las
referencias y propuestas no aprobadas. `fadena-lenguajes` continúa bloqueado:
los resultados de `clone()` son de function-cloning GNU C, no del syscall.
`fadena-teleco` tiene tres pasajes con grado 1 propuesto que cubren solo partes
de vida útil/layout Stack/Heap; no explican velocidad. `fadena-std` tiene dos
pasajes con grado 2 propuesto sobre mutex y semáforo contador, pero la
propiedad del mutex no aparece explícita y la explicación del semáforo usa
`asyncio`.

No se cambió ningún qrel ni dataset y `v2.402-positive-segments-adjudicated`
permanece sin cambios. Próximo gate: adjudicar o rechazar expresamente los
candidatos parciales; no desbloquear scopes ni iniciar retrieval mientras
queden sin adjudicación.

#### Adjudicación y nuevo fixture parcial — 2026-09-28

El usuario adjudicó los cinco candidatos: los tres chunks de
`fadena-teleco` y `chk_db97c77518c6_729_1` de `fadena-std` recibieron grado 1
y quedaron excluidos; `chk_db97c77518c6_821_1` recibió grado 2 y fue aceptado
como evidencia parcial para `GS2-CMP-011`. El
[registro](../reports/gate2_scope_candidate_adjudication_2026-09-28.json)
mantiene el racional de cada decisión.

La fixture
[v2.402-positive-segments-std-mutex-adjudicated](../reports/gate2_scope_candidate_adjudicated_v2_402/)
se generó en modo fixture con ese único qrel nuevo. El
[reporte del validador](../reports/gate2_scope_candidate_adjudicated_v2_402/gate2_v2.402-positive-segments-std-mutex-adjudicated.segment-validation.json)
pasó con seis consultas, cinco chunks qrel, `release_eligible=true` y
`retrieval_executed=false`. El paquete previo de cinco consultas se dejó
intacto; este resultado no autoriza ejecutar retrieval ni el benchmark
completo. `fadena-teleco` no obtuvo qrels y `fadena-lenguajes` permanece
bloqueado.

#### Readiness de scopes y alcance de la fixture — 2026-09-28

El
[inventario de impacto](../reports/gate2_scope_readiness_impact_v2_402.md)
compara las seis consultas adjudicadas con los 400 casos de v2.400 y los 420
de v2.401. Cinco IDs son históricos y el control negativo es nuevo; la fixture
cubre cinco de los seis scopes de v2.400, pero representa solo 5/400 IDs
históricos. `fadena-teleco` no aparece; `fadena-lenguajes` solo tiene la
negativa por scope y carece de positivo para `clone()`.

`release_eligible=true` se limita a la fixture, no al conjunto Gate 2 completo.
`fadena-lenguajes` y `fadena-teleco` siguen bloqueados por falta de positivos
semánticamente válidos. Los otros cuatro scopes tienen slices parciales que no
adjudican sus conjuntos completos. El benchmark total permanece bloqueado,
especialmente la reparación de scope/qrels de v2.401; no correr retrieval antes
de completar la matriz de cobertura y oráculos.
