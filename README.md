# Study Engine

Motor de estudio y tutoría inteligente basado en evidencia y arquitectura multicapa.

## Estructura del Proyecto

```text
study-engine/
├── README.md
├── pyproject.toml
├── requirements.txt
├── requirements.lock
├── config/
├── data/
├── docs/
├── scripts/
├── src/study_engine/  # paquetes Python
├── tests/             # suites clasificadas en config/test_perimeter.json
└── ...
```

El árbol omite los directorios de build y caché, y no enumera todos los
archivos. Los paquetes reales de primer nivel de
`src/study_engine/` son: `adapters`, `assessment`, `audit`, `context`,
`contracts`, `curriculum`, `diagnostics`, `evidence`, `execution`,
`federation`, `generation`, `hierarchy`, `ingestion`, `llm`, `memory`,
`metrics`, `pedagogy`, `quality`, `retrieval`, `roadmap`, `security`,
`session`, `state`, `storage`, `student`, `tester`, `tutor`, `utils` y `web`.

Las suites de primer nivel bajo `tests/` son: `adversarial`, `benchmark`,
`ci`, `cli`, `context`, `contract`, `experiments`, `hierarchy`,
`integration`, `llm`, `llm_pool`, `memory`, `pedagogy`, `performance`,
`protected`, `retrieval`, `security`, `session`, `storage`, `survival`,
`system`, `unit`, `utils` y `web`; `fixtures` contiene datos compartidos.
El manifiesto
[`config/test_perimeter.json`](config/test_perimeter.json) clasifica las suites:
`performance` y `survival` son de cualificación requerida, `utils` es
support-only, y los dos módulos live/network de `integration` son opcionales.
El resto de las suites listadas es requerido. El
[contrato del perímetro](docs/TEST_CERTIFICATION_PERIMETER.md) define el
alcance exacto.

## Instalación y dependencias

`pyproject.toml` es la fuente declarativa única de dependencias runtime y extras.
`requirements.lock` es el lock generado para desarrollo, pruebas y todos los
extras; se regenera con la versión de `uv` y el comando registrados en
[`docs/DEPENDENCY_REPRODUCIBILITY.md`](docs/DEPENDENCY_REPRODUCIBILITY.md).
`requirements.txt` es una lista parcial obsoleta, no una vía de instalación
soportada.

Para instalar el entorno de desarrollo desde el proyecto:

```bash
python -m pip install -e \
  ".[dev,gate2-diagnostics,experiments,local-inference]"
```

Para reconstruir el entorno bloqueado, consulta el procedimiento reproducible;
no instales encima del `.venv` existente durante esa verificación.

## Documentación

Nomenclatura de fases (evitar confundir Golden Set con red team): [`PHASES.md`](PHASES.md).

Mapa integral de navegación V1 → V1.5 → corpus/Colab → V2 y destinos de
herramientas: [`docs/TALOS_ROADMAP_V1_V1_5_V2.md`](docs/TALOS_ROADMAP_V1_V1_5_V2.md).
Es un índice de dependencias, no reemplaza la autoridad operativa V1 ni la
metodológica V1.5.

Mapa operativo único de estado y camino restante (actualizado al 2026-10-07):
[`docs/PLAN_MAESTRO_CIERRE_TALOS.md`](docs/PLAN_MAESTRO_CIERRE_TALOS.md).
El mapa declara `V1 = BASELINE / CONTROL CERRADO`, `V1.5 = ACTIVE ROADMAP`,
`P0 = COMPLETE`, `P1 = READY / NOT_STARTED`, `P2/P3 = DEFERRED` e ingesta
Colab congelada hasta P3. `ACTIVE ROADMAP` no significa que P1 haya comenzado
ni autoriza por sí solo cambios de runtime.

[`docs/ROADMAP_V1_5_MASTER.md`](docs/ROADMAP_V1_5_MASTER.md) conserva la
metodología y evidencia histórica de las líneas experimentales V1.5; no
reemplaza la secuencia operativa P0–P3 del mapa maestro. `PHASES.md` es un
glosario y no define un orden operativo alternativo.

Consultar el directorio [`docs/`](docs/) para especificaciones completas:
- [`docs/01-SPEC-V1.0.md`](docs/01-SPEC-V1.0.md): Especificación técnica V1.0.
- [`docs/02-ADVERSARIAL-AUDIT.md`](docs/02-ADVERSARIAL-AUDIT.md): Auditoría adversarial.
- [`docs/03-EXECUTION-PLAN-V1.0.md`](docs/03-EXECUTION-PLAN-V1.0.md): Plan de ejecución incremental y certificación.
- [`docs/04-DEVELOPMENT-SAFETY-POLICY.md`](docs/04-DEVELOPMENT-SAFETY-POLICY.md): Política de seguridad y desarrollo.
- [`docs/TEST_CERTIFICATION_PERIMETER.md`](docs/TEST_CERTIFICATION_PERIMETER.md): perímetro y significado de los perfiles de prueba.
- [`docs/DEPENDENCY_REPRODUCIBILITY.md`](docs/DEPENDENCY_REPRODUCIBILITY.md): lock e instalación reproducible.
