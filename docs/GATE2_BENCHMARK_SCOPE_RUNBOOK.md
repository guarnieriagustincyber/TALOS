# Gate 2 — Procedimiento seguro para corregir y validar scopes del benchmark

**Estado:** procedimiento de ejecución; todavía no autoriza poda de ACL ni
ejecución de un benchmark completo.  
**Alcance:** corregir la asignación curricular y los oráculos de
`golden_set_v2_401`; mantener intactos los archivos históricos y las bases
activas.  
**Fecha:** 2026-09-28.

## Decisión de entorno

Esta prueba no necesita OCR ni procesamiento de libros. La comparación de
scopes y qrels se hace localmente con archivos JSON y consultas SQLite de solo
lectura.

- **Validaciones de estructura y fixtures:** local, con pytest; carga de CPU
  baja y sin abrir los índices reales.
- **Prueba de retrieval con corpus real:** en el hardware destino, sobre copias
  verificadas de `knowledge_store.db` y `vector_store.db`. Así se mide el
  entorno cuya capacidad interesa y se puede controlar temperatura, memoria y
  concurrencia.
- **Google Colab:** no es la opción recomendada para esta prueba. Colab mediría
  otro hardware y requeriría subir corpus, índice y/o código. No subir bases,
  libros, credenciales ni datos del workspace a un servicio externo como parte
  de este procedimiento. El uso de Colab para OCR/procesamiento de libros es
  un flujo separado y no se modifica ni se necesita aquí.

## Por qué hacerlo antes de cambiar la ACL

v2.401 reasignó a SEC-01 70 consultas que en v2.400 pertenecían a cinco scopes
secundarios. En sus qrels actuales hay 330 referencias a chunks para esos
casos y 224 pertenecen a fuentes no autorizadas por el scope anterior. Por
tanto, restaurar solamente `notebook_scope` tampoco es una reparación válida.
Además, v2.400 representa abstenciones negativas por scope con una semántica
que el runner actual no acepta. Hasta resolver ambos problemas, las métricas no
son una base confiable para decidir qué fuentes retirar de SEC-01.

## Secuencia de trabajo

### 1. Preservar y registrar los originales

1. No sobrescribir `golden_set_v2_400.json`, `golden_set_v2_401.json`, sus
   qrels ni sus metadatos.
2. Registrar SHA-256 de los archivos fuente y el commit/configuración usados.
3. Crear una nueva versión para cualquier reparación. El número de versión se
   asignará al implementar; no publicar cambios bajo el nombre v2.401.
4. No ejecutar los generadores actuales para este análisis: escriben artefactos
   versionados y pueden regenerar qrels mediante retrieval contra la base.

### 2. Fijar el contrato de cada tipo de consulta

Cada caso debe tener una intención explícita y verificable:

| Tipo | Pregunta que responde | Resultado esperado |
|---|---|---|
| Positiva en scope | ¿El notebook contiene evidencia para este objetivo? | Qrels no vacíos, chunks del scope declarado y evaluación de ranking. |
| OOD global | ¿La pregunta es ajena a todos los contenidos disponibles? | Abstención; cero chunks y cero citas. |
| Negativa por scope | ¿El tema existe en el corpus, pero no está autorizado en este notebook? | Cero chunks/citas para ese scope; contabilizar como prueba de aislamiento, no como OOD global ni como consulta positiva. |

Una consulta no se clasificará como negativa por scope solo por su título,
categoría o KC: debe confirmarse que el objetivo queda fuera del material
autorizado para ese scope. Las consultas ambiguas quedan fuera del conjunto
aprobado hasta revisión curricular.

### 3. Preparar la nueva versión y sus qrels

1. Tomar v2.400/v2.401 como evidencia histórica, no como entrada lista para
   publicar.
2. Revisar las 70 consultas cuyo scope cambió y mantener un registro de
   decisión por `query_id`: scope aprobado, tipo de oráculo, KC, decisión de
   qrels y revisor.
3. Revisar por separado las 20 consultas nuevas de depuración. SEC-01 es una
   asignación candidata por tema, pero sus qrels deben verificarse bajo esa
   ACL; no heredar qrels de otro scope.
4. Generar qrels de consultas positivas por scope, con retrieval sobre una
   copia consistente de las bases. Ningún chunk qrel puede provenir de una
   fuente fuera de la ACL declarada para ese caso.
