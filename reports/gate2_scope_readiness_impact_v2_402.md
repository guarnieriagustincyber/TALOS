# Gate 2 — Inventario de readiness e impacto de la fixture v2.402

**Fecha:** 2026-09-28  
**Modalidad:** auditoría local, sin retrieval; consultas SQLite read-only para
ACL y chunks referenciados.  
**Conclusión:** la fixture de seis consultas es elegible como subconjunto
estructural, pero **no completa ni libera los scopes del benchmark histórico**.

## Impacto cuantitativo

| Métrica | v2.400 histórico | v2.401 histórico | Fixture nueva |
|---|---:|---:|---:|
| Consultas | 400 | 420 | 6 |
| Scopes distintos | 6 | 1 (`NB-SEC-01-C-PTR`) | 5 |
| Consultas con qrels | 48 | 360 | 4 |
| Referencias qrel | 165 | 1704 | 5 |
| Consultas positivas en fixture con qrels | — | — | 4/4 |
| Negativas por scope / OOD global en fixture | — | — | 1 / 1 |

Cinco IDs de la fixture ya existían en v2.400 y uno (`G2-PILOT-NEG-001`) es
un control agregado. Por tanto, la fixture representa **6/400 (1,5%)** de los
casos v2.400 contando el control nuevo, o **5/400 (1,25%)** de IDs históricos
distintos. Los cinco qrels representan **5/165 (3,0%)** de las referencias
qrel históricas v2.400. Estos cocientes miden alcance, **no calidad, ranking
ni rendimiento**.

La validación estructural del paquete reporta `release_eligible=true` para
estas seis consultas y sus decisiones; no significa que los scopes completos
ni v2.400/v2.401 sean liberables. Cuatro consultas positivas tienen qrels;
una OOD y una negativa por scope conservan qrels vacíos. El manifiesto indica
`mode=fixture` y `retrieval.executed=false`.

## Readiness por scope

Los totales históricos son los de v2.400; el estado de fixture se refiere solo
al subconjunto de seis consultas. “ACL operativa” indica que el scope tiene
asociaciones persistidas en la base; **no** prueba pertinencia curricular ni
resuelve qrels históricos.

| Scope | v2.400 consultas / qrel refs | Fixture v2.402: consultas | Estado del segmento incluido | Readiness del scope completo |
|---|---:|---|---|---|
| `NB-CYBERSECURITY-V1` | 10 / 7 | `GS2-VULN-004` (positiva; 2 qrels) | Estructuralmente validado | **Incompleto**: un caso de 10; no es adjudicación del conjunto completo |
| `NB-SEC-01-C-PTR` | 330 / 131 | `GS2-VULN-018` (positiva; 1 qrel), `GS2-OOD-001` (OOD) | Estructuralmente validado | **Bloqueado para reparación/liberación completa**: el historial incluye 330 casos; v2.401 reasignó 70 consultas a este scope y en esas referencias 224/330 qrels no respetan los scopes v2.400 correspondientes. No podar ACL ni usar las métricas históricas como base |
| `fadena-so2` | 10 / 5 | `GS2-VULN-007` (positiva; 1 qrel) | Estructuralmente validado | **Incompleto**: un caso de 10; no habilita el benchmark completo del scope |
| `fadena-std` | 10 / 0 | `GS2-CMP-011` (positiva; 1 qrel grado 2) | Estructuralmente validado tras adjudicación | **Incompleto**: solo un caso de 10 y evidencia parcial; nueve consultas históricas siguen fuera de esta fixture |
| `fadena-lenguajes` | 20 / 6 | `G2-PILOT-NEG-001` (negativa por scope) | Control negativo estructuralmente validado; no es positivo | **Bloqueado para positivos de `clone()`**: los qrels históricos de GS2-SYN-002/003/004 tratan function-cloning GNU C, no el syscall Linux. La negativa no resuelve ese mismatch |
| `fadena-teleco` | 20 / 16 | Ninguna | No representado | **Bloqueado**: los qrels históricos no corresponden a la comparación Stack/Heap solicitada; los tres candidatos adjudicados grado 1 se excluyeron |

La ACL activa contiene asociaciones para los seis scopes de v2.400. El conteo
read-only distingue cantidad de fuentes asociadas y chunks alcanzables:

