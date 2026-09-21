#!/usr/bin/env bash
set -euo pipefail

echo "Running test suite..."
pytest tests/