5. No asignar qrels positivos a consultas OOD globales o negativas por scope.
   El runner debe reconocer esas clases de forma explícita y reportarlas en
   métricas separadas; no convertir errores de recuperación en abstenciones
   esperadas.
6. Derivar los conteos de metadata del dataset final; no mantenerlos a mano.

### 4. Verificar primero sin retrieval pesado

Antes de abrir bases reales, ejecutar pruebas unitarias con fixtures pequeños
y recuperación simulada. Deben fallar si:

- hay IDs duplicados o faltantes, qrels sin consulta o consultas positivas sin
  qrels;
- una consulta negativa/OOD tiene qrels positivos, o una consulta positiva se
  declara como abstención;
- un chunk de qrels no existe en el fixture o pertenece a otra ACL;
- un caso cambia de scope sin una decisión registrada;
- los totales por tipo/scope no coinciden con los registros;
- una respuesta vacía se interpreta como aprobación para una consulta positiva.

Esta etapa no usa embeddings, reranker, modelo externo ni las bases activas.

### 5. Ejecutar un piloto real acotado en el hardware destino

Solo después de aprobar el contrato y los fixtures:

1. Crear copias consistentes de `knowledge_store.db` y
   `vector_store.db` en un directorio temporal/local con espacio suficiente.
   Confirmar que el runner apunta a esas copias y a un directorio de salida
   nuevo, no a los archivos activos ni a reportes históricos.
2. Confirmar hashes/modelo/configuración compatibles entre corpus, índice y
   benchmark; documentar cualquier diferencia.
3. Elegir un conjunto piloto pequeño que cubra, al menos, una positiva SEC-01,
   una positiva de cada scope secundario que se vaya a evaluar, una negativa
   por scope y una OOD global. Si falta un scope operacional o no tiene ACL
   persistida, no inventarlo: dejar su consulta bloqueada y registrarlo.
4. Ejecutar en serie, con una sola instancia, concurrencia 1 y `top_k` bajo
   (máximo 5). Registrar temperatura, frecuencia/throttling, uso de CPU/RAM,
   tiempo por consulta, candidatos devueltos y fuentes. No usar modo profundo,
   paralelismo ni regeneración masiva de embeddings.
5. Detener inmediatamente si la temperatura alcanza el límite conservador
   definido para ese equipo, aparece throttling, el sistema deja de responder
   o la memoria se acerca al límite operativo. Como ya se observó 93 °C, no
   iniciar el piloto sin monitorización térmica y sin verificar el límite del
   fabricante.
6. Si el piloto es estable, ampliar el tamaño de forma gradual y con pausas.
   No saltar directamente a los 420 casos. La ejecución completa requiere
   aprobación separada basada en el comportamiento térmico y en los resultados
   del piloto.

### 6. Criterios para considerar el benchmark válido

- Scopes por `query_id` aprobados y reproducibles.
- Qrels positivos resueltos bajo la ACL exacta; cero referencias fuera de
  scope y cero chunks inexistentes.
- Positivas, OOD globales y negativas por scope reportadas separadamente.
- Conteos de dataset, qrels y metadata reconciliados automáticamente.
- Reporte guardado en una ruta nueva con hashes del dataset, qrels, corpus,
  índice y configuración.
- Ninguna escritura en las bases activas; integridad y hashes del original
  conservados.
- Resultados térmicos y de capacidad aceptables en el hardware destino.

Si falla cualquiera de estos criterios, el benchmark queda **inconcluso** y
no se usa para podar ACL. Se corrige el dataset o la configuración primero.

## Artefactos a producir al ejecutar

La implementación del runner versionado debe generar, en un directorio de
salida nuevo:

1. dataset JSON versionado;
2. qrels versionados;
3. manifiesto de decisiones por consulta y hashes;
4. reporte de integridad de scopes/qrels;
5. reporte del piloto o benchmark con métricas por scope, tipo de oráculo,
   latencia, candidatos, RSS/CPU y temperatura observada.

No generar ni reemplazar estos artefactos manualmente mediante edición de los
JSON históricos.

## Plan de implementación del generador

El plan detallado para el generador versionado, sus snapshots, invariantes,
pruebas y criterios de habilitación del piloto está en
[GATE2_GENERATOR_IMPLEMENTATION_PLAN.md](./GATE2_GENERATOR_IMPLEMENTATION_PLAN.md).

