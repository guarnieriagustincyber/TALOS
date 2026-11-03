# Adjudicación documental — lote 01, referencias S01

Fecha: 2026-10-01

## Alcance e identidad

Este lote revisa las 24 referencias potenciales a S01 de las 194 filas que
originalmente no tenían una superficie candidata. La revisión es documental y
estática. Se contrastaron la cola y las definiciones de superficie de
[`A_PRE_0_SURFACE_MANIFEST.json`](../files/A_PRE_0_SURFACE_MANIFEST.json), el
estado de
[`A_PRE_0_QUALIFICATION_LEDGER.json`](../files/A_PRE_0_QUALIFICATION_LEDGER.json)
y la especificación A-PRE-0 con documentación de interfaces Linux.

Este documento conserva el análisis estático y registra la decisión humana
explícita recibida el 2026-10-01. Una aceptación materializa únicamente una
relación candidata con S01; no adjudica la disposición del syscall ni afirma
alcanzabilidad, cobertura o enforcement. Una exclusión significa “excluir esta
relación con S01”, no excluir el syscall del inventario.

## Criterio aplicado

Se consideró S01 como la dimensión de resolución, selección, identificación o
descubrimiento de ubicación de un objeto filesystem cuando forma parte de la
semántica del syscall. Esa membresía no implica que el efecto funcional
completo pertenezca a “Opening/resolution”. Para cada referencia se contrastó
el efecto descrito, los argumentos/recursos relevantes, las rutas por
descriptor o handle y su relación con Model B. Una coincidencia de nombre no
basta.

La documentación consultada establece semántica de interfaces, no demuestra
que una llamada sea alcanzable en el workload, que ocurra en fase WORKLOAD, ni
que esté permitida o denegada por el control. Esos extremos y el cierre de
particiones siguen fuera de este lote.

## Resultado del lote

| Propuesta respecto de S01 | Referencias |
|---|---:|
| Membresía candidata S01 aceptada explícitamente por decisión humana | 13 |
| Relación con S01 excluida | 4 |
| Relación con S01 mantenida `UNKNOWN` | 7 |
| **Total revisado** | **24** |

### Membresías candidatas S01 aceptadas

| NR | Syscall | Fundamento documental y límite |
|---:|---|---|
| 78 | `getdents` | Interactúa con un objeto directorio ya seleccionado mediante FD y permite descubrir su contenido/topología. S01 cubre esa interacción con el objeto; adquisición y ciclo de vida del FD también pertenecen a S03. |
| 79 | `getcwd` | Descubre la ubicación filesystem del `cwd` y devuelve su representación pathname. S01 captura descubrimiento de ubicación/contexto, no apertura de objeto. |
| 80 | `chdir` | Resuelve un pathname y modifica el `cwd`, alterando el punto de referencia de futuras resoluciones relativas. Relación directa con S01. |
| 81 | `fchdir` | Establece el `cwd` desde un FD que identifica un directorio. S01 cubre resolución/contexto del objeto; S03 cubre adquisición, identidad y ciclo de vida del FD. |
| 137 | `statfs` | Selecciona/resuelve un objeto filesystem mediante pathname para consultar metadata del filesystem subyacente. La membresía S01 representa selección/resolución, no apertura. |
| 138 | `fstatfs` | Consulta el filesystem asociado a un objeto identificado por FD. S01 cubre selección/identidad del objeto; S03 cubre procedencia y ciclo de vida del FD. |
| 191 | `getxattr` | Resuelve/selecciona mediante pathname el objeto filesystem cuyos atributos se consultan. S01 representa esa ruta de resolución; el efecto xattr no se atribuye íntegramente a S01. |
| 192 | `lgetxattr` | Como `getxattr`, pero selecciona el symlink mismo sin desreferenciarlo. La variante no-follow permanece explícita. |
| 193 | `fgetxattr` | Selecciona el objeto mediante FD para consultar atributos. S01 representa identificación/selección; S03 cubre procedencia y capacidad del FD. |
| 194 | `listxattr` | Resuelve/selecciona mediante pathname el objeto cuyos nombres xattr se enumeran. S01 representa la ruta de resolución, no todo el efecto de enumeración xattr. |
| 195 | `llistxattr` | Selecciona mediante pathname el symlink mismo, sin seguirlo, para enumerar xattrs. |
| 196 | `flistxattr` | Selecciona el objeto mediante FD para enumerar xattrs. S01 representa identificación/selección; S03 cubre procedencia y ciclo de vida del FD. |
| 303 | `name_to_handle_at` | Resuelve/selecciona el objeto mediante `dirfd`/pathname y deriva un handle opaco y mount ID. Aceptación limitada a esa ruta de identificación; no implica aceptar `open_by_handle_at` (304). |

