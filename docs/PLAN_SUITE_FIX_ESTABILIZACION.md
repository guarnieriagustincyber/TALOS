# Suite de fixes y estabilización previa a Fase 7

**Fecha:** 2026-09-28
**Estado:** punto 0 completado; gates de corrección pendientes
**Alcance:** armonizar políticas, contratos multi-cuaderno y fiabilidad antes de
continuar con evaluación pedagógica multi-currículo.

## Objetivo

Corregir defectos y contradicciones que bloquean una evaluación fiable de
TALOS, y demostrar las correcciones mediante pruebas reproducibles. Esto no es
una limpieza general del repositorio, una refactorización amplia ni una nueva
fase de producto. No agregar capacidades fuera de los hallazgos acotados aquí.

La suite se ejecuta sobre cambios pequeños y verificables. Se registran los
fallos preexistentes aparte de los regresivos, y no se modifica ni descarta
trabajo que ya esté en el árbol.

## Punto 0 — Congelar y medir el punto de partida

Antes de tocar código de producción:

1. Guardar y comprometer por separado la documentación de diagnóstico y este
   plan, sin mezclarla con fixes de aplicación.
2. Confirmar rama, commit `HEAD`, árbol limpio y configuración del entorno de
   pruebas.
3. Capturar la suite global existente y los chequeos específicos relevantes
   para F5, SSE/UI y contratos pedagógicos. Registrar comandos, conteos,
   skips, warnings y fallos, sin corregirlos todavía.
4. Identificar por evidencia qué fallos son preexistentes, cuáles se deben a
   entorno/configuración y cuáles aparecen como regresiones durante esta
   suite.
5. Conservar resultados previos como snapshots históricos; la suite global
   previamente reportada (2695 passed, 7 skipped) no sustituye una ejecución
   actual.

**Salida:** baseline fechada, reproducible y asociada al commit inicial de la
suite. Si la suite global no puede ejecutarse, registrar el bloqueo concreto y
usar solo checks alternativos que no se presenten como equivalentes.

### Resultado de baseline — 2026-09-28

- Punto de partida: rama `main`, commit `0e57eea`, árbol limpio antes de las
  pruebas; Python 3.12.3 y pytest 9.1.1 en `.venv`.
- Suite global: `.venv/bin/pytest -q` — **2695 passed, 7 skipped, 0 failed**,
  138 warnings, 313.47 s.
- Suite focalizada de contexto F5, endpoint SSE/UI, rewriter, finish reason,
  pipeline adaptativo y prompt socrático — **100 passed**, 5 warnings,
  7.19 s.
- Sintaxis del consumidor UI: `node --check
  src/study_engine/web/static/js/chat.js` — pasó.
- Las pruebas globales reescribieron cuatro resultados versionados:
  `benchmark/results/evaluation_report.json`,
  `benchmark/results/evaluation_report.md`,
  `benchmark/results/latest_summary.json` y
  `data/experiments/survival/l5_concurrency_race_50.json`. Se restauraron a su
  contenido del commit inicial después de revisar los diffs; el árbol quedó
  limpio. El reporte Fase 4-eval generado durante tests sintéticos mostró
  MRR@5/nDCG@5 de retrieval en cero y estado FAIL, aunque pytest terminó sin
  fallos. Tratar esto como un problema de aislamiento/efectos laterales de la
  suite y no como un resultado de evaluación del producto; no modificar esos
  umbrales ni promocionar ese reporte.

**Conclusión de punto 0:** la base funcional es reproducible en el entorno
actual. Antes de usar repetidamente la suite global como gate, conviene
aislar sus salidas generadas para que no reescriba reportes y evidencia
versionados.

## Gate 1 — Alinear políticas y nomenclatura

- Resolver la contradicción entre la prohibición global de soluciones completas
  y la atención a una solicitud explícita segura. Distinguir práctica libre de
  evaluaciones con solucionario protegido.
- Fijar precedencia: seguridad y exactitud; fuentes y alcance curricular;
  solicitud explícita del turno; objetivo pedagógico; preferencias duraderas
  solo cuando no contradicen el pedido actual.
- Distinguir los nombres de Fases 0–7 del plan pedagógico de las fases de
  producto, evaluación, seguridad y retrieval.

