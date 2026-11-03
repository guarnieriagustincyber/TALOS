"""Capture high-level Python audit events for synthetic A-PRE qualification."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from typing import Any

EFFECT_EVENTS = {
    "open",
    "os.listdir",
    "os.mkdir",
    "os.remove",
    "os.rename",
    "os.rmdir",
    "os.symlink",
    "os.link",
    "sqlite3.connect",
    "socket.__new__",
    "socket.bind",
    "socket.connect",
    "socket.getaddrinfo",
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.fork",
}
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND


def _path_value(value: Any) -> Path | None:
    if isinstance(value, bytes):
        try:
            value = os.fsdecode(value)
        except (UnicodeError, ValueError):
            return None
    if not isinstance(value, (str, os.PathLike)):
        return None
    try:
        return Path(value)
    except (TypeError, ValueError, OSError):
        return None


class EffectObserver:
    """Record Python audit events without claiming syscall coverage."""

    def __init__(self, repository_root: Path, scratch_root: Path) -> None:
        self.repository_root = repository_root.resolve()
        self.scratch_root = scratch_root.resolve()
        if not self.scratch_root.is_dir():
            raise ValueError("scratch root must be an existing directory")
        if self.scratch_root.is_relative_to(self.repository_root):
            raise ValueError("scratch root must be outside the repository")
        self.events: list[dict[str, Any]] = []
        self._case_id = threading.local()
        self._installed = False
        self._active = False

    def install(self) -> None:
        if self._installed:
            raise RuntimeError("effect observer is already installed")
        sys.addaudithook(self._audit)
        self._installed = True
        self._active = True
        self.set_case("pytest::startup-and-collection")

    def close(self) -> None:
        self._active = False
        self.set_case(None)

    def set_case(self, case_id: str | None) -> None:
        self._case_id.value = case_id

    def _classify_path(
        self, event: str, args: tuple[Any, ...]
    ) -> tuple[str, str | None, str]:
        raw_path = args[0] if args else None
        path = _path_value(raw_path)
        if path is None:
            return "UNKNOWN", None, "event path is unavailable or unsupported"
        if not path.is_absolute():
            path = Path.cwd() / path
        try:
            resolved = path.resolve(strict=False)
        except (OSError, RuntimeError, ValueError):
            return "UNKNOWN", str(path), "event path cannot be resolved"

        writes = event in {
            "open",
            "os.mkdir",
            "os.remove",
            "os.rename",
            "os.rmdir",
            "os.symlink",
            "os.link",
        }
        if event == "open":
            mode = args[1] if len(args) > 1 else None
            flags = args[2] if len(args) > 2 else None
            if isinstance(mode, str):
                writes = any(marker in mode for marker in ("w", "a", "x", "+"))
            elif isinstance(flags, int) and not isinstance(flags, bool):
                writes = bool(flags & WRITE_FLAGS)
            elif mode is not None or flags is not None:
                return (
                    "UNKNOWN",
                    str(resolved),
                    "open mode/flags are not interpretable",
                )
        if not writes and resolved.is_relative_to(self.repository_root):
            return "NONE", str(resolved), "read confined to repository inputs"
        if resolved.is_relative_to(self.scratch_root):
            return "TEMPORARY", str(resolved), "path confined to scratch root"
        return "REAL", str(resolved), "filesystem access outside scratch"

    def observe(
        self,
        event: str,
        args: tuple[Any, ...],
        *,
        case_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Classify one event for deterministic fixture tests."""
        if event not in EFFECT_EVENTS:
            return None
        if event in {
            "open",
            "os.listdir",
            "os.mkdir",
            "os.remove",
            "os.rename",
            "os.rmdir",
            "os.symlink",
            "os.link",
        }:
            if event in {"os.rename", "os.symlink", "os.link"}:
                if len(args) < 2:
                    status, path, reason = (
                        "UNKNOWN",
                        None,
                        "multi-path filesystem event has incomplete arguments",
                    )
                    paths = []
                else:
                    paths = [
                        self._classify_path(event, (argument,))
                        for argument in args[:2]
                    ]
                if paths:
                    statuses = {entry[0] for entry in paths}
                    if "UNKNOWN" in statuses:
                        status = "UNKNOWN"
                    elif "REAL" in statuses:
                        status = "REAL"
                    elif "TEMPORARY" in statuses:
                        status = "TEMPORARY"
                    else:
                        status = "NONE"
                    path = ";".join(entry[1] or "?" for entry in paths)
                    reason = (
                        "all paths considered for multi-path filesystem event"
                    )
            else:
                status, path, reason = self._classify_path(event, args)
        elif event == "sqlite3.connect":
            target = args[0] if args else None
            if target == ":memory:" or (
                isinstance(target, (str, bytes))
                and "mode=memory" in os.fsdecode(target)
            ):
                status, path, reason = (
                    "TEMPORARY",
                    str(target),
                    "SQLite database is explicitly in memory",
                )
            elif isinstance(target, (str, bytes, os.PathLike)):
                value = _path_value(target)
                if value is None:
                    status, path, reason = (
                        "UNKNOWN",
                        None,
                        "SQLite target is not interpretable",
                    )
                else:
                    if not value.is_absolute():
                        value = Path.cwd() / value
                    status, path, reason = (
                        "REAL",
                        str(value.resolve(strict=False)),
                        "SQLite database connection requested",
                    )
            else:
                status, path, reason = (
                    "UNKNOWN",
                    None,
                    "SQLite target is not interpretable",
                )
        else:
            status, path, reason = (
                "REAL",
                None,
                "network or process operation requested",
            )

        record = {
            "case_id": (
                case_id
                if case_id is not None
                else getattr(self._case_id, "value", None)
            ),
            "event": event,
            "classification": status,
            "path": path,
            "reason": reason,
        }
        self.events.append(record)
        return record

    def _audit(self, event: str, args: tuple[Any, ...]) -> None:
        if self._active:
            self.observe(event, args)

    def pytest_runtest_setup(self, item: Any) -> None:
        self.set_case(item.nodeid)

    def pytest_runtest_teardown(self, item: Any) -> None:
        del item
        self.set_case("pytest::between-cases")

    def report(self) -> dict[str, Any]:
        counts: dict[str, int] = {}
        for event in self.events:
            category = event["classification"]
            counts[category] = counts.get(category, 0) + 1
        incomplete_attribution = any(
            event["classification"] == "UNKNOWN" or event["case_id"] is None
            for event in self.events
        )
        return {
            "schema_version": 1,
            "coverage": {
                "python_audit_hooks": self._installed,
                "native_syscalls": False,
                "complete": False,
                "limitation": (
                    "Python audit events do not cover all native extension "
                    "syscalls; absence of events cannot certify sterility."
                ),
            },
            "event_count": len(self.events),
            "classification_counts": counts,
            "events": list(self.events),
            "overall_classification": (
                "UNKNOWN"
                if not self.events or incomplete_attribution
                else "OBSERVED"
            ),
        }

    def write_report(self, output_path: Path) -> None:
        output = output_path.resolve()
        if output.is_relative_to(self.repository_root):
            raise ValueError("effects report must be outside the repository")
        output.parent.mkdir(parents=True, exist_ok=True)
        encoded = (
            json.dumps(
                self.report(), ensure_ascii=False, indent=2, sort_keys=True
            )
            + "\n"
        )
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            delete=False,
        ) as stream:
            temporary_path = Path(stream.name)
            stream.write(encoded)
            stream.flush()
        try:
            temporary_path.replace(output)
        finally:
            if temporary_path.exists():
                temporary_path.unlink()
