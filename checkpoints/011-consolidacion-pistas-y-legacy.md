# Consolidación de pistas y filas legacy

## Alcance

Se consolidó documentalmente la revisión de las 194 filas sin superficie candidata. No se ejecutaron probes, TALOS, suites, parser/validador ni cambios de VM, overlay o lock.

## Resultado

- 194 filas revisadas; todas permanecen sin membresía canónica y `UNKNOWN`.
- 186 filas tienen una o más referencias potenciales a superficies existentes.
- Las 204 referencias se distribuyen en 168 filas con una referencia y 18 filas con dos referencias solapadas.
- Distribución de referencias: S01=24, S02=19, S04=6, S05=17, S06=19, S10=38, S11=27, S15=3 y S16=51.
- No se introdujeron superficies nuevas, exclusiones ni cambios de `candidate_surface_ids`.
- Las ocho filas `_sysctl`, `afs_syscall`, `getpmsg`, `getrandom`, `nfsservctl`, `putpmsg`, `tuxcall` y `vserver` conservan razones explícitas para permanecer `UNKNOWN`; ninguna fue declarada ausente, inofensiva o fuera de alcance.

## Criterio preservado

Una referencia semántica por nombre es una pista de adjudicación, no evidencia de alcanzabilidad ni cobertura. Cada pista requiere decisión por argumentos, recursos, fase, ruta alternativa y trazabilidad exacta; si falta esa evidencia, permanece `UNKNOWN`.

## Estado

- `inventory.frozen=false`
- A-PRE-0: `NOT READY`
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`
