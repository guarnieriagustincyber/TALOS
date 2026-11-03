# TALOS V1.5 — STEP-25: Adjudicación de STEP-24 y camino de resolución

**Resultado:** `ADJUDICATED_WITH_EXPLICIT_RESOLUTION_PATHS`  
**Repositorio:** `/media/agustin/Laboratorio/study-engie`  
**Rama / HEAD de referencia:** `talos-current-audit` / `cc8acfae623f9d10c8366871470319786b6a7ca4`  
**Estado canónico al cierre:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`  
**TALOS V1:** `FROZEN`  
**B1-R:** no autorizado  
**Harness externo:** implementación no autorizada  
**Anomalía histórica Git:** `UNRESOLVED_HISTORICAL_EVIDENCE`

## 1. Resumen ejecutivo

STEP-24 identifica una causa sistémica bien sustentada: el código del checkout que inicia el Quality Gate también participa en la validación previa al worker, la construcción de Bubblewrap y la lectura de configuración. La raíz local `trust_root.py` protege el digest de un manifiesto concreto; no autentica independientemente el runner, el runtime, los imports, la configuración o el propio verificador. Una verificación que comienza después de cargar el código que debe validar no establece una raíz externa.

La inspección documental confirma además una brecha de contrato B1-R: se planean 30 observaciones, pero los registros individuales no identifican la repetición, el run ni el worker. El orden de una lista no es una identidad estable ni prueba exactamente una observación por clave. El test B1-R también consulta Git desde el proceso que corre el test, mientras el helper de aislamiento examinado oculta `.git`; la incompatibilidad es **probable por inspección**, no confirmada en ejecución.

STEP-24 propone una dirección arquitectónica útil, pero no cierra decisiones humanas ni evidencia experimental. La disponibilidad de `bwrap`, su argv candidato, una clasificación `required`, un digest o un documento coherente no demuestran autoridad, autenticidad, aislamiento efectivo, recolección de cobertura ni ejecución de B1-R.

El camino mínimo recomendado es secuencial: (A) que el operador defina modelo de autoridad y amenaza; (B–D) cerrar diseño de confianza, aislamiento y evidencia; (E) emitir autorización específica de implementación; (F) emitir otra autorización para pruebas sintéticas; (G) adjudicar evidencia antes de cualquier decisión P1.2/P1.3. STEP-25 no ejecuta ni aprueba ninguno de esos gates.

La anomalía histórica continúa `UNRESOLVED_HISTORICAL_EVIDENCE`. Los digests de las capturas STEP-23C validan igualdad de los bytes actualmente preservados con esos digests; no autentican las capturas perdidas de STEP-23A ni explican toda la transición 82→84.

## 2. Identidad, alcance y reglas de evidencia

### 2.1 Identidad y preservación

`OBSERVED`: antes de la inspección, el repositorio resolvió a la ruta declarada, rama `talos-current-audit` y HEAD `cc8acfae623f9d10c8366871470319786b6a7ca4`; coinciden con la referencia de STEP-25. El destino de este informe no existía. Git reportó 1.863 rutas staged, 23 unstaged, 88 untracked y cero conflictos.

El árbol ya contenía cambios ajenos a STEP-25. En particular, STEP-24 registra `config/test_perimeter.json` y `scripts/quality_gate.py` modificados unstaged, y `scripts/quality_gate_isolation.py` y dos módulos unitarios relevantes como untracked; no se tratan como aprobados ni como cambios introducidos por STEP-25. Las observaciones de STEP-24 sobre el worktree son evidencia estática de ese candidato local, no de HEAD ni de un artefacto autenticado.

### 2.2 Alcance

Se adjudicaron [STEP-24](./STEP-24-INVESTIGACION-DIRIGIDA-DE-BLOQUEOS.md), los expedientes STEP-22 a STEP-23C.1 que STEP-24 y este expediente citan, y el contenido documental directamente relacionado. Esta adjudicación no vuelve a ejecutar búsquedas dinámicas para validar el host descrito históricamente por STEP-24.

No se ejecutaron tests, `pytest` ni `--collect-only`, Quality Gate, scripts, imports de TALOS, workers, Bubblewrap, `unshare`, builds, hooks o experimentos de aislamiento. No se accedió a bases, corpus, snapshots ni estado de aprendizaje. No se modificaron código, tests, configuración, dependencias, políticas, perímetro, índice, refs o expedientes anteriores.

### 2.3 Clasificaciones

- **CONFIRMADO ESTÁTICAMENTE:** se desprende directamente de una fuente identificada leída en esta revisión o de un artefacto conservado con identidad suficiente para esa afirmación limitada.
- **INFERENCIA ESTÁTICA:** consecuencia probable del diseño/código leído; requiere prueba para confirmación conductual.
- **NO VERIFICADO DINÁMICAMENTE:** requiere una prueba futura autorizada; no implica que haya fallado ni pasado.
- **DECISIÓN DEL OPERADOR:** elección de autoridad, política, amenaza o riesgo residual que no puede tomar el implementador por sí mismo.
- **IRRECUPERABLE CON LA EVIDENCIA DISPONIBLE:** faltan artefactos históricos necesarios; una captura nueva no los sustituye.
- **RESUELTO:** requisito cuya evidencia objetiva existe y satisface su criterio de cierre. Una recomendación, propuesta o test no ejecutado no cuenta como resuelto.

## 3. Tabla de hallazgos y adjudicación de STEP-24

| ID | Hallazgo / evidencia identificable | Clasificación | Impacto | Requisito de salida y criterio objetivo de cierre | Dependencia |
|---|---|---|---|---|---|
| H-01 | `quality_gate.py` importa/verifica `trust_root.py` del checkout; la constante SHA-256 se aplica a `tests/protected/manifest.json`, no a la cadena completa del controller. [STEP-18 §§3.1–3.3](./TALOS-P1.2-STEP-18-HOST-AUTHORITY-COVERAGE-OWNERSHIP.md), [trust_root.py](../src/study_engine/contracts/trust_root.py), [STEP-24 §5.1](./STEP-24-INVESTIGACION-DIRIGIDA-DE-BLOQUEOS.md) | **CONFIRMADO ESTÁTICAMENTE** para el alcance del verificador; existencia de autoridad externa actual **NO VERIFICADO DINÁMICAMENTE** | No puede afirmarse autenticidad del controller/runtime antes de ejecutar código del checkout. | Bootstrap independiente verifica identidad, alcance y vigencia antes del primer import host del checkout; conservar evidencia verificable de qué bytes se ejecutaron. | D1, D2; Gate A antes de B. |
| H-02 | STEP-24 observó `quality_gate.py` y configuración dirty, helper/tests untracked y helper ausente de HEAD. | **CONFIRMADO ESTÁTICAMENTE** como estado registrado por STEP-24; aprobación/procedencia **NO VERIFICADO DINÁMICAMENTE** | El contenido candidato no es sin más el comportamiento versionado/aprobado. | Fijar tree/commit y artefactos exactos en policy; no usar conteos Git como sustituto de identidad/procedencia. | D2, D6; Gates A–B. |
| H-03 | STEP-24 reporta `bwrap` en PATH y fragmentos con namespaces/mounts, pero explícitamente no ejecutó el binario. | **CONFIRMADO ESTÁTICAMENTE** que STEP-24 documentó esas observaciones; comportamiento efectivo **NO VERIFICADO DINÁMICAMENTE** | No demuestra que el worker quedó confinado ni que el ejecutable sea íntegro/aprobado. | Identificar binario/procedencia y probar boundary desde observador externo bajo autorización. | D2–D4; Gates B–C y F. |
| H-04 | No se observó en el helper leído un filtro seccomp ni configuración explícita de cuotas CPU/memoria/PIDs; el gate no pasa timeout al helper según STEP-24. | **CONFIRMADO ESTÁTICAMENTE** para las rutas/versiones inspeccionadas; enforcement del host **NO VERIFICADO DINÁMICAMENTE** | Riesgo de agotamiento de recursos, duración no acotada y superficie syscall no definida. | Policy cuantificada y verificación efectiva de límites; preflight falla cerrado si el host no los puede aplicar. | D3; Gates A y C antes de F. |
| H-05 | B1-R fija diez IDs y tres ejecuciones; las observaciones tienen `case_id`, y el array position distingue repeticiones. No incluyen identidad individual run/worker/repetition/artefacto. [b1r_contract.json](../tests/audit/b1r_contract.json), [test](../tests/audit/test_b1_route_repeatability.py), [verifier](../scripts/verify_b1r_artifact.py), STEP-24 §8.1. | **CONFIRMADO ESTÁTICAMENTE** | No se puede adjudicar exactamente una observación por repetición estable ni asociarla a una ejecución/artefacto autenticado. | Esquema estricto con clave mínima `(run_id, profile_id, nodeid, case_id, repetition_index, attempt_id)` y `observation_id` derivado de codificación canónica; consumidor rechaza IDs/cardinalidad contradictorios. El ID no autentica por sí solo. | D5; Gate D antes de E. |
| H-06 | Verifier controla conjunto de cases, tamaño de lista, campos esperados y repetibilidad; no asigna ordinal único, no rechaza explícitamente JSON duplicate keys ni aplica strict schema general, según lectura STEP-24. | **CONFIRMADO ESTÁTICAMENTE** en el verifier inspeccionado | Duplicados semánticos/de claves o campos no autorizados pueden no quedar detectados por esas validaciones actuales. | Parser que rechace claves JSON duplicadas, schema allowlist/versionada y tests negativos autorizados para missing/extra/duplicate/contradictory data. | D5; Gate D. |
| H-07 | B1-R usa `git -C ... status` dentro del test; el helper inspeccionado enmascara `.git` en el worker. [test](../tests/audit/test_b1_route_repeatability.py), helper documentado en [STEP-24 §6.3](./STEP-24-INVESTIGACION-DIRIGIDA-DE-BLOQUEOS.md). | **INFERENCIA ESTÁTICA**: el Git del test probablemente falla como no-repository en ese sandbox; no hay resultado ejecutado. | Puede impedir el flujo B1-R propuesto o crear presión para exponer `.git`, lo que violaría separación host/worker. | Git before/after en observer/controller host; el worker no accede a `.git`; test sintético autorizado confirma enlace y manejo de error. | D4, D5; Gate D y luego F. |
| H-08 | Las suites `tests/unit`/`tests/audit` se marcan `required` y la selección del runner pasa paths de suite a pytest; no se ejecutó colección ni se comparó con inventario normativo externo. | Config/flujo **CONFIRMADO ESTÁTICAMENTE**; selección/ejecución individual **NO VERIFICADO DINÁMICAMENTE**; autoridad del inventario **DECISIÓN DEL OPERADOR**. | No se puede certificar cobertura de los once items por perfiles a partir de suite labels. | Inventario exacto por perfil anclado fuera del checkout; futura colección/resultados comparados exactamente por ID, con recolección autorizada separada de ejecución. | D6; Gate D antes de F. |
| H-09 | STEP-23A/23B registran inventarios históricos insuficientes; STEP-23C conservó capturas distintas. No hay capturas STEP-23A completas y emparejadas disponibles en expediente. [STEP-23B](./STEP-23B-HISTORICAL-INDEX-CAPTURE-VALIDATION.md), [STEP-23C baseline](./STEP-23C-BASELINE-ACTUAL-Y-PRESERVACION-DEL-ESTADO.md), [STEP-23C.1](./STEP-23C.1-ADJUDICACION-FINAL.md) | **IRRECUPERABLE CON LA EVIDENCIA DISPONIBLE** para reconciliar completamente la transición 82→84; los digests STEP-23C solo verifican igualdad de sus bytes actuales. | No atribuir rutas, actor o causalidad ni usar el inventario actual como sustituto histórico. | Mantener `UNRESOLVED_HISTORICAL_EVIDENCE`; solo evidencia nominal histórica nueva y comparable podría cambiar la adjudicación. | Independiente de Gates A–G para historia futura. |
| H-10 | STEP-22 propone arquitectura/protocolos, pero autoridad, ancla, política concreta, límites y lifecycle no están aprobados. [STEP-22 Decisions](./STEP-22-DECISIONS-AND-BLOCKERS.md), STEP-24 §11. | **DECISIÓN DEL OPERADOR** | No hay base legítima para iniciar implementación, worker o ejecución B1-R. | Decisiones D1–D6 explícitas, versionadas y atribuibles; no completar con la opinión del agente. | Gate A. |

**Adjudicación de estado:** ningún hallazgo crítico está clasificado `RESUELTO`. Los defectos de contrato H-05/H-06 y la incompatibilidad probable H-07 requieren cambio/diseño y después evidencia, no solo adjudicación documental. La causa de H-09 se cierra únicamente como incertidumbre histórica no recuperable con lo preservado.

## 4. Cadena de confianza circular: qué se puede afirmar

1. **`CONFIRMADO ESTÁTICAMENTE`:** el verificador del manifiesto protegido compara bytes contra un digest constante en un módulo del checkout. Su scope identificado es ese manifiesto; no autentica el controller completo.
2. **`CONFIRMADO ESTÁTICAMENTE` según la ruta descrita por STEP-18/24:** el Quality Gate importa módulos del checkout en el host antes de Bubblewrap. Una verificación interna posterior no puede ser bootstrap independiente de ese primer código cargado.
3. **`NO VERIFICADO DINÁMICAMENTE`:** si una variante del checkout realmente fue ejecutada durante esta fase o cuál fue la cadena exacta de bytes de una corrida histórica. No hubo ejecución autorizada.
4. **`NO VERIFICADO DINÁMICAMENTE`:** que exista fuera de las rutas inspeccionadas una organización, servicio o infraestructura que autorice actualmente el controller. Los documentos previos reportan no haberlo encontrado dentro de sus scopes; eso no prueba inexistencia universal.
5. **Conclusión:** hash = identidad de bytes bajo una comparación; firma = declaración autenticada por una clave, condicionada a procedencia/autoridad de esa clave; provenance = declaración de producción bajo confianza en el builder. Ninguno por sí solo acredita ejecución efectiva del mismo bytecode, aislamiento del worker o corrección del resultado.

La salida necesaria es un bootstrap cuyo propio byte y configuración se anclan fuera del checkout (por un proceso/control del operador o del OS explícitamente decidido). Debe verificar la policy/controller antes de imports host, ejecutar los bytes fijados evitando TOCTOU y conservar una attestation/recibo consumible por una parte con rol distinto. Esto sigue `PROPOSED`; exige D1/D2 y Gate B.

## 5. Aislamiento y límites: siete afirmaciones separadas

| Afirmación | Estado STEP-25 | Evidencia / lo que falta |
|---|---|---|
| 1. Existe un ejecutable Bubblewrap en el entorno descrito por STEP-24 | `DOCUMENTED` por la consulta de entorno narrada en STEP-24; no se reconsultó aquí. | Resolución de ruta no demuestra versión, integridad ni aprobación. |
| 2. Hay una configuración candidata de namespaces/mounts | `CONFIRMADO ESTÁTICAMENTE` en el helper del worktree descrito por STEP-24. | Configuración candidata monta checkout RO, workspace RW y oculta paths identificados; no equivale a policy aprobada. |
| 3. Ejecutable/controller y configuración son íntegros y autorizados | `NO VERIFICADO DINÁMICAMENTE` / bloqueo H-01 a H-03. | Hace falta inventario y ancla aprobada fuera del checkout; evitar sustitución hasta y durante uso. |
| 4. Hay límites efectivos de CPU/memoria/PIDs/tiempo/espacio | No demostrados; la inspección estática STEP-24 no encontró límites explícitos en rutas seleccionadas. | Definir valores según carga/riesgo; verificar enforcement del worker y descendientes. |
| 5. Red, capacidades, secretos, sockets y dispositivos están restringidos | El argv candidato usa namespaces y entorno reducido; el comportamiento efectivo permanece `NO VERIFICADO DINÁMICAMENTE`. | Enumerar mounts/env/sockets permitidos, probar conectividad y acceso con probes sintéticos. No presumir que namespace equivale a política completa. |
| 6. El worker realmente obedece el boundary | `NO VERIFICADO DINÁMICAMENTE`. | Observador externo debe recoger mount/ns/capability/resource y comportamiento adversarial; no aceptar auto-reporte del worker como única evidencia. |
| 7. Amenaza de escape de namespace/kernel está cubierta | `DECISIÓN DEL OPERADOR` sobre threat model; garantía actual no existe. | Si kernel exploit está in-scope, namespaces comparten kernel host y no son frontera suficiente por sí solos; evaluar VM y su hipervisor/host TCB. |

No se asume que cgroups, seccomp, user namespaces, rlimits o VM están disponibles o configurados. La existencia y el funcionamiento deben formar parte del preflight y prueba de Gate C/F. La disponibilidad de `bwrap`, un test PASS o la revisión de argv no permiten marcar `ISOLATION_DEMONSTRATED`.

## 6. B1-R, cobertura e incompatibilidad Git

### 6.1 Contrato y esquema

`CONFIRMADO ESTÁTICAMENTE`: contrato y test contienen exactamente los casos `success`, `error`, `abstention`, `clarification`, `truncated`, `stream_aborted`, `eof_without_terminal`, `duplicate_terminal`, `error_after_tokens`, `abrupt_close`; tres repeticiones por caso; 30 observaciones planificadas.

El esquema futuro debe incluir, al menos:

```text
run_id
profile_id
parent_nodeid
case_id
repetition_index
attempt_id
observation_id
worker_id
producer_identity
started_at
completed_at
functional_result
artifact_refs[{artifact_id, name, size, sha256, immutable_ref}]
timeout_or_signal
limitations[]
```

`observation_id` se calcula desde una serialización canónica de los IDs, pero no aporta autenticidad. La autenticidad y procedencia las da una identidad de productor verificada por el consumidor y evidencia externa del run.

Reglas que deben cerrarse en Gate D:

- Repetition index pertenece al plan (1..3); `attempt_id` diferencia un retry explícitamente autorizado. No reemplazar ni borrar intentos fallidos.
- El mismo `(run_id, profile_id, nodeid, case_id, repetition_index, attempt_id)` repetido es duplicado y bloquea; dos contenidos distintos con la misma clave son contradicción y bloquean.
- Caso/repetición faltante, extra o identificador no esperado implica cobertura incompleta/inválida.
- JSON duplicate keys, campos críticos desconocidos, schema no soportado, payload truncado, artifact missing/digest mismatch o worker/run mismatch implican rechazo explícito.
- Resultado funcional, integridad del artefacto, aislamiento, observación Git y cobertura son dimensiones separadas; ninguna compensa otra.
- Verifier debe consumir exactamente los mismos bytes preservados por el collector, y su identidad debe ser independiente del producer conforme al assurance decidido.

`NO VERIFICADO DINÁMICAMENTE`: no se ha ejecutado B1-R ni se han producido 30 observaciones. Ningún expediente puede afirmarlo.

### 6.2 Once nodeids

Los once nodeids documentados en [STEP-22 Aggregation Matrix §2](./STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md) permanecen sin reclasificación: 8 de `test_quality_gate_isolation.py`, 2 de `test_quality_gate_focal_execution.py` y 1 de `test_b1_route_repeatability.py`. Las suites `tests/unit` y `tests/audit` aparecen `required` en el JSON revisado por STEP-24 y el flujo estático activa suites `required` para `required` y `release`.

Esto confirma configuración/paths de suite observados en ese worktree, no una policy normativa autenticada ni recolección efectiva de los 11 items. Los dos módulos unit aparecen como untracked en el inventario STEP-24; por tanto, la fuente de suite no es necesariamente parte de HEAD. La lista exacta por perfil debe ser aprobada fuera del checkout y el ejecutor futuro debe comparar igualdad exacta `expected_nodeids == observed_nodeids`; no deducir item PASS de una suite PASS.

No se ejecuta `pytest --collect-only`. Si la colección debe verificarse más adelante, requerirá autorización específica de colección, executor y perimeter identity; collection prueba presencia/selección, no resultado funcional, aislamiento o release.

### 6.3 Git dentro del worker

`INFERENCIA ESTÁTICA PROBABLE`: si el test ejecuta `git status` desde el worker al que se le oculta `.git`, la llamada puede terminar como error por no-repository; no se ha confirmado por ejecución. No hacer disponible `.git` real para acomodar ese test.

Separación propuesta: observer/controller con autoridad captura Git antes y después sobre el mismo checkout y comando; worker realiza únicamente el trabajo sintético; verifier valida identidad/run y evidencia de ambas capturas. Igualdad pre/post limita la afirmación a igualdad del estado Git reportado y no prueba ausencia de escrituras transitorias, archivos ignorados o efectos externos.

## 7. Anomalía histórica Git

| Momento/expediente | Conteo declarado | Alcance probatorio |
|---|---:|---|
| Registro previo / STEP-22, anterior a anomalía | 76 untracked | Conteo documentado, no inventario completo autenticado para comparar con STEP-23A. |
| STEP-23A | 82 untracked; staged agregado reportado como 1.863 frente a 1.869 previo | `PARTIALLY_RECONCILED`; las capturas temporales nominales citadas ya no están preservadas. |
| STEP-23C baseline | 84 untracked | Captura porcelain v2 preservada externamente en el workspace de sesión; bytes y digest verificados después, no procedencia/tiempo autenticados. |
| STEP-23C final | 86 untracked | La captura final refleja los dos informes creados durante STEP-23C; igualdad nominal con una salida posterior verifica solo ese estado observado. |

`IRRECUPERABLE CON LA EVIDENCIA DISPONIBLE`: reconciliación completa ruta-por-ruta de la transición 82→84 y explicación de la discrepancia staged. STEP-23B documenta que los dos archivos temporales STEP-23A no estaban disponibles. Dos paths posteriores compatibles con informes nuevos no demuestran que expliquen todo el delta. Hashes recalculados de STEP-23C no autentican momentos históricos.

**Estado a preservar:** `UNRESOLVED_HISTORICAL_EVIDENCE`. No se atribuye autoría/causalidad, no se deducen rutas por diferencia aritmética y no se usa baseline actual como reconstrucción.

**Protocolo futuro (para prevenir nueva pérdida, no para reparar el pasado):** una invocación única `git status --porcelain=v2 --branch --untracked-files=all -z`; conservar stdout/stderr binarios, exit code, hora con zona, checkout branch/HEAD, flags/version Git, parser y reglas de conteo; calcular digest de bytes exactos; derivar todos los conteos del mismo artefacto; preservar captura inicial/final fuera del repo en ubicación autorizada y comparar entradas nominales. Limitar el claim a Git observado: escrituras transitorias pueden no aparecer.

## 8. Matriz de decisiones para el operador

Ninguna decisión de esta tabla queda aprobada por la directiva de STEP-25. La autoridad para aprobar la decisión es el operador/propietario que este designe; no se presume una institución externa.

| ID / pregunta | Alternativas y consecuencias | Recomendación razonada | Aprobación faltante |
|---|---|---|---|
| **D1 — Modelo de autoridad:** ¿quién aprueba policy/controller y revoca? | Operador local exclusivo: simple y reversible, mayor riesgo de error/self-review. Operador + segundo revisor: independencia humana mayor, coste/coordinación. Autoridad institucional: controles existentes si realmente aplica, no asumirla. | Para proyecto personal, operador explícito puede ser policy owner con registro de decisión; un verificador técnicamente separado. Segundo revisor solo si el riesgo/assurance lo requiere. | Identidad/rol del aprobador, alcance, revisión y registro auditable. |
| **D2 — Ancla:** ¿cómo confiar en bootstrap/policy antes de checkout? | Digest guardado fuera: simple, pero confía en custodia/host y requiere actualización manual. Policy firmada + clave pública anclada: rotación/alcance mejor expresables; requiere custodia, revocación y protección de clave pública. Bootstrap protegido por OS: aprovecha package trust/permissions; desplaza confianza a OS/admin y no fija policy TALOS automáticamente. | Elegir mecanismo mínimo según amenaza; en cualquiera, ancla debe estar fuera de checkout y el bootstrap ejecutarse antes de importarlo. Archivo externo editable por el mismo proceso no es independiente. | Canal/custodio, signer identity o proceso manual, anti-rollback/expiry/revocation. |
| **D3 — Amenaza:** ¿qué ataques se deben cubrir? | Tests defectuosos/maliciosos; escrituras fuera de workspace; secretos/red; agotamiento recursos; escape de namespace; kernel exploit. Cobertura más alta cuesta en aislamiento/observabilidad. | Declarar explícitamente si kernel exploit está dentro del scope; si sí, VM candidata, reconociendo hipervisor/host como TCB. No inferirlo de herramientas ya instaladas. | Threat model, activos, adversario y riesgo residual aceptado. |
| **D4 — Independencia de observer/verifier:** ¿qué componente puede dar resultado confiable? | Mismo proceso: menor coste pero sustitución conjunta y authority laundering. Proceso fuera del checkout: separa test de evaluación. Segundo host/persona: independencia más fuerte, coste mayor. | Mínimo observer/verifier fuera del checkout y no modificable por worker; elevar a segundo host/revisor según D3. | Identidades, relación producer/consumer, evidence store y nivel de independencia. |
| **D5 — Repetición/retry:** ¿qué significa “tres”? | Tres observaciones seriales en un run; tres workers separados; retries adicionales. Retries pueden ocultar fallos si sustituyen evidencia previa. | Identidad de repetición estable 1..3; no retry por defecto. Si se aprueba, `attempt_id` separado, preservación íntegra y regla de agregación antes de correr. | Semántica de aislamiento entre repeticiones y tratamiento de fallos/retries. |
| **D6 — Cobertura:** ¿quién fija nodeids exactos por perfil? | Suite roots en checkout: flexible, mutable, cambios de selección no autenticados. Inventory exacto externo: control preciso, más mantenimiento al cambiar tests. | Expected set por profile fuera del checkout; cambios explícitos, versionados y aprobados; checkout config se compara como candidate. | Authority del perímetro, IDs exactos y proceso de update. |

La autorización para investigar/documentar STEP-25 no se interpreta como aprobación de D1–D6.

## 9. Plan de resolución por gates, entradas y salidas

Dependencias: `A → B → C/D → E → F → G`. E-01 (historia Git) permanece aparte; no debe usarse como razón para reescribir capturas previas.

| Gate | Entrada requerida | Trabajo posterior permitido solo con nueva autorización | Salida y criterio de cierre | No significa |
|---|---|---|---|---|
| **A — Autoridad y amenaza** | Decisiones D1–D6 presentadas al operador; estado P1 bloqueado. | Aprobar modelo de autoridad, threat model y lifecycle, sin implementación automática. | Decisiones identificadas/fechadas; roles approver/revoker/reviewer; riesgos residuales y scope documentados. | No autoriza código ni pruebas. |
| **B — Contrato de confianza** | Gate A aprobado. | Diseñar ancla→bootstrap→controller/runtime→policy/inputs→workspace→worker→evidencias→verifier→adjudicación. | Identidad de cada artefacto/consumer; bootstrap antes de imports; mismo-byte check-to-use; revocación, expiración y rollback; esquemas revisables. | No demuestra funcionamiento ni instala mecanismo. |
| **C — Aislamiento y recursos** | Threat model y arquitectura B acordados. | Diseñar mounts/capabilities/network/secrets, user/process namespaces, límites CPU/mem/PID/time/storage, teardown y opciones VM/seccomp/cgroup. | Policy evaluable y preflight que falla cerrado si capability/limit no existe; riesgos kernel explícitos. | No demuestra boundary real ni permite ejecutar workers. |
| **D — Evidencia y cobertura** | Policy/identidades y perfiles tentativos disponibles. | Cerrar B1-R IDs/repetitions/retries, strict parsing, artifacts, Git observer, verifier, 11 nodeids y estados/precedencia. | Expected set autenticado por profile; cardinalidad exacta; decisiones sobre `PASS/FAIL/BLOCKED/UNKNOWN`; reject matrix completa. | No ejecuta collection o B1-R. |
| **E — Implementación** | Gates A–D revisados y aprobados; autorización de modificación separada, con archivos permitidos y plan de preservación. | Implementar solo componentes y rutas autorizadas; no ejecutar B1-R automáticamente. | Diff acotado; identity/inventory/provenance; code review y checks permitidos explícitamente. | No autoriza prueba dinámica de aislamiento. |
| **F — Validación sintética** | Implementación aprobada; directiva separada con comandos, ambiente, límites, outputs, timeout/abort y safe synthetic fixtures. | Probar bootstrap negativo, TOCTOU, recursos, network/mount boundary; luego collection/ejecución según scopes autorizados; B1-R solo con autorización específica adicional si no está incluida explícitamente. | Artifacts preservados, verifier independiente, cobertura exacta, límites observados, failures/unknowns sin ocultar. | Test PASS no adjudica por sí solo P1.2/P1.3 ni aislamiento global. |
| **G — Adjudicación de desbloqueo** | Evidencia F completa y consumer evaluation autorizada. | Revisar contradicciones, riesgos residuales y scope de release. | Decisión explícita del actor autorizado por cada fase; estados canónicos se cambian solo mediante autoridad correspondiente. | STEP-25 no habilita transición. |

## 10. Riesgos y evidencia que continúa ausente

- **`NO VERIFICADO DINÁMICAMENTE`:** autenticación, expiración/revocación, anti-rollback y no-replay del bootstrap.
- **`NO VERIFICADO DINÁMICAMENTE`:** identidad efectiva del controller/runtime/imports/config y continuidad byte-identical de verificación a ejecución.
- **`NO VERIFICADO DINÁMICAMENTE`:** mounts, namespace IDs, capacidades, red, secretos, devices y filesystem access del worker.
- **`NO VERIFICADO DINÁMICAMENTE`:** límites CPU/memoria/PID/tiempo/espacio y terminación de procesos descendientes.
- **`NO VERIFICADO DINÁMICAMENTE`:** recolección exacta de los once nodeids, ejecución por perfil y contrato B1-R.
- **`INFERENCIA ESTÁTICA`:** incompatibilidad `git status` del test con `.git` enmascarado por worker.
- **`IRRECUPERABLE CON LA EVIDENCIA DISPONIBLE`:** inventories históricos STEP-23A completos y comparables; mantener anotación de irrecoverability salvo evidencia primaria nueva.
- **`DECISIÓN DEL OPERADOR`:** approver, trust anchor, kernel threat, independencia del reviewer, retry semantics y authority del expected coverage.

## 11. Siguiente gate y autorizaciones

El primer gate que puede abordarse es **Gate A**, porque requiere únicamente que el operador elija y documente autoridad, amenaza y decisiones D1–D6. No necesita implementación, tests, colección ni acceso a datos protegidos. El presente documento deja comparadas alternativas y recomendaciones, pero no contiene las aprobaciones.

Luego de Gate A, cada Gate B–G requiere revisión/decisión y autorización propia conforme al plan. En especial:

- diseño no autoriza implementación;
- implementación no autoriza tests;
- colección no autoriza B1-R;
- B1-R no se ejecuta sin autorización explícita que delimite perfil, entorno, artefactos, límites y abort;
- ninguna fase posterior modifica P1.2/P1.3 automáticamente.

## 12. Informe de cierre obligatorio

- **Resultado STEP-25:** `ADJUDICATED_WITH_EXPLICIT_RESOLUTION_PATHS`.
- **Confirmado estáticamente:** alcance estrecho de trust root; configuración de suites/paths documentada en STEP-24; campos ausentes de identidad B1-R; ubicación host-side del observer Git propuesta y `.git` oculto en helper candidato.
- **Inferido:** Git del test probablemente falla dentro del worker descrito; esto aún no es prueba ejecutada.
- **No verificado:** autenticidad del controller, aislamiento real, límites, cobertura ejecutada, B1-R y cualquier bootstrap externo fuera del scope revisado.
- **Irrecuperable:** reconciliación histórica completa de 82→84 con las capturas disponibles; permanece `UNRESOLVED_HISTORICAL_EVIDENCE`.
- **Decisiones del operador:** D1 autoridad; D2 ancla; D3 amenaza/kernel; D4 independencia de verifier/observer; D5 repetición/retry; D6 inventory de nodeids.
- **Primer gate recomendado:** Gate A; requiere decisiones explícitas, no una directiva de implementación.
- **Archivos consultados:** [STEP-24](./STEP-24-INVESTIGACION-DIRIGIDA-DE-BLOQUEOS.md), [STEP-23C.1](./STEP-23C.1-ADJUDICACION-FINAL.md), [STEP-23B](./STEP-23B-HISTORICAL-INDEX-CAPTURE-VALIDATION.md), [STEP-22 contract](./STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md), [STEP-22 trust matrix](./STEP-22-TRUST-BOUNDARY-MATRIX.md), [STEP-22 aggregation matrix](./STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md), [STEP-22 decisions](./STEP-22-DECISIONS-AND-BLOCKERS.md), además de las fuentes estáticas citadas en STEP-24.
- **Único documento creado:** este expediente STEP-25.
- **Ejecución:** no se ejecutaron tests, `--collect-only`, workers, scripts ni mecanismos de aislamiento.
- **Preservación:** no se alteraron código, configuración, Git ni datos protegidos; los cambios preexistentes se conservaron.
- **Estado canónico final:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`; TALOS V1 congelado; B1-R no autorizado; harness externo no autorizado.

**STEP-25 se detiene aquí.** No avanza automáticamente a STEP-26, no implementa el harness y no ejecuta B1-R.
