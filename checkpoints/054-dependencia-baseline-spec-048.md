# Checkpoint 054 — dependencia de baseline spec en la reconciliación 048

Fecha: 2026-10-01
Repositorio: `guarnieriagustincyber/TALOS`
HEAD inicial: `f81134fc2293916210d53c8065f3a0049e52b0b4`

## 1. Resultado

**`CROSSWALK_048_BASELINE_DEPENDENCY = NO` para el crosswalk descriptivo de
385 filas basado exclusivamente en datos y decisiones ya serializados.**

La reconciliación 048 completa sí tiene dependencia **parcial** de la
autoridad normativa de baseline: verificar significado/adecuación normativa,
resolver disputas semánticas, cerrar cobertura/variantes y evaluar A-PRE-0 no
puede hacerse sin saber qué contrato normativo gobierna. Eso no impide el
inventario row-wise de campos existentes ni la trazabilidad literal de
adjudicaciones y provenance ya documentadas.

Esto es un análisis de dependencia, no una reanudación de 048. Se conservan
sin cambio:

```text
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
STOP_REASON = UNRESOLVED_PROVENANCE
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
```

Checkpoint 053 dejó 048 bloqueado. Este documento demuestra que ese bloqueo
es globalmente más amplio que la dependencia documental probada: la
reconciliación oficial permanece detenida hasta que una autorización posterior
delimite la fase que puede continuar. No se construyó el crosswalk de 385
filas.

## 2. Operaciones reales contempladas en 048

048 describe estas tareas en §§1, 3–7 y 9:

1. Parsear el manifest y comprobar filas, nombres y números únicos, estados
   globales, relaciones y estados de freeze.
2. Recalcular literalmente los campos agregados frente a las filas
   serializadas y explicar los deltas; no corregir campos canónicos.
3. Comparar la representación actual con 045–047 y con los checkpoints de
   origen S01–S16; distinguir relaciones materializadas, decisiones sólo
   documentadas, exclusiones, leads y casos UNKNOWN.
4. Construir un crosswalk row-wise 385×S01–S16 con superficie/contexto,
   `candidate_surface_ids`, adjudicación, estado de representación y fuente.
5. Clasificar el estado de cada relación existente sin transformar una
   relación YES/NO en disposición syscall global ni en evidencia runtime.
6. Reconciliar discrepancias manifest↔checkpoint y la procedencia de cada
   fila; detenerse y declarar unresolved donde los registros no decidan.
7. Informar invariantes A-PRE-0 y límites de cobertura de forma parcial. 048
   no evaluó los 17 checks del predicate ni afirmó un readiness pass.
8. Preservar `UNKNOWN`, `inventory.frozen=false` y A-PRE-1 no autorizado; no
   actualizar contadores ni normalizar el manifest.

048 explícitamente dice que no construyó ni validó el crosswalk semántico de
385 filas; sus cifras por superficie eran provisionales. La regla de parada
original era el delta de contadores no explicado. 049 lo reconstruyó como
`STALE_COUNTER`; 050 recomendó resolver tanto su representación como la
autoridad spec antes de reanudar. 051/052/053 mantuvieron STOP por provenance,
pero no citaron una regla que prohíba separar la correlación documental de la
interpretación normativa.

## 3. Matriz de dependencia

`YES` significa que el contrato/contenido consultado demuestra dependencia
material. `NO` significa que la actividad puede limitarse a observación de
los registros existentes sin aplicar reglas normativas no resueltas. `PARTIAL`
marca una tarea mixta, con subpasos descriptivos y de juicio normativo.
`UNKNOWN` se reserva para falta de evidencia para resolver dependencia.

