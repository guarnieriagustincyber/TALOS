# Adjudicación documental — lote 12, S12 io_uring

Fecha: 2026-10-01

## 1. Alcance y baseline

Esta adjudicación resuelve exclusivamente las tres candidaturas de
[`035-preparacion-lote-12-s12.md`](./035-preparacion-lote-12-s12.md): `io_uring_setup`
(425), `io_uring_enter` (426) y `io_uring_register` (427), según los números
del inventario target-bound x86_64.

Hashes verificados antes de editar:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `efcd4a9898cc088c660d88b41633733745f9cc1fac4fb628f13dbe7e47b97a98` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |

Baseline documental:

- S10: 37 relaciones; 31 YES, 6 NO y 0 UNKNOWN. Sus 12 leads
  poll/select/epoll permanecen sin promover.
- S11: 17 YES, 0 NO y 0 UNKNOWN. Sus 14 leads permanecen sin promover.
- S12: tres candidaturas `UNREVIEWED` antes de esta adjudicación.
- Disposiciones generales: 385/385 `UNKNOWN`; cero finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

## 2. Doctrina aplicada

> **S12 = interfaz nativa Linux io_uring: creación/configuración del ring,
> entrada/ejecución de operaciones y registro/configuración de recursos
> mediante la interfaz io_uring.**

La decisión es de membership de superficie; no es disposición global de la
syscall, prueba de reachability, resultado de ejecución ni cobertura
exhaustiva de variantes. Se adjudica por la función directa de cada operación
en la interfaz nativa. Los efectos de las operaciones sometidas o los
recursos relacionados siguen separados en sus superficies correspondientes.

## 3. Decisiones individuales

| NR / syscall | Decisión | Fundamento y condición / alcance |
|---|---|---|
| 425 `io_uring_setup` | **YES** | Es la operación nativa que crea/configura una instancia ring de io_uring. La revisión abarca `entries`, `io_uring_params`, flags `IORING_SETUP_*`, features y parámetros/offsets del ring. Un setup exitoso establece el ring; un fallo no demuestra que se haya creado. El FD devuelto tiene lifecycle S03 separado: no es motivo para trasladar toda la syscall a S03. El setup vacío observado históricamente no es requisito para la membership ni evidencia de una SQE. |
| 426 `io_uring_enter` | **YES** | Es la interfaz de entrada para someter SQEs y gestionar el progreso/espera del ring. Mantener `to_submit`, `min_complete`, flags de entrada y la interacción con SQ/CQ como variantes. Incluye las rutas de entrada/espera/despertar propias del ring aunque una llamada concreta no someta una SQE. El caso histórico de cero SQE sólo acredita ese subcaso y no evidencia ejecución de operaciones. Los efectos posteriores de SQEs no alteran esta clasificación. |
| 427 `io_uring_register` | **YES** | Es la interfaz nativa para registrar, desregistrar o configurar recursos/opciones del ring, determinada por `opcode`, `nr_args` y `arg`. La revisión incluye, cuando estén soportadas, categorías como buffers, files/FDs, personalities, restricciones y otras opciones de registro/configuración. Cada categoría conserva sus cruces propios; el recurso registrado no convierte automáticamente esos efectos en S12 ni en otra membership. La falta de un caso histórico exitoso no revoca la semántica directa de la interfaz. |

**Resultado:** 3 YES, 0 NO, 0 UNKNOWN. No se excluyeron candidaturas ni se
amplió el lote.

## 4. Materialización

Se registraron exclusivamente estas tres relaciones humanas `S12 YES` en
`static_disposition_review.surface_membership_adjudications` de sus filas
target-bound, con referencia a este checkpoint y `disposition_unchanged:
UNKNOWN`. Los contextos de candidatura S12 correspondientes se actualizaron
a `HUMAN_ADJUDICATED_CANDIDATE`.

No se modificaron memberships S01–S11, las listas declarativas de syscalls
por superficie ni las disposiciones globales. En particular:

- S02 no absorbe la membership de la interfaz por ser payload de una SQE.
- S03 conserva separado el lifecycle del FD del ring y de FDs registrados.
- S05/S06 conservan sus dimensiones de mappings y memoria.
- S07/S08 conservan las dimensiones de red y AF_UNIX.
- S09 conserva passing/acquisition de capacidades por mecanismos externos.
- S10 conserva IPC/coordinación.
- S11 conserva proceso/exec/terminación.

La lista de syscalls declarada bajo S12 ya enumeraba estas tres candidaturas;
la materialización de las decisiones se registra en las relaciones
adjudicadas por fila, sin expandir dicha lista.

## 5. Evidencia histórica de efecto: alcance y separación

El manifiesto ya registraba para el perfil
`a-pre-native-async-deny-v1`, SHA-256
`ff44e7f9573fe503fd023792d1e38c44ba8b4ac53275097559eaece82e0ea9e9`,
casos separados de `BLOCKED` con `EPERM` para `io_uring_setup`,
`io_uring_enter` e `io_uring_register`. Los casos están enlazados al mismo
`seccomp-probe.json` (SHA-256
`350d5d8c40125417a9475ed7caa77fcd1acf15bc49f80da817a1cb17695f9d8b`) y
`isolation.json` (SHA-256
`17d94bac187ca74b008a34e192c29706e170080e25dc626e13e4b9fb81d8226d`).
En el conjunto combinado io_uring y Linux native AIO constan 9/9
denegaciones históricas `EPERM`: estas tres llamadas más `io_setup`,
`io_destroy`, `io_getevents`, `io_submit`, `io_cancel` e `io_pgetevents`.

Para S12, la cobertura histórica `BLOCKED` se refiere a los casos/syscalls
exactos bajo ese perfil e identidad. La denegación de una syscall no se
infiere de la de otra; no se extrapola a otras configuraciones, perfiles,
rutas o variantes, ni se entiende como cobertura exhaustiva de SQE u
operaciones. Los casos `OBSERVED` existentes se limitan al setup exitoso de
un ring sintético vacío y al enter con cero SQE. El manifiesto documenta que
estos artefactos históricos no están re-vinculados al overlay calificado
actual. No se repitieron ni ejecutaron probes en esta tarea.

La evidencia de efectos `BLOCKED` no fue fundamento de las decisiones YES:

```text
membership documental S12 ≠ effect coverage ≠ disposición global
```

## 6. Estado e invariantes de salida

- Disposiciones globales: 385/385 `UNKNOWN`; cero finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- S10 permanece en 31 YES / 6 NO dentro de 37 relaciones; 12 leads de
  poll/select/epoll siguen sin promover.
- S11 permanece en 17 YES / 0 NO / 0 UNKNOWN; 14 leads siguen sin promover.
- Ninguna membership S01–S11 fue modificada.
- Ledger y `requirements.lock` permanecen byte-identical.
- No se modificaron código funcional, perfil seccomp, E5/Qwen, corpus,
  modelos ni bases protegidas.
- No se ejecutaron TALOS, workloads, probes ni actividad dinámica.
- No se avanzó a S13.