| Scope | Fuentes asociadas | Asociaciones con source registrado | Chunks asociados |
|---|---:|---:|---:|
| `NB-CYBERSECURITY-V1` | 10 | 10 | 36.847 |
| `NB-SEC-01-C-PTR` | 42 | 41 | 105.179 |
| `fadena-lenguajes` | 17 | 17 | 15.459 |
| `fadena-so2` | 14 | 14 | 12.371 |
| `fadena-std` | 30 | 30 | 46.530 |
| `fadena-teleco` | 12 | 12 | 27.475 |

`NB-SEC-01-C-PTR` conserva una asociación huérfana, ya documentada en la
auditoría de identidad. La existencia de estas asociaciones solo confirma que
la ACL está persistida; no otorga aprobación curricular ni evidencia semántica.

## Contexto histórico e integridad

- v2.400 distribuía sus 400 consultas entre los seis scopes de la tabla.
  En los **165 chunks qrel referenciados** se confirmó, por scope histórico,
  que existen en la base y su source pertenece a la ACL activa persistida para
  ese scope: **0 inexistentes y 0 fuera de ACL**. Esto acredita membership
  contra el estado actual, no reconstruye una ACL histórica ni demuestra
  relevancia semántica; permanecen los problemas de clasificación/oráculo y
  qrels temáticamente incorrectos descritos en las auditorías previas.
- v2.401 asigna sus 420 consultas exclusivamente a `NB-SEC-01-C-PTR` y contiene
  1.704 referencias qrel. La auditoría anterior registró 224 referencias fuera
  de los scopes v2.400 de las 70 consultas que habían cambiado de scope.
  v2.401 no es una reparación confiable por sí sola.
- La fixture de seis consultas mantiene cuatro segmentos positivos con qrels
  adjudicados y dos segmentos de abstención/aislamiento sin qrels. No se
  generaron resultados de retrieval ni métricas de ranking.
- Hashes revisados:
  - v2.400 dataset: `7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1`
  - v2.400 qrels: `68af7033fcd4e607b830245901774d2daac610d909763cb0b999b024b1ed7abc`
  - v2.401 dataset: `4442e267f5c5eddb778fa2f36065db4841a8c221fbc4ee7a12aa8513ef844857`
  - v2.401 qrels: `a76b18d6b113b164c3e68455577bfea8777789af4efb179464ad1d8be87d32e6`
  - knowledge store: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`

## Decisión de readiness y siguiente Gate

1. **Bloqueados por evidencia positiva:** `fadena-lenguajes` para el caso
   `clone()` y `fadena-teleco` para Stack/Heap. No tienen positivos aprobados en
   la fixture actual.
2. **Segmento positivo presente, scope global incompleto:** `NB-CYBERSECURITY-V1`,
   `NB-SEC-01-C-PTR`, `fadena-so2` y `fadena-std`. `fadena-std` tiene un caso
   nuevo aprobado de grado 2, pero esto no adjudica sus otros nueve casos.
3. **Gate global v2.400/v2.401:** sigue bloqueado. La fixture cubre seis casos,
   no revisa las 400/420 consultas, no corrige metadata histórica y no produce
   evidencia de retrieval o abstención end-to-end.
4. Próximo paso: desglosar los casos pendientes por scope y adjudicar/descartar
   decisiones curriculares y qrels en paquetes independientes. Mantener las
   ACL y los golden sets inmutables; no ejecutar retrieval ni el benchmark
   completo hasta que el plan de cobertura tenga positivos y oráculos aprobados
   por cada scope que se pretenda incluir.

## Fuentes de evidencia

- [Runbook de scopes Gate 2](../docs/GATE2_BENCHMARK_SCOPE_RUNBOOK.md)
- [Auditoría local de evidencia](./gate2_scope_evidence_audit_2026-09-28.md)
- [Adjudicación de cinco candidatos](./gate2_scope_candidate_adjudication_2026-09-28.json)
- [Fixture v2.402 de seis consultas](./gate2_scope_candidate_adjudicated_v2_402/)
- [Validación estructural/ACL](./gate2_scope_candidate_adjudicated_v2_402/gate2_v2.402-positive-segments-std-mutex-adjudicated.segment-validation.json)
