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
    gate_git_observation = _gate_git_observation()
    if gate_git_observation is None:
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
    if gate_git_observation is None:
        assert (
            _git_status(repo_root) == repo_status_before
        ), "B1-R changed repository state."
    # Inside the Quality Gate the supervisor owns the authoritative pre/post
    # comparison and fails the gate closed on any mismatch or tampering.


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


GATE_GIT_OBSERVATION_ENV = "TALOS_QUALITY_GATE_GIT_OBSERVATION"
GATE_GIT_OBSERVATION_FIELDS = (
    "schema_version",
    "phase",
    "run_identity",
    "gate_identity",
    "run_token",
    "captured_at",
    "git_command",
    "head_commit",
    "porcelain",
)


def _gate_git_observation() -> dict | None:
    """Load the supervisor Git observation inside the Quality Gate sandbox.

    STEP-14: the sandbox masks ``.git``, so this worker cannot observe the
    checkout itself.  The supervisor captures the authoritative pre/post
    pair host-side, delivers the signed pre-record for this exact run, and
    fails the gate closed on any change or tampering.  Outside the gate the
    test keeps its legacy in-process sterility check (returns None).
    """
    if os.environ.get("TALOS_TEST_ISOLATED") != "1":
        return None
    path = os.environ.get(GATE_GIT_OBSERVATION_ENV)
    if not path:
        raise AssertionError(
            "STEP-14 fail-closed: gate sandbox active without a supervisor "
            "Git observation"
        )
    try:
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise AssertionError(
            f"STEP-14 fail-closed: unreadable observation: {error}"
        ) from error
    if (
        not isinstance(envelope, dict)
        or set(envelope) != {"record", "hmac_sha256"}
        or not isinstance(envelope.get("record"), dict)
        or not isinstance(envelope.get("hmac_sha256"), str)
    ):
        raise AssertionError(
            "STEP-14 fail-closed: malformed observation envelope"
        )
    record = envelope["record"]
    missing = [
        field for field in GATE_GIT_OBSERVATION_FIELDS if field not in record
    ]
    if (
        missing
        or record.get("schema_version") != 1
        or record.get("phase") != "pre"
    ):
        raise AssertionError(
            "STEP-14 fail-closed: incomplete or unexpected observation record"
        )
    for field, expected in (
        ("run_identity", os.environ.get("TALOS_TEST_RUN_ID")),
        ("gate_identity", os.environ.get("TALOS_TEST_GATE_ID")),
        ("run_token", os.environ.get("TALOS_QUALITY_GATE_START_TOKEN")),
    ):
        if not expected or record.get(field) != expected:
            raise AssertionError(
                f"STEP-14 fail-closed: observation {field} does not match "
                "this run"
            )
    command = record.get("git_command")
    if (
        not isinstance(command, list)
        or len(command) != 6
        or command[:2] != ["git", "-C"]
        or command[3:] != ["status", "--porcelain", "--untracked-files=all"]
    ):
        raise AssertionError(
            "STEP-14 fail-closed: unexpected observation command"
        )
    if (
        not isinstance(record.get("porcelain"), str)
        or not isinstance(record.get("head_commit"), str)
        or not record["head_commit"]
        or not isinstance(record.get("captured_at"), str)
        or not record["captured_at"]
    ):
        raise AssertionError(
            "STEP-14 fail-closed: observation payload is incomplete"
        )
    return record


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
    from b1r_academic_fixture import (
        AcademicAuditor, AcademicBackend, QUERY, SOURCE, TEXT, context as academic_context,
    )

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
    from study_engine.audit.generation_adapter import audit_generation_payload

    real_pipeline = chat.StructuredResponsePipeline

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
            self.real = real_pipeline(**kwargs)

        async def generate_phased_response(self, **kwargs):
            nonlocal pipeline_token_events
            if active_case["case_id"] in {"success", "truncated", "duplicate_terminal"}:
                async for event in self.real.generate_phased_response(**kwargs):
                    if event.event_type == "phase_token":
                        pipeline_token_events += 1
                    yield event
                return
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
                if event_type == "phase_token":
                    pipeline_token_events += 1
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
        auditor=AcademicAuditor(),
    )
    app.dependency_overrides[dependencies.get_container] = (
        synthetic_container_dependency
    )
    active_case = {"case_id": ""}
    active_observed_exceptions: list[str] = []
    pipeline_token_events = 0
    seen_audit_requests: set[str] = set()

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
        contract, context_pack, chunks = academic_context(
            chat, empty=is_abstention or is_clarification,
            clarification=is_clarification,
        )
        scope = ResolvedScope(
            scope_type=ScopeType.NOTEBOOK,
            scope_id="b1r-notebook",
            folder_id="b1r-folder",
            notebook_id="b1r-notebook",
        )
        return (
            scope,
            contract,
            context_pack,
            chunks,
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
        return AcademicBackend()

    async def inline_to_thread(function, *args, **kwargs):
        if function not in (chat._prepare_chat_context, audit_generation_payload):
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

    class AcademicCutTransport:
        """Explicit wire anomalies; never attribute injected frames to TALOS."""
        def __init__(self):
            self.injection = "none"
            self.pre_injection_completions = 0

        async def __call__(self, scope, receive, send):
            closed = False
            projection = None

            async def observe(message):
                nonlocal closed, projection
                if closed:
                    return
                if message["type"] == "http.response.body":
                    frames = _parse_sse(message.get("body", b"").decode())
                    for frame in frames:
                        if frame["event_type"] == "audit_verdict":
                            projection = frame["payload"].get("audit_projection")
                    self.pre_injection_completions += sum(
                        frame["event_type"] == "phase_complete" for frame in frames
                    )
                    cut = active_case["case_id"] == "truncated" and any(
                        frame["event_type"] == "phase_token" for frame in frames
                    )
                    if cut:
                        assert projection and projection["decision"] == "APPROVED"
                        assert projection["emission"] == "authorized"
                        assert not any(frame["event_type"] == "phase_complete" for frame in frames)
                        self.injection = "cut_after_authorized_token"
                        await send({**message, "more_body": False})
                        closed = True
                        return
                    if active_case["case_id"] == "duplicate_terminal" and any(
                        frame["event_type"] == "phase_complete" for frame in frames
                    ):
                        assert self.pre_injection_completions == 1
                        assert projection and projection["decision"] == "APPROVED"
                        assert projection["emission"] == "authorized"
                        assert message.get("more_body") is True
                        assert len(frames) == 1, "Duplicate only the terminal, never content"
                        self.injection = "duplicate_terminal_frame"
                        await send(message)
                await send(message)

            await app(scope, receive, observe)

    async def execute_case(case_id: str) -> dict[str, object]:
        nonlocal route_requests, pipeline_token_events
        active_case["case_id"] = case_id
        active_observed_exceptions.clear()
        pipeline_token_events = 0
        for cache_name in (
            "_ACTIVE_TURN_HISTORIES",
            "_ACTIVE_PROTECTED_ASSESSMENTS",
            "_CONV_TURN_BUFFER",
            "_LAST_EPISTEMIC_PACK",
            "_KC_TURN_STREAKS",
            "_DIGEST_SHOWN",
        ):
            getattr(chat, cache_name).clear()

        wire_transport = AcademicCutTransport()
        async with AsyncClient(
            transport=ASGITransport(app=wire_transport),
            base_url="http://127.0.0.1:8000",
        ) as client:
            response = await client.post(
                "/api/chat/query",
                json={
                    "prompt": QUERY,
                    "scope_type": "notebook",
                    "scope_id": "b1r-notebook",
                    "session_id": f"b1r-{case_id}",
                    "requested_phase": "conceptual",
                },
            )
        events = _parse_sse(response.text)
        if case_id in {"success", "truncated", "duplicate_terminal"}:
            projections = [e["payload"]["audit_projection"] for e in events
                           if e["event_type"] == "audit_verdict"
                           and "audit_projection" in e["payload"]]
            assert len(projections) == 1, "Fixture did not reach validated S4.4"
            projection = projections[0]
            report = container.auditor.reports[-1]
            audit_input = container.auditor.inputs[-1]
            assert report.overall_verdict.value == "APPROVED" and report.nli_executed
            assert projection["request_id"] == audit_input.request.request_id == report.request_id
            assert report.request_id not in seen_audit_requests, "Audit reused across invocations"
            seen_audit_requests.add(report.request_id)
            assert projection["audit_id"] == report.audit_id
            assert projection["session_id"] == f"b1r-{case_id}"
            assert projection["notebook_id"] == projection["scope_id"] == "b1r-notebook"
            assert projection["decision"] == "APPROVED" and projection["emission"] == "authorized"
            assert projection["content_sha256"] == hashlib.sha256(TEXT.encode()).hexdigest()
            assert projection["content_binding_id"]
            manifests = [e["payload"]["citations"] for e in events if e["event_type"] == "evidence_manifest"]
            assert len(manifests) == 1 and len(manifests[0]) == 1
            assert manifests[0][0]["source_id"] == "b1r-source"
            assert manifests[0][0]["document_id"] == "b1r-document"
            assert manifests[0][0]["chunk_id"] == "b1r-chunk"
            assert manifests[0][0]["chunk_text"] == SOURCE
            assert manifests[0][0]["doc_hash"] == hashlib.sha256(SOURCE.encode()).hexdigest()
            assert manifests[0][0]["page_start"] == manifests[0][0]["page_end"] == 1
            emitted = "".join(e["payload"]["token"] for e in events if e["event_type"] == "phase_token")
            if case_id in {"success", "duplicate_terminal"}:
                assert emitted == TEXT
                completions = [e["event_type"] for e in events].count("phase_complete")
                assert completions == (2 if case_id == "duplicate_terminal" else 1)
                assert wire_transport.pre_injection_completions == 1
                assert events[-1]["event_type"] == "phase_complete"
            else:
                assert 0 < len(emitted) < len(TEXT) and TEXT.startswith(emitted)
                assert not any(e["event_type"] in {"phase_complete", "abstention"} for e in events)
            assert next(i for i,e in enumerate(events) if e["event_type"] == "audit_verdict") < next(
                i for i,e in enumerate(events) if e["event_type"] == "phase_token")
        route_requests += 1
        event_types = [event["event_type"] for event in events]
        published_tokens = event_types.count("phase_token")
        decisions = [e["payload"].get("verdict") for e in events if e["event_type"] == "audit_verdict"]
        if case_id not in {"success", "truncated", "duplicate_terminal"}:
            assert published_tokens == 0, "Unaudited fixture leaked academic tokens"
        if case_id in {"error_after_tokens", "abrupt_close"}:
            assert pipeline_token_events == 1, "Historical case never supplied its internal token"
            assert "phase_complete" not in event_types
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
            "route_properties": {
                "pipeline_token_events": pipeline_token_events,
                "published_token_events": published_tokens,
                "completion_count": event_types.count("phase_complete"),
                "pre_injection_completion_count": wire_transport.pre_injection_completions,
                "transport_injection": wire_transport.injection,
                "audit_decision": decisions[-1] if decisions else None,
            },
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
        # G1 must reject a foreign host before any evidence or pipeline access.
        before = (
            synthetic_backend_resolutions,
            synthetic_pipeline_constructions,
            synthetic_context_calls,
            protected_data_accesses,
            real_provider_calls,
            list(forbidden_accesses),
            list(external_calls),
        )
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://b1r.invalid",
        ) as client:
            rejected = await client.post(
                "/api/chat/query",
                json={
                    "prompt": "Explain a synthetic concept.",
                    "scope_type": "notebook",
                    "scope_id": "b1r-notebook",
                    "session_id": "b1r-success",
                    "requested_phase": "conceptual",
                },
            )
        assert rejected.status_code == 403, "G1 accepted a foreign host"
        assert rejected.headers.get("content-type", "").startswith("application/json")
        assert rejected.json() == {
            "detail": "Acceso permitido solo desde el entorno local de TALOS."
        }
        assert _parse_sse(rejected.text) == []
        assert before == (
            synthetic_backend_resolutions,
            synthetic_pipeline_constructions,
            synthetic_context_calls,
            protected_data_accesses,
            real_provider_calls,
            list(forbidden_accesses),
            list(external_calls),
        ), "G1 rejection reached evidence, backend, or pipeline"
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
