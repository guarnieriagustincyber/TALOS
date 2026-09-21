"""FastAPI Application Factory for KASIU Web Engine (Hito 10)."""

from pathlib import Path
import os
import signal
import time
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from study_engine.web.routes.chat import router as chat_router
from study_engine.web.routes.curriculum import router as curriculum_router
from study_engine.web.routes.evidence import router as evidence_router
from study_engine.web.routes.federation import router as federation_router
from study_engine.web.routes.health import router as health_router
from study_engine.web.routes.ingestion import router as ingestion_router
from study_engine.web.routes.llm_pool import router as llm_pool_router
from study_engine.web.routes.practice import router as practice_router
from study_engine.web.routes.sources import router as sources_router
from study_engine.web.routes.student import router as student_router
from study_engine.web.routes.threatintel import router as threatintel_router
from study_engine.web.routes.telemetry import router as telemetry_router
from study_engine.web.routes.pedagogy import router as pedagogy_router
from study_engine.web.routes.dialogue import router as dialogue_router
from study_engine.web.routes.study_session import router as study_session_router
from study_engine.web.routes.notebook import router as notebook_router
from study_engine.web.routes.student_exercises import router as student_exercises_router



def create_app() -> FastAPI:
    """Create and configure the authoritative KASIU FastAPI application."""
    app = FastAPI(
        title="KASIU Study Engine API",
        description="Sovereign Multilayer Architecture & Deterministic Learning Loop REST API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Local CORS protection: bind to localhost and frontend dev ports
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5174",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        """Eagerly initialize singleton container to ensure zero cold-start latency for UI requests."""
        from study_engine.web.dependencies import get_container
        get_container()

    # Register API Routers
    app.include_router(health_router)
    app.include_router(curriculum_router)
    app.include_router(student_router)

    # Legacy /api/session decommissioning: Explicit 410 Gone (Ola 4)
    @app.api_route("/api/session/{path:path}", methods=["GET", "POST", "PUT", "DELETE"], status_code=410)
    def session_retired(path: str) -> dict:
        import logging
        logging.getLogger(__name__).info("DEPRECATED_ENDPOINT_HIT: /api/session/%s", path)
        return {
            "error": "ENDPOINT_RETIRED",
            "message": "/api/session fue decomisionado. Usá /api/chat/query o /api/pedagogy/episode/*.",
            "migration_guide": "docs/api_migration_session_to_chat.md",
        }

    app.include_router(chat_router)
    app.include_router(llm_pool_router)
    app.include_router(sources_router)
    app.include_router(practice_router)
    app.include_router(evidence_router)
    app.include_router(ingestion_router)
    app.include_router(federation_router)
    app.include_router(threatintel_router)
    app.include_router(telemetry_router)
    app.include_router(pedagogy_router)
    app.include_router(dialogue_router)
    app.include_router(study_session_router)
    app.include_router(notebook_router)
    app.include_router(student_exercises_router)

    # Mount static assets directory
    static_dir = (Path(__file__).parent / "static").resolve()
    static_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # Mount storage directory for library covers and source materials
    repo_root = Path(__file__).resolve().parents[3]
    storage_dir = (repo_root / "kasiu-lab" / "storage").resolve()
    if not storage_dir.exists():
        storage_dir = (repo_root / "storage").resolve()
    storage_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/storage", StaticFiles(directory=str(storage_dir)), name="storage")

    # Client Heartbeat & Auto-Shutdown Watchdog
    client_state = {
        "last_seen": time.time(),
        "has_connected": False,
        "shutdown_scheduled": None,
    }

    @app.post("/api/system/heartbeat")
    def client_heartbeat() -> dict:
        """Register active UI presence and cancel any pending shutdown."""
        client_state["last_seen"] = time.time()
        client_state["has_connected"] = True
        client_state["shutdown_scheduled"] = None  # Cancel shutdown on page reload
        return {"status": "ok", "timestamp": client_state["last_seen"]}

    @app.post("/api/system/shutdown")
    def client_shutdown(background_tasks: BackgroundTasks) -> dict:
        """Schedule graceful shutdown with grace window to permit page refreshes."""
        target_time = time.time() + 8.0
        client_state["shutdown_scheduled"] = target_time

        def check_and_kill():
            time.sleep(8.0)
            if (
                client_state["shutdown_scheduled"] is not None
                and time.time() >= client_state["shutdown_scheduled"]
                and (time.time() - client_state["last_seen"]) >= 6.0
            ):
                os.kill(os.getpid(), signal.SIGTERM)

        background_tasks.add_task(check_and_kill)
        return {"status": "shutdown_scheduled", "grace_seconds": 8.0}

    @app.get("/", response_class=HTMLResponse)
    def index_route() -> HTMLResponse:
        """Serve the Single Page Application shell or initial launch message."""
        index_file = static_dir / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
        return HTMLResponse(
            content="""<!DOCTYPE html>
<html>
<head><title>KASIU Study Engine</title></head>
<body style="font-family: sans-serif; background: #0f172a; color: #f8fafc; padding: 2rem;">
  <h1>🚀 KASIU Study Engine - API Operativa</h1>
  <p>El servidor FastAPI de KASIU está activo en <code>http://127.0.0.1:8000</code>.</p>
  <ul>
    <li><a style="color: #38bdf8;" href="/docs">Documentación OpenAPI (/docs)</a></li>
    <li><a style="color: #38bdf8;" href="/api/health">Estado del Sistema (/api/health)</a></li>
    <li><a style="color: #38bdf8;" href="/api/curriculum/roadmap">Roadmap Curricular (/api/curriculum/roadmap)</a></li>
  </ul>
</body>
</html>"""
        )

    return app
app = create_app()