### Excluir explícitamente la relación con S01

| NR | Syscall | Razón de exclusión de S01; no es exclusión del inventario |
|---:|---|---|
| 253 | `inotify_init` | Crea una instancia de notificación y devuelve un FD. Por sí sola no selecciona un path ni enumera/abre un objeto filesystem; la vigilancia de objetos se configura por separado. Revisar el FD/cola bajo las superficies de descriptor y coordinación que correspondan. |
| 255 | `inotify_rm_watch` | Retira una watch de una instancia mediante su descriptor/identificador de watch; no resuelve ni selecciona un path u objeto filesystem en esta operación. No concluye nada sobre los eventos recibidos ni la política general de inotify. |
| 294 | `inotify_init1` | Variante de creación de instancia con flags; como `inotify_init`, su efecto inmediato es crear el FD/objeto de notificación, no descubrir un path. Los flags deben revisarse por separado fuera de S01. |
| 300 | `fanotify_init` | Crea un grupo de notificación y devuelve un FD; la selección de filesystem/objetos ocurre en una operación distinta. No se excluye la superficie de monitoreo ni el syscall del universo. |

### Mantener `UNKNOWN`

| NR | Syscall | Motivo para no decidir esta relación todavía |
|---:|---|---|
| 136 | `ustat` | La documentación describe estadísticas de un filesystem seleccionado por número de dispositivo, no por path/dirfd/enum. S01 no define explícitamente consultas filesystem-wide por `dev_t`; la relación de amenaza es plausible, pero requiere decidir si se amplía la superficie o se asigna a otra. No excluir el efecto filesystem. |
| 254 | `inotify_add_watch` | Recibe un path y registra una watch, lo que sí resuelve/selecciona un objeto filesystem, pero su efecto central es establecer observación de eventos y no una operación de descubrimiento/open-create descrita expresamente por S01. Requiere decidir si S01 incluye vigilancia y revisar cruces con FD/cola de eventos (S03/S10); no clasificar sólo por el argumento pathname. |
| 301 | `fanotify_mark` | Marca un archivo, directorio, filesystem o mount para notificaciones y, según grupo/eventos, puede participar en decisiones de permiso. Hay intersección material con S01, pero el recurso/efecto es monitoreo/intercepción de eventos y la definición vigente no lo delimita. Requiere relación explícita con S01 y cruces de descriptor/cola (S03/S10); mantener desconocida hasta resolver el alcance. |
| 464 | `getxattrat` | La tabla target-bound y el nombre no bastan para confirmar la semántica exacta de argumentos, flags, resolución y relación con dirfd. No se obtuvo en esta revisión una página de interfaz específica ni una fuente del kernel 7.0 que cierre esos puntos; no inferir por el nombre. |
| 465 | `listxattrat` | Igual limitación que NR 464: falta fuente específica verificada para determinar valores, resolución, flags y objeto consultado. Conservar `UNKNOWN`; no inferir que sea idéntico a `listxattr` más `dirfd`. |
| 304 | `open_by_handle_at` | Permanece `UNKNOWN` respecto de S01. El acceso por handle opaco no se aceptó por inferencia a partir de `name_to_handle_at`; requiere definición explícita de alcance para S01. |
| 468 | `file_getattr` | Falta fuente específica verificada para definir el objeto, las operaciones/campos seleccionables, flags y relación con path/FD. El nombre sugiere metadata, pero no constituye evidencia suficiente. Conservar `UNKNOWN`. |

Las seis relaciones `UNKNOWN` iniciales permanecen: `ustat` (136),
`inotify_add_watch` (254), `fanotify_mark` (301), `getxattrat` (464),
`listxattrat` (465) y `file_getattr` (468). Se conserva además
`open_by_handle_at` (304) como séptimo `UNKNOWN` tras la decisión humana.

