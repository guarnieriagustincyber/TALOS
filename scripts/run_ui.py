#!/usr/bin/env python3
"""Launcher script for KASIU Web Engine & REST API (Hito 10).

Usage:
    .venv/bin/python scripts/run_ui.py [--port 8000] [--reload]
"""

import argparse
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Load .env if present
env_path = REPO_ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            clean_k = k.strip()
            clean_v = v.strip().strip("'\"")
            if clean_k not in os.environ and clean_v:
                os.environ[clean_k] = clean_v

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="KASIU Web UI & API Server")
    parser.add_argument("--host", default="127.0.0.1", help="Binding interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    # Enforce local loopback binding security invariant
    if args.host not in ("127.0.0.1", "localhost"):
        print(f"⚠️ [SEGURIDAD] Rechazando host '{args.host}'. KASIU se restringe estrictamente a 127.0.0.1.")
        sys.exit(1)

    print("===========================================================================")
    print("🚀 INICIANDO KASIU STUDY ENGINE - WEB API (HITO 10)")
    print(f"📍 Servidor disponible en: http://{args.host}:{args.port}")
    print(f"📖 Documentación OpenAPI: http://{args.host}:{args.port}/docs")
    print(f"🩺 Chequeo de salud:      http://{args.host}:{args.port}/api/health")
    print("===========================================================================")

    uvicorn.run(
        "study_engine.web.app:create_app",
        host=args.host,
        port=args.port,
        factory=True,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
