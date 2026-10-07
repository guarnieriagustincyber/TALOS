"""Repeatability and sterility regression for the synthetic chat route.

This tests only the isolated HTTP/SSE route boundary.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

CONTRACT_ID = "TALOS-B1-R-1"
REPETITIONS = 3
CASES = (
    "success",
    "error",
    "abstention",
    "clarification",
    "truncated",
    "stream_aborted",
    "eof_without_terminal",
    "duplicate_terminal",
    "error_after_tokens",
    "abrupt_close",
)


def test_synthetic_chat_route_is_repeatable_and_sterile(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    child_cwd = tmp_path / "cwd"
    child_home = tmp_path / "home"
    child_tmp = tmp_path / "tmp"
    child_cwd.mkdir()
    child_home.mkdir()
    child_tmp.mkdir()

    child_env = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "LC_ALL", "TMPDIR", "SYSTEMROOT", "WINDIR")
        if key in os.environ
    }
    child_env.update(
        {
            "HOME": str(child_home),
            "TMPDIR": str(child_tmp),
            "PYTHONPATH": os.pathsep.join(
                (str(repo_root / "src"), str(repo_root))
            ),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
    )
    repo_status_before = _git_status(repo_root)
    report_path = tmp_path / "b1r-evidence.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(Path(__file__).resolve()),
            "--worker",
            str(repo_root),
            str(report_path),
        ],
        cwd=child_cwd,
        env=child_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, (
        "B1-R subprocess failed.\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    assert report_path.is_file(), "B1-R worker did not produce its report."
    verifier = subprocess.run(
        [
            sys.executable,
            "-B",
            str(repo_root / "scripts/verify_b1r_artifact.py"),
            "--contract",
            str(repo_root / "tests/audit/b1r_contract.json"),
            "--report",
            str(report_path),
        ],
        cwd=child_cwd,
        env=child_env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert verifier.returncode == 0, (
        "Independent B1-R verifier failed.\n"
        f"stdout:\n{verifier.stdout}\n"
        f"stderr:\n{verifier.stderr}"
    )
    assert json.loads(verifier.stdout) == {
        "status": "TECHNICAL PASS",
        "findings": [],
    }
    assert (
        _git_status(repo_root) == repo_status_before
    ), "B1-R changed repository state."


def _git_status(repo_root: Path) -> str:
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain",
            "--untracked-files=all",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


def _run_worker(repo_root: Path, report_path: Path) -> None:
    import asyncio
    import hashlib
    import json as json_module
    import os as os_module
    from pathlib import Path as PathClass
    import socket
    import sqlite3
    import subprocess as subprocess_module
    import sys as sys_module
    import threading
    from types import SimpleNamespace

    from httpx import ASGITransport, AsyncClient
    from study_engine.hierarchy.scope_resolver import ResolvedScope, ScopeType

    project_root = repo_root.resolve()
    worker_temp_dir = PathClass(os_module.environ["TMPDIR"]).resolve()
    if not worker_temp_dir.is_dir():
        raise AssertionError("B1-R private temporary directory is unavailable.")
    contract_bytes = (
        project_root / "tests/audit/b1r_contract.json"
    ).read_bytes()
    contract_sha256 = hashlib.sha256(contract_bytes).hexdigest()
    forbidden_accesses: list[str] = []
    external_calls: list[str] = []
    protected_data_accesses = 0
    real_provider_calls = 0
    synthetic_backend_resolutions = 0
    synthetic_pipeline_constructions = 0
    synthetic_context_calls = 0
    real_container_constructions = 0
    normal_lifespan_runs = 0
    thread_starts = 0
    route_requests = 0
    guard_probes: dict[str, dict[str, object]] = {}
    allowed_app_directories = {
        (project_root / "src/study_engine/web/static").resolve(),
        (project_root / "kasiu-lab/storage").resolve(),
        (project_root / "kasiu-lab/storage/sources").resolve(),
        (project_root / "kasiu-lab/storage/covers").resolve(),
    }
    if not all(path.is_dir() for path in allowed_app_directories):
        raise AssertionError(
            "Expected app directories must exist before B1-R."
        )

    protected_names = {".env"}
    protected_parts = {"data", "corpus", "models"}
    protected_suffixes = {".db", ".sqlite", ".sqlite3"}
    write_flags = (
        os_module.O_WRONLY
        | os_module.O_RDWR
        | os_module.O_CREAT
        | os_module.O_TRUNC
        | os_module.O_APPEND
    )

    def _as_path(value: object) -> PathClass | None:
        if isinstance(value, int):
            return None
        try:
            return PathClass(os_module.fsdecode(value)).resolve()
        except (TypeError, ValueError, OSError):
            return None

    def _is_within(path: PathClass, root: PathClass) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _reject(category: str, detail: object) -> None:
        message = f"{category}: {detail}"
        forbidden_accesses.append(message)
        raise RuntimeError(f"B1-R forbidden operation ({message})")

    def _audit(event: str, args: tuple[object, ...]) -> None:
        nonlocal protected_data_accesses
        if event == "open" and args:
            path = _as_path(args[0])
            if path is None:
                return
            if (
                path.name in protected_names
                or protected_parts.intersection(path.parts)
                or path.suffix.lower() in protected_suffixes
            ):
                protected_data_accesses += 1
                _reject("protected-file", path)
            mode = args[1] if len(args) > 1 else ""
            flags = (
                args[2] if len(args) > 2 and isinstance(args[2], int) else 0
            )
            writing = (
                isinstance(mode, str) and any(flag in mode for flag in "wax+")
            ) or bool(flags & write_flags)
            if writing and _is_within(path, project_root):
                _reject("project-write", path)
        elif event == "sqlite3.connect":
            _reject("sqlite", args[0] if args else "connect")
        elif event in {
            "socket.connect",
            "socket.connect_ex",
            "socket.bind",
            "socket.getaddrinfo",
            "socket.gethostbyname",
            "socket.gethostbyaddr",
            "socket.sendto",
        }:
            _reject("network", event)
        elif event in {
            "subprocess.Popen",
            "os.system",
            "os.exec",
            "os.posix_spawn",
            "os.spawn",
        }:
            _reject("process", event)
        elif event == "os.mkdir" and args:
            path = _as_path(args[0])
            if (
                path is None
                or path not in allowed_app_directories
                or not path.is_dir()
            ):
                _reject("directory-create", path or args[0])
        elif event in {
            "os.chmod",
            "os.chown",
            "os.link",
            "os.remove",
            "os.rename",
            "os.replace",
            "os.rmdir",
            "os.symlink",
            "os.truncate",
            "os.unlink",
            "os.utime",
        }:
            path = _as_path(args[0]) if args else None
            if (
                event in {"os.remove", "os.unlink"}
                and path is not None
                and path.parent == worker_temp_dir
                and path.is_file()
            ):
                return
            _reject("filesystem-mutation", event)

    def _deny_external(name: str):
        def denied(*args, **kwargs):
            nonlocal thread_starts
            external_calls.append(name)
            if name == "threading.Thread.start":
                thread_starts += 1
            _reject("external-call", name)

        return denied

    original_socket = socket.socket

    class GuardedSocket(original_socket):
        def __new__(
            cls,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=0,
            fileno=None,
        ):
            if family == socket.AF_UNIX and type & socket.SOCK_STREAM:
                return super().__new__(cls, family, type, proto, fileno)
            external_calls.append("socket.socket")
            _reject("external-call", "socket.socket")

    sys_module.addaudithook(_audit)
    import tempfile

    tempfile.tempdir = None
    if PathClass(tempfile.gettempdir()).resolve() != worker_temp_dir:
        raise AssertionError("B1-R did not use its private temporary directory.")
    socket.socket = GuardedSocket
    socket.create_connection = _deny_external("socket.create_connection")
    socket.getaddrinfo = _deny_external("socket.getaddrinfo")
    socket.gethostbyname = _deny_external("socket.gethostbyname")
    threading.Thread.start = _deny_external("threading.Thread.start")

    import study_engine.web.app as web_app
    import study_engine.web.dependencies as dependencies
    import study_engine.web.routes.chat as chat

    real_app_container = dependencies.AppContainer

    class ForbiddenAppContainer(real_app_container):
        def __init__(self, *args, **kwargs) -> None:
            nonlocal real_container_constructions
            real_container_constructions += 1
            _reject("real-container", "AppContainer constructor")

    dependencies.AppContainer = ForbiddenAppContainer
    chat.AppContainer = ForbiddenAppContainer

    class SyntheticPipeline:
        def __init__(self, **kwargs) -> None:
            nonlocal synthetic_pipeline_constructions
            synthetic_pipeline_constructions += 1
            self._last_abstention_decision = None

        async def generate_phased_response(self, **kwargs):
            for event_type, payload in _events_for_case(
                active_case["case_id"]
            ):
                if event_type == "raise":
                    active_observed_exceptions.append(
                        "RuntimeError: synthetic-pipeline-error"
                    )
                    raise RuntimeError("synthetic-pipeline-error")
                if event_type == "cancel":
                    active_observed_exceptions.append("asyncio.CancelledError")
                    raise asyncio.CancelledError()
                yield SimpleNamespace(event_type=event_type, payload=payload)

    app = web_app.app

    def fail_if_startup_runs() -> None:
        nonlocal normal_lifespan_runs
        normal_lifespan_runs += 1
        _reject("normal-lifespan", "FastAPI startup handler")

    app.router.on_startup[:] = [fail_if_startup_runs]

    async def synthetic_container_dependency():
        return container

    container = SimpleNamespace(
        knowledge_store=object(),
        controller=SimpleNamespace(last_abstention_decision=None),
        last_abstention_decision=None,
    )
    app.dependency_overrides[dependencies.get_container] = (
        synthetic_container_dependency
    )
    active_case = {"case_id": ""}
    active_observed_exceptions: list[str] = []

    def deny_provider_construction() -> None:
        nonlocal real_provider_calls
        real_provider_calls += 1
        _reject("real-provider", "provider construction")

    def run_guard_probe(
        probe_id: str,
        expected_category: str,
        action,
    ) -> None:
        nonlocal protected_data_accesses, real_provider_calls
        nonlocal real_container_constructions, normal_lifespan_runs
        nonlocal thread_starts
        previous_forbidden_count = len(forbidden_accesses)
        previous_external_count = len(external_calls)
        previous_protected_count = protected_data_accesses
        previous_provider_count = real_provider_calls
        previous_container_count = real_container_constructions
        previous_lifespan_count = normal_lifespan_runs
        previous_thread_count = thread_starts
        try:
            action()
        except RuntimeError as exc:
            rejected = (
                f"B1-R forbidden operation ({expected_category}:" in str(exc)
            )
        else:
            rejected = False
        observed_violations = forbidden_accesses[previous_forbidden_count:]
        guard_probes[probe_id] = {
            "rejected": rejected,
            "category": expected_category if rejected else None,
            "observed_violations": len(observed_violations),
        }
        del forbidden_accesses[previous_forbidden_count:]
        del external_calls[previous_external_count:]
        protected_data_accesses = previous_protected_count
        real_provider_calls = previous_provider_count
        real_container_constructions = previous_container_count
        normal_lifespan_runs = previous_lifespan_count
        thread_starts = previous_thread_count
        if not rejected or len(observed_violations) != 1:
            raise AssertionError(
                f"Guard probe {probe_id} did not fail closed."
            )

    def prepare_chat_context(**kwargs):
        nonlocal synthetic_context_calls
        synthetic_context_calls += 1
        case_id = active_case["case_id"]
        is_abstention = case_id == "abstention"
        is_clarification = case_id == "clarification"
        context_pack = SimpleNamespace(
            abstained=is_abstention or is_clarification,
            is_sufficient=not (is_abstention or is_clarification),
            abstention_reason="SYNTHETIC_OUT_OF_SCOPE",
            clarification_message=(
                "Synthetic clarification required."
                if is_clarification
                else None
            ),
            resolved_item=None,
            formatted_context="",
            reference_disclaimer=None,
        )
        scope = ResolvedScope(
            scope_type=ScopeType.NOTEBOOK,
            scope_id="b1r-notebook",
            folder_id="b1r-folder",
            notebook_id="b1r-notebook",
        )
        return (
            scope,
            SimpleNamespace(base_system_prompt="synthetic"),
            context_pack,
            [],
            None,
            "basic",
            None,
            None,
            None,
            None,
            {},
        )

    def resolve_backend(*args, **kwargs):
        nonlocal synthetic_backend_resolutions
        synthetic_backend_resolutions += 1
        return SimpleNamespace()

    async def inline_to_thread(function, *args, **kwargs):
        if function is not chat._prepare_chat_context:
            _reject(
                "thread-offload",
                getattr(function, "__qualname__", repr(function)),
            )
        return function(*args, **kwargs)

    chat._prepare_chat_context = prepare_chat_context
    chat._resolve_chat_backend = resolve_backend
    chat.StructuredResponsePipeline = SyntheticPipeline
    chat._build_cognitive_profile_block = lambda *args, **kwargs: None
    chat._update_curriculum_progress = lambda *args, **kwargs: None
    chat._trigger_background_memory_extraction = lambda *args, **kwargs: None
    chat._detect_evidence_discrepancies = lambda *args, **kwargs: []
    asyncio.to_thread = inline_to_thread

    guard_actions = {
        "protected_file_read": lambda: open(project_root / ".env", "rb"),
        "sqlite_connection": lambda: sqlite3.connect(":memory:"),
        "outbound_socket": lambda: socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        ),
        "subprocess_creation": lambda: subprocess_module.Popen(
            [sys_module.executable, "-c", "pass"]
        ),
        "project_write": lambda: open(
            project_root / "b1r-prohibited-write-probe.tmp",
            "w",
            encoding="utf-8",
        ),
        "filesystem_mutation_outside_temp": lambda: os_module.remove(
            PathClass.cwd() / "b1r-prohibited-delete.tmp"
        ),
        "app_container_construction": lambda: dependencies.AppContainer(
            use_mock=True
        ),
        "normal_startup": app.router.on_startup[0],
        "thread_start": lambda: threading.Thread(target=lambda: None).start(),
        "provider_construction": deny_provider_construction,
    }
    required_guard_probes = {
        "protected_file_read": "protected-file",
        "sqlite_connection": "sqlite",
        "outbound_socket": "external-call",
        "subprocess_creation": "process",
        "project_write": "project-write",
        "filesystem_mutation_outside_temp": "filesystem-mutation",
        "app_container_construction": "real-container",
        "normal_startup": "normal-lifespan",
        "thread_start": "external-call",
        "provider_construction": "real-provider",
    }
    for probe_id, expected_category in required_guard_probes.items():
        run_guard_probe(
            probe_id,
            expected_category,
            guard_actions[probe_id],
        )

    async def execute_case(case_id: str) -> dict[str, object]:
        nonlocal route_requests
        active_case["case_id"] = case_id
        active_observed_exceptions.clear()
        for cache_name in (
            "_ACTIVE_TURN_HISTORIES",
            "_ACTIVE_PROTECTED_ASSESSMENTS",
            "_CONV_TURN_BUFFER",
            "_LAST_EPISTEMIC_PACK",
            "_KC_TURN_STREAKS",
            "_DIGEST_SHOWN",
        ):
            getattr(chat, cache_name).clear()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://b1r.invalid",
        ) as client:
            response = await client.post(
                "/api/chat/query",
                json={
                    "prompt": "Explain a synthetic concept.",
                    "scope_type": "notebook",
                    "scope_id": "b1r-notebook",
                    "session_id": f"b1r-{case_id}",
                    "requested_phase": "conceptual",
                },
            )
        events = _parse_sse(response.text)
        route_requests += 1
        event_types = [event["event_type"] for event in events]
        observation = {
            "case_id": case_id,
            "http_status": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "events": event_types,
            "last_event": event_types[-1] if event_types else None,
            "phase_complete_present": "phase_complete" in event_types,
            "stream_closed": response.is_closed,
            "observed_exceptions": list(active_observed_exceptions),
            "consumer_observer": "SOURCE_TRACED_NOT_RUNTIME_TESTED",
            "forbidden_accesses": list(forbidden_accesses),
        }
        if forbidden_accesses:
            raise AssertionError(
                f"Forbidden access attempts: {forbidden_accesses}"
            )
        return observation

    async def run_all_cases() -> dict[str, list[dict[str, object]]]:
        results: dict[str, list[dict[str, object]]] = {}
        for case_id in CASES:
            results[case_id] = []
            for _ in range(REPETITIONS):
                results[case_id].append(await execute_case(case_id))
        return results

    report = {
        "schema_version": 1,
        "contract_id": CONTRACT_ID,
        "contract_sha256": contract_sha256,
        "case_count": len(CASES),
        "repetitions_per_case": REPETITIONS,
        "cases": asyncio.run(run_all_cases()),
        "guard_probes": guard_probes,
        "forbidden_accesses": forbidden_accesses,
        "external_calls": external_calls,
        "real_provider_calls": real_provider_calls,
        "synthetic_backend_resolutions": synthetic_backend_resolutions,
        "synthetic_pipeline_constructions": synthetic_pipeline_constructions,
        "synthetic_context_calls": synthetic_context_calls,
        "real_container_constructions": real_container_constructions,
        "protected_data_accesses": protected_data_accesses,
        "normal_lifespan_runs": normal_lifespan_runs,
        "thread_starts": thread_starts,
        "route_requests": route_requests,
        "functional_changes": 0,
        "consumer_observation": "SOURCE_TRACED_NOT_RUNTIME_TESTED",
    }
    report_path.write_text(
        json_module.dumps(report, sort_keys=True),
        encoding="utf-8",
    )


def _events_for_case(case_id: str) -> list[tuple[str, dict[str, object]]]:
    if case_id == "success":
        return [
            ("phase_start", {"phase": "conceptual"}),
            (
                "phase_token",
                {"phase": "conceptual", "token": "Synthetic answer."},
            ),
            ("evidence_manifest", {"citations": [], "abstained": False}),
            ("phase_complete", {"completed_phase": "conceptual"}),
        ]
    if case_id == "error":
        return [("raise", {})]
    if case_id in {"abstention", "clarification"}:
        return []
    if case_id == "truncated":
        return [
            ("phase_start", {"phase": "conceptual"}),
            ("truncated", {"message": "Synthetic truncation notice."}),
            ("audit_verdict", {"verdict": "synthetic"}),
            ("evidence_manifest", {"citations": [], "abstained": False}),
            ("phase_complete", {"completed_phase": "conceptual"}),
        ]
    if case_id == "stream_aborted":
        return [
            ("phase_start", {"phase": "conceptual"}),
            ("stream_aborted", {"message": "Synthetic cancellation."}),
            ("cancel", {}),
        ]
    if case_id == "eof_without_terminal":
        return [("phase_start", {"phase": "conceptual"})]
    if case_id == "duplicate_terminal":
        return [
            ("phase_complete", {"completed_phase": "conceptual"}),
            ("phase_complete", {"completed_phase": "conceptual"}),
        ]
    if case_id == "error_after_tokens":
        return [
            ("phase_start", {"phase": "conceptual"}),
            (
                "phase_token",
                {"phase": "conceptual", "token": "Partial answer."},
            ),
            ("raise", {}),
        ]
    if case_id == "abrupt_close":
        return [
            ("phase_start", {"phase": "conceptual"}),
            (
                "phase_token",
                {"phase": "conceptual", "token": "Partial answer."},
            ),
        ]
    raise AssertionError(f"Unknown synthetic case: {case_id}")


def _parse_sse(body: str) -> list[dict[str, object]]:
    events = []
    for block in body.split("\n\n"):
        for line in block.splitlines():
            if line.startswith("data: "):
                parsed = json.loads(line[6:])
                if isinstance(parsed, dict) and isinstance(
                    parsed.get("event_type"), str
                ):
                    events.append(parsed)
    return events


if __name__ == "__main__" and len(sys.argv) == 4 and sys.argv[1] == "--worker":
    _run_worker(Path(sys.argv[2]), Path(sys.argv[3]))
