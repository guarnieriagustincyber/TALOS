# Gate 2 — Inventario de cobertura y validez de v2.400

**Fecha:** 2026-09-28  
**Modo:** read-only; sin retrieval, embeddings, reranking, generación ni escrituras SQLite.  
**Fuente canónica:** v2.400. v2.401 se conserva solo como evidencia de auditoría.

## Resumen

- Consultas inventariadas: **400**
- Scopes: **6**
- Referencias qrel: **165**
- Qrels no encontrados: **0**
- Qrels fuera de ACL actual del scope v2.400: **0**
- Qrels pendientes de adjudicación semántica: **149**
- Consultas con al menos un qrel conservado y confirmado: **1**
- Consultas con al menos un qrel conservado como evidencia parcial: **2**

### Estado de consultas

| Estado | Consultas |
|---|---:|
| `APPROVED_NEGATIVE` | 0 |
| `APPROVED_OOD` | 1 |
| `APPROVED_POSITIVE` | 0 |
| `BLOCKED_SCOPE` | 0 |
| `BLOCKED_SEMANTIC` | 3 |
| `INVALID_HISTORICAL_QREL` | 0 |
| `NO_VALID_QREL` | 282 |
| `PARTIALLY_VALID` | 3 |
| `PENDING_ADJUDICATION` | 111 |

### Estado agregado de qrels por consulta

| Estado | Consultas |
|---|---:|
| `ABSENT` | 352 |
| `INVALID` | 3 |
| `PARTIAL` | 3 |
| `PENDING` | 42 |
| `VALID` | 0 |

### Estado de referencias qrel

| Estado qrel | Referencias |
|---|---:|
| `INVALID` | 13 |
| `PARTIAL` | 2 |
| `PENDING` | 149 |
| `VALID` | 1 |

| Estado de chunk / ACL | Referencias |
|---|---:|
| `INVALID_SEMANTIC` | 13 |
| `MISSING` | 0 |
| `OUTSIDE_ACL` | 0 |
| `PARTIAL` | 2 |
| `PENDING_ADJUDICATION` | 149 |
| `VALID` | 1 |

| Estado ACL | Referencias |
|---|---:|
| `IN_SCOPE` | 165 |
| `NOT_FOUND` | 0 |
| `OUTSIDE_ACL` | 0 |

## Resumen por scope

| Scope | Consultas v2.400 | Qrels v2.400 | Estados de consulta | Estados qrel | Cambios v2.401 salientes / entrantes | Qrels v2.401 entrantes | Integridad histórica | Acción |
|---|---:|---:|---|---|---:|---|---|---|
| `NB-CYBERSECURITY-V1` | 10 | 7 | NO_VALID_QREL: 8, PARTIALLY_VALID: 1, PENDING_ADJUDICATION: 1 | INVALID: 1, PENDING: 5, VALID: 1 | 10 / 0 | 0 | `VIOLATION_DETECTED` | `NONE` |
| `NB-SEC-01-C-PTR` | 330 | 131 | APPROVED_OOD: 1, NO_VALID_QREL: 232, PARTIALLY_VALID: 1, PENDING_ADJUDICATION: 96 | INVALID: 1, PARTIAL: 1, PENDING: 129 | 0 / 70 | 330 | `VIOLATION_DETECTED` | `NONE` |
| `fadena-lenguajes` | 20 | 6 | BLOCKED_SEMANTIC: 3, NO_VALID_QREL: 17 | INVALID: 6 | 20 / 0 | 0 | `VIOLATION_DETECTED` | `NONE` |
| `fadena-so2` | 10 | 5 | NO_VALID_QREL: 9, PARTIALLY_VALID: 1 | INVALID: 4, PARTIAL: 1 | 10 / 0 | 0 | `VIOLATION_DETECTED` | `NONE` |
| `fadena-std` | 10 | 0 | NO_VALID_QREL: 10 | — | 10 / 0 | 0 | `VIOLATION_DETECTED` | `NONE` |
| `fadena-teleco` | 20 | 16 | NO_VALID_QREL: 6, PENDING_ADJUDICATION: 14 | INVALID: 1, PENDING: 15 | 20 / 0 | 0 | `VIOLATION_DETECTED` | `NONE` |

