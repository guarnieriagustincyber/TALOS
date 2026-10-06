# Checkpoint 071 — decisión de reapertura del Camino A

Fecha: 2026-10-01

## Decisión vigente registrada

La primera anotación de CP071 dejó el Camino A como `NOT_AUTHORIZED` porque
no había respuesta afirmativa humana disponible en ese turno. Esa anotación
era correcta para el estado de entonces, pero queda supersedida por la
autorización explícita posterior del usuario: **“si, luz verde”**
(2026-10-01 19:42:58 -03:00), en respuesta directa a la pregunta de reapertura
del Camino A.

```text
DECISION = AUTHORIZED
REOPEN_PATH_A = YES
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
AUTHORIZATION_SCOPE = Se autoriza una futura investigación separada de evidencia externa destinada exclusivamente a establecer una autoridad normativa válida para el cierre formal de A-PRE-0.
DECISION_EFFECT = Se autoriza iniciar esa investigación futura; no resuelve BASELINE_SPEC_AUTHORITY ni identifica f058….
NEXT_MINIMAL_ACTION = OPEN_SEPARATE_EXTERNAL_EVIDENCE_INVESTIGATION
```

## Base y límites

La decisión explícita autoriza una **tarea futura y separada**. No se hizo
ninguna búsqueda dentro de esta tarea. La autorización no determina cuál
artefacto posee autoridad, no identifica `f058…`, no prueba que exista
evidencia externa ni autoriza modificar canon.

CP070 estableció que una autoridad normativa válida es material para el
cierre normativo actualmente definido y la calificación formal A-PRE-0. La
eventual investigación tendría que evaluar identidad/hash, autoridad, scope,
precedencia y relación con el snapshot requerido; una coincidencia de bytes
o hash aislada no bastaría. La investigación autorizada debe limitarse a
esos elementos y no adjudicar las cuatro familias.

## Invariantes preservados

```text
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
A_PRE_0 = NOT_READY
A_PRE_1 = NOT_AUTHORIZED / NOT_EXECUTED
inventory.frozen = false
385 rows = unique
385 global dispositions = UNKNOWN
SCOPE_UNPROVEN = PRESERVED
EXTERNAL_SEARCH_EXECUTED = NO (en CP071)
```

No se crearon decision packets, no se adjudicaron syscalls y no se modificó
canon. La anotación histórica `NOT_AUTHORIZED` se conserva como estado previo,
no como el estado vigente del gate.
