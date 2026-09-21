# Study Engine

Motor de estudio y tutoría inteligente basado en evidencia y arquitectura multicapa.

## Estructura del Proyecto

```text
study-engine/
│
├── README.md
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── .env.example
│
├── docs/
│   ├── 01-SPEC-V1.0.md
│   ├── 02-ADVERSARIAL-AUDIT.md
│   ├── 03-EXECUTION-PLAN-V1.0.md
│   └── 04-DEVELOPMENT-SAFETY-POLICY.md
│
├── src/
│   └── study_engine/
│       ├── __init__.py
│       │
│       ├── ingestion/
│       ├── retrieval/
│       ├── evidence/
│       ├── context/
│       ├── llm/
│       ├── tutor/
│       ├── tester/
│       └── quality/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── security/
│   └── protected/
│
├── scripts/
│   ├── test.sh
│   ├── quality_gate.py
│   └── context_pack.py
│
├── configs/
│   └── .gitkeep
│
├── data/
│   ├── fixtures/
│   └── benchmark/
│
├── state/
│   └── .gitkeep
│
├── logs/
│   └── .gitkeep
│
└── docker/
    └── .gitkeep
```

## Documentación

Consultar el directorio [`docs/`](docs/) para especificaciones completas:
- [`docs/01-SPEC-V1.0.md`](docs/01-SPEC-V1.0.md): Especificación técnica V1.0.
- [`docs/02-ADVERSARIAL-AUDIT.md`](docs/02-ADVERSARIAL-AUDIT.md): Auditoría adversarial.
- [`docs/03-EXECUTION-PLAN-V1.0.md`](docs/03-EXECUTION-PLAN-V1.0.md): Plan de ejecución incremental y certificación.
- [`docs/04-DEVELOPMENT-SAFETY-POLICY.md`](docs/04-DEVELOPMENT-SAFETY-POLICY.md): Política de seguridad y desarrollo.
