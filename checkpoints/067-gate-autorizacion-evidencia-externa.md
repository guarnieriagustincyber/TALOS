# Checkpoint 067 — gate de autorización de evidencia externa

Fecha: 2026-10-01

## Decisión registrada

```text
DECISION: NOT_AUTHORIZED
AUTHORIZATION_STATUS: NOT_AUTHORIZED
DECISION_SCOPE: Sólo autorización para una futura búsqueda de evidencia externa destinada exclusivamente a intentar resolver la autoridad de BASELINE_SPEC.
DECISION_EFFECT: La ruta de búsqueda externa permanece bloqueada; no resuelve la autoridad del baseline.
NEXT_MINIMAL_ACTION: INDEPENDENT_WORK_ONLY
```

## Base del registro

La Directiva 067 solicitó registrar una elección humana entre autorizar o no
autorizar, antes de cualquier búsqueda. No se obtuvo respuesta afirmativa
humana disponible a la pregunta del gate. Para no interpretar silencio como
consentimiento, se registra `NOT_AUTHORIZED`: no se concedió autorización.
Este registro no afirma que el usuario haya expresado un rechazo explícito.

La decisión tiene un solo efecto: no habilita una búsqueda externa. No
resuelve `BASELINE_SPEC_AUTHORITY`, no recupera ni identifica `f058…`, no
adjudica ninguna de las cuatro familias y no autoriza cambios. Cualquier
búsqueda futura requerirá una autorización humana explícita en una tarea
separada.

## Estado preservado

```text
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = NOT_AUTHORIZED
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
STOP_REASON = OPEN_EXTERNAL_EVIDENCE_REQUIRED
SCOPE_UNPROVEN
inventory.frozen = false
A_PRE_0 = NOT_READY
A_PRE_1 = NOT_AUTHORIZED / NOT_EXECUTED
385 rows = unique
385 global dispositions = UNKNOWN
EXTERNAL_SEARCH_EXECUTED = NO
```

No se ejecutaron búsquedas web, consultas a repositorios remotos o
documentación externa, contactos ni recuperación del artefacto. No se
presentaron packets ni se modificaron manifest, ledger, specs, membresías,
disposiciones o readiness. La decisión sólo registra que no existe
autorización para iniciar búsqueda externa en este momento.

## Estado posterior

La autorización `NOT_AUTHORIZED` anterior fue supersedida por una respuesta
humana explícita posterior, “si, luz verde”, registrada en CP071. El estado
vigente está definido allí:

```text
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = AUTHORIZED
REOPEN_PATH_A = YES
```

Esta actualización no cambia el hecho histórico de que ninguna búsqueda se
había autorizado ni ejecutado al crear CP067. La autorización vigente habilita
únicamente una investigación futura separada; CP067 no inicia esa búsqueda y
no resuelve autoridad.