## Estado y próximo paso

La auditoría estática de v2.400/v2.401 quedó registrada en el
[plan rector](./PLAN_SUITE_FIX_ESTABILIZACION.md) y en
`config/notebook_identity_decisions.json`. El generador ya está implementado;
el piloto mínimo autorizado resultó inconcluso y su auditoría offline está
registrada en el plan rector y en el
[plan del generador](./GATE2_GENERATOR_IMPLEMENTATION_PLAN.md). No se
modificaron bases activas, ACL ni qrels históricos.

Se hizo una adjudicación técnica de un solo revisor para los dos qrels
históricos y el candidato nuevo de `GS2-VULN-004`; el usuario aceptó las tres
decisiones y la rúbrica. El
[registro de adjudicación](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-adjudication.json)
documenta la limitación de revisor único. El paquete versionado
[v2.402-pilot1-adjudicated](../reports/gate2_pilot_v2_402_adjudicated/)
excluye Spraul, asigna 2 al ejemplo de lockfile y 3 al ejemplo TOCTOU; qrels
OOD y negativa permanecen vacíos. Se generó sin retrieval, en directorio
nuevo fuera de `data/eval`.

Los generadores históricos asignaban 3/2/1 por rango de recuperación; la
rúbrica semántica aprobada se registra explícitamente para no confundir ambas
escalas. La validación estructural y de ACL read-only pasó; no se alteraron
datasets históricos, ACL ni bases activas. El paquete cubre solo tres
consultas: adjudicar el benchmark completo y diseñar la evaluación end-to-end
de abstención/citas son pasos posteriores separados.

Antes de ampliar retrieval se implementó el gate segmentado
[`validate_gate2_segments.py`](../scripts/validate_gate2_segments.py) con
pruebas sintéticas. El
[reporte de integridad](../reports/gate2_pilot_v2_402_adjudicated/gate2_v2.402-pilot1-adjudicated.segment-validation.json)
agrupa por scope y tipo de oráculo, valida qrels/grados/existencia/ACL en
SQLite read-only y confirma tres segmentos válidos. Retrieval no ejecutado.

Se preparó a continuación un paquete de revisión segmentado; los detalles y
su decisión manual pendiente aparecen abajo. No ejecutar el full set de 420
consultas ni evaluación end-to-end todavía.

Se preparó la siguiente etapa como paquete de revisión
[v2.402-positive-segments-review](../reports/gate2_positive_segments_v2_402/).
Incluye un candidato Deadlock para SEC-01 y uno de mitigaciones defensivas
para `fadena-so2`, ambos con propuestas grade 2 pendientes. El gate offline
pasó estructura y ACL para cinco consultas/cuatro segmentos, pero declara
`release_eligible=false` por esos dos casos pendientes. No ejecutó retrieval.

No se forzó cobertura en los otros scopes: los qrels históricos de
`fadena-lenguajes` refieren GNU C function-cloning, no el syscall `clone`;
`fadena-teleco` tiene qrels de overflow para una consulta de Stack/Heap
lifetime/contigüidad/velocidad; `fadena-std` no tiene qrels positivos. Para
Cybersecurity se conserva el positivo ya adjudicado y se excluye el otro
candidato porque pide shellcode ejecutable. Revisar primero las dos
propuestas del archivo
[selection-review](../reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-selection-review.json).

### Estado posterior a la adjudicación — 2026-09-28

Las dos propuestas fueron aceptadas y publicadas en el paquete
[v2.402-positive-segments-adjudicated](../reports/gate2_positive_segments_v2_402_adjudicated/).
La validación segmentada está en
[el reporte](../reports/gate2_positive_segments_v2_402_adjudicated/gate2_v2.402-positive-segments-adjudicated.segment-validation.json):
`status=passed`, `release_eligible=true`, cinco consultas y cero decisiones
pendientes. Se generó como fixture sin retrieval; SQLite se abrió read-only
para comprobar únicamente la ACL representada y los chunks qrel. No se
alteraron bases activas, ACL ni golden sets históricos.

El siguiente gate es revisar evidencia positiva de los scopes aún bloqueados
antes de ampliar retrieval. La aprobación estructural de este subconjunto no
equivale a aprobar el benchmark completo ni la evaluación end-to-end.

