# Perímetro de pruebas y evidencia de certificación

**Contrato:** `config/test_perimeter.json`
**Validador y ejecutor:** `scripts/quality_gate.py`
**Estado:** perímetro A-1 formalizado; la clasificación `tests/audit` se añadió
para las pruebas B1-R. La hermeticidad total del perímetro sigue pendiente de
validación módulo por módulo.

Este documento explica el contrato. La fuente normativa de la clasificación
es `config/test_perimeter.json`, validada y ejecutada por
`scripts/quality_gate.py`; el comando oficial de perfil release es
`scripts/test.sh`. Los conteos o declaraciones de gate en informes anteriores
son evidencia histórica, no una segunda configuración vigente.

## Qué significa cada clase

| Clase | Perfil | Efecto |
|---|---|---|
| `required` | `--profile required` y `--profile release` | Debe ejecutarse y pasar para que el test gate correspondiente pase. Son pruebas deterministas/locales; “local” no exime de proteger datos versionados ni demuestra por sí solo ausencia de efectos laterales. |
| `qualification-required` | `--profile release` | Debe ejecutarse y pasar para la cualificación de release. Se mantiene fuera del perfil requerido rápido porque depende de recursos, capacidad o variabilidad temporal; sus resultados necesitan contexto de hardware/runtime. |
| `optional` | No se ejecuta en los perfiles del gate | La omisión aparece con ruta y motivo. Es evidencia externa separada, no un skip convertido en PASS ni una suite cubierta por el resultado del gate. |
| `support-only` | No se ejecuta como suite | Se registra con motivo, pero contiene fixtures/helpers y no casos pytest. No suma cobertura ni permite marcar una suite de pruebas como aprobada. |

El perfil `required` es una comprobación determinista parcial, no certifica un
release. El perfil `release` ejecuta tanto `required` como
`qualification-required`, pero tampoco constituye por sí solo una declaración
de certificación: la certificación necesita además un perímetro conocido,
dependencias y condiciones documentadas, reproducibilidad, revisión del reporte
y comprobación de invariantes/artefactos protegidos.

## Perímetro vigente

El manifiesto contiene 25 suites de primer nivel. En el commit que introdujo el
perímetro (`99bd754`), había 447 archivos `test_*.py`: 446 módulos ejecutables
y el helper `tests/utils/test_registry.py`, marcado `support-only`. Esto
explica el origen de la cifra 446 del documento anterior. Después se añadieron
cuatro módulos ejecutables en `HEAD=b12e340`:

- `tests/unit/diagnostics/test_backend_selection_adjudication_packets.py`
- `tests/unit/diagnostics/test_backend_selection_contract.py`
- `tests/unit/diagnostics/test_vector_space_contract.py`
- `tests/unit/diagnostics/test_vector_space_promotion.py`

Por eso `b12e340` tiene 451 archivos `test_*.py` versionados, de los cuales
450 son módulos ejecutables y uno es `support-only`; no son cinco módulos
faltantes ni un cambio de alcance del perfil. El árbol de trabajo actual
agrega los dos módulos B1-R no comprometidos y tres fixtures A-PRE (reporter,
observer y harness); con `tests/audit` registrado en el manifiesto, la
validación estructural cubre 456 archivos en 25 suites. En ese árbol actual, la
clasificación por archivo es 440 `required`, 13 `qualification-required`, 2 módulos `optional`
(overrides dentro de suites `required`) y 1 `support-only`; el perfil `release`
selecciona 453 archivos.
A-PRE-0 exige recalcular el conteo en el snapshot limpio que eventualmente se
certifique. Uno de los archivos,
`tests/utils/test_registry.py`, es un helper de fixtures con `__test__ = False`,
no un módulo que recolecte casos; queda clasificado `support-only`. Los otros
archivos heredan la clasificación de su suite; las excepciones externas son
módulos completos identificados por ruta. Los conteos de casos se descubren en
cada ejecución y no se fijan como baseline en el manifiesto.

### Requeridas

`tests/adversarial`, `tests/audit`, `tests/benchmark`, `tests/ci`, `tests/cli`,
`tests/context`, `tests/contract`, `tests/experiments`, `tests/hierarchy`,
`tests/integration` (excepto los dos overrides opcionales), `tests/llm`,
`tests/llm_pool`, `tests/memory`, `tests/pedagogy`, `tests/protected`,
`tests/retrieval`, `tests/security`, `tests/session`, `tests/storage`,
`tests/system`, `tests/unit` y `tests/web`.

