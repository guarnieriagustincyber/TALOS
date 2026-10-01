# Punto de guardado 013 — cierre de sesión y reanudación

Fecha de creación: 2026-10-01 05:11 -03:00

## 1. Identidad del punto de partida

- Repositorio: `guarnieriagustincyber/TALOS`.
- Branch al iniciar este guardado: `main`.
- Commit persistente de recuperación: `fae02256a82160f0538b42b0cbc9b2534f0e44aa`.
- Tree de ese commit: `2b1823eb03e99945f1bfdf38b25c0378161416a9`.
- Parent: `b12e34099336760e8fd55455526a580cd479dade`.
- El commit `fae02256a82160f0538b42b0cbc9b2534f0e44aa` es explícitamente el
  punto persistente de recuperación para reanudar el trabajo documental A-PRE.
- Estado del working tree al crear este checkpoint: **DIRTY**. Había cambios
  ajenos a este guardado; no se incorporan ni se descartan. Los únicos archivos
  autorizados para el commit de este guardado son este checkpoint y
  `checkpoints/index.md`.

## 2. Estado documental A-PRE-0

- Target documental: `fadena-lab`.
- Sistema objetivo: Ubuntu 26.04 LTS (Resolute), x86_64.
- Kernel objetivo: `7.0.0-34-generic`.
- Tabla normativa: `arch/x86/entry/syscalls/syscall_64.tbl`.
- SHA-256 de la tabla normativa:
  `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
- CPython baseline: `3.10.21`.
- Universo enumerado: 385 filas native x86_64, con enumeración 1:1.
- Disposición general: **385 UNKNOWN**.
- Casos históricos syscall-específicos: **27**, en 17 filas; **16 OBSERVED /
  11 BLOCKED**. Son resultados acotados a su syscall, variante y ruta.
- Filas inicialmente sin candidata: **194**.
- Filas de ese grupo con referencias potenciales: **186**.
- Referencias potenciales totales: **204**.
- Distribución: **168** filas con una referencia; **18** con dos referencias
  potenciales solapadas.
- Filas sin relación suficientemente justificada: **8** — `_sysctl`,
  `afs_syscall`, `getpmsg`, `getrandom`, `nfsservctl`, `putpmsg`, `tuxcall`,
  `vserver`.
- `inventory.frozen=false`.
- A-PRE-0: **NOT READY**.
- A-PRE-1: **NOT AUTHORIZED / NOT EXECUTED**.
- x32 e i386 compat permanecen fuera del alcance declarado.

## 3. Aclaración semántica obligatoria

- `potential_surface_refs` son pistas documentales de revisión, **no**
  membresías canónicas.
- Ninguna de las 204 referencias fue convertida en `candidate_surface_ids`.
- Los 27 casos históricos son cierres acotados por syscall/variante/ruta; no
  elevan la disposición general de una syscall ni de una fila.
- `UNKNOWN` permanece como estado fail-closed cuando la evidencia no permite
  una decisión acotada.
- Ni una coincidencia de nombre ni una relación de familia constituye por sí
  sola evidencia de membresía, cobertura, `OBSERVED` o `BLOCKED`.

## 4. Trabajo documental cerrado — no rehacer

- Provenance e identidad del target documental.
- Enumeración normativa 1:1 de las 385 filas para el target fijado.
- Revisión documental del grupo de 194 filas inicialmente sin candidata.
- Consolidación de 204 referencias potenciales sobre 186 filas, con 8 filas
  sin relación suficientemente justificada.
- Adjudicación acotada de los 27 casos históricos: 16 `OBSERVED` y 11
  `BLOCKED`, sin generalización a la disposición completa.
- Recuperación y persistencia de los artefactos documentales A-PRE-0 y puntos
  de continuidad asociados en el estado persistente señalado arriba.

## 5. Trabajo pendiente

Continuar únicamente con la adjudicación documental de las **186 pistas**:

1. Evaluar argumentos, recursos, fase de ejecución, rutas alternativas y
   relación con Model B.
2. Para cada pista, decidir sólo entre membresía canónica respaldada,
   exclusión explícita justificada o permanencia en `UNKNOWN`.
3. Resolver las ocho filas unresolved sólo con evidencia suficiente; de lo
   contrario, mantenerlas `UNKNOWN` y documentar la razón.
4. Revisar variantes y trazabilidad, sin inferir particiones finitas donde no
   estén documentadas.
5. Mantener readiness y el estado de autorización sin cambios.

Las 18 filas con dos referencias requieren resolver explícitamente si las dos
superficies son válidas, si una referencia se excluye con justificación o si
la relación permanece `UNKNOWN`. No escoger una por intuición.

## 6. Restricciones vigentes

Hasta una autorización explícita posterior:

- No ejecutar probes.
- No ejecutar TALOS.
- No ejecutar suites.
- No ejecutar parsers ni validadores A-PRE.
- No modificar la VM.
- No modificar el overlay v4.
- No modificar `requirements.lock`.
- No tocar corpus, modelos ni bases de datos.
- No compilar ni cambiar el runtime.
- No declarar `inventory.frozen=true`.
- No cambiar A-PRE-0 a `READY`.
- No autorizar ni ejecutar A-PRE-1.
- No convertir una pista semántica en membresía, cobertura, `OBSERVED` o
  `BLOCKED` por inferencia de nombre o familia.
- No modificar los artefactos A-PRE existentes en esta tarea de guardado.
- No adjudicar las 186 pistas durante esta tarea.

## 7. Principio rector

**OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN DECISION → FUTURE CHANGE**

## 8. Reanudación

**Al reanudar, verificar primero que el checkout esté sobre el commit persistente y leer este checkpoint. No rehacer trabajo previo. Continuar únicamente desde la cola documental de las 186 pistas.**