### Resultado de la auditoría local — 2026-09-28

La inspección de los tres scopes se realizó sobre SQLite read-only, limitada a
fuentes ACL-autorizadas y sin ejecutar el pipeline de retrieval ni
embeddings/reranking. El
[reporte detallado](../reports/gate2_scope_evidence_audit_2026-09-28.md)
registra candidatos y límites:

- `fadena-lenguajes`: no se halló evidencia del syscall `clone()`; las
  coincidencias disponibles son sobre el atributo GNU C de optimización.
- `fadena-teleco`: tres posibles pasajes grado 1 cubren parcialmente ciclo de
  vida/layout Stack/Heap, pero no velocidad; no se agregan qrels.
- `fadena-std`: dos pasajes grado 2 podrían apoyar parcialmente Mutex vs
  semáforo contador, aunque no acreditan toda la propiedad del mutex ni cubren
  todas las variantes; requieren adjudicación.

El estado de adjudicación posterior y el único qrel aceptado se registran en
la sección siguiente.

### Adjudicación de candidatos y fixture parcial — 2026-09-28

El usuario asignó grado 1 y excluyó de qrels los tres candidatos de
`fadena-teleco` y `chk_db97c77518c6_729_1` de `fadena-std`. Aceptó
`chk_db97c77518c6_821_1` como evidencia parcial grado 2 para `GS2-CMP-011`.
El [registro de adjudicación](../reports/gate2_scope_candidate_adjudication_2026-09-28.json)
conserva las cinco decisiones.

Se generó la fixture nueva
[v2.402-positive-segments-std-mutex-adjudicated](../reports/gate2_scope_candidate_adjudicated_v2_402/)
con solo ese qrel nuevo. La
[validación segmentada](../reports/gate2_scope_candidate_adjudicated_v2_402/gate2_v2.402-positive-segments-std-mutex-adjudicated.segment-validation.json)
pasó (`release_eligible=true`, seis consultas, cinco chunks qrel); usó SQLite
read-only y no ejecutó retrieval. El paquete de cinco consultas previo, las
ACL activas y los golden sets históricos permanecen intactos. `fadena-
lenguajes` sigue bloqueado por mismatch semántico.

### Inventario de readiness e impacto — 2026-09-28

Se comparó la fixture de seis consultas con v2.400/v2.401 y la ACL
persistida. El
[reporte de impacto](../reports/gate2_scope_readiness_impact_v2_402.md)
concluye que `release_eligible=true` aplica a esa fixture, no al benchmark
completo. La fixture cubre cinco de los seis scopes de v2.400 y solo 5/400 IDs
históricos (más un control nuevo); `fadena-teleco` no está representado y
`fadena-lenguajes` aparece únicamente con una negativa por scope, no con un
positivo del tema `clone()`.

Persisten bloqueos positivos semánticos en `fadena-lenguajes` y
`fadena-teleco`; los otros cuatro scopes tienen solo slices parciales, no
cobertura adjudicada de sus conjuntos históricos. v2.401 tampoco es entrada
liberable: sus 420 casos apuntan a SEC-01 y mantiene la inconsistencia qrel
registrada. No se ejecutó retrieval y no se modificaron fuentes históricas ni
ACL.

### Inventario histórico read-only de v2.400 — 2026-09-28

El paso siguiente fue producir el inventario auditable por consulta y por
referencia qrel, sin reparar el dataset:

- [Fuente JSON](../reports/gate2_v2400_coverage_inventory_2026-09-28.json)
  con 400 consultas, 165 qrels y decisiones explícitas por cada par query/qrel.
- [Vista Markdown](../reports/gate2_v2400_coverage_inventory_2026-09-28.md)
  con totales por taxonomía y scope.
- [Registro de decisiones](../reports/gate2_v2400_explicit_decision_register_2026-09-28.json)
  separado de los datos históricos.
- Constructor reproducible:
  [`build_gate2_v2400_coverage_inventory.py`](../scripts/build_gate2_v2400_coverage_inventory.py).

