"""FastAPI Application Factory for KASIU Web Engine (Hito 10)."""

import contextlib
import logging
from pathlib import Path
import os
import signal
import time
from typing import Any, List
from fastapi import FastAPI, BackgroundTasks
from study_engine.web.local_access import configure_local_access
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
from study_engine.web.routes.notebook import admin_router as curriculum_admin_router
from study_engine.web.routes.notebook import router as notebook_router
from study_engine.web.routes.student_exercises import router as student_exercises_router
from study_engine.web.routes.retrieval import router as retrieval_router
from study_engine.web.routes.eval import router as eval_router

logger = logging.getLogger(__name__)
if not logging.getLogger("study_engine.web").handlers:
    # El proyecto no configura logging y el root queda en WARNING: sin esto,
    # los markers operativos (warmup, struggle protocol, auditorías) quedan
    # invisibles aunque sean la única señal operativa del proceso.
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("%(levelname)s: %(name)s: %(message)s"))
    _web_logger = logging.getLogger("study_engine.web")
    _web_logger.addHandler(_h)
    _web_logger.setLevel(logging.INFO)


def _warmup_notebooks(store: Any, db_path: Path | None = None) -> List[str]:
    """Notebooks con embeddings disponibles (best-effort; vacío si no hay vector store)."""
    import sqlite3

    if db_path is None:
        repo_root = Path(__file__).resolve().parents[3]
        db_path = repo_root / "data" / "web_state" / "vector_store.db"
    if not db_path.exists():
        return []
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            rows = con.execute("SELECT DISTINCT notebook_id FROM chunk_embeddings").fetchall()
        finally:
            con.close()
        return [r[0] for r in rows]
    except Exception:
        return []


def _schedule_retrieval_warmup(
    container: Any,
    *,
    enabled: bool | None = None,
) -> None:
    """Warm the configured vector store unless the runtime profile disables it."""
    import os
    import threading

    if enabled is False:
        logger.info("Warmup de retrieval desactivado por perfil de ejecución")
        return

    from study_engine.config import settings

    if not getattr(settings, "enable_retrieval_warmup", True):
        logger.info("Warmup de retrieval desactivado por configuración (TALOS_ENABLE_WARMUP=0)")
        return
    if os.getenv("TALOS_ENABLE_WARMUP", "1") == "0":
        logger.info("Warmup de retrieval desactivado por variable de entorno TALOS_ENABLE_WARMUP=0")
        return
    if getattr(container, "use_mock", False):
        logger.info("Warmup de retrieval desactivado para contenedor mock")
        return
    if os.getenv("PYTEST_CURRENT_TEST"):
        logger.info("Warmup de retrieval desactivado en entorno de pruebas pytest")
        return

    def _warm() -> None:
        t0 = time.perf_counter()
        try:
            store = getattr(container, "knowledge_store", None)
            if store is None:
                return
            container_working_dir = getattr(container, "working_dir", None)
            vector_db_path = (
                Path(container_working_dir) / "vector_store.db"
                if container_working_dir is not None
                else None
            )
            notebooks = _warmup_notebooks(store, vector_db_path)
            if notebooks:
                primary_nb = "fase0-soc" if "fase0-soc" in notebooks else notebooks[0]
                store.vector_search(query="warmup", notebook_id=primary_nb, limit=1)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.info("Warmup de retrieval completado en %.0f ms", elapsed_ms)
        except Exception as exc:  # warmup nunca debe tirar el server
            logger.warning("Warmup de retrieval falló (no fatal): %s", exc)

    threading.Thread(target=_warm, name="retrieval-warmup", daemon=True).start()


def create_app(
    *,
    static_dir: Path | None = None,
    storage_dir: Path | None = None,
    enable_retrieval_warmup: bool | None = None,
) -> FastAPI:
    """Create and configure the authoritative KASIU FastAPI application."""
    app = FastAPI(
        title="KASIU Study Engine API",
        description="Sovereign Multilayer Architecture & Deterministic Learning Loop REST API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    configure_local_access(app)

    @contextlib.asynccontextmanager
    async def _lifespan(app: FastAPI):
        """Application lifespan: startup initializes container; shutdown closes all storages."""
        from study_engine.web.dependencies import get_container, set_container

        container = get_container()

        # Fase 5.3b: forzar carga síncrona del catálogo KC antes de aceptar
        # queries (había un race post-restart: kc=None en el primer turno).
        kc_catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
        n_kcs = sum(len(v.get("kcs", [])) for v in kc_catalog.values() if isinstance(v, dict))
        logger.info("Catálogo KC cargado: %d notebooks, %d KCs", len(kc_catalog), n_kcs)

        _schedule_retrieval_warmup(container, enabled=enable_retrieval_warmup)

        try:
            yield
        finally:
            # Shutdown: close all storage connections owned by the container.
            # Order: student, session, knowledge, vector, quota, etc.
            for attr in (
                "student_storage",
                "session_store",
                "knowledge_store",
                "context",
            ):
                obj = getattr(container, attr, None)
                if obj is None:
                    continue
                if attr == "context" and isinstance(obj, dict):
                    for v in obj.values():
                        close = getattr(v, "close", None)
                        if callable(close):
                            try:
                                close()
                            except Exception:
                                logger.exception("Error closing %s from context", attr)
                else:
                    close = getattr(obj, "close", None)
                    if callable(close):
                        try:
                            close()
                        except Exception:
                            logger.exception("Error closing %s", attr)
            set_container(None)
            logger.info("Application shutdown complete: all storages closed")

    app = FastAPI(
        title="KASIU Study Engine API",
        description="Sovereign Multilayer Architecture & Deterministic Learning Loop REST API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    configure_local_access(app)

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
    app.include_router(curriculum_admin_router)
    app.include_router(student_exercises_router)
    app.include_router(retrieval_router)
    app.include_router(eval_router)

    # Mount static assets directory
    resolved_static_dir = (
        Path(static_dir).resolve()
        if static_dir is not None
        else (Path(__file__).parent / "static").resolve()
    )
    app.state.static_dir = resolved_static_dir
    app.mount(
        "/static",
        StaticFiles(directory=str(resolved_static_dir), check_dir=False),
        name="static",
    )

    # Mount storage directory for library covers and source materials
    repo_root = Path(__file__).resolve().parents[3]
    if storage_dir is not None:
        resolved_storage_dir = Path(storage_dir).resolve()
    else:
        resolved_storage_dir = (repo_root / "kasiu-lab" / "storage").resolve()
        if not resolved_storage_dir.exists():
            resolved_storage_dir = (repo_root / "storage").resolve()
    app.state.storage_dir = resolved_storage_dir
    app.mount(
        "/storage",
        StaticFiles(directory=str(resolved_storage_dir), check_dir=False),
        name="storage",
    )

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
        index_file = resolved_static_dir / "index.html"
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