## Fuentes semánticas consultadas

Fuentes del proyecto: la definición S01 y su cierre propuesto en el manifiesto
canónico, la tabla target-bound identificada por SHA-256
`93e42d351de2002418bf499b9a538f189fd683e8ecd52b4adc8a0bbe59130455`, y la
regla del ledger de que referencias potenciales no establecen membresía,
alcanzabilidad, exclusión, cierre de variantes ni cobertura.

Documentación Linux man-pages consultada:

- [`getdents(2)`](https://man7.org/linux/man-pages/man2/getdents.2.html)
- [`getcwd(3)`](https://man7.org/linux/man-pages/man3/getcwd.3.html)
- [`chdir(2)`](https://man7.org/linux/man-pages/man2/chdir.2.html)
- [`ustat(2)`](https://man7.org/linux/man-pages/man2/ustat.2.html)
- [`statfs(2)`](https://man7.org/linux/man-pages/man2/statfs.2.html)
- [`getxattr(2)`](https://man7.org/linux/man-pages/man2/getxattr.2.html)
- [`listxattr(2)`](https://man7.org/linux/man-pages/man2/listxattr.2.html)
- [`inotify(7)`](https://man7.org/linux/man-pages/man7/inotify.7.html)
- [`fanotify(7)`](https://man7.org/linux/man-pages/man7/fanotify.7.html)
- [`open_by_handle_at(2)`](https://man7.org/linux/man-pages/man2/open_by_handle_at.2.html)

Estas referencias documentan interfaces; no certifican el comportamiento
efectivo del target, la alcanzabilidad, el modelo de despliegue ni el control
activo. No se usaron para afirmar `OBSERVED`, `BLOCKED` o cobertura.

## Materialización de la decisión humana

El usuario aceptó explícitamente como membresías candidatas de S01 las 13 filas
enumeradas arriba. Para cada una se añadió `S01` a `candidate_surface_ids` y a
la lista `S01.syscalls`, y se registró la decisión y su límite semántico en el
registro de esa fila del manifiesto.

- Las operaciones basadas en FD conservan cruces a S03: `getdents` (78),
  `fchdir` (81), `fstatfs` (138), `fgetxattr` (193) y `flistxattr` (196).
  `name_to_handle_at` (303) conserva el cruce por `dirfd`.
- `getxattr`/`listxattr` y sus variantes están aceptadas por selección/
  resolución del objeto; no se asigna a S01 todo el efecto xattr.
- `getcwd` está aceptada por ubicación/contexto, no como apertura.
- No se modificó ninguna disposición general: los 385 `disposition_status`
  siguen `UNKNOWN`, incluidas las 13 filas con membresía candidata aprobada.
- `open_by_handle_at` (304) sigue sin S01 en `candidate_surface_ids` y su
  disposición general permanece `UNKNOWN`.
- Las cuatro exclusiones de relación con S01 y las seis incertidumbres
  originales se conservaron; 304 es adicionalmente `UNKNOWN`.
- Ningún cambio implica `OBSERVED`, `BLOCKED`, cobertura, readiness ni cierre
  de variantes.

## Efecto sobre el inventario y siguiente paso

Las 24 referencias originales permanecen trazadas como pistas históricas. Se
materializaron sólo las 13 relaciones expresamente aceptadas; las cuatro
exclusiones y siete `UNKNOWN` no se convierten en membresías. No cambian los
385 estados generales `UNKNOWN`, `inventory.frozen=false`, A-PRE-0 `NOT READY`
ni A-PRE-1 `NOT AUTHORIZED / NOT EXECUTED`.

Siguiente revisión documental: revisar las siete relaciones `UNKNOWN` y los
cruces de inotify/fanotify con S03/S10; obtener y verificar semántica de las
syscalls NR 464, 465 y 468 contra una fuente versionada del target. Cualquier
otra referencia requiere decisión humana separada.

No se ejecutaron probes, TALOS, suites, parsers ni validadores A-PRE. No se
modificaron VM, overlay, runtime, lock, corpus, modelos ni bases de datos.
