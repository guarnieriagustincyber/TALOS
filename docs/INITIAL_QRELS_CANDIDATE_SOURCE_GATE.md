# Initial Qrels Candidate Source Gate

**Estado:** `BLOCKED_SOURCE_UNSELECTED`<br>
**Resultado de la investigación:** `SOURCE_INSUFFICIENT`<br>
**Pregunta del gate:** ¿qué fuente metodológicamente independiente proporciona
los primeros pares consulta/chunk para qrels iniciales?<br>
**Contrato de benchmark:** sin cambios; permanece congelado.<br>
**Ejecución técnica:** ninguna.

## Hallazgo que abre el gate

Los paquetes ciegos actuales contienen 400 consultas por juez, pero **cero pares
consulta/chunk y cero contenido de chunks**. Permiten una revisión de intención
y scope; no permiten asignar grados de relevancia ni producir qrels.

El contrato requiere qrels iniciales antes de ejecutar cualquier backend. La
expansión pooled posterior exige candidatos de Qwen, E5 y baseline lexical, que
solo se considera después de congelar qrels iniciales. Usar esos resultados
para fabricar los qrels iniciales violaría el orden acordado. No se ejecutará
ningún backend para resolver esta dependencia sin autorización separada.

## Auditoría read-only de procedencia

Se inspeccionaron los datasets v2.400/v2.401, qrels, fixtures backend, el
inventario y cola Gate 2, registro de decisiones, paquetes de review/adjudicación
v2.402, auditorías de candidatos y los reportes de revisión query/qrel
existentes. La búsqueda local encontró 17 reportes JSON con alguna relación
`query_id`–`chunk_id`; son representaciones solapadas de evidencia anterior,
no 17 fuentes distintas. No se modificaron esos datos ni se ejecutó retrieval.

| Hallazgo | Procedencia comprobada | Evaluación para qrels iniciales |
|---|---|---|
| v2.400: 165 referencias positivas en 48 consultas; `expected.relevant_chunks` coincide con las referencias heredadas | La documentación de Gate 2 registra que los grados heredados 3/2/1 se asignaron por posición de retrieval, no por juicio semántico | Rechazada como fuente independiente de candidatos y labels |
| Cola/inventario y lotes de adjudicación v2.400: referencias y candidatos de revisión | La cola copia las referencias de qrels históricos; los lotes citan sus `chunk_id` como base de revisión | Revisión manual posterior no elimina el sesgo de selección del pool original |
| Gate 2 pilot v2.402: candidatos y qrels de `GS2-VULN-004` | El manifiesto registra `retrieval_executed=true`, top-k 1, `qrels_provenance=retrieval_proposal`; la adjudicación fue de un solo revisor y luego aceptada por el usuario | Rechazada como independiente de los rankings; aprobación semántica no cambia cómo se seleccionó el candidato |
| Gate 2 positive-segments: `GS2-VULN-007` y `GS2-VULN-018` | La selección-review declara inputs v2.400/qrels leídos sin retrieval; todos los candidatos examinados corresponden a referencias qrel históricas | Procedencia de candidate-set heredada; no es un pool inicial independiente |
| Auditoría de scopes bloqueados: pasajes de `fadena-teleco` y `fadena-std` | El informe especifica búsquedas locales FTS con anclas léxicas curadas; cinco pares inspeccionados, uno ya qrel histórico; una nueva pareja de `GS2-CMP-011` fue aceptada por el usuario y las otras cuatro fueron excluidas | Evidencia local rastreable e independiente del ranking denso, pero explícitamente léxica, correlacionada con FTS/BM25 y muy incompleta; no cumple independencia del baseline ni cobertura suficiente |
| Golden-set scopes/KC/tags y relaciones notebook-source | Asignaciones de query a scope, tema o fuentes; no son asociaciones juzgadas de query a chunk | No proporcionan pares adjudicables |
| Fixtures de backend selection | Casos sintéticos de formato/validación | No son evidencia del corpus real |

La búsqueda de reportes halló **un** nuevo par real aceptado que no aparece en
los qrels v2.400 (`GS2-CMP-011` → `chk_db97c77518c6_821_1`, grado 2). Su
procedencia documentada es una búsqueda FTS con anclas léxicas y revisión
humana de un solo par; puede servir como evidencia puntual, pero no como
fuente independiente del baseline lexical ni como cobertura del benchmark.
Los demás pares reales revisados en estos artefactos provienen de qrels
históricos o de propuestas basadas en ellos.

La independencia de un juicio de relevancia y la independencia de la selección
del candidato son claims separados. Aprobaciones humanas pueden mejorar la
confianza en la etiqueta de un par, pero no vuelven independiente la fuente que
seleccionó ese par. Del mismo modo, inspección FTS no equivale al ranking
BM25/FTS de producción, pero comparte el canal léxico y no califica como fuente
independiente bajo la pregunta estricta de este gate.

## Estado de las fuentes consideradas