La consulta SQLite fue read-only; no se ejecutaron retrieval, embeddings,
reranking, generación ni benchmarks. v2.401 es exclusivamente evidencia de
auditoría (`canonical_for_repair=false`, `historical_evidence=true`). La
comparación registró 70 cambios de scope, 330 referencias qrel asociadas y 224
fuera de la ACL correspondiente de v2.400; la acción sigue siendo `NONE`.
`NB-SEC-01-C-PTR` muestra las 70 consultas y 330 referencias importadas, pero
eso no determina su pertenencia curricular. La ACL persistida actual tampoco
reconstruye automáticamente la ACL histórica.

Los estados `PENDING_ADJUDICATION`, `NO_VALID_QREL` y `PARTIALLY_VALID`
requieren tratamiento distinto. La ausencia de qrels no demuestra que una
consulta sea negativa; una referencia aprobada no valida automáticamente las
demás referencias de la consulta; y una abstención fuera de `ood_trampas`
queda pendiente hasta identificar si su intención era negativa por scope u
otra clase de oráculo.

**Próximo paso:** revisar lotes acotados por scope empezando por la intención
y tipo de oráculo de cada consulta; después adjudicar individualmente cada
referencia pendiente. No modificar ACL/qrels históricos, no usar la
comparación con v2.401 para reasignar scopes y no iniciar retrieval hasta
cerrar las decisiones pertinentes.

#### Lote inicial de revisión

El inventario reporta 111 consultas en estado `PENDING_ADJUDICATION`. De ellas,
42 tienen referencias qrel históricas (150 referencias en conjunto); 149
referencias siguen sin juicio individual y una ya tiene decisión registrada.
Las otras 69 consultas pendientes no tienen qrels y no pertenecen a este
primer lote de adjudicación de evidencia.

La [cola JSON](../reports/gate2_v2400_query_adjudication_queue_2026-09-28.json)
y la [vista Markdown](../reports/gate2_v2400_query_adjudication_queue_2026-09-28.md)
enumeran ese lote sin proponer resultados. Primero se decide intención/scope/
oráculo de la consulta; después, cada chunk individualmente. Los IDs y fuentes
permiten abrir evidencia en el entorno local; los textos de chunk se omiten
del paquete. El [constructor de cola](../scripts/build_gate2_v2400_query_adjudication_queue.py)
no modifica los registros históricos ni el registro de decisiones explícitas.

Las pruebas focalizadas del inventario y de la cola pasaron (**11 passed**).
Este artefacto únicamente prepara la revisión manual: no equivale a
adjudicación ni habilita retrieval.

Como primer sublote estructural se revisaron las variantes
`GS2-CMP-041`…`GS2-CMP-045`, sin registrar decisiones semánticas. Las cinco
comparten una única referencia qrel pendiente de grado histórico 3; la fuente
y el chunk existen y la asociación actual está en la ACL de SEC-01. La nota de
cada consulta exige diversidad de dos capítulos o fuentes en el top 5, algo
que la referencia compartida no permite verificar por sí sola. Esto queda
como pregunta de cobertura, no como señal de qrel inválido ni como decisión.
El [paquete del sublote](../reports/gate2_v2400_review_batch_cmp_041_045_2026-09-28.md)
conserva los campos de decisión vacíos. No se modificaron históricos ni ACL y
no se ejecutó retrieval.

La lectura semántica posterior produjo una propuesta técnica independiente
para cada par query/qrel:
[informe](../reports/gate2_v2400_review_batch_cmp_041_045_adjudication_2026-09-28.md).
El chunk se propone con grado 1 en las cinco variantes, con razones distintas
según la dimensión exigida; las propuestas no se copiaron automáticamente por
compartir `chunk_id`. La diversidad de dos capítulos/fuentes se conserva como
criterio de top-5 separado de la relevancia individual. Las cinco decisiones
canónicas siguen pendientes de aceptación; el registro explícito y los qrels
históricos no se modificaron.

El siguiente grupo por intención, `GS2-FUN-111`…`GS2-FUN-115`
(`aritmetica_punteros`), se revisó en sus 15 pares query/qrel. Las propuestas
varían por formulación: los pasajes completos obtienen grados 3 para la
pregunta base, 2 cuando se exige formalismo/fuente específica/detalle adicional
y hasta 1 cuando la dimensión de implicancias de sistemas no está cubierta.
La extracción OCR duplicada y truncada se mantiene en grado propuesto 1; no
cuenta como corroboración independiente. Ver
[el informe detallado](../reports/gate2_v2400_review_batch_fun_111_115_adjudication_2026-09-28.md).
También aquí todas las decisiones canónicas siguen pendientes; no se
modificaron históricos ni ACL y no se ejecutó retrieval.

