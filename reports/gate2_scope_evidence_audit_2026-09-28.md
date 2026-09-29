# Gate 2 — Auditoría local de evidencia para scopes bloqueados

**Fecha:** 2026-09-28  
**Estado:** inspección completada; las propuestas siguen pendientes de
adjudicación semántica.  
**Alcance:** `fadena-lenguajes`, `fadena-teleco` y `fadena-std`.

## Método y límites

- Corpus consultado: `data/web_state/knowledge_store.db`, mediante conexión
  SQLite `mode=ro`.
- La inspección se limitó a fuentes que aparecen en la ACL persistida de cada
  scope; no se modificaron ACL, chunks, datasets históricos ni qrels.
- Se usaron búsquedas lexicales locales sobre `chunks_fts` y lectura de los
  pasajes candidatos. **No** se ejecutó el pipeline de retrieval del producto,
  embeddings, reranking, generación ni benchmark.
- Los grados de abajo son propuestas para revisión humana; no son qrels
  aprobados ni fueron agregados a un dataset.
- La pertenencia a ACL acredita autorización técnica del source, no pertinencia
  curricular ni relevancia semántica suficiente.

Fingerprints comprobados al terminar la inspección:

| Recurso | SHA-256 |
|---|---|
| `data/web_state/knowledge_store.db` | `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` |
| `data/eval/golden_set_v2_400.json` | `7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1` |
| `data/eval/qrels/golden_set_v2_400.qrels.json` | `68af7033fcd4e607b830245901774d2daac610d909763cb0b999b024b1ed7abc` |
| `data/eval/golden_set_v2_401.json` | `4442e267f5c5eddb778fa2f36065db4841a8c221fbc4ee7a12aa8513ef844857` |

## Hallazgos

### `fadena-lenguajes` — `clone()` / syscall

**Resultado: bloqueado; no se encontró evidencia positiva defendible para las
consultas actuales.**

La ACL contiene 17 fuentes. Las búsquedas por `clone`, `clone3`, `sys_clone`,
syscall, flags, proceso y Linux solo devolvieron pasajes del *GNU C Language
Reference Manual* sobre el atributo de optimización *function cloning*. Los
chunks históricos `chk_fa5f80f8da3c_233_1` y
`GNU-c-language-manual.pdf:p233:c0004` describen ese atributo del compilador,
no la llamada al sistema Linux `clone()` ni sus flags, recursos compartidos o
valores de retorno.

No se propone qrel nuevo. Mantener bloqueadas `GS2-SYN-002`,
`GS2-SYN-003` y `GS2-SYN-004` hasta que haya material autorizado que cubra el
syscall, o hasta una decisión curricular explícita de cambiar el objetivo.

### `fadena-teleco` — Stack vs Heap

**Resultado: hay evidencia marginal de algunas dimensiones, pero no una
respuesta suficiente al objetivo completo.**

El scope tiene 12 fuentes autorizadas. Los qrels históricos para
`GS2-CMP-001`, `GS2-CMP-002`, `GS2-CMP-004` y `GS2-CMP-005` apuntan a
buffer-overflow, mitigaciones de seguridad y detalles de stack frame; no
justifican las calificaciones altas históricas para la comparación solicitada.

Se encontraron los siguientes candidatos locales en *Computer Security:
Principles and Practice*; los tres están bajo la ACL de `fadena-teleco`:

| Chunk candidato | Grado propuesto | Evidencia parcial | Falta respecto de la consulta |
|---|---:|---|---|
| `chk_0aa9aa4cc0b2_365_1` | 1 | Explica que el frame local se reserva al entrar a la función y se descarta al retornar. | No explica el ciclo de vida del heap ni compara velocidades. |
| `chk_0aa9aa4cc0b2_366_1` | 1 | Describe la disposición del espacio de proceso, crecimiento opuesto de stack/heap y frames colocados uno debajo de otro. | No desarrolla contigüidad comparativa ni velocidad de asignación. |
| `chk_0aa9aa4cc0b2_416_1` | 1 | Indica que la memoria dinámica del heap se reserva cuando se necesita y se libera al terminar. | No compara con stack ni trata contigüidad o velocidad. |

Las tres piezas podrían ser útiles marginalmente en conjunto, pero ninguna
contesta todas las dimensiones de vida útil, contigüidad y velocidad. No crear
qrels aún. Mantener el scope bloqueado hasta que se adjudique si estos pasajes
parciales sirven para el benchmark tal como está redactado o si se debe
replantear la consulta; no propagar decisiones a las variantes 002/004/005 por
similitud textual.

