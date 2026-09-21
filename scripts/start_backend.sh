#!/bin/bash
set -e
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi
exec uvicorn src.study_engine.web.app:app --reload --host 0.0.0.0 --port 8000