| Operación de 048 | Evidencia necesaria | ¿Requiere BASELINE_SPEC? | Fuente que demuestra dependencia o independencia | Estado |
|---|---|---|---|---|
| Validar JSON, 385 filas, unicidad por nombre/número, `UNKNOWN` global y `frozen=false` | Parsing JSON, claves/valores del manifest y ledger | No | Manifest `syscall_disposition_contract` contiene las 385 filas, contadores declarados y estados; 048 §6 ya especifica estos invariantes como comprobaciones estructurales | `NO` |
| Recalcular contexto, IDs, refs y complementos; cotejar con resumen stale | Arrays row-wise y fórmulas cardinales explícitas | No para medir ni describir diferencias; sí para reparar/renombrar canónicamente contadores | 049 formula el recálculo desde los arrays y reconstruye el origen histórico. 048 §9 prohíbe modificar valores antes de una autorización separada | `PARTIAL` |
| Registrar por syscall los campos existentes: name/nr/context/IDs/status/disposition | `syscall_disposition_contract.rows` | No | Manifest define las filas; ledger apunta a `A_PRE_0_SURFACE_MANIFEST.json#syscall_disposition_contract.rows` | `NO` |
| Vincular una decisión explícita a su checkpoint de origen | Referencia serializada en la relación o contraste literal con checkpoints 014–047 | No para registrar lo que el documento dice; no permite validar autenticidad/intención más allá del registro | Filas de manifest contienen `human_adjudication_ref`; checkpoints 014–047 contienen decisiones y alcance. 049 §10 ya muestra por fila refs disponibles y limita filas sin cita específica | `NO` |
| Distinguir materializado en manifest de checkpoint-only | Contexto/IDs/adjudication arrays actuales más decisiones de 024/026/028/046 | No para informar diferencia de representación | 048 §§4–6 y 046 describen relaciones checkpoint-only y materialización pendiente. La comparación es contra el registro y su fuente, no una decisión de elegibilidad normativa | `NO` |
| Trazar candidatos, exclusiones explícitas, leads y UNKNOWN existentes | Arrays de contexto, IDs, `potential_surface_refs`, revisión sin candidato, adjudicaciones y checkpoints | No para documentar exactamente qué está registrado | Manifest conserva esos campos; ledger referencia no-candidate review y decisiones; 049 §10 documenta el esquema por fila | `NO` |
| Asignar una categoría descriptiva según el estado/decisión ya explícitos | Estado serializado y fuente primaria explícita; para conflictos, ambos registros | No cuando reproduce una decisión existente; ninguna nueva resolución ante conflicto | Manifest marca `HUMAN_ADJUDICATED_CANDIDATE`, `HUMAN_ADJUDICATED_NOT_MEMBER`, `UNREVIEWED_CANDIDATE` y `disposition_status=UNKNOWN`; checkpoints fuente dicen el alcance. 048 §6 prohíbe inferir | `PARTIAL` |
| Decidir si una pista o relación no adjudicada debe ser YES/NO/UNKNOWN por su efecto o amenaza | Semántica de superficie, argumentos, recursos, fase, rutas, Modelo B y reglas de cierre | Sí | `files/A_PRE_0_BASELINE_SPEC.md` §4.1/“Cruce estático 1:1”, §“Revisión estática…” declara que las pistas requieren decisión normativa; la autoridad de ese contrato está unresolved | `YES` |
| Resolver incompatibilidades semánticas entre checkpoint, manifest, ledger o copias normativas | Autoridad de la regla aplicable y provenance con prioridad | Sí; no hay criterio alternativo que seleccione el contrato | 052 y 053 identifican las specs locales dispares y `f058…` no recuperado; 048 exige detener ante contradicción que requiera inferencia | `YES` |
| Declarar crosswalk global completo/cerrado según requisitos de baseline | Criterio de completitud, dimensiones requeridas, unidad de cobertura y cierre UNKNOWN/variante | Sí | Spec `files/` §§4.1, “Cruce estático 1:1” e “Identidad de ABI…” fija contenido/cierre; ledger predicate exige inventario y cobertura completos y sin UNKNOWN. No hay autoridad única en 053 | `YES` |
| Cambiar disposiciones globales, cerrar variantes, congelar inventory o corregir canónicos | Decisión normativa/evidencia; autorización explícita de cambio | Sí, y fuera de alcance de 048/054 | Manifest contract mantiene `final_surface_or_exclusion_disposition_count=0`; ledger exige evidencia, límites y cambio controlado; 048 prohíbe modificar canónicos | `YES` |
| Evaluar de nuevo A-PRE-0 READY / elegibilidad del ledger | Predicate, hash de spec/snapshot, evidencia y checks completos | Sí para revisión del criterio normativo; el ledger actual ya reporta `false` | Ledger `qualification_identity.current_normative_spec` cita `f058…` ausente del overlay; `predicate.result=false` y causas actuales incluyen “qualified overlay does not contain current normative spec hash” | `YES` |
| Ejecutar A-PRE-1, TALOS o pruebas dinámicas | Autorización y evidencia técnica | No es operación de 048 y permanece prohibida | Ledger `a_pre_1_authorized=false`; 050–053 mantienen `NOT_AUTHORIZED / NOT_EXECUTED` | `NO` (fuera de alcance; no ejecutar) |

