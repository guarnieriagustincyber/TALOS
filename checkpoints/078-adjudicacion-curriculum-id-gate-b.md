# Checkpoint 078 — adjudicación de `curriculum_id` en Gate B

## 1. Alcance y decisión de release vigente

Se evalúa exclusivamente la semántica y autoridad de `curriculum_id` para
los cinco notebooks del release. El scope fijado por decisión humana se
preserva:

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
```

La cuestión no es qué valor convendría escribir, sino qué evidencia define
cada representación y qué significado tiene hoy `fadena_v1`. La inspección
fue estática/read-only. No se abrió ni modificó SQLite en esta tarea; para el
valor y las filas persistidas se utiliza la lectura SQLite `mode=ro`
documentada en CP077 y los inventarios read-only existentes en
`docs/PLAN_SUITE_FIX_ESTABILIZACION.md`.

Fuentes técnicas revisadas:

- `config/notebook_kc_catalog.json`.
- `src/study_engine/pedagogy/fase0_seed.py`.
- `src/study_engine/web/dependencies.py`.
- `src/study_engine/contracts/notebook.py`.
- `src/study_engine/storage/knowledge_store.py`.
- `src/study_engine/storage/sqlite_engine.py`.
- `src/study_engine/federation/notebook_registry.py`.
- `tests/web/test_notebook_upload_identity.py`.
- `tests/pedagogy/test_socratic_system_prompt.py`.
- `tests/pedagogy/test_pedagogical_contract_persistence.py`.
- `checkpoints/077-reconciliacion-identidad-gate-b.md`.
- `docs/PLAN_SUITE_FIX_ESTABILIZACION.md`, secciones G2.0, resultado de alta
  y reconciliación read-only, decisiones de identidad y revalidación.
- Documentación de Gate B en `docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md`.

No se usó historial Git: las fuentes actuales documentan la contradicción y
el tratamiento pendiente; el código permite establecer el efecto y el
comportamiento actual. El origen histórico exacto de las cinco escrituras no
está disponible en estas fuentes, y no se atribuye a un commit/proceso no
verificado.

## 2. Hallazgo ejecutivo

Las fuentes sí permiten determinar lo siguiente:

1. `fadena_v1` es el valor genérico repetido en las filas persistidas locales
   de estos cinco notebooks. La documentación técnica anterior lo denomina
   valor genérico del estado SQLite local y registra la migración/mapeo como
   pendiente, no aprobado.
2. No hay evidencia de que sea un identificador genérico deliberado
   compatible con los cinco currículos: `get_system_prompt_for_notebook`
   requiere igualdad exacta con el ID del perfil; el test existente confirma
   que `fadena_v1` no coincide y produce el prompt neutral para
   `fadena-std`.
3. El esquema no define `fadena_v1` como default. La migración v1→v2 sólo
   agrega una columna nullable y no hace backfill. El código de alta toma los
   IDs específicos del catálogo al crear notebooks; si la fila ya existe, el
   seeder no actualiza su `curriculum_id`.
4. Por lo tanto, el sistema actual puede explicar por qué el valor local
   persiste (alta idempotente que no actualiza filas previas), pero no quién
   escribió originalmente `fadena_v1` ni qué intención tuvo esa escritura.
5. La documentación de Gate 2 ya establece que el catálogo versionado es la
   fuente del mapeo de IDs curriculares de aplicación de los cinco scopes y
   que la columna SQLite representa estado de instalación, no autoridad. Eso
   sostiene la autoridad del catálogo para el mapeo de aplicación, no
   autoridad académica externa del programa ni una autorización para migrar
   datos.

Dictamen:

```text
PERSISTED_VALUE_ROLE = LEGACY / RESIDUAL INSTALLATION STATE
PERSISTED_VALUE_ORIGIN = UNKNOWN
PERSISTED_VALUE_COMPATIBLE_WITH_EXACT_PROFILE_IDENTITY = NO
CURRICULUM_ID_STATUS = CONTRADICTORY
```

“Legacy/residual” describe su condición en la instalación persistida frente
al mapeo de aplicación documentado; no identifica el autor, la fecha ni el
motivo histórico de la escritura. No se interpreta como default deliberado,
alias curricular ni evidencia de una migración completada.

## 3. Matriz de autoridad por representación

| Representación | Fuente y semántica observada | Quién la consume | Autoridad demostrada | Resultado |
|---|---|---|---|---|
| `config/notebook_kc_catalog.json` — `curriculum_id` | Mapeo versionado exacto entre notebook ID y currículo que también organiza KCs. `docs/PLAN_SUITE_FIX_ESTABILIZACION.md`, G2.1, declara que el catálogo KC versionado es la fuente de los IDs curriculares de aplicación para sus entradas; las decisiones de identidad y tests lo usan para los cinco perfiles. El documento advierte que esto no certifica por sí solo autoridad académica oficial del programa. | `_load_notebook_curriculum_ids()` lee el campo; `_seed_curriculum_tree()` lo usa al construir un Notebook nuevo. Tests cotejan sus valores con perfiles y provisioning. | Sí para **mapeo de identidad de aplicación** según la decisión documentada de Gate 2. No para certificación académica externa ni precedencia normativa fuera de ese scope. | `AUTHORITATIVE` dentro del mapeo de aplicación declarado; autoridad académica no establecida por este campo. |
| `NOTEBOOK_PROFILES` — `curriculum_id` | Valor esperado por cada perfil curricular exacto; el campo se imprime en el prompt cuando la identidad valida. Tests verifican igualdad campo a campo con el catálogo. | `get_system_prompt_for_notebook(notebook_id, curriculum_id=...)` selecciona perfil sólo con ID exacto y `curriculum_id` idéntico; cualquier mismatch retorna `TALOS_BASE_SYSTEM_PROMPT`. `KnowledgeStore.get_pedagogical_contract()` pasa el valor persistido a la resolución del contrato default. | Especificación ejecutable y duplicación comprobada del mapeo de catálogo; no es una designación independiente ni una fuente de autoridad curricular académica. | `SUPPORTED` como representación runtime derivada/alineada al catálogo; requiere igualdad exacta. |
| Persistencia — `notebooks.curriculum_id` | Columna nullable en estado SQLite de instalación. CP077 observó `fadena_v1` en las cinco filas. La documentación G2.1 dice que SQLite local representa estado de instalación y no prevalece sobre el mapeo de catálogo; registra el tratamiento de migración como pendiente, no autorizado. | Se lee al construir el contrato pedagógico default desde `KnowledgeStore`; el resolver lo usa para validar el perfil. También forma parte de la API/modelo Notebook y CRUD. | Ninguna para autoridad del mapeo curricular. Tiene autoridad fáctica sobre lo que esa instalación persiste, no sobre la identidad de aplicación declarada. | El valor observado es `CONTRADICTORY` frente al mapeo/perfil esperado. Como dato histórico, tiene rol de estado local legacy/residual; origen exacto `UNKNOWN`. |
| Valor exacto persistido `fadena_v1` | Mismo literal observado para las cinco filas, sin equivalencia o significado genérico documentado para esos cinco currículos. La documentación lo identifica como discrepante/genérico de la instalación local y deja pendiente el mapeo/migración. | Llega al resolver a través de `KnowledgeStore.get_pedagogical_contract()`; por mismatch no activa el perfil específico. | No se demostró autoridad semántica. El uso histórico/intención del escritor original tampoco se conoce. | Rol histórico probable de valor residual/legacy documentado como discrepante; clasificación de relación vigente `CONTRADICTORY`; procedencia original `UNKNOWN`. |
| Registry estático `DEFAULT_NOTEBOOKS` | Declara IDs, nombres, subjects, fuentes y matriz de autoridad temática. Su modelo `federation.notebook_registry.Notebook` no declara `curriculum_id`. | `NotebookRegistry` provee los notebooks usados por el seeder; este cruza su ID exacto con el catálogo para obtener el `curriculum_id`. | No representa ni decide `curriculum_id`. Aporta identidad exacta del notebook y metadatos declarados, pero no puede resolver la discrepancia curricular. | `UNKNOWN`/no representado para el campo `curriculum_id`; no es evidencia en favor de `fadena_v1`. |
| Migración de esquema SQLite | `_migrate_to_v2()` añade `curriculum_id TEXT` si falta. No asigna valor ni actualiza filas. | `SQLiteStorageEngine.initialize_schema()` aplica migraciones aditivas por versión. | Autoridad sólo sobre evolución estructural; no designa ID curricular. | `SUPPORTED` para concluir que esta migración no originó ni explica el valor `fadena_v1`. |

### Alcance exacto de “autoridad”

La autoridad atribuida al catálogo es la que `docs/PLAN_SUITE_FIX_ESTABILIZACION.md`
llama explícitamente fuente de los IDs curriculares de aplicación para las
entradas canónicas. No significa que un ID en JSON pruebe que la institución
académica haya aprobado el programa detallado. Para `fadena-std`, la autoridad
académica sigue pendiente del criterio 5 de Gate B.

## 4. Semántica del valor persistido y mecanismos de escritura

### 4.1 Esquema y migraciones

`src/study_engine/storage/sqlite_engine.py` define
`notebooks.curriculum_id TEXT` sin `DEFAULT`. La migración v1→v2 sólo ejecuta
`ALTER TABLE notebooks ADD COLUMN curriculum_id TEXT` si la columna no existe.
No contiene asignación a `fadena_v1`, backfill desde nombres ni mapeo por
notebook.

Resultado:

```text
SCHEMA_DEFAULT_FOR_CURRICULUM_ID = NONE
V1_TO_V2_BACKFILL = NONE
MIGRATION_EVIDENCE_EXPLAINS_FADENA_V1 = NO
```

### 4.2 Provisioning/seed de notebooks

`src/study_engine/web/dependencies.py::_load_notebook_curriculum_ids()` toma
los valores por notebook ID exacto del catálogo. En
`AppContainer._seed_curriculum_tree()`:

- para notebook ID ausente, crea `contracts.notebook.Notebook` y pasa
  `curriculum_id=curriculum_ids.get(nb.notebook_id)`;
- para notebook ID ya existente, no actualiza `curriculum_id`; sólo prepara
  los vínculos de fuentes declarados que falten.

`KnowledgeStore.create_notebook()` inserta el valor recibido y, si ya existe
un notebook con ese ID y sus atributos difieren, reporta conflicto en lugar
de actualizarlo.

Resultado:

```text
NEW_ROW_CURRICULUM_ID_SOURCE = exact catalog entry (when present)
EXISTING_ROW_CURRICULUM_ID_UPDATED_BY_SEED = NO
CURRENT_SEEDER_CAN_EXPLAIN_PERSISTENCE_OF_OLD_VALUE = YES
CURRENT_SEEDER_CAN_EXPLAIN_ORIGINAL_WRITE_OF_FADENA_V1 = NO
```

El seeder actual explica por qué una fila histórica puede conservar un valor
anterior, pero no prueba cuándo, por quién ni con qué semántica se escribió
`fadena_v1`.

### 4.3 Pruebas y consumidor del perfil

`tests/web/test_notebook_upload_identity.py` verifica que `_load_notebook_curriculum_ids`
y el provisioning producen los cinco IDs específicos al crear filas nuevas.
`tests/pedagogy/test_socratic_system_prompt.py` verifica:

- que cada perfil tiene el mismo `curriculum_id` que la entrada exacta del
  catálogo;
- que `fadena-std` con `fadena_std_2026` recibe su perfil;
- que `fadena-std` con `fadena_v1` recibe el prompt neutral.

Estas pruebas establecen el contrato que implementa el código; no fueron
ejecutadas en esta tarea. La búsqueda estática del repositorio encontró
`fadena_v1` como valor de producción en la documentación del inventario/
decisión de identidad y como mismatch deliberado en tests; no encontró un
default `fadena_v1` en schema, seeder o migración.

Consecuencia funcional directa ya demostrada por el código y registrada por
el test: para las filas que persisten `fadena_v1`, el default resolver no
selecciona el perfil específico; usa el fallback neutral. No se afirma aquí
que las cinco rutas productivas actuales hayan sido ejecutadas ni se
extrapola a configuración de otros despliegues.

## 5. Evaluación de los cinco scopes

| Scope | ID del notebook | `curriculum_id` esperado por catálogo/perfil | Persistido según CP077 | Relación semántica | Autoridad del valor | Estado |
|---|---|---|---|---|---|---|
| Fase 0 — `fase0-soc` | `fase0-soc` | `roadmap_kasiu_v4_fase0` | `fadena_v1` | Valor genérico persistido no igual al mapeo exacto del Roadmap/Fase 0; no se documenta equivalencia. | Catálogo autorizado para mapeo de aplicación; autoridad de `fadena_v1` no demostrada. | `CONTRADICTORY` |
| FADENA Lenguajes 2026 — `fadena-lenguajes` | `fadena-lenguajes` | `fadena_lenguajes_2026` | `fadena_v1` | Valor genérico persistido no igual al ID curricular específico; no se documenta equivalencia. | Catálogo autorizado para mapeo de aplicación; autoridad de `fadena_v1` no demostrada. | `CONTRADICTORY` |
| FADENA Sistemas Operativos II 2026 — `fadena-so2` | `fadena-so2` | `fadena_so2_2026` | `fadena_v1` | Valor genérico persistido no igual al ID específico de SO II; no se documenta equivalencia. | Catálogo autorizado para mapeo de aplicación; autoridad de `fadena_v1` no demostrada. | `CONTRADICTORY` |
| FADENA Sistema de Tratamiento de Datos 2026 — `fadena-std` | `fadena-std` | `fadena_std_2026` | `fadena_v1` | Valor genérico persistido no igual al ID específico; el mismatch neutraliza la selección exacta del perfil. No establece ni niega autoridad académica. | Catálogo autorizado para mapeo de aplicación; autoridad de `fadena_v1` no demostrada. Autoridad académica del programa sigue pendiente. | `CONTRADICTORY` |
| FADENA Telecomunicaciones 2025 — `fadena-teleco` | `fadena-teleco` | `fadena_teleco_2025` | `fadena_v1` | Valor genérico persistido no igual al ID curricular específico; no se documenta equivalencia. | Catálogo autorizado para mapeo de aplicación; autoridad de `fadena_v1` no demostrada. | `CONTRADICTORY` |

El patrón observable (mismo valor en las cinco filas) es uniforme como dato
persistido, pero no basta para asignarle una semántica común intencional.
Para cada scope por separado, la única relación demostrada es el mismatch
literal con su ID esperado y la ausencia de una equivalencia documentada.

## 6. Evaluación de `subject`

El campo `subject`:

- es opcional/descriptivo en `contracts.notebook.Notebook` y en el esquema
  SQLite;
- se llena desde `DEFAULT_NOTEBOOKS.subject` al crear una fila, y también se
  copia a `description`;
- aparece como etiqueta `Materia:` en `NOTEBOOK_PROFILES`, que es texto
  independiente de la columna persistida;
- puede utilizarse como metadato/filtro de retrieval en `federation/curriculum_gate.py`;
- **no** participa en la condición de identidad curricular exacta de
  `get_system_prompt_for_notebook()`, que compara `notebook_id` y
  `curriculum_id`.

Por tanto, `subject` no es el identificador normativo del currículo en el
contrato de selección de perfil. Las diferencias anotadas en CP077
(abreviaturas/etiquetas entre perfil y registry, incluida Fase 0 y SO2) no se
convierten en otro bloqueo artificial de `curriculum_id`. Si una diferencia
de `subject` altera filtrado de retrieval en un camino concreto, corresponde
evaluarla como evidencia de alcance/retrieval en los criterios 2–4; esta
tarea no probó ese efecto ni adjudicó etiquetas.

## 7. Aliases preservados

Esta adjudicación no añade equivalencias:

- `fase0-soc` no es alias FADENA.
- `fadena-so2` no es `fadena-so`.
- `fadena-prog` no se convierte automáticamente en alias de Fase 0 ni de
  Lenguajes.
- `fadena-so` no se convierte automáticamente en alias de `fadena-so2`.

El `alias_target: null` de `config/notebook_identity_decisions.json` significa
que esa decisión audit-only no declara un target de alias. En combinación
con las decisiones textuales de no equivalencia para Fase 0/SO2 y de
preservación separada de los scopes legacy, no existe un alias positivo
autorizado que explique `fadena_v1`.

## 8. Resultado y evidencia que justifica el bloqueo

```text
CURRICULUM_ID_STATUS = CONTRADICTORY
CURRICULUM_ID_RECONCILED = NO
CRITERION_1 = BLOCKED
```

Justificación concreta:

1. El mapeo de aplicación versionado asigna cinco IDs específicos, respaldado
   por la declaración documental de Gate 2 y por el consumidor/provisioner.
2. Las cinco filas persistidas contienen `fadena_v1`; ningún documento o
   código examinado declara que ese valor sea alias o ID genérico válido para
   los cinco.
3. El resolver requiere igualdad exacta y trata el valor persistido como
   mismatch; un test existente confirma el fallback neutral con
   `fadena_v1`.
4. La columna no tiene default; la migración de esquema sólo la agrega.
5. El seeder actual no actualiza filas existentes, y la documentación
   clasifica el cambio/migración local como pendiente y no autorizado.
6. El origen histórico preciso del valor sigue sin establecerse; esa
   incertidumbre de provenance no borra la contradicción efectiva.

La discrepancia puede resolverse sólo mediante una decisión/acción futura
separada que establezca identidad y autorice cualquier cambio de datos. Este
checkpoint no prescribe cuál valor debe escribirse, no aprueba una migración
y no solicita que se edite la base. Si se requiere identificar autor/commit
original de las escrituras, deberá abrirse una búsqueda de provenance
histórica separada; no es necesaria para describir el conflicto presente.

## 9. Gates restantes

- **Criterio 1:** permanece bloqueado por `curriculum_id` persistido y las
  discrepancias de representación de identidad aún no adjudicadas. No se
  modifican alias ni registros.
- **Criterios 2–4:** continúan pendientes según CP077. Hace falta decidir
  source roles/asociaciones y producir evidencia integrada de retrieval,
  selección de perfil y no contaminación; esta tarea no los cierra.
- **Criterio 5 (`fadena-std`):** permanece pendiente por autoridad curricular
  del programa detallado. La identidad técnica `fadena_std_2026` no prueba
  autoridad académica.

No se cierra Gate B ni `PRODUCT_COMPLETE`.

## 10. Invariantes y no-acciones

- Se preserva `RELEASE_SCOPE = 5 currículos` y
  `FADENA_STD_RELEASE_SCOPE = INCLUDED`.
- No se modificaron DB, código, catálogo, perfil, registry, source roles,
  ACL, asociaciones, tests, fixtures ni gates.
- No se ejecutaron tests, TALOS/FastAPI, providers ni benchmarks.
- No se ejecutó una migración ni se reemplazó `fadena_v1`.
- Se preservan A-PRE, la autoridad externa pendiente y CP072.
- Se preservaron los cambios preexistentes del worktree.

## Estado final

```text
CURRICULUM_ID_STATUS = CONTRADICTORY
CRITERION_1 = BLOCKED
```