## Referencia de auditoría v2.401

- Canonical para reparación: **False**
- Evidencia histórica: **True**
- Cambios de scope al comparar con v2.400: **70 consultas**
- Referencias qrel de esas consultas: **330**
- Fuera de la ACL del scope correspondiente en v2.400: **224**
- Referencias faltantes: **0**
- Acción: **NONE** (hallazgo de integridad; no reasignar scopes ni eliminar qrels automáticamente).

## Inventario de las 400 consultas

La tabla incluye todas las consultas v2.400. El JSON contiene los campos completos y el detalle independiente de cada chunk qrel.

| Query ID | Scope | Categoría / intención | Oráculo histórico | Qrels | Estado | Justificación resumida |
|---|---|---|---|---:|---|---|
| `GS2-OOD-001` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `APPROVED_OOD` | Previously retained as the approved global OOD control; its historical qrels are empty. |
| `GS2-OOD-002` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-003` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-004` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-005` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-006` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-007` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-008` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-009` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-010` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-011` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-012` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-013` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-014` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-015` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-016` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-017` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-018` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-019` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-020` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-021` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-022` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-023` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-024` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-025` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-026` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-027` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-028` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-029` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-030` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-031` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-032` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-033` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-034` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-035` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-036` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-037` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-038` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-039` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-040` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-041` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-042` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-043` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-044` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-045` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-046` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-047` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-048` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-049` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-050` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-051` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-052` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-053` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-054` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-055` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-056` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-057` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-058` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-059` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-OOD-060` | `NB-SEC-01-C-PTR` | ood_trampas / Global abstention / OOD | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical OOD intent has no explicit approved query-level adjudication. |
| `GS2-VULN-001` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-031` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-002` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-032` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-003` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-033` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-004` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 2 | `PARTIALLY_VALID` | At least one qrel is explicitly retained while other references are excluded or still pending; only retained references are eligible. |
| `GS2-VULN-034` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-005` | `NB-CYBERSECURITY-V1` | vulnerabilidades / Historical oracle: anti_shortcut_oracle | `anti_shortcut_oracle` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-VULN-035` | `NB-CYBERSECURITY-V1` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-006` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-036` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-007` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 5 | `PARTIALLY_VALID` | At least one qrel is explicitly retained while other references are excluded or still pending; only retained references are eligible. |
| `GS2-VULN-037` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-008` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-038` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-009` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-039` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-010` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-040` | `fadena-so2` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-011` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-041` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-012` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-042` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-013` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-043` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-014` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-044` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-015` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-045` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-016` | `NB-SEC-01-C-PTR` | vulnerabilidades / Historical oracle: anti_shortcut_oracle | `anti_shortcut_oracle` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-046` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-017` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-047` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-018` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 2 | `PARTIALLY_VALID` | At least one qrel is explicitly retained while other references are excluded or still pending; only retained references are eligible. |
| `GS2-VULN-048` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-019` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-049` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-020` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-VULN-050` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-021` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-051` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-022` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-052` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-023` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-053` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-024` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-054` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-025` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-055` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-026` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-VULN-056` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 1 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-VULN-027` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-057` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-028` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-058` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-029` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-059` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-030` | `NB-SEC-01-C-PTR` | vulnerabilidades / Historical oracle: anti_shortcut_oracle | `anti_shortcut_oracle` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-VULN-060` | `NB-SEC-01-C-PTR` | vulnerabilidades / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-001` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-002` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 2 | `BLOCKED_SEMANTIC` | Historical evidence is GNU C function-cloning, not the Linux clone syscall asked by the query. |
| `GS2-SYN-003` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 2 | `BLOCKED_SEMANTIC` | Historical evidence is GNU C function-cloning, not the Linux clone syscall asked by the query. |
| `GS2-SYN-004` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 2 | `BLOCKED_SEMANTIC` | Historical evidence is GNU C function-cloning, not the Linux clone syscall asked by the query. |
| `GS2-SYN-005` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-006` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-007` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-008` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-009` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-010` | `fadena-lenguajes` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-011` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-012` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-013` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-014` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-015` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-016` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-017` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-018` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-019` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-020` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-021` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-022` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-023` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-024` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-025` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-026` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-027` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-028` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-029` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-030` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-031` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-032` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-033` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-034` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-035` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-036` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-037` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-038` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-039` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-040` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-041` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-042` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-043` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-044` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-045` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 2 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-046` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-047` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-048` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 5 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-SYN-049` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-050` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-051` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-052` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-053` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-054` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-055` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-056` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-057` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-058` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-059` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-060` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-061` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-062` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-063` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-064` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-065` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-066` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-067` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-068` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-069` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-070` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-071` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-072` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-073` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-074` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-075` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-076` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-077` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-078` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-079` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-SYN-080` | `NB-SEC-01-C-PTR` | sintaxis_codigo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-001` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-002` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-003` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-004` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-005` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 4 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-006` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-007` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-008` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-009` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-010` | `fadena-teleco` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-011` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-012` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-013` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-014` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-015` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-016` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-017` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-018` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-019` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-020` | `fadena-std` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-021` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-022` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-023` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-024` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-025` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-026` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-027` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-028` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-029` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-030` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-031` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-032` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-033` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-034` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-035` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-036` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-037` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-038` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-039` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-040` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-041` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 1 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-042` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 1 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-043` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 1 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-044` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 1 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-045` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 1 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-CMP-046` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-047` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-048` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-049` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-050` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-051` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-052` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-053` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-054` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-055` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-056` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-057` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-058` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-059` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-060` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-061` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-062` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-063` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-064` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-065` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-066` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-067` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-068` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-069` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-070` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-071` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-072` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-073` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-074` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-075` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-076` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-077` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-078` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-079` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-CMP-080` | `NB-SEC-01-C-PTR` | multi_capitulo / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-001` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-002` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-003` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-004` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-005` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-006` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-007` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-008` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-009` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-010` | `fadena-teleco` | fundamentos / Historical abstention assertion outside the OOD category | `abstention_oracle` | 0 | `PENDING_ADJUDICATION` | Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated. |
| `GS2-FUN-011` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-012` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-013` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-014` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-015` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-016` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-017` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-018` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-019` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-020` | `fadena-lenguajes` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-021` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-022` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-023` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-024` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-025` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-026` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-027` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-028` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-029` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-030` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-031` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-032` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-033` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-034` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-035` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-036` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-037` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-038` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-039` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-040` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-041` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-042` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-043` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-044` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-045` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-046` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-047` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-048` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-049` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-050` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-051` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-052` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-053` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-054` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-055` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-056` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-057` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-058` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-059` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-060` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-061` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-062` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-063` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-064` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-065` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-066` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-067` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-068` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-069` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-070` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-071` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-072` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-073` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-074` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-075` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-076` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-077` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-078` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-079` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-080` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-081` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-082` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-083` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-084` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-085` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-086` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-087` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-088` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-089` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-090` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-091` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-092` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-093` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-094` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-095` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-096` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-097` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-098` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-099` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-100` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-101` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-102` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-103` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-104` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-105` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-106` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-107` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-108` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-109` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-110` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 0 | `NO_VALID_QREL` | No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence. |
| `GS2-FUN-111` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 3 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-112` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 3 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-113` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 3 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-114` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 3 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-115` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 3 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-116` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 2 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-117` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 2 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-118` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 2 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-119` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 2 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |
| `GS2-FUN-120` | `NB-SEC-01-C-PTR` | fundamentos / In-scope retrieval and citation | `retrieval_citation` | 2 | `PENDING_ADJUDICATION` | At least one historical qrel reference has no explicit semantic decision. |