## 4. Dependencia del crosswalk 385

Para un crosswalk **descriptivo, de sólo lectura**, las fuentes existentes
bastan para registrar:

- `nr`, `name`, ABI/source line del registro;
- `candidate_surface_context`, `candidate_surface_ids` y estados de
  relación/disposición serializados;
- referencias a `surface_membership_adjudications` y al checkpoint citado;
- decisiones YES/NO/UNKNOWN tal como aparecen literalmente en checkpoints;
- distinción entre relación materializada, checkpoint-only, lead,
  `no_candidate_review` y ausencia de registro;
- discrepancia de representación cuando los registros no concuerdan;
- que la disposición syscall global continúa `UNKNOWN`.

Base documental: el manifest declara que sus registros realizan
`STATIC_CROSSWALK_RECORDED; EFFECT_DISPOSITIONS_PENDING` y que la pertenencia
candidata no establece efecto/alcanzabilidad/readiness. Cada fila contiene
los campos de revisión y refs; el ledger apunta directamente al array de
filas. Los checkpoints de lote aportan decisions y scopes, mientras 045–047
aportan revisiones de representación, decisiones pendientes y materialización.
049 §10 prueba que ese esquema y provenance por fila pueden ser descritos
sin convertirlos en disposición global.

Por eso:

```text
CROSSWALK_048_BASELINE_DEPENDENCY = NO
```

El `NO` está limitado a correlacionar los datos existentes y asignar una
etiqueta de reporte que refleje sin reinterpretación su estado serializado y
fuente. **No** afirma que la autoridad documental ya esté resuelta ni que la
spec pueda ignorarse para cierre normativo.

Si una fila requiere resolver el significado normativo de una superficie,
inferir una adjudicación, reconciliar fuentes incompatibles, declarar
completitud normativa o promover una relación, esa fila debe documentar la
discrepancia como pendiente/unresolved y detener esa resolución. No se permite
usar el `NO` anterior para inferir YES/NO, completar un lead, cambiar un
UNKNOWN o certificar el conjunto como final.

No se construye el crosswalk ahora; sólo se evalúa su dependencia.

## 5. Qué puede continuar y qué debe esperar

### `UNBLOCKED_BY_BASELINE_SPEC`

Estas actividades son documentalmente posibles sin elegir `docs/` o
`files/`, pero este checkpoint no las inicia:

1. Recalcular y reportar métricas estructurales desde manifest/JSON y exponer
   `STALE_COUNTER` sin reparar valores.
2. Enumerar las 385 filas y volcar sus campos actuales, comprobando nombres,
   números, `UNKNOWN` y freeze.
3. Unir cada relación ya explícita a la referencia/checkpoint fuente
   disponible y registrar la cita exacta, alcance y estado.
4. Marcar qué está materializado, qué sólo consta en checkpoint, qué es lead,
   exclusión contextual o UNKNOWN.