### Soporte, no suite ejecutable

`tests/utils` contiene `test_registry.py`, un helper de fixture declarado con
`__test__ = False`. Se informa como `SUPPORT ONLY`, se excluye de la colección y
no cuenta como suite aprobada.

La inclusión de `benchmark` y `experiments` se limita a sus pruebas herméticas
y deterministas. No ejecuta ni aprueba evaluaciones de retrieval en vivo,
Golden Sets, benchmarks Gate 2, ni canoniza qrels, ACL o decisiones
experimentales.

### Cualificación requerida

| Suite | Condición |
|---|---|
| `tests/performance` | Ejecutar con condiciones y hardware registrados; interpretar sus umbrales junto con ese contexto. |
| `tests/survival` | Ejecutar con recursos/tiempos controlados; registrar entorno y cualquier variabilidad relevante. |

### Opcionales y fuera del gate

| Módulo | Por qué no se ejecuta en el gate |
|---|---|
| `tests/integration/test_llm_latency.py` | Acceso de red/proveedor externo. Requiere un procedimiento separado que registre proveedor, credenciales disponibles sin revelarlas, red y configuración. |
| `tests/integration/test_study_loop_real_llm.py` | Requiere explícitamente `KASIU_LIVE_TESTS=1` y `GEMINI_API_KEY`; es una evaluación de modelo en vivo, no una regresión determinista. |

Un resultado del gate debe mostrar estas exclusiones como `NOT RUN` junto con
su motivo. Para ejecutar una evaluación opcional, usar el procedimiento
específico de esa evaluación y reportar sus resultados aparte; no quitar el
override sin cambiar y revisar el contrato.

## Detección de cambios en el árbol

Antes de ejecutar pruebas, el validador compara las suites registradas con los
directorios que contienen `test_*.py`:

- una suite/directorio nuevo sin entrada en el manifiesto detiene el gate;
- una entrada obsoleta sin módulos de test también lo detiene;
- un override debe apuntar a un módulo de test existente y tener motivo;
- toda suite necesita una clasificación permitida y una justificación no vacía.

Un módulo nuevo bajo una suite registrada hereda su clase y queda incluido por
el path de la suite. Si necesita condiciones distintas, debe añadirse como
override explícito y documentado. Los helpers con prefijo `test_` que no deban
recolectarse necesitan clasificación `support-only` y un motivo. Revisar la
clasificación antes de añadir dependencias externas o efectos secundarios
nuevos.

La categoría efectiva de cada módulo es exactamente una: hereda la clasificación
de la suite o, si está registrado una sola vez como excepción, queda
`optional`. Un override solo puede sustituir una suite `required`; por tanto,
no puede convertir silenciosamente una prueba de cualificación ni un helper
support-only en otra categoría. Claves JSON duplicadas, suites duplicadas,
overrides duplicados, módulos desconocidos y suites vacías son errores
bloqueantes.

El manifiesto es la fuente única del perímetro para `scripts/quality_gate.py`.
`scripts/test.sh` invoca ese gate con el perfil `release`; no mantiene una
segunda lista paralela de suites.

## Interpretación de PASS

`PASS` significa exclusivamente que el perfil solicitado se ejecutó con el
perímetro manifestado, pytest terminó sin fallos y todas las suites requeridas
por ese perfil recolectaron y completaron casos. El reporte incluye casos
recolectados, aprobados, omitidos y fallidos por suite, además de las
exclusiones opcionales.

`PASS` no significa:

- que se ejecutaron las evaluaciones externas/live;
- que se certificó el comportamiento de proveedores/modelos no incluidos;
- que un benchmark experimental o sus qrels sean canónicos;
- que datos protegidos fueran modificados o validados solo por pytest;
- que el resultado sea reproducible sin conservar commit, dependencias,
  configuración, plataforma y condiciones de ejecución.

Un skip dentro de una suite requerida se informa como `skipped`; no se convierte
en ejecución satisfactoria de la funcionalidad omitida. Una suite requerida
vacía, un fallo de colección, suite desconocida o salida pytest distinta de cero
hace fallar el gate.

## Mantenimiento

Cuando aparezca una suite nueva: revisar contenido, determinismo, dependencias,
red/modelo y efectos laterales; asignar `required` o
`qualification-required` con justificación, o registrar una excepción de módulo
`optional` con motivo y procedimiento alternativo. Actualizar este documento si
cambia el significado o alcance de una clase. No sumar conteos históricos como
si fueran evidencia de la ejecución actual.
