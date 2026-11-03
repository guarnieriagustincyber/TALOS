# TALOS V1.5 — STEP-23C.1: Adjudicación final de evidencia y consistencia

**Resultado:** `ADJUDICATED_WITH_OPEN_BLOCKERS`  
**Estado canónico:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`  
**Anomalía histórica:** `UNRESOLVED_HISTORICAL_EVIDENCE`  
**Harness externo:** implementación no autorizada  
**B1-R:** ejecución no autorizada  
**Código y perímetro:** sin cambios autorizados por esta fase

## 1. Identidad, alcance y estado inicial

`OBSERVED`: repositorio `/media/agustin/Laboratorio/study-engie`, rama `talos-current-audit`, HEAD `cc8acfae623f9d10c8366871470319786b6a7ca4`. Coinciden con la identidad esperada. El informe nuevo estaba ausente antes de crearlo.

`OBSERVED`: la captura nominal de STEP-23C antes de crear sus dos informes tiene 1.863 rutas staged, 23 unstaged, 84 untracked; la salida Git actual antes de crear este informe tiene digest `f720d1ceb5ea1587ae8e7ff001851dfab0202888da4a33ea48d41385d1a06d4e`, igual al declarado por la captura final de STEP-23C. No se usa esa captura para reconstruir estados anteriores a STEP-23C.

Se revisaron los ocho expedientes existentes:

1. [Contrato de ejecución STEP-22](./STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md)
2. [Matriz de fronteras STEP-22](./STEP-22-TRUST-BOUNDARY-MATRIX.md)
3. [Matriz de agregación y rechazos STEP-22](./STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md)
4. [Decisiones y bloqueos STEP-22](./STEP-22-DECISIONS-AND-BLOCKERS.md)
5. [Anomalía Git STEP-23A](./STEP-23A-GIT-ANOMALY-ADJUDICATION.md)
6. [Capturas históricas STEP-23B](./STEP-23B-HISTORICAL-INDEX-CAPTURE-VALIDATION.md)
7. [Baseline STEP-23C](./STEP-23C-BASELINE-ACTUAL-Y-PRESERVACION-DEL-ESTADO.md)
8. [Adjudicación STEP-23C](./STEP-23C-ADJUDICACION-DOCUMENTAL-Y-BLOQUEOS-ABIERTOS.md)

`DOCUMENTED`: STEP-23A terminó `PARTIALLY_RECONCILED`; STEP-23B terminó `UNRESOLVED_HISTORICAL_EVIDENCE`. STEP-23C no revirtió ni autenticó esos estados históricos.

Clases usadas: `OBSERVED` = inspección directa de artefactos/estado; `DOCUMENTED` = afirmación contenida en documento; `PROPOSED` = diseño futuro no desplegado; `INFERRED` = conclusión acotada; `UNVERIFIED` = no demostrada por la evidencia disponible.

## 2. Capturas y discrepancia histórica 82/84

`OBSERVED`: se recalcularon los digests de ambas capturas externas STEP-23C:

| Captura | Bytes / líneas | SHA-256 recalculado | Resultado |
|---|---:|---|---|
| `step23c-git-status-v2.txt` | 407.534 / 1.957 | `5877c09f5d2729b5066bf36cfd4f3f31a4e6fdb82e50e1a946a3fddc7848fe5c` | Coincide con STEP-23C |
| `step23c-git-status-v2-final.txt` | 407.658 / 1.959 | `f720d1ceb5ea1587ae8e7ff001851dfab0202888da4a33ea48d41385d1a06d4e` | Coincide con STEP-23C y con una nueva salida nominal pre-informe |

Las capturas están en el directorio persistente de esta sesión, fuera del repositorio. `OBSERVED`: sus bytes coinciden con los digests declarados y la captura final corresponde a la salida nominal consultada ahora. `UNVERIFIED`: el digest no autentica host, reloj, productor ni cadena de custodia; tampoco autentica retroactivamente capturas STEP-23A.

`DOCUMENTED`: STEP-23A registró 82 entradas untracked; STEP-23C contó 84 con `--untracked-files=all`. `OBSERVED`: la captura STEP-23C enumera como untracked, entre otras, las dos rutas de informes STEP-23A y STEP-23B. `DOCUMENTED`: esos informes se crearon en sus respectivas fases después de las observaciones iniciales citadas.

Esto da una explicación acotada para dos rutas presentes en la captura posterior, pero **no demuestra que esas sean exactamente las únicas dos diferencias entre ambos inventarios**. Las capturas nominales temporales de STEP-23A ya no están disponibles; no se puede comparar el conjunto completo ruta por ruta ni comprobar identidad temporal, formato y conteo común para ambos instantes. La explicación de granularidad (directorios frente a archivos) descrita en STEP-23A corresponde a otra comparación y no resuelve por sí sola el delta 82/84.

**Adjudicación:** `UNRESOLVED_HISTORICAL_EVIDENCE`. No se atribuye la diferencia a un actor o fase, no se deducen rutas faltantes por aritmética y no se afirma que la causa global esté explicada. El baseline actual y sus digests solo validan las capturas STEP-23C.

## 3. Matriz de consistencia cruzada STEP-22

`DOCUMENTED`: los cuatro documentos se declaran propuestas, no implementadas. Que varias piezas repitan un requisito no lo convierte en mecanismo desplegado, aprobación externa ni evidencia runtime.

| Dimensión | Requisito/documentos | Estado | Evidencia y adjudicación | Acción pendiente |
|---|---|---|---|---|
| Aprobación, revocación y actualización | Contrato §§2–3; trust matrix §1; decisions B-01/B-06 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: requieren autoridad externa. No se identifica una persona/entidad autorizada ni un registro verificable. | Decisión de gobernanza externa; designación, alcance, revocación, actualización y revisión independiente. |
| Bootstrap y ancla independientes | Contrato §§2–4; trust matrix §1; B-02 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: se exige verificación anterior a cargar código del checkout. Se declara que no se encontró/eligió un bootstrap ni trust anchor desplegado. | Aprobar identidad, distribución, custodia y lifecycle; después demostrar provisión. |
| Identidad transitiva del controller/runtime/dependencias | Contrato §§3–4; trust matrix controller/runtime; B-03 | `NOT_IMPLEMENTED` | `PROPOSED`: cubrir imports, módulos, runtime, config y herramientas pre-worker. `UNVERIFIED`: no hay inventario aprobado ni bytes ejecutados verificados. | Inventario reproducible, procedencia aprobada y demostración de identidad efectiva. |
| TOCTOU y check-to-use | Contrato §3.3; trust matrix bootstrap/controller; B-04 | `UNDERSPECIFIED` | `DOCUMENTED`: se requiere ejecutar los mismos bytes verificados; ubicación protegida/copia inmutable son alternativas, no procedimiento seleccionado. | Elegir mecanismo aprobado y criterios de rechazo/sustitución/rollback. |
| Separación host/worker | Contrato §§2, 5; trust matrix §§1–2; aggregation §§1, 3 | `CONSISTENT` | `PROPOSED`: el host/controller autoriza, observa y agrega; el worker ejecuta inputs no confiables y no certifica su aislamiento. Coherencia documental, sin implementación demostrada. | Preservar límites y verificarlos en fase futura autorizada. |
| Comandos, roots, mounts y recursos | Contrato §§3, 5; trust matrix configuración/workspace; B-05/B-10 | `UNDERSPECIFIED` | `PROPOSED`: allowlists y límites; los valores y policy exactos no están aprobados. | Aprobar perfil, paths, capacidades, límites, timeouts/retries y reglas de versionado. |
| Integridad/procedencia de inputs, resultados y artefactos | Contrato §§4, 6; trust matrix artefactos; aggregation §§3–5 | `CONSISTENT` | `PROPOSED`: run IDs, hashes, schemas, paths permitidos y enlace producer/consumer. El hash no demuestra autenticidad, verdad, ejecución correcta o aislamiento. | Aprobar schemas/identidades y demostrar ingestión/preservación independiente. |
| Verificador independiente | Contrato §§2, 6, 8; trust matrix verifier; B-08/B-09 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: debe separarse del productor. No hay identidad externa aprobada; el verifier del checkout no adquiere independencia nominalmente. | Designar identidad/scope y demostrar que verifica los mismos bytes preservados. |
| Evidencia efectiva de aislamiento | Contrato §§5–6, 8; trust matrix observer; aggregation §4; B-08/B-11 | `NOT_IMPLEMENTED` | `PROPOSED`: evaluación separada del boundary real. `UNVERIFIED`: no hubo ejecución ni evidencia de aislamiento en esta fase. | Provisión y evaluación independientes autorizadas; no sustituir por test PASS o Git equality. |
| Git antes/después | Contrato §7; trust matrix Git; aggregation §4–5 | `CONSISTENT` | `PROPOSED`: capturas del mismo checkout/comando/scope; fallo o diferencia bloquea. El propio contrato limita la afirmación: igualdad no descarta escrituras transitorias. | Aprobar identidad del observador y, si se requiere, evidencia adicional de escrituras. |
| Agregación, errores, timeout y contradicción | Contrato §§6, 9–10; aggregation §§3–6; trust matrix agregador | `CONSISTENT` | `PROPOSED`: rechazos fail-closed para ausencia, duplicado, conflicto, error, timeout y cobertura incompleta. El agregador externo no está implementado. | Esquema/policy final y validación futura autorizada de casos negativos. |
| Caducidad, revocación y anti-rollback | Contrato §§3.1–3.3; trust matrix autoridad/bootstrap; B-01/B-02/B-06 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: obligación coherente, pero actor, formato y mecanismo no elegidos ni desplegados. | Decisión externa y prueba del ciclo de vida. |
| Responsables y salida | Decisions B-01..B-11; trust matrix §§1–4; contrato §§10–11 | `UNRESOLVED_AUTHORITY` | `DOCUMENTED`: roles y criterios propuestos; identidades de responsables no asignadas. | Designación externa; el agente no puede resolverla. |
| Estados y transiciones | Contrato §9; aggregation §6 | `UNDERSPECIFIED` | `DOCUMENTED`: estados terminales y etiquetas de etapa se mezclan en el flujo; las matrices piden conservar causas, pero no cierran una máquina formal de transición/precedencia para todas las combinaciones. | Modelo de estado normalizado, precedencia versionada y tablas de transición aprobadas. |
| Contrato de observación B1-R | Contrato §8; aggregation §§1, 3–5; `b1r_contract.json`; verifier actual | `UNDERSPECIFIED` | `DOCUMENTED`: la matriz futura define clave `(run_id, nodeid, case_id, repetition=1..3)`. `OBSERVED`: el artefacto/verifier actual verifica tres elementos ordenados por caso y repetibilidad; cada observación identifica `case_id`, pero no porta ordinal/repetition ni identidad individual de observación/run. | Fijar ordinal/ID único y binding a run/worker; verificar cardinalidad y rechazar identidad duplicada/contradictoria. |

**Decisión de consistencia:** no se halló una contradicción directa entre los cuatro documentos que invalide la arquitectura conceptual; sí hay especificaciones abiertas y bloqueos de autoridad/provisión. Por tanto, existe coherencia parcial de diseño propuesto, no un contrato operativo completo ni una aprobación.

## 4. B1-R: cobertura prevista y límites de lo verificable

`OBSERVED`: `tests/audit/b1r_contract.json` enumera exactamente diez condiciones —`success`, `error`, `abstention`, `clarification`, `truncated`, `stream_aborted`, `eof_without_terminal`, `duplicate_terminal`, `error_after_tokens`, `abrupt_close`— y `repetitions_per_case=3`. `tests/audit/test_b1_route_repeatability.py` enumera los mismos diez casos y tres repeticiones. El total **planificado** es 30; no es evidencia de ejecución.

`OBSERVED`: el verifier actual rechaza IDs de casos distintos al contrato, casos ausentes/extra, arrays de repetición cuya longitud no sea tres, observaciones mal formadas, campos/resultados que no coincidan, observaciones no repetibles y discrepancias en probes/contadores requeridos.

`OBSERVED`: ese verifier no demuestra por sí mismo identidad única por repetición, `run_id`/worker autenticado, verificación independiente del artefacto, aislamiento efectivo ni comparación Git pre/post. Estas dimensiones pertenecen a la propuesta de agregación externa y no están satisfechas por contar 30 elementos. Las reglas propuestas de rechazo para ausencias, duplicados, contradicciones, identidades inconsistentes, artefactos/verifier, aislamiento, Git y terminaciones anormales se consideran requisitos documentados, no controles desplegados.

`UNVERIFIED`: ninguna de las 30 observaciones se ejecutó durante STEP-23C.1; no se ejecutó test, script, worker ni verifier.

## 5. Perímetro y once nodeids

La lista exacta se conserva sin reclasificación: ocho items en `tests/unit/diagnostics/test_quality_gate_isolation.py`, dos en `tests/unit/diagnostics/test_quality_gate_focal_execution.py`, y el item `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile`. Sus nombres están enumerados en la matriz STEP-22 de agregación.

`OBSERVED`: [config/test_perimeter.json](../config/test_perimeter.json) clasifica `tests/unit` y `tests/audit` como `required`. La inspección estática de [quality_gate.py](../scripts/quality_gate.py) muestra que:

- descubre módulos `test_*.py` y los agrupa por suite de primer nivel;
- exige correspondencia entre suites descubiertas y registradas, con overrides de módulo solo a `optional`;
- activa suites `required` para los perfiles `required` y `release`;
- pasa las rutas de suite activas como directorios/paths a pytest.

Los once nombres exactos aparecen estáticamente en los módulos actuales de esas suites. Esto respalda la **selección configurada por suite** para ambos perfiles y la conservación documental de la clasificación; no es correcto inferirla únicamente del nombre de la suite, pero aquí también se inspeccionó el flujo estático de expansión/selección.

Límites: `UNVERIFIED` selección/recolección efectiva de cada nodeid por pytest, cantidad exactamente uno, condición de ejecución y resultado. No se ejecutó colección. Además, el JSON clasifica suites, no contiene un inventario externo autenticado de los once nodeids; STEP-22 declara que ese expected inventory debe proceder de policy aprobada fuera del checkout. `OBSERVED`: en el estado inicial de STEP-23C, `config/test_perimeter.json` estaba modificado en el árbol de trabajo y los archivos de test de interés estaban untracked. Por ello, esta inspección describe el candidato de checkout, no autentica una política normativa externa.

**Adjudicación de perímetro:** no se observó degradación/clasificación distinta de esos once nodeids en los documentos examinados y su ubicación actual cae en suites `required`; el perímetro autoritativo externo y la selección efectiva individual permanecen no verificados. No se cambió clasificación ni configuración.

## 6. Bloqueos y responsables de decisión

**A. Gobernanza externa — abiertos**

- Designar quién puede aprobar, revocar y actualizar controller/policy; establecer scope, registro y revisión independiente.
- Decidir cómo se autentican identidad, autorización, caducidad y revocación.
- Identificar custodio del bootstrap/ancla y responsables de verifier, observador y agregador.
- No se asignan nombres ni se interpreta este expediente como aprobación.

**B. Diseño documental — abiertos**

- Cerrar protocolo/schema e identidad de cada observación B1-R, ordinales exactly-once y vínculo run/worker.
- Cerrar TOCTOU, identidad transitiva, perfiles, allowlists, límites y retries.
- Formalizar máquina de estados, precedencia, errores/timeouts y criterios de evidencia por dimensión.
- Definir expected nodeid inventory externo autenticado y relación explícita por perfil.

**C. Provisión y validación técnica futura — no demostrados**

- Proveer bootstrap/ancla y controller fuera del checkout con cadena de identidad aprobada.
- Implementar verifier/agregador externos; demostrar boundary de aislamiento real.
- Ejecutar B1-R y cobertura de nodeids únicamente bajo autorizaciones futuras separadas.
- Una especificación o suite marcada `required` no cierra estos bloqueos técnicos.

## 7. Criterios de aceptación para una fase futura

Antes de cualquier implementación/ejecución posterior se requiere, como mínimo:

1. Decisión externa verificable que designe autoridad y lifecycle.
2. Bootstrap/ancla fuera del checkout, identidad y procedencia verificadas antes de cargar código no confiable.
3. Identidad transitiva aprobada y demostración de que se ejecutan los mismos bytes verificados, con protección TOCTOU/rollback.
4. Policy externa versionada con perfiles, inventario exacto de once nodeids, límites, comandos, mounts, roots y reglas de rechazo.
5. Schema con ID/ordinal único para cada observación B1-R y binding inequívoco a run, worker, artefacto y consumidor.
6. Verifier, observador de aislamiento y agregador con identidades aprobadas y responsabilidades separadas.
7. Capturas Git pre/post comparables y tratamiento fail-closed de errores; no presentar igualdad como prueba de ausencia de escrituras transitorias.
8. Evidencia independiente de boundary efectivo y adjudicación separada de funcionalidad, artefactos, aislamiento, Git y cobertura.
9. Autorizaciones específicas para implementación y para ejecución; revisión de resultados por actor autorizado.

Cumplir estos criterios en documentación no autoriza por sí solo ninguna actividad técnica ni cambio canónico.

## 8. Actividad, estado final y límites

`OBSERVED`: tras crear este informe, rama/HEAD siguen en `talos-current-audit` / `cc8acfae623f9d10c8366871470319786b6a7ca4`; el inventario reporta 1.863 staged, 23 unstaged, 87 untracked y cero conflictos. La comparación nominal con `step23c-git-status-v2-final.txt` muestra exactamente una entrada añadida —este expediente— y ninguna otra diferencia.

No se ejecutaron tests, scripts del proyecto, hooks, builds, workers, Quality Gate, B1-R ni código del repositorio. Solo se realizaron lecturas estáticas, consulta de grafo de solo lectura y comandos Git/status/digest de lectura. No se modificaron código, tests, configuración, índice, refs ni perímetro. Este expediente es el único archivo nuevo de STEP-23C.1.

`DOCUMENTED`: STEP-23A=`PARTIALLY_RECONCILED`; STEP-23B=`UNRESOLVED_HISTORICAL_EVIDENCE`; la anomalía staged histórica permanece no resuelta y la diferencia 82/84 no queda reconciliada ruta por ruta.

**Resultado STEP-23C.1:** `ADJUDICATED_WITH_OPEN_BLOCKERS`.  
**Estado canónico final:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`.  
**Harness externo:** no autorizado para implementación.  
**B1-R:** no autorizado para ejecución.  
**Código/perímetro:** sin cambios.  
**Siguiente acción:** decisión explícita del operador/gobernanza para resolver bloqueos A; esta adjudicación no concede permiso para implementar, ejecutar, reabrir P1.2 ni iniciar P1.3.