## Decisiones por referencia qrel

| Query ID | Scope | Chunk ID | Grado histórico | Estado | ACL | Semántica | Decisión | Fuente |
|---|---|---|---:|---|---|---|---|---|
| `GS2-VULN-004` | `NB-CYBERSECURITY-V1` | `chk_0aa9aa4cc0b2_428_1` | 3 | `VALID` | `IN_SCOPE` | `CONFIRMED` | `KEEP` | `reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-adjudication.json` |
| `GS2-VULN-004` | `NB-CYBERSECURITY-V1` | `chk_07e0f6d0fb24_58_1` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-adjudication.json` |
| `GS2-VULN-005` | `NB-CYBERSECURITY-V1` | `chk_0aa9aa4cc0b2_358_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-005` | `NB-CYBERSECURITY-V1` | `chk_0aa9aa4cc0b2_389_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-005` | `NB-CYBERSECURITY-V1` | `chk_0aa9aa4cc0b2_373_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-005` | `NB-CYBERSECURITY-V1` | `Computer_Security_Stallings_3rd_Ed.pdf:p373:c0005` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-005` | `NB-CYBERSECURITY-V1` | `chk_0aa9aa4cc0b2_377_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-007` | `fadena-so2` | `chk_0aa9aa4cc0b2_385_1` | 3 | `PARTIAL` | `IN_SCOPE` | `PARTIAL` | `KEEP` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-007` | `fadena-so2` | `chk_0aa9aa4cc0b2_358_1` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-007` | `fadena-so2` | `chk_0aa9aa4cc0b2_394_1` | 1 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-007` | `fadena-so2` | `chk_0aa9aa4cc0b2_393_1` | 1 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-007` | `fadena-so2` | `chk_0aa9aa4cc0b2_365_1` | 1 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-018` | `NB-SEC-01-C-PTR` | `chk_92876e0f2bc2_425_1` | 3 | `PARTIAL` | `IN_SCOPE` | `PARTIAL` | `KEEP` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-018` | `NB-SEC-01-C-PTR` | `Codigo limpio - Robert Cecil Martin.pdf:p425:c0000` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json` |
| `GS2-VULN-020` | `NB-SEC-01-C-PTR` | `chk_92876e0f2bc2_243_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-020` | `NB-SEC-01-C-PTR` | `Codigo limpio - Robert Cecil Martin.pdf:p243:c0003` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-020` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_320_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-020` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_282_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-020` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_281_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-026` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_387_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-026` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_369_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-026` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_365_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-026` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p387:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-VULN-056` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_387_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-002` | `fadena-lenguajes` | `chk_fa5f80f8da3c_233_1` | 3 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_evidence_audit_2026-09-28.md` |
| `GS2-SYN-002` | `fadena-lenguajes` | `GNU-c-language-manual.pdf:p233:c0004` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_evidence_audit_2026-09-28.md` |
| `GS2-SYN-003` | `fadena-lenguajes` | `chk_fa5f80f8da3c_233_1` | 3 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_evidence_audit_2026-09-28.md` |
| `GS2-SYN-003` | `fadena-lenguajes` | `GNU-c-language-manual.pdf:p233:c0004` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_evidence_audit_2026-09-28.md` |
| `GS2-SYN-004` | `fadena-lenguajes` | `chk_fa5f80f8da3c_233_1` | 3 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_evidence_audit_2026-09-28.md` |
| `GS2-SYN-004` | `fadena-lenguajes` | `GNU-c-language-manual.pdf:p233:c0004` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_evidence_audit_2026-09-28.md` |
| `GS2-SYN-011` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_325_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-011` | `NB-SEC-01-C-PTR` | `luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf:p534:c0000` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-011` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-011` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_304_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-011` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_302_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-012` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_304_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-012` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_302_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-012` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_303_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-012` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p303:c0002` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-012` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p304:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-013` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_374_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-013` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_384_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-013` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_366_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-013` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_386_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-013` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p366:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-014` | `NB-SEC-01-C-PTR` | `hacking-etico-carlos-tori.pdf:p258:c0000` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-014` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_373_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-014` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_620_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-014` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_380_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-014` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p820:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-015` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_373_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-015` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_120_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-015` | `NB-SEC-01-C-PTR` | `hacking-etico-carlos-tori.pdf:p258:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-015` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p373:c0006` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-015` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p373:c0007` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-016` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_373_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-016` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_120_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-016` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_620_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-016` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_380_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-016` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p377:c0002` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-018` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p198:c0002` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-018` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p197:c0004` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-018` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_305_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-018` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p336:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-018` | `NB-SEC-01-C-PTR` | `Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf:p287:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-019` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p198:c0002` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-019` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p197:c0004` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-019` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p336:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-019` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_305_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-019` | `NB-SEC-01-C-PTR` | `Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf:p287:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-020` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p198:c0002` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-020` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p197:c0004` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-020` | `NB-SEC-01-C-PTR` | `seguridad-en-redes.pdf:p336:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-020` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_305_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-020` | `NB-SEC-01-C-PTR` | `Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf:p287:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-022` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_301_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-022` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_760_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-022` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p760:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-022` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-023` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_301_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-023` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-023` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_760_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-023` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p760:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-024` | `NB-SEC-01-C-PTR` | `chk_0aa9aa4cc0b2_301_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-024` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_760_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-024` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p760:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-024` | `NB-SEC-01-C-PTR` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-026` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_606_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-026` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_760_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-026` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_218_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-026` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p606:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-026` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p218:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-027` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_606_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-027` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p606:c0003` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-027` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_760_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-027` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_218_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-027` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p218:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-028` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_760_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-028` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_606_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-028` | `NB-SEC-01-C-PTR` | `chk_76e248a62974_218_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-028` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p606:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-028` | `NB-SEC-01-C-PTR` | `Operating Systems - Internals and Design Principles 7th.pdf:p218:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-045` | `NB-SEC-01-C-PTR` | `Clase1SOII.pdf:p11:c0000` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-045` | `NB-SEC-01-C-PTR` | `chk_a92d5b22837a_11_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-046` | `NB-SEC-01-C-PTR` | `chk_1217dd5e6038_350_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-046` | `NB-SEC-01-C-PTR` | `chk_a92d5b22837a_11_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-046` | `NB-SEC-01-C-PTR` | `chk_92876e0f2bc2_52_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-046` | `NB-SEC-01-C-PTR` | `Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf:p350:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-046` | `NB-SEC-01-C-PTR` | `Codigo limpio - Robert Cecil Martin.pdf:p52:c0002` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-047` | `NB-SEC-01-C-PTR` | `chk_a92d5b22837a_11_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-047` | `NB-SEC-01-C-PTR` | `chk_1217dd5e6038_350_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-047` | `NB-SEC-01-C-PTR` | `chk_92876e0f2bc2_52_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-047` | `NB-SEC-01-C-PTR` | `Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf:p350:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-047` | `NB-SEC-01-C-PTR` | `Clase1SOII.pdf:p11:c0002` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-048` | `NB-SEC-01-C-PTR` | `chk_1217dd5e6038_350_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-048` | `NB-SEC-01-C-PTR` | `chk_92876e0f2bc2_52_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-048` | `NB-SEC-01-C-PTR` | `chk_a92d5b22837a_11_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-048` | `NB-SEC-01-C-PTR` | `Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf:p350:c0001` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-SYN-048` | `NB-SEC-01-C-PTR` | `Codigo limpio - Robert Cecil Martin.pdf:p52:c0002` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-001` | `fadena-teleco` | `chk_0aa9aa4cc0b2_385_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-001` | `fadena-teleco` | `chk_0aa9aa4cc0b2_365_1` | 2 | `INVALID` | `IN_SCOPE` | `INVALID_SEMANTIC` | `EXCLUDE` | `reports/gate2_scope_candidate_adjudication_2026-09-28.json` |
| `GS2-CMP-001` | `fadena-teleco` | `chk_0aa9aa4cc0b2_386_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-001` | `fadena-teleco` | `Computer_Security_Stallings_3rd_Ed.pdf:p386:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-002` | `fadena-teleco` | `chk_0aa9aa4cc0b2_385_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-002` | `fadena-teleco` | `chk_0aa9aa4cc0b2_365_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-002` | `fadena-teleco` | `chk_0aa9aa4cc0b2_386_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-002` | `fadena-teleco` | `Computer_Security_Stallings_3rd_Ed.pdf:p386:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-004` | `fadena-teleco` | `chk_0aa9aa4cc0b2_385_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-004` | `fadena-teleco` | `chk_0aa9aa4cc0b2_365_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-004` | `fadena-teleco` | `chk_0aa9aa4cc0b2_386_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-004` | `fadena-teleco` | `Computer_Security_Stallings_3rd_Ed.pdf:p386:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-005` | `fadena-teleco` | `chk_0aa9aa4cc0b2_385_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-005` | `fadena-teleco` | `chk_0aa9aa4cc0b2_365_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-005` | `fadena-teleco` | `chk_0aa9aa4cc0b2_386_1` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-005` | `fadena-teleco` | `Computer_Security_Stallings_3rd_Ed.pdf:p386:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-041` | `NB-SEC-01-C-PTR` | `chk_d3b4fecfde23_17_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-042` | `NB-SEC-01-C-PTR` | `chk_d3b4fecfde23_17_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-043` | `NB-SEC-01-C-PTR` | `chk_d3b4fecfde23_17_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-044` | `NB-SEC-01-C-PTR` | `chk_d3b4fecfde23_17_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-CMP-045` | `NB-SEC-01-C-PTR` | `chk_d3b4fecfde23_17_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-111` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_243_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-111` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_102_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-111` | `NB-SEC-01-C-PTR` | `Introduccion-a-la-programacion-en-C.pdf:p243:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-112` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_243_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-112` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_102_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-112` | `NB-SEC-01-C-PTR` | `Introduccion-a-la-programacion-en-C.pdf:p243:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-113` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_243_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-113` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_102_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-113` | `NB-SEC-01-C-PTR` | `Introduccion-a-la-programacion-en-C.pdf:p243:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-114` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_243_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-114` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_102_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-114` | `NB-SEC-01-C-PTR` | `Introduccion-a-la-programacion-en-C.pdf:p243:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-115` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_243_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-115` | `NB-SEC-01-C-PTR` | `chk_dc44a8665f2b_102_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-115` | `NB-SEC-01-C-PTR` | `Introduccion-a-la-programacion-en-C.pdf:p243:c0003` | 1 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-116` | `NB-SEC-01-C-PTR` | `chk_776399a65bec_105_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-116` | `NB-SEC-01-C-PTR` | `chk_bed831d843c0_440_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-117` | `NB-SEC-01-C-PTR` | `chk_776399a65bec_105_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-117` | `NB-SEC-01-C-PTR` | `chk_bed831d843c0_440_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-118` | `NB-SEC-01-C-PTR` | `chk_776399a65bec_105_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-118` | `NB-SEC-01-C-PTR` | `chk_bed831d843c0_440_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-119` | `NB-SEC-01-C-PTR` | `chk_776399a65bec_105_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-119` | `NB-SEC-01-C-PTR` | `chk_bed831d843c0_440_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-120` | `NB-SEC-01-C-PTR` | `chk_776399a65bec_105_1` | 3 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |
| `GS2-FUN-120` | `NB-SEC-01-C-PTR` | `chk_bed831d843c0_440_1` | 2 | `PENDING` | `IN_SCOPE` | `PENDING` | `PENDING` | `pending_adjudication` |

## Política de interpretación

- Cada consulta tiene un estado principal; cada referencia qrel tiene su propio estado, decisión y motivo.
- Una membresía ACL válida no implica validez semántica.
- Estados de query y de qrel se calculan por separado; una query puede ser parcialmente válida aunque una referencia esté excluida.
- `VIOLATION_DETECTED` solo registra una inconsistencia histórica; la acción es `NONE`, sin reasignación ni eliminación automática.
- Los qrels no adjudicados quedan `PENDING_ADJUDICATION`; no se completan juicios por inferencia.
- v2.401 tiene `canonical_for_repair=false` y `historical_evidence=true`.

## Hashes congelados

- v2.400 dataset: `sha256:7ac3c707a973aa7dbc2e79c48c14a6208ac6f72bcba3d184433c2f2bc6b337c1`
- v2.400 qrels: `sha256:68af7033fcd4e607b830245901774d2daac610d909763cb0b999b024b1ed7abc`
- v2.401 dataset (referencia): `sha256:4442e267f5c5eddb778fa2f36065db4841a8c221fbc4ee7a12aa8513ef844857`
- v2.401 qrels (referencia): `sha256:a76b18d6b113b164c3e68455577bfea8777789af4efb179464ad1d8be87d32e6`
- knowledge store: `sha256:fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`

El JSON adyacente es la fuente estructurada de verdad; este Markdown es una vista auditable derivada.