El siguiente grupo, `GS2-FUN-116`…`GS2-FUN-120`
(`punteros_dobles`), permite distinguir diversidad de fuentes de evidencia
pertinente. Sus qrels provienen de dos fuentes distintas, pero la lectura
propone grado 1 para el ejemplo de parámetro `int*` (adyacente, no demuestra
`T**`) y grado 0 para el pasaje de hashing/almacenamiento de una base de datos
(fuera de tema). Por tanto, no se cuentan automáticamente dos fuentes como
dos evidencias independientes. Ver
[el informe detallado](../reports/gate2_v2400_review_batch_fun_116_120_adjudication_2026-09-28.md).
Las diez propuestas qrel y las cinco decisiones de consulta permanecen no
canónicas y pendientes de aceptación; no se modificaron históricos ni ACL y
no se ejecutó retrieval.

Como siguiente contraste de fuentes potencialmente complementarias se
revisaron `GS2-SYN-015` y `GS2-SYN-016` (`execve`): una pregunta de operación
general y otra de parámetros/retorno. `Computer Security: Principles and
Practice` aporta detalle de reemplazo de imagen y preparación de argumentos
en un tratamiento de shellcode; `Operating Systems: Internals and Design
Principles` confirma por separado la función general de ejecución, pero solo
en una línea. Se propusieron grados distintos para cada pregunta y referencia.
Tres fragmentos de la página 373 son solapados con el chunk completo y no se
cuentan como corroboración independiente; los IDs de fuente tampoco prueban
independencia de autoría. Ver
[el informe detallado](../reports/gate2_v2400_review_batch_syn_015_016_adjudication_2026-09-28.md).
Las decisiones siguen no canónicas y los qrels históricos `PENDING`; no hubo
cambios de ACL/históricos ni retrieval.

Como prueba del caso inverso, se revisó `GS2-SYN-014` (`execve`): dos
referencias de autores distintos reciben propuesta grado 2 por dimensiones
complementarias —forma de invocación y comportamiento/reemplazo de imagen—.
La autoría y los libros distintos hacen plausible la independencia
documental, aunque ambos textos están en contextos de seguridad. Las otras
tres referencias se evaluaron por separado; dos quedan propuestas grado 0
por ser solo una mención y una entrada de índice. Ver
[el informe detallado](../reports/gate2_v2400_review_batch_syn_014_complementarity_2026-09-28.md).
La evaluación inicial se refinó contra el alcance exacto de `SYN-014`: sus
facetas explícitas son sintaxis de invocación y comportamiento, cubiertas
respectivamente por Tori y Stallings e incluidas en `expected`. El conjunto
se propone ahora **suficiente para esas facetas centrales**, no como referencia
API/POSIX exhaustiva ni como resolución de `SYN-016`. Es una propuesta de
suficiencia, no una decisión canónica; los cinco qrels históricos siguen
`PENDING`. No se modificaron datos históricos ni ACL, y no se ejecutó
retrieval.

## Señales diagnósticas de duplicación y procedencia

Se añadió
[`gate2_evidence_relations.py`](../src/study_engine/diagnostics/gate2_evidence_relations.py)
como ayuda local opt-in para comparar pares de pasajes ya seleccionados:
usa RapidFuzz para similitud textual, SimHash determinista para distancia
aproximada y metadatos de procedencia (`source_id`, documento, autor y
páginas) leídos desde SQLite en modo solo lectura. Se instala únicamente para
esta tarea con `pip install -e '.[gate2-diagnostics]'`; no es dependencia del
runtime normal.

El resultado solo emite señales como `REVIEW_POSSIBLE_DUPLICATE`, similitudes
y razones de procedencia. No concluye que los textos sean duplicados,
independientes o corroborativos: `independence_decision` permanece
`NOT_ADJUDICATED`, la decisión canónica queda `null` y se exige revisión
humana. Contrato: la salida diagnóstica nunca promueve, degrada, excluye ni
canoniza un qrel; no produce acciones qrel. Las señales no deben usarse para
asignar grados ni modificar qrels. La herramienta es por pares y sobre IDs
explícitos, con un máximo de 100 evidencias por lote; no recorre masivamente el
knowledge store ni ejecuta retrieval. La comparación de páginas usa la
procedencia `source_id` y no depende de que los IDs internos de documento
coincidan, pues ingestas distintas pueden representar la misma página con
`document_id` diferente.