5. Etiquetar filas como representación inconsistente o provenance
   insuficiente cuando la evidencia disponible no permita una correlación
   inequívoca; no resolver el conflicto por inferencia.
6. Informar invariantes de estado ya establecidos por ledger/manifest, sin
   ejecutar el predicate ni modificar el estado.

“Unblocked” aquí describe suficiencia documental del análisis, no autorización
para reanudar 048 en este turno; el estado oficial fijado en 053 no se cambia.

### `BLOCKED_BY_BASELINE_SPEC`

Estas decisiones dependen materialmente de la autoridad normativa y siguen
bloqueadas:

1. Resolver qué significado normativo prevalece si spec, manifest y
   adjudicaciones históricas discrepan.
2. Determinar/crear una adjudicación donde no existe decisión documental
   explícita, incluyendo la interpretación de semántica, argumentos,
   recursos, fase o modelo de amenaza.
3. Decidir si una relación/lead/exclusión satisface la definición normativa
   de superficie o cierre; las pistas por nombre no bastan.
4. Cerrar variantes, unidades requeridas, rutas alternativas, trazabilidad
   nativa o criterios de freeze.
5. Declarar reconciliación normativa global terminada, modificar dispositions
   o contadores canónicos, congelar inventory o cambiar UNKNOWN.
6. Recalcular readiness A-PRE-0 o elegibilidad de evidencia histórica frente
   al overlay: el ledger vincula ese juicio al hash externo `f058…`, que
   permanece no recuperado.

## 6. ¿Bloqueo global o parcial?

La documentación no demuestra que **cada actividad** de 048 requiera una
autoridad única para `BASELINE_SPEC`. El manifest y ledger permiten
reproducir conteos/estados y el registro por fila; checkpoints permiten
atribuir decisiones explícitas y detectar diferencias de representación.
Ninguno de esos pasos, si se limita a transcribir y cotejar, declara qué
especificación histórica es canónica.

La dependencia demostrada es **parcial**: el juicio normativo, la resolución
de conflictos semánticos, el cierre de requisitos y readiness requieren
resolver la autoridad. El crosswalk descriptivo no. La instrucción de 050 y
el gate C de 053 impusieron un bloqueo procesal a toda reanudación de 048;
no documentaron un contrato que exija baseline para cálculos estructurales y
cotejo literal. Por ello, esa regla de parada no debe confundirse con una
dependencia técnica de cada suboperación.

No se modifica la marca oficial de 048, el STOP de 053 ni se concede
autorización para proceder. La decisión que queda para un checkpoint
posterior es si se autoriza una reanudación **acotada al crosswalk
descriptivo**, conservando las tareas normativas como bloqueadas.

## 7. Estado A-PRE e invariantes

| Estado | Valor al inicio y al cierre |
|---|---|
| `BASELINE_SPEC_AUTHORITY` | `AUTHORITY_UNRESOLVED` |
| `STOP_REASON` | `UNRESOLVED_PROVENANCE` |
| `EXTERNAL_SPEC_ARTIFACT` | `UNRECOVERED` |
| A-PRE-0 | `NOT_READY`; `predicate_result=false` |
| A-PRE-1 | `NOT_AUTHORIZED / NOT_EXECUTED` |
| Inventory | `frozen=false` |
| Disposiciones globales | 385/385 `UNKNOWN` |
| 048 oficial | Continúa detenido; no se realizó reconciliación |

## 8. Verificación de integridad

| Artefacto | SHA-256 inicial = final |
|---|---|
| `files/A_PRE_0_SURFACE_MANIFEST.json` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Baseline `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Baseline `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |

Manifest y ledger JSON válidos; 385 filas, 385 nombres únicos y 385 números
únicos; todas las disposiciones siguen UNKNOWN. `git diff --check` pasó. No se
modificó ningún artefacto canónico y no hubo actividad dinámica ni acceso a
VM/DB/corpus/modelos.
