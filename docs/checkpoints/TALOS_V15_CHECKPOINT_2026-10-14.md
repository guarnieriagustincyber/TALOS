# TALOS V1.5 — checkpoint de recuperación

**ID:** `TALOS-V15-RECOVERY-20261014`  
**Propósito:** snapshot local WIP de continuidad; no es una aceptación funcional, certificación de aislamiento ni release.  
**Repositorio:** `/media/agustin/Laboratorio/study-engie`  
**Rama de recuperación:** `checkpoint/talos-v15-20261014`  
**Base del snapshot:** `032339436639d33d310c437c88fe01d94e977449` (`talos-current-audit` al crear la rama). La rama remota no se actualizó; la base estaba dos commits detrás de `origin/talos-current-audit`.

## Proyecto y alcance

TALOS (KASIU / Study Engine) es un sistema personal de estudio de ciberseguridad basado en evidencia, con retrieval y provenance, evaluación pedagógica determinista, auditoría de generación, estado de aprendizaje y una interfaz HTTP/SSE. Principio rector: **Deterministic code first. AI second.** El agente ayuda a desarrollar TALOS, pero no sustituye sus autoridades de política, evidencia, aislamiento ni release.

Este commit preserva el estado local existente como **WIP**. Incluye cambios funcionales y documentales mezclados que ya estaban en el worktree, sin adjudicarlos como correctos ni promoverlos. No se ejecutaron tests durante esta consolidación.

## Continuidad anterior y plan

Conservar como antecedente [checkpoint 2026-10-13](./TALOS_V15_CHECKPOINT_2026-10-13.md), que registra el historial disponible y los cierres de Fases 1A–1E, F2A-012, B06/B10, STEP-28/46 y CP127. Los documentos rectores y sus límites de procedencia allí registrados siguen aplicando. El Plan Maestro comunicado conserva **20 paquetes T01–T20** y la enmienda `T13a → T06 → T13b`, el orden corregido de T10/T11, T15 en paralelo y la división de T16/T18/T19 en hitos. Algunos documentos del plan completo siguen siendo antecedentes conversacionales y no deben considerarse archivos recuperados si no están presentes.

## Estado de paquetes

- **T01 — Identidad S4.4:** implementación reportada completa; 50 tests focales PASS en ejecución autorizada previa. Perímetro de imports no completamente verificado; la integración de esos efectos se trasladó a T15. No equivale a aceptación global de P1.2.
- **T04 — Identidad ejercicio/KC:** implementación reportada completa; 32 tests focales PASS. Integración UI de `exercise_id` corresponde a T12 y permanece fuera de aceptación integrada.
- **T07 — Identidad vectorial:** implementación y corrección T07-R1 reportadas; ejecución focal final 28 PASS/0 FAIL. Evidencia sintética de identidad y fallback FTS5; no certifica baseline C0 completo ni integración productiva.
- **T08/T09:** pendientes. El trabajo se mantiene detenido antes de implementar una estrategia nueva de ingesta PDF en Colab. No se inició el piloto ni se autorizan Colab, rclone, red, sustitución de corpus o promoción densa por este checkpoint.
- **T02, T03, T05, T06, T10–T20:** conservar el estado y dependencias del plan de 20 paquetes; este snapshot no adjudica su aceptación. La relación `T13a → T06 → T13b`, dependencias T10/T11, T15 paralelo y subdivisiones T16a–d/T18a–c/T19a–c se preservan.

Los conteos focales son antecedentes de ejecución, no resultados reproducidos por este commit. No se suman ejecuciones anteriores ni se extrapolan a suites, arquitectura o release.

## Gates y decisiones preservados

```text
G0 = DOCUMENTALLY_CLOSED_WITH_LIMITATIONS
G1 = APPROVED_DOCUMENTALLY
G2 = NOT_APPROVED
G3 = NOT_AUTHORIZED
G5 = NOT_AUTHORIZED
A-T02 = NOT_READY
DEC-A06 = PENDING_HUMAN_DECISION
P1.2 = OPEN
B1-R = FAIL
RELEASE = NOT_AUTHORIZED
```

La aprobación documental G1 no acredita contención efectiva. Las autorizaciones focales T01/T04/T07 ya consumidas no se convierten en autorización global G3/G5. No se autoriza trabajo T08/T09, Colab ni release.

## Alcance Git y exclusiones

El commit incluye el checkpoint anterior y este documento, los cambios rastreados de código, tests, scripts, configuración de perímetro y documentación del worktree que se encontraron al preparar el snapshot, y archivos nuevos de código/tests/documentación presentes entonces. Los cambios mezclados se conservan como WIP; no se separaron por hunk.

Se excluyeron deliberadamente `.opencode/opencode.json`, la eliminación local de `.opencode/plugins/graphify.js`, todo `graphify-out/` (caché/reportes/grafo generado), bases SQLite, corpus, modelos, snapshots y evidencia externa, archivos `.env`/credenciales y demás datos operativos. Los directorios externos de snapshots B06 se mantienen fuera de Git; sus payloads no se copiaron ni modificaron. Un examen previo encontró estructuras y tamaños repetidos, pero no terminó una comparación hash; por tanto, duplicación byte a byte y recuperabilidad de espacio quedan **sin verificar**.

La rama parte del HEAD local indicado, no de los dos commits remotos pendientes. Este commit no incorpora esos commits, no actualiza referencias remotas y no hace push. Los archivos excluidos —en especial configuración local de OpenCode y artefactos Graphify— no forman parte del snapshot; consultar el estado local original si se necesitan.

## Reanudación

1. Leer este documento y el [checkpoint 2026-10-13](./TALOS_V15_CHECKPOINT_2026-10-13.md).
2. Confirmar rama, HEAD y worktree reales sin asumir que el snapshot es el estado actual.
3. Mantener separados implementación, test focal, aislamiento, integración, aceptación, gates y release.
4. No repetir auditorías generales ni reabrir T01/T04/T07 sin evidencia nueva.
5. Esperar la estrategia del responsable para T08/T09. No iniciar Colab, rclone, red ni cambios del corpus sin autorización específica.

**Integridad:** recuperación Git local de desarrollo, intencionalmente WIP. No es un checkout limpio ni una reproducción certificada; los tests no se ejecutaron en esta operación.