La validación inicial v0.1 sobre cuatro micro-lotes reales está en
[informe](../reports/gate2_evidence_relation_tool_validation_2026-09-28.md)
y [JSON](../reports/gate2_evidence_relation_tool_validation_2026-09-28.json).
En 78 comparaciones por query no hubo pares que cruzaran simultáneamente los
umbrales textuales; sí hubo señales de procedencia compartida en fragmentos
conocidos de las páginas 373, 301 y 760, incluidos casos con `document_id`
distinto. Las fuentes complementarias de SYN-014 no se marcaron como
procedencia compartida. La validación confirma utilidad como señal de triage,
no precisión corpus-wide; las salidas no alteran propuestas ni decisiones
qrel.

La suite adversarial reproducible está en
[`gate2_evidence_relations_adversarial.json`](../tests/fixtures/gate2_evidence_relations_adversarial.json)
y sus pruebas cubren duplicado exacto, variación OCR, fragmento contenido,
misma página con distinto contenido/`document_id`, misma fuente en páginas
distintas, misma afirmación entre fuentes, evidencia complementaria, texto
corto, colisión léxica `fork`/`pipe`/`dup2` y contenido ajeno. Los ejemplos
están separados en `development` y `holdout`; sirven para comprobar el
contrato de señales, no para estimar precisión/recall corpus-wide ni para
ajustar thresholds.

Cada caso registra por separado relación semántica esperada (solo etiqueta de
la fixture), señal textual, solapamiento de página, `source_id`, señal del
analizador y `qrel_mutation_expected=false`. La prueba confirma que la salida
no expone etiquetas semánticas, grade, aceptación o inclusión de qrel; solo
devuelve `qrel_actions=NOT_PRODUCED`, `NOT_ADJUDICATED` y decisión canónica
`null`. Se mantienen `0.88/16` sin calibrar. El texto corto idéntico se marca
como candidato textual para revisión, no como equivalencia semántica.

Después se revisó `GS2-SYN-022`…`GS2-SYN-024` (`dup2`,
`retrieval_citation`), con doce pares query/qrel. Los cuatro chunks únicos
solo nombran `dup2`: una tabla de llamadas Linux monitorizadas en un texto de
seguridad y la lista de instrucciones de una simulación Fork-pipe. En cada
página hay además una extracción fragmentaria solapada; se mantuvieron
individualizadas por query, pero no se contaron como explicaciones o
corroboraciones nuevas. Se propone grado 1 para las doce referencias por su
contexto marginal, sin evidencia sustantiva sobre operación, argumentos o
retornos.

Con umbral 2 quedan descubiertas las facetas requeridas de `SYN-022` (operación
y sintaxis/contrato), `SYN-023` (operación POSIX/Linux y efecto en
descriptores) y `SYN-024` (parámetros y retornos). Ver
[el informe detallado](../reports/gate2_v2400_review_batch_syn_022_024_adjudication_2026-09-28.md).
Las doce propuestas siguen pendientes de aceptación; no hubo cambios en
históricos, registro explícito ni ACL y no se ejecutó retrieval.

Continuando el lote de llamadas POSIX, se revisó
`GS2-SYN-026`…`GS2-SYN-028` (`pthread_create`, `retrieval_citation`), 15 pares
query/qrel. La evidencia sustantiva se concentra en la página 218 de
*Operating Systems: Internals and Design Principles*: muestra la llamada,
explica la rutina de inicio, el retorno cero/no-cero y el ciclo de vida del
hilo. Se propone grado 3 para el chunk completo frente a la pregunta de
sintaxis/comportamiento (`SYN-026`) y grado 2 en las preguntas con requisitos
más específicos/contexto POSIX-Linux y parámetros exactos (`SYN-027/028`).
El fragmento p218 se calificó por separado, pero comparte fuente/página y no
se cuenta como corroboración independiente. Las páginas 606 (compatibilidad
eCos) y 760 (mención en una lista de simulación) quedan propuestas como grado
1 en los pares por su contexto limitado.

