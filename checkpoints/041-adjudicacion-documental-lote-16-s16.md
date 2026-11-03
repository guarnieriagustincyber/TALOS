# Adjudicación documental — lote 16, S16 namespaces, mounts y privilegios

Fecha: 2026-10-01

## 1. Alcance y baseline

Esta adjudicación resuelve las **33 relaciones syscall S16 ya identificadas**
en `surfaces[id=S16].syscalls` y en el inventario target-bound. No añade
candidaturas. Las 51 referencias S16 marcadas como potenciales leads en
`no_candidate_review` permanecen fuera de esta adjudicación y sin promover.

Hashes basales verificados antes de editar:

| Artefacto | SHA-256 |
|---|---|
| Manifiesto `files/A_PRE_0_SURFACE_MANIFEST.json` | `11de7646449809ba82f9f75835ea682ec1959d21c9f0f75ee723baca4b21480f` |
| Ledger `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Relaciones/superficies S01–S15 (digest semántico pre-edición) | `cd9e375f70062982f5500dd2acc3ad64e00a880f649b00dd75b9df6e177b2378` |

SHA-256 del manifiesto posterior a materializar S16:  
`866b2dd8cbf88db6918f3091851f2ba7ef3f240ce6e29726650b9065c79a9219`.

Estado previo:

- S10: 31 YES / 6 NO.
- S11: 17 YES.
- S12: 3 YES.
- S13: 6 YES.
- S14: 9 YES.
- S15: 3 YES / 1 UNKNOWN.
- Disposiciones globales: 385/385 `UNKNOWN`; 0 finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.

## 2. Doctrina aplicada

S16 cubre las dimensiones de namespaces/asociación de procesos, topología de
mounts, credenciales/capabilities y controles privilegiados/de ejecución.
Cada YES está condicionado a la operación y variante descritas abajo. Una
relación S16 no afirma que la llamada se haya realizado, haya tenido éxito,
que el proceso posea privilegios determinados ni que exista enforcement
efectivo.

```text
membership semántica ≠ effect coverage ≠ enforcement
```

## 3. Decisiones individuales

### Namespaces y asociación de procesos — 4 YES

| NR / syscall | Decisión y alcance |
|---|---|
| 56 `clone` | **YES**, sólo dimensión namespace cuando flags `CLONE_NEW*` aplicables (p. ej. NEWNS, NEWUTS, NEWIPC, NEWUSER, NEWPID, NEWNET, NEWCGROUP y tipos soportados) efectúan creación/asociación de namespace. La creación del hijo permanece en la relación S11 ya adjudicada; flags de memoria/FD/señales no se absorben en S16. |
| 435 `clone3` | **YES**, sólo dimensión namespace indicada por `clone_args.flags` y variantes soportadas. Creación proceso/hilo permanece en S11; `pidfd`, memoria, FD y otros campos conservan su dimensión propia. |
| 272 `unshare` | **YES**, para la separación/creación de namespaces seleccionada por flags en el task llamador. La cobertura depende del tipo de namespace/flags, permisos, user namespace y resultado; no se afirma que todos los tipos ni toda llamada tengan éxito. |
| 308 `setns` | **YES**, para asociar el calling task al namespace existente seleccionado por namespace FD y tipo/flags. Distinguir los tipos soportados, identidad/propiedad del namespace, permisos y resultado; no se infiere cobertura de todos los tipos. |

### Mount y filesystem topology — 11 YES

| NR / syscall | Decisión y alcance |
|---|---|
| 165 `mount` | **YES**, montaje/configuración elegidos por source, target, filesystem type, flags/data y mount namespace; condicionado a resolución, permisos/capabilities y resultado. Topología S16 separada de cambios de contenido/namespace filesystem S04. |
| 166 `umount2` | **YES**, detach/unmount del target y flags aplicables (incluidos detach/expire/force cuando soportados), dentro del mount namespace; resolución, privilegios y resultado son condiciones. No clasifica automáticamente contenido filesystem como S16. |
| 155 `pivot_root` | **YES**, cambio de root/pivot mount usando `new_root`/`put_old` y relaciones de mounts en el namespace; preservar resolución, permisos y resultado. No implica mutación del contenido de archivos. |
| 161 `chroot` | **YES**, cambio del root directory del proceso según path resuelto y permisos. Es cambio de vista/resolución del proceso; no demuestra confinement efectivo ni mutación del filesystem. |
| 428 `open_tree` | **YES**, apertura/clonado de mount tree según dirfd/path/flags y variantes admitidas. Distinguir obtención de handle FD (S03) de cualquier cambio posterior en topología. |
| 429 `move_mount` | **YES**, mover/adjuntar mount entre source y destination seleccionados por FD/path/flags; mount namespace, permisos y resultado son explícitos. |
| 430 `fsopen` | **YES**, creación de filesystem context para el filesystem/flags elegido. Es etapa de configuración; no equivale a un mount ya adjuntado. FD devuelto mantiene cruce S03. |
| 431 `fsconfig` | **YES**, configuración del contexto identificado por fs FD, particionada por command, key/value o FD auxiliar y operaciones de create/reconfigure; no implica por sí sola attach. |
| 432 `fsmount` | **YES**, creación del mount object desde filesystem context/flags; distinguir el objeto/FD creado de su posterior attachment a namespace topology. |
| 433 `fspick` | **YES**, selección de un filesystem context a partir de dirfd/path/flags de un mount existente; resolución S01 y lifecycle FD S03 siguen separados. |
| 442 `mount_setattr` | **YES**, cambio de atributos seleccionado por dirfd/path/flags, estructura de atributos, set/clear masks y recursive scope cuando aplique; target mount, namespace, permisos y resultado delimitan la relación. |

### Credenciales y capabilities — 11 YES

| NR / syscall | Decisión y alcance |
|---|---|
| 105 `setuid` | **YES**, cambios real/effective/saved UID bajo reglas de credenciales, capabilities y user namespace; conservar UID pedido/resultado. No se infiere éxito ni elevación. |
| 106 `setgid` | **YES**, cambios de GID bajo permisos/capabilities y reglas de user namespace; valores y estado resultante son condiciones. |
| 113 `setreuid` | **YES**, cambio de real/effective UID y reglas asociadas al saved ID; particionar argumentos y resultado. |
| 114 `setregid` | **YES**, cambio de real/effective GID y reglas asociadas al saved ID; particionar argumentos y resultado. |
| 116 `setgroups` | **YES**, reemplazo de supplementary group IDs sujeto a user namespace, privilegios/capability y validación de lista; no se infiere que `CAP_SETGID` esté disponible ni que la llamada tenga éxito. |
| 117 `setresuid` | **YES**, cambio de real/effective/saved UID; preservar los tres valores pedidos, sentinel semantics, reglas de autorización y resultado. |
| 119 `setresgid` | **YES**, cambio de real/effective/saved GID; preservar valores, sentinel semantics, permisos y resultado. |
| 122 `setfsuid` | **YES**, dimensión filesystem UID según UID solicitado y credenciales; preservar semántica de transición/consulta y valor retornado, sin inferir éxito sólo por el retorno. |
| 123 `setfsgid` | **YES**, dimensión filesystem GID según GID solicitado y credenciales; preservar transición/consulta y retorno, sin asumir éxito. |
| 125 `capget` | **YES**, consulta de conjuntos de capabilities seleccionada por header/version y PID; no se infiere ningún valor concreto ni que una capability sea utilizable. |
| 126 `capset` | **YES**, solicitud de actualización de effective/permitted/inheritable sets según header/version/PID, condicionada a reglas del kernel y namespace; no se infiere éxito ni disponibilidad efectiva. |

### `prctl`, seccomp y controles privilegiados — 7 YES

| NR / syscall | Decisión y alcance |
|---|---|
| 157 `prctl` | **YES condicional**, sólo subcomandos que directamente alteran/consultan estado de seguridad o privilegio (por ejemplo `PR_SET_NO_NEW_PRIVS`, `PR_SET_SECCOMP`, `PR_CAPBSET_DROP` cuando soportados). No toda invocación `prctl` pertenece a S16; comandos de process-tree conservan S11. |
| 317 `seccomp` | **YES condicional**, sólo comandos de instalación/configuración de modo strict/filter y sus flags/input/precondiciones/scope de thread. Una llamada exitosa no demuestra por sí sola que una política específica esté activa o tenga el enforcement esperado. No se modificó ni creó perfil alguno. |
| 175 `init_module` | **YES**, solicitud privilegiada de carga de imagen de módulo y parámetros; objeto, requisitos de privilegio y resultado delimitan la operación. No implica que el caller tenga la capability ni que el módulo se cargue. |
| 313 `finit_module` | **YES**, solicitud privilegiada de carga desde FD, parámetros y flags/validación del archivo; lifecycle del FD S03 y resultado permanecen separados. |
| 176 `delete_module` | **YES**, solicitud privilegiada de unload por nombre/flags, condicionada por uso/referencias, autorización y resultado; no se infiere unload exitoso. |
| 246 `kexec_load` | **YES**, carga/staging privilegiado de kernel image según entry, segmentos, flags y arquitectura; cargar no prueba una transición posterior de ejecución/reboot. |
| 320 `kexec_file_load` | **YES**, staging privilegiado de kernel image desde kernel/initrd FDs, command line y flags; conservar verificación, permisos y resultado. No implica ejecutar la imagen cargada. |

**Resumen de candidaturas principales:** 33; **33 YES / 0 NO / 0 UNKNOWN**.
Los scopes condicionales, en especial los de `clone`/`clone3`, `prctl` y
`seccomp`, son límites de relación y no hechos de ejecución.

## 4. Materialización y preservación de relaciones

Se materializaron exactamente las 33 relaciones S16 YES en las filas
target-bound con scope, rationale, referencia a este checkpoint y
`disposition_unchanged: UNKNOWN`. Para `clone` y `clone3` sólo se añadió la
dimensión namespace; sus relaciones S11 preexistentes de creación de proceso
se preservaron literalmente. No se modificaron relaciones S01–S15, ni
disposiciones generales ni el listado declarativo de syscalls S16.

## 5. Leads que permanecen sin promover

El manifiesto conserva **51 potential-surface leads S16** en
`no_candidate_review`; no se promovieron ni adjudicaron en este lote:

`uname` 63, `getrlimit` 97, `sysinfo` 99, `getuid` 102, `syslog` 103,
`getgid` 104, `geteuid` 107, `getegid` 108, `getgroups` 115, `getresuid`
118, `getresgid` 120, `uselib` 134, `personality` 135, `sysfs` 139,
`setpriority` 141, `vhangup` 153, `modify_ldt` 154, `arch_prctl` 158,
`adjtimex` 159, `setrlimit` 160, `acct` 163, `settimeofday` 164, `swapon`
167, `swapoff` 168, `reboot` 169, `sethostname` 170, `setdomainname` 171,
`iopl` 172, `ioperm` 173, `create_module` 174, `get_kernel_syms` 177,
`query_module` 178, `set_thread_area` 205, `get_thread_area` 211,
`lookup_dcookie` 212, `add_key` 248, `request_key` 249, `keyctl` 250,
`ioprio_set` 251, `ioprio_get` 252, `clock_adjtime` 305,
`landlock_create_ruleset` 444, `landlock_add_rule` 445,
`landlock_restrict_self` 446, `statmount` 457, `listmount` 458,
`lsm_get_self_attr` 459, `lsm_set_self_attr` 460, `lsm_list_modules` 461,
`open_tree_attr` 467 y `listns` 470.

Estos leads, la falta de trazabilidad de callsites/implementaciones y las
rutas/gaps aún abiertos permanecen visibles. Este checkpoint no intenta
resolverlos ni habilita congelar el inventario o marcar A-PRE-0 READY.

## 6. Cruces con S01–S15

- **S01:** resolución de paths/objetos para mount, chroot, pivot y APIs
  relacionadas; no queda subsumida por S16.
- **S02:** payload I/O no se adjudica por cambiar namespace/topología.
- **S03:** FD lifecycle de mount/fs contexts y otros descriptores; separado
  de la semántica S16 del objeto/topología.
- **S04:** filesystem mutations/contenido, separadas de attach/detach y
  topology S16.
- **S05/S06:** mappings, memoria file-backed, anónima o memfd; no inferidos
  por namespace/mount controls ni por seccomp.
- **S07/S08:** red IP y AF_UNIX permanecen separadas de la creación/entrada
  a namespaces.
- **S09:** capability passing permanece independiente de la configuración
  de capabilities/credenciales S16.
- **S10:** IPC/señales no se absorben por los cambios de namespace.
- **S11:** `clone`/`clone3` retienen la relación de creación de procesos
  previamente adjudicada; S16 sólo añade flags namespace. Workers y process
  lifecycle permanecen aparte.
- **S12/S13/S14:** io_uring, Linux native AIO y POSIX AIO no se modifican;
  sus interfaces no convierten sus efectos en S16.
- **S15:** APIs opacas no se modifican. S16 seccomp/prctl controls no
  transforman una propuesta de política S15 en enforcement demostrado.

## 7. Membership, cobertura y enforcement

Las decisiones se basan en la semántica de las candidaturas S16 y variantes
descritas, no en propuestas de seccomp, default-deny, capacidades asumidas o
políticas futuras. No se afirma que los intentos tengan éxito, que un
namespace/credential/kernel state haya cambiado, ni que un filtro esté
instalado o aplique efectivamente. No se registró nueva evidencia OBSERVED o
BLOCKED en este lote; no hubo actividad dinámica.

## 8. Estado global posterior

- S16 candidaturas identificadas: 33; YES 33, NO 0, UNKNOWN 0.
- Leads S16 existentes sin promover: 51.
- Disposiciones globales: 385/385 `UNKNOWN`; 0 finales.
- `inventory.frozen=false`.
- A-PRE-0: `NOT READY`; la adjudicación de superficies no satisface por sí
  sola su readiness predicate.
- A-PRE-1: `NOT AUTHORIZED / NOT EXECUTED`.
- S10 = 31 YES / 6 NO; S11 = 17 YES; S12 = 3 YES; S13 = 6 YES;
  S14 = 9 YES; S15 = 3 YES / 1 UNKNOWN.
- S01–S15 preservadas; ledger y `requirements.lock` byte-identical.
- No se ejecutaron TALOS, workloads, probes ni actividad dinámica.
- No se modificaron seccomp, código funcional, E5/Qwen, corpus, modelos ni
  bases protegidas.
- Se trataron documentalmente las 16 superficies canónicas; no se avanzó a
  otra superficie ni se cerraron por inferencia los leads/gaps restantes.
