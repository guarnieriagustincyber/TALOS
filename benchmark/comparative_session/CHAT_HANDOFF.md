# Traspaso de conversación: TALOS y benchmark pedagógico

Este archivo conserva el contexto operativo para continuar en un chat nuevo. Es
un resumen de decisiones y estado, no una transcripción literal de todos los
mensajes.

## Objetivo actual

Preparar una comparación pedagógica TALOS vs NotebookLM con 20 preguntas
consecutivas, protegiendo el estado real del estudiante y evitando cambios en
backend. Después de las pruebas, restaurar la base de datos usando el backup
consistente creado antes de la sesión.

## Decisiones y antecedentes

- El trabajo previo corrigió la calibración pedagógica y propagó contexto BKT
  hacia la experiencia de chat.
- En la UI se priorizó respetar los contratos reales: no inventar metadata de
  citas ni estados BKT ausentes; el porcentaje de dominio se muestra como
  porcentaje cuando el dato existe.
- Se corrigieron previamente errores SSE/HTTP y se agregó bloqueo mutuo a las
  operaciones de ingestión.
- Los metadatos de citas como autor, sección y rol epistémico pueden faltar;
  deben tratarse como opcionales, sin completarlos artificialmente.
- No se solicitó ni se hizo push. No ejecutar pytest para la sesión comparativa.

## Setup realizado

- Las 20 preguntas están en `benchmark_questions.json`.
- Se creó un backup consistente de SQLite usando `Connection.backup()`, no una
  copia en caliente:
  `benchmark/backups/student_state_backup_20260928_012803_541510.db`
- SHA-256 del backup:
  `5d697fedbbe06b4004861ba2a62a139efe57b8cac4e529a2cb93807660a644f3`
- El snapshot previo del estado BKT está en `bkt_snapshot_before.json` y
  contiene datos de la base del estudiante. No debe publicarse ni agregarse al
  repositorio.
- El manifiesto registra la ruta y hash del backup en
  `restore/restore_manifest.json`.
- El restaurador está en `restore_student_state.sh`. Recibe la ruta del backup
  y aborta si el backend responde en `127.0.0.1:8000`; detener el backend antes
  de usarlo.
- El backend ya estaba escuchando en el puerto 8000 durante el setup. No se
  inició ni detuvo ningún proceso.
- El hash del auditor se verificó intacto:
  `cf5b9062f95de7f635738b5c4f0bea074c2fbcfada5c2eccc53cb06e3f277b57`
- No se ha ejecutado aún la sesión de benchmark ni se ha restaurado la DB.

Restauración, una vez terminada la prueba y detenido el backend:

```bash
bash benchmark/comparative_session/restore_student_state.sh \
  benchmark/backups/student_state_backup_20260928_012803_541510.db
```

La comparación con NotebookLM debe registrar las respuestas para las mismas
preguntas y evaluar los criterios de cada caso; no asumir que BKT cambia de modo
por una sola respuesta ni exigir conductas que el contrato no garantice.

## Estado de Git al preparar este traspaso

- Rama: `main`, tres commits por delante de `origin/main`.
- Había seis archivos UI modificados localmente: `ChatWorkspace.tsx`,
  `CurriculumProgress.tsx`, `EvidencePanel.tsx`, `NotebooksView.tsx`,
  `types.ts` y `tsconfig.json`.
- Esos cambios preexistían al setup del benchmark y no se deben descartar.
- El backup `.db` está excluido por el patrón existente `*.db`.
- El snapshot JSON contiene datos del estudiante y se debe mantener local,
  fuera del commit.
- El objetivo solicitado es guardar este handoff, crear un commit que preserve
  el trabajo pendiente sin incluir datos privados, y dejar limpio el árbol de
  trabajo. No hacer push.

## Diagnóstico de CPU de VS Code

- En la revisión del 2026-09-28, el renderer de VS Code PID `119961` se mantuvo
  entre 111% y 114% de CPU en mediciones separadas por dos segundos, equivalente
  aproximadamente a un núcleo. Los otros procesos de VS Code observados tenían
  un consumo muy inferior.
- No se terminó ningún proceso. La recomendación fue guardar archivos y usar
  `Developer: Reload Window`; si vuelve a ocurrir, abrir `Help → Open Process
  Explorer` y luego `Help: Start Extension Bisect` para localizar una vista o
  extensión causante.
- Es una medición puntual; volver a comprobar antes de atribuir la causa a una
  rama, extensión o proceso específico.