La cobertura de facetas es diagnóstica, no una afirmación de exhaustividad:
en `SYN-028` el texto muestra la llamada y retorno cero/no-cero, pero no explica
todos los tipos/semánticas de parámetros ni enumera errores. La v0.1 de
relaciones solo ayudó a localizar pares de misma página 218/606; sus señales
no modificaron propuestas. Ver
[el informe detallado](../reports/gate2_v2400_review_batch_syn_026_028_adjudication_2026-09-28.md).
Las quince propuestas siguen pendientes de aceptación; golden set, qrels,
registro y ACL permanecen intactos y no se ejecutó retrieval.

El siguiente lote de llamadas de sistema por intención/oráculo fue
`GS2-SYN-018`…`GS2-SYN-020` (`pipe`, `retrieval_citation`). La lectura de sus
quince pares query/qrel separó tres sentidos: la tubería IPC de Unix
(`chk_76e248a62974_305_1`), el operador de shell `|` (pp. 197–198 de
*Seguridad en Redes*) y el uso metafórico de “pipe” para un enlace de red.
Solo el texto de sistemas operativos aporta evidencia sustantiva de operación
IPC (grado propuesto 2), sin especificar la interfaz `pipe(2)`; las muestras
de shell quedan como contexto marginal (grado 1) y la metáfora de red como
irrelevante (grado 0). Para `SYN-020`, ninguna referencia cubre a grado
sustantivo los parámetros exactos o los retornos.

La cobertura de facetas se usó solo como diagnóstico: `SYN-018` y `SYN-019`
obtienen cobertura de las dimensiones de comportamiento respaldadas por el
texto de sistemas operativos, sin inferir cobertura de una firma o contrato
de retorno de `pipe(2)` que no se pidió en esas consultas; las facetas de
parámetros y retornos de `SYN-020` quedan descubiertas.
Ver
[el informe detallado](../reports/gate2_v2400_review_batch_syn_018_020_adjudication_2026-09-28.md).
Las quince decisiones siguen pendientes de aceptación; no se modificaron
históricos, registro explícito ni ACL y no se ejecutó retrieval.

Como siguiente lote por tema y oráculo se revisaron `GS2-SYN-011` y
`GS2-SYN-012` (`fork`, `retrieval_citation`). La lectura de los diez chunks
identificó una colisión léxica: los qrels principales remiten a cubiertos del
problema de los filósofos, no al syscall de creación de procesos. En `SYN-011`
dos fragmentos solo identifican marginalmente el API/syscall (grado propuesto
1); ninguno explica sustantivamente su operación. En `SYN-012`, que pide
parámetros y valores de retorno, las cinco referencias quedan propuestas
grado 0. El análisis auxiliar de cobertura deja descubiertas las facetas
requeridas con umbral 2; no decide canonización ni invalida por sí solo la
consulta. Ver
[el informe detallado](../reports/gate2_v2400_review_batch_syn_011_012_adjudication_2026-09-28.md).
Las diez decisiones siguen pendientes de aceptación; no se modificaron qrels,
golden set, registro explícito ni ACL, y no se ejecutó retrieval.

SYN-014 queda preservada como fixture de referencia
[`gate2_syn_014_facet_coverage.json`](../tests/fixtures/gate2_syn_014_facet_coverage.json)
para el criterio de suficiencia por facetas. La función
[`evaluate_facet_coverage`](../src/study_engine/diagnostics/gate2_facet_coverage.py)
solo calcula cobertura frente a un umbral de grado propuesto y falla ante
facetas sin evidencia elegible o referencias desconocidas; independencia,
complementariedad y aceptación canónica se mantienen como juicios separados.
Las pruebas del fixture confirman que rebajar la única evidencia de sintaxis
por debajo del umbral deja explícitamente esa faceta sin cubrir.

La misma función se verifica también con la fixture de
[`GS2-CMP-011`](../tests/fixtures/gate2_cmp_011_facet_coverage.json), un caso
de comparación mutex/semáforo con dos facetas distintas: las decisiones
previamente adjudicadas cubren el semáforo a grado 2, pero el mutex quedó a
grado 1 y no alcanza el umbral de cobertura de propiedad del hilo. El resultado
debe señalar solo esa faceta como descubierta. Ambos chunks provienen de la
misma fuente, y la prueba no los considera independientes ni modifica el
registro o los qrels.
