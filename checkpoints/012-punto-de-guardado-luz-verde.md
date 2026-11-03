# Punto de guardado 012 — reanudar con «luz verde»

## Instrucción de reanudación

Cuando el usuario escriba únicamente **«luz verde»** en una conversación nueva,
reanudar desde este checkpoint y continuar documentalmente desde la cola de
adjudicación de las pistas de superficie. No volver al inicio, no rehacer la
provenance del target ni enumerar otra vez la tabla de syscalls.

## Estado exacto al guardar

- Target documental: `fadena-lab`, Ubuntu 26.04 LTS (Resolute), x86_64.
- Kernel objetivo: `7.0.0-34-generic`.
- Tabla normativa: `arch/x86/entry/syscalls/syscall_64.tbl`.
- SHA-256 de la tabla: `93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`.
- Universo normativo: 385 filas native x86_64, enumeradas 1:1.
- x32 e i386 compat: fuera de alcance declarado.
- CPython baseline: 3.10.21.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

## Trabajo documental ya cerrado

- La identidad del target y la procedencia de la tabla quedaron ligadas por
  paquete/source metadata y hash de tabla; no se rehizo la enumeración
  existente.
- Las 385 filas tienen disposición explícita, pero las 385 permanecen
  `UNKNOWN` como disposición final.
- Hay 27 casos históricos acotados en 17 filas: 16 `OBSERVED` y 11 `BLOCKED`.
  Son casos por syscall + variante + ruta, no cierres de filas completas.
- Se revisaron las 194 filas que inicialmente no tenían superficie candidata:
  - 186 tienen una o más referencias potenciales a superficies existentes;
  - 204 referencias totales;
  - 168 filas tienen una referencia;
  - 18 filas tienen dos referencias solapadas;
  - no se modificó `candidate_surface_ids`;
  - no se agregaron superficies;
  - no se registraron exclusiones;
  - las 194 filas siguen `UNKNOWN`.
- Distribución de las 204 referencias potenciales:
  - `S01=24`
  - `S02=19`
  - `S04=6`
  - `S05=17`
  - `S06=19`
  - `S10=38`
  - `S11=27`
  - `S15=3`
  - `S16=51`
- Las ocho filas sin relación existente suficientemente justificada siguen
  `UNKNOWN`, sin declararlas ausentes, inofensivas ni fuera de alcance:
  `_sysctl`, `afs_syscall`, `getpmsg`, `getrandom`, `nfsservctl`, `putpmsg`,
  `tuxcall`, `vserver`.
- Se revisaron siete grupos de variantes; cero particiones finitas quedaron
  cerradas.
- La trazabilidad exacta callsite → CPython/libc/extensión/dependencia →
  syscall → partición de argumentos sigue abierta; hay cero cadenas exactas
  demostradas.

## Artefactos actualizados

- `files/A_PRE_0_SURFACE_MANIFEST.json`
  - contiene el inventario de 385 filas, casos históricos, revisión de las
    194 filas, distribución de referencias y razones de las ocho filas
    unresolved.
- `files/A_PRE_0_QUALIFICATION_LEDGER.json`
  - replica los conteos y el estado `NOT_READY`.
- `files/A_PRE_0_BASELINE_SPEC.md`
  - contiene la consolidación documental de las pistas y filas legacy.
- `checkpoints/011-consolidacion-pistas-y-legacy.md`
  - checkpoint anterior sobre la consolidación de pistas.

## Restricciones vigentes

Hasta una autorización explícita posterior:

- no ejecutar probes;
- no ejecutar TALOS;
- no ejecutar suites;
- no ejecutar parser/validador A-PRE;
- no modificar la VM;
- no modificar el overlay v4;
- no modificar `requirements.lock`;
- no tocar corpus, modelos ni bases de datos;
- no compilar ni cambiar el runtime;
- no declarar `inventory.frozen=true`;
- no cambiar A-PRE-0 a `READY`;
- no autorizar ni ejecutar A-PRE-1;
- no convertir una pista semántica en membresía, cobertura, `OBSERVED` o
  `BLOCKED` por inferencia de nombre o familia.

## Próximo trabajo al recibir «luz verde»

Continuar únicamente con la adjudicación documental de las 186 pistas:

1. revisar cada pista por argumentos, recursos, fase, rutas alternativas y
   relación con el modelo de amenaza B;
2. decidir, sólo con evidencia suficiente, entre membresía canónica,
   exclusión explícita justificada o permanencia en `UNKNOWN`;
3. resolver documentalmente las ocho filas legacy/special o dejarlas
   `UNKNOWN` con la razón exacta;
4. mantener sin cambios el estado de readiness y las restricciones anteriores;
5. actualizar sólo los artefactos documentales relacionados y crear el
   siguiente checkpoint.

Principio rector: **OBSERVE → MEASURE → CORRELATE → CLASSIFY → HUMAN
DECISION → FUTURE CHANGE**.