### `fadena-std` — Mutex vs semáforo contador

**Resultado: se encontraron dos candidatos ACL-autorizados, con cobertura
parcial complementaria.**

La ACL contiene 30 fuentes. Dentro de *Fluent Python*:

| Chunk candidato | Grado propuesto | Evidencia parcial | Falta respecto de la consulta |
|---|---:|---|---|
| `chk_db97c77518c6_729_1` | 2 | Identifica el mutex como lock de exclusión mutua y explica el uso del lock para proteger una estructura compartida. | No establece explícitamente la propiedad del lock por el hilo que lo adquiere. |
| `chk_db97c77518c6_821_1` | 2 | Presenta el semáforo de Dijkstra y explica su contador, `acquire`, `release` y la espera cuando el contador llega a cero. | El desarrollo concreto corresponde a `asyncio.Semaphore`; no profundiza en todas las variantes de semáforo contador ni contrasta directamente su propiedad con la del mutex. |

Estos chunks parecen responder una parte sustancial de la distinción, pero la
dimensión de propiedad del mutex queda sin evidencia explícita y el pasaje de
semáforo está contextualizado en Python/asyncio. Proponerlos para adjudicación
manual, no incorporarlos automáticamente. No propagar los qrels a
`GS2-CMP-012`…`GS2-CMP-015`: esas variantes añaden rendimiento, seguridad,
trade-offs o ejemplos que estos pasajes no cubren.

## Estado de salida

| Scope | Resultado | ¿Qrels incorporados? | Próxima decisión |
|---|---|---:|---|
| `fadena-lenguajes` | Sin evidencia pertinente para el syscall `clone()` | No | Conseguir material autorizado o mantener bloqueado |
| `fadena-teleco` | Candidatos grado 1; cobertura parcial incompleta | No | Adjudicar candidatos o ajustar la pregunta |
| `fadena-std` | Candidatos grado 2; distinción parcial complementaria | No | Adjudicar candidatos y aceptar explícitamente las limitaciones |

Esta inspección no cambia la elegibilidad ni el contenido del paquete
`v2.402-positive-segments-adjudicated`. No habilita retrieval, ampliación del
benchmark, ni liberación de los tres scopes bloqueados.

## Adjudicación de candidatos — 2026-09-28

El usuario adjudicó individualmente los cinco candidatos según la pregunta
completa y la rúbrica semántica. Las decisiones quedan registradas en
[gate2_scope_candidate_adjudication_2026-09-28.json](./gate2_scope_candidate_adjudication_2026-09-28.json):

| Scope | Chunk | Grado | Decisión |
|---|---|---:|---|
| `fadena-teleco` | `chk_0aa9aa4cc0b2_365_1` | 1 | Excluir de qrels |
| `fadena-teleco` | `chk_0aa9aa4cc0b2_366_1` | 1 | Excluir de qrels |
| `fadena-teleco` | `chk_0aa9aa4cc0b2_416_1` | 1 | Excluir de qrels |
| `fadena-std` | `chk_db97c77518c6_729_1` | 1 | Excluir de qrels: no acredita ownership del mutex |
| `fadena-std` | `chk_db97c77518c6_821_1` | 2 | Aceptar como evidencia parcial |

Solo se publicó el qrel grado 2 en una **nueva fixture**:
[v2.402-positive-segments-std-mutex-adjudicated](./gate2_scope_candidate_adjudicated_v2_402/).
La consulta `GS2-CMP-011` de `fadena-std` se incorporó al fixture con el qrel
`chk_db97c77518c6_821_1: 2`. El
[reporte read-only](./gate2_scope_candidate_adjudicated_v2_402/gate2_v2.402-positive-segments-std-mutex-adjudicated.segment-validation.json)
pasó con `status=passed`, `release_eligible=true`, seis consultas, cinco
chunks qrel y cero adjudicaciones pendientes. El manifiesto registra
`mode=fixture` y `retrieval.executed=false`.

Los tres candidatos de `fadena-teleco` y el candidato mutex de
`fadena-std` permanecen fuera de qrels. `fadena-lenguajes` sigue bloqueado por
la acepción incorrecta de `clone`. El paquete
`v2.402-positive-segments-adjudicated`, golden sets históricos y ACL activa
no se modificaron.