| Fuente candidata | Evidencia actual | Estado |
|---|---|---|
| Paquetes de jueces existentes | Consultas y scopes; no contienen chunks ni pares | Insuficiente |
| Qrels históricos v2.400 | 165 referencias en 48 queries, generadas/rankeadas históricamente por retrieval | Rechazados como fuente independiente |
| Decisiones previas de Gate 2 | Algunas decisiones semánticas explícitas, pero los candidatos proceden de qrels históricos; piloto v2.402 registra retrieval | No reparan independencia de selección |
| Auditoría local FTS de scopes | Cinco pares inspeccionados; una pareja nueva aprobada, con búsqueda lexical curada | Independiente del ranking denso, no del canal lexical; incompleta |
| Búsqueda lexical usada como baseline | No se ejecutó para este gate; la auditoría FTS previa comparte familia metodológica | No aprobar como única fuente inicial |
| Qwen/E5 | Requeriría inferencia/candidate generation antes de qrels iniciales | Prohibido en esta fase |
| Selección humana independiente de evidencia curricular | Metodológicamente posible si se define un procedimiento repetible y no guiado por rankings de los backends | No demostrada/disponible todavía |

**Conclusión:** no se encontró una fuente ya disponible que demuestre
procedencia independiente de Qwen, E5 **y** del baseline lexical con cobertura
adecuada para crear los qrels iniciales. Resultado `SOURCE_INSUFFICIENT`; el
estado operativo permanece `BLOCKED_SOURCE_UNSELECTED`. No se presume que una
fuente exista por el solo hecho de que haya chunks en la base.

## Rutas que podrían evaluarse en el gate

### A. Evidencia curricular seleccionada independientemente

Definir un procedimiento de selección de chunks basado en navegación curricular
o inspección humana del material, sin rankings de Qwen/E5 ni una recuperación
lexical exclusiva. Antes de generar paquetes habría que fijar:

- universo de chunks elegibles y scope/ACL aplicable por consulta;
- cómo se eligen candidatos y cómo se evita selección retrospectiva favorable;
- trazabilidad de cada par a chunk, fuente y snapshot hasheado;
- cobertura por consulta y tratamiento de consultas sin evidencia candidata;
- reviewers independientes, aliases opacos, evidencia visible y adjudicación;
- regla explícita para las consultas OOD y las negativas dentro del scope.

Esta ruta no se considera factible hasta que el protocolo pueda aplicarse de
forma uniforme y auditable al corpus completo.

### B. Autorizar una fase separada de candidate generation para pool ciego

El usuario podría autorizar una actividad experimental delimitada para que los
backends produzcan candidatos exclusivamente para construir el pool ciego,
**sin calcular métricas, comparar calidad, seleccionar backend ni activar
producción**. Esta ruta requiere una autorización nueva que especifique
modelos, artefactos, dependencias, hardware, límites operacionales, almacenamiento,
aislamiento y conducta ante fallos. La generación no se deriva de la
autorización de adjudicación humana existente.

Una búsqueda lexical se incluiría según el pooling del contrato, no se tomaría
como fuente única por defecto.

## Condiciones de salida

El gate solo puede cerrarse al documentar una fuente seleccionada y un
procedimiento verificable que:

1. no use resultados de Qwen/E5 para producir qrels iniciales;
2. no confunda qrels históricos no confirmados con juicios nuevos;
3. preserve scope/ACL y versionado/hash de corpus, pares y paquetes;
4. entregue evidencia suficiente a ambos jueces, con asignación ciega e
   independiente;
5. mantenga `UNKNOWN` distinto de grado 0 y no declare cobertura exhaustiva por
   ausencia de candidatos;
6. indique explícitamente si candidate generation requiere una autorización
   separada.

El resultado de este gate puede ser `SOURCE_APPROVED`, `SOURCE_INSUFFICIENT` o
`REQUIRES_SEPARATE_EXPERIMENT_AUTHORIZATION`. Ningún resultado por sí solo
congela qrels ni habilita el benchmark completo.

Con la evidencia presente, la ruta sin fuente independiente suficiente es
solicitar una autorización separada y delimitada para generar un pool ciego.
Esto es una recomendación de proceso, **no** una autorización concedida: no se
ejecutará Qwen/E5, recuperación lexical, candidate generation ni instalación de
dependencias bajo la autorización humana vigente.
La propuesta y el límite de autorización están registrados en el
[Blind Pool Generation Authorization Gate](./BLIND_POOL_GENERATION_AUTHORIZATION_GATE.md),
que permanece `PENDING`.

## Límites vigentes

Hasta cerrar el gate y obtener cualquier autorización adicional:

- no generar candidatos ni ejecutar recuperación;
- no ejecutar Qwen, E5 ni baseline lexical;
- no generar embeddings, descargar/instalar modelos ni crear índices;
- no puntuar métricas ni elegir backend;
- no alterar paquetes existentes, qrels históricos, índices ni producción.

`READY_FOR_HUMAN_ADJUDICATION` describía la preparación de paquetes; no elimina
este bloqueo material. El estado de pares/query-chunk es
`ADJUDICATION_BLOCKED_NO_CANDIDATE_PAIRS`.