**Salida:** reglas coherentes y no ambiguas antes de modificar el ensamblado
de prompts.

## Gate 2 — Aislar el perfil pedagógico por cuaderno

- Resolver perfiles por IDs registrados exactos, no por subcadena ambigua.
- Corregir `fadena-std` para que corresponda a Tratamiento de Datos.
- Retirar del contrato fallback fases y analogías específicas de programación;
  usar un contrato neutral si el cuaderno no tiene perfil explícito.
- Limitar supuestos de C/x86-64 a los cuadernos, materiales o pedidos que los
  justifiquen, no al prompt global.
- Verificar el recorrido real de cuaderno/currículum/fuentes hasta contrato y
  prompt final.

**Pruebas de salida:** perfiles de programación, Sistemas Operativos,
Tratamiento de Datos y Telecomunicaciones; assertions positivas de lo propio y
negativas de contaminación cruzada. Un ID desconocido usa un perfil neutral o
falla con un diagnóstico explícito; nunca hereda un perfil parecido.

## Gate 3 — Cerrar criterios de aceptación de F5

Añadir o completar pruebas deterministas para:

- una instrucción puntual que contradice una preferencia histórica;
- referencias y ejercicios cuando falta el antecedente, enunciado o intento;
- feedback limitado al intento visible y su contexto;
- ausencia de mutación BKT/perfil por conversación ordinaria sin evidencia
  evaluativa;
- alcance y límites de los avisos heurísticos de discrepancia entre fuentes.

**Salida:** continuidad aislada, trazable y basada en evidencia, sin inferir
aprendizaje o dominio a partir de la mera conversación.

## Gate 4 — Cerrar F6 de extremo a extremo

- Definir estados terminales distintos para éxito completo, truncamiento,
  cancelación, error y abstención/clarificación cuando corresponda.
- No guardar ni presentar como completa una respuesta que no tenga una
  terminación exitosa explícita; conservar y rotular texto parcial como
  incompleto cuando sea útil.
- Manejar truncamiento, aborto, EOF sin terminal, terminal duplicado y error
  posterior a texto en la UI.
- Separar mensajes públicos seguros de detalles de excepción internos.
- Probar el flujo endpoint SSE → consumidor UI con dobles deterministas;
  mantener separada cualquier validación con proveedor real.

**Salida:** ningún camino probado convierte una respuesta incompleta o fallida
en éxito silencioso.

## Gate 5 — Regresión global y habilitación de F7

- Ejecutar pruebas focalizadas después de cada gate y la suite global una vez
  integrados los cambios.
- Construir una matriz equilibrada de currículos e intenciones: explicar,
  resumir, “no entendí”, ejercicio, corrección y seguimiento.
- Fijar la rúbrica y los criterios de aceptación antes de puntuar respuestas.
- Reportar resultados por currículo e intención, con límites y fallos visibles.
- Mantener evaluación de respuestas separada de cualquier afirmación de
  retención o transferencia del estudiante.

**Salida:** decisión documentada de aceptar, iterar o declarar inconclusa la
evaluación; comenzar F7 solo cuando los gates anteriores sean satisfactorios.

## Criterio global de cierre

La suite queda cerrada cuando:

1. las políticas y la nomenclatura son coherentes;
2. ningún cuaderno recibe por fallback pedagogía de otro currículum;
3. los criterios pendientes de F5 están cubiertos por pruebas;
4. los estados de SSE/UI no presentan truncamientos o fallos como éxito;
5. las pruebas focalizadas y globales pasan, o cada excepción tiene causa,
   alcance e impacto documentados sin ocultar un fallo;
6. los documentos describen exactamente lo implementado y validado.

## Límites

- No repetir la comparación TALOS/NotebookLM de 20 preguntas sin solicitud
  explícita y protocolo registrado.
- No copiar al repositorio el historial privado de NotebookLM.
- No modificar umbrales, límites de tokens ni timeouts sin evidencia medida.
- No tratar datos curriculares configurados como prueba suficiente del
  comportamiento de extremo a extremo.
- No iniciar refactorizaciones ajenas a estos gates durante la suite.

## Documentos de contexto

- [Diagnóstico multi-cuaderno y plan de continuidad](./DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md)
- [Plan rector de mejora pedagógica](./PLAN_MEJORA_PEDAGOGICA_TALOS.md)
