"""Linux process and filesystem boundary for Quality Gate workers."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Mapping, Sequence


class IsolationError(RuntimeError):
    """Raised when the Quality Gate process boundary cannot be established."""


PROTECTED_DIRECTORIES = (
    "data/student",
    "data/web_state",
    "data/student_submissions",
    "student",
    "web_state",
)

_PRUNED_DIRECTORIES = {
    ".git",
    ".venv",
    "node_modules",
    "graphify-out",
}
_DATABASE_SUFFIXES = (
    ".db",
    ".db-wal",
    ".db-shm",
    ".db-journal",
    ".sqlite",
    ".sqlite3",
    ".sqlite-wal",
    ".sqlite3-wal",
    ".sqlite-shm",
    ".sqlite3-shm",
    ".sqlite-journal",
    ".sqlite3-journal",
)
_SANDBOX_REPOSITORY = "/workspace/repository"
_SANDBOX_WORKSPACE = "/workspace/run"
_SANDBOX_VENV = "/opt/talos-venv"
_ENVIRONMENT_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")


def _is_database_file(name: str) -> bool:
    lowered = name.lower()
    return lowered.endswith(_DATABASE_SUFFIXES) or ".db.bak" in lowered


def _raise_walk_error(error: OSError) -> None:
    raise IsolationError(f"Cannot inspect filesystem path: {error}")


def _validate_mount_roots(repository_root: Path, workspace_root: Path) -> None:
    repository_root = repository_root.resolve(strict=True)
    if workspace_root.is_symlink():
        raise IsolationError("Quality Gate workspace must not be a symlink")
    try:
        workspace_root = workspace_root.resolve(strict=True)
    except OSError as exc:
        raise IsolationError(
            f"Quality Gate workspace is unavailable: {exc}"
        ) from exc
    if not workspace_root.is_dir():
        raise IsolationError("Quality Gate workspace must be a directory")
    if not workspace_root.is_relative_to(Path("/tmp")):
        raise IsolationError(
            "Writable Quality Gate workspace must be under /tmp"
        )
    if workspace_root == repository_root or workspace_root.is_relative_to(
        repository_root
    ):
        raise IsolationError(
            "Writable Quality Gate workspace cannot be inside the repository"
        )
    if repository_root.is_relative_to(workspace_root):
        raise IsolationError(
            "Quality Gate workspace cannot contain the repository"
        )


def workspace_guest_path(workspace_root: Path, host_path: Path) -> Path:
    """Map a path inside the host workspace to its Bubblewrap guest path."""
    workspace_root = Path(workspace_root).resolve(strict=True)
    host_path = Path(host_path).resolve(strict=True)
    try:
        relative_path = host_path.relative_to(workspace_root)
    except ValueError as exc:
        raise IsolationError(
            "Guest workspace path must be inside the host workspace"
        ) from exc
    return Path(_SANDBOX_WORKSPACE) / relative_path


def _paths_to_mask(repository_root: Path) -> list[Path]:
    protected_file_identities: set[tuple[int, int]] = set()
    for relative in PROTECTED_DIRECTORIES:
        protected_root = repository_root / relative
        if protected_root.is_symlink():
            raise IsolationError(
                f"Protected path cannot be a symlink: {relative}"
            )
        if not protected_root.exists():
            continue
        if not protected_root.is_dir():
            raise IsolationError(
                f"Protected path must be a real directory: {relative}"
            )
        for current, directory_names, filenames in os.walk(
            protected_root, followlinks=False, onerror=_raise_walk_error
        ):
            current_path = Path(current)
            directory_names[:] = [
                name
                for name in directory_names
                if not (current_path / name).is_symlink()
            ]
            for filename in filenames:
                path = current_path / filename
                if path.is_symlink():
                    continue
                try:
                    metadata = path.stat()
                except OSError as exc:
                    raise IsolationError(
                        f"Cannot inspect protected path {path}: {exc}"
                    ) from exc
                if stat.S_ISREG(metadata.st_mode):
                    protected_file_identities.add(
                        (metadata.st_dev, metadata.st_ino)
                    )

    protected_roots = tuple(
        (repository_root / relative).resolve()
        for relative in PROTECTED_DIRECTORIES
        if (repository_root / relative).exists()
    )
    masked_paths: list[Path] = []
    for current, directory_names, filenames in os.walk(
        repository_root, followlinks=False, onerror=_raise_walk_error
    ):
        current_path = Path(current)
        directory_names[:] = [
            name
            for name in directory_names
            if name not in _PRUNED_DIRECTORIES
            and not any(
                (current_path / name).resolve() == root
                or (current_path / name).resolve().is_relative_to(root)
                for root in protected_roots
            )
        ]
        for filename in filenames:
            path = current_path / filename
            if path.is_symlink():
                continue
            try:
                metadata = path.stat()
            except OSError as exc:
                raise IsolationError(
                    f"Cannot inspect repository path {path}: {exc}"
                ) from exc
            is_protected_alias = (
                metadata.st_dev,
                metadata.st_ino,
            ) in protected_file_identities
            if stat.S_ISREG(metadata.st_mode) and (
                _is_database_file(filename) or is_protected_alias
            ):
                masked_paths.append(path.relative_to(repository_root))
    return masked_paths


def _runtime_command(
    command: Sequence[str], python_executable: str | Path | None
) -> tuple[list[str], Path | None]:
    if not command:
        raise IsolationError("Sandbox command must not be empty")
    executable = Path(python_executable or sys.executable)
    if not executable.is_absolute():
        raise IsolationError("Sandbox Python executable must be absolute")

    virtual_environment = Path(sys.prefix)
    if virtual_environment != Path(sys.base_prefix):
        try:
            relative_executable = executable.relative_to(virtual_environment)
        except ValueError:
            pass
        else:
            return [
                str(Path(_SANDBOX_VENV) / relative_executable),
                *command[1:],
            ], virtual_environment

    resolved_executable = executable.resolve()
    if not resolved_executable.is_relative_to(Path("/usr")):
        raise IsolationError(
            "Sandbox Python must be in the system runtime or active virtual "
            "environment"
        )
    return [str(resolved_executable), *command[1:]], None


def run_isolated_process(
    repository_root: Path,
    workspace_root: Path,
    command: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
    additional_writable_mounts: Sequence[tuple[Path, str]] = (),
    python_executable: str | Path | None = None,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a child with only the repository, workspace, and OS exposed."""
    repository_root = Path(repository_root).resolve(strict=True)
    workspace_root = Path(workspace_root)
    _validate_mount_roots(repository_root, workspace_root)
    workspace_root = workspace_root.resolve(strict=True)

    bubblewrap = shutil.which("bwrap")
    if bubblewrap is None:
        raise IsolationError(
            "bubblewrap is unavailable; refusing to launch pytest without "
            "process isolation"
        )

    runtime_command, virtual_environment = _runtime_command(
        command, python_executable
    )
    child_environment = {
        "HOME": f"{_SANDBOX_WORKSPACE}/home",
        "PATH": (
            f"{_SANDBOX_VENV}/bin:/usr/local/bin:/usr/bin:/bin"
            if virtual_environment is not None
            else "/usr/local/bin:/usr/bin:/bin"
        ),
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": (f"{_SANDBOX_REPOSITORY}:{_SANDBOX_REPOSITORY}/src"),
        "PYTHONUTF8": "1",
        "TMPDIR": "/tmp",
        "VIRTUAL_ENV": (
            _SANDBOX_VENV if virtual_environment is not None else ""
        ),
    }
    for name, value in (environment or {}).items():
        if not _ENVIRONMENT_NAME.fullmatch(name) or not isinstance(value, str):
            raise IsolationError(
                f"Invalid sandbox environment variable: {name}"
            )
        child_environment[name] = value

    with tempfile.TemporaryDirectory(prefix="talos-gate-masks-") as mask_value:
        mask_root = Path(mask_value)
        arguments = [
            bubblewrap,
            "--unshare-all",
            "--die-with-parent",
            "--new-session",
            "--clearenv",
            "--ro-bind",
            "/usr",
            "/usr",
        ]
        for system_path in ("/lib", "/lib64"):
            if Path(system_path).exists():
                arguments.extend(["--ro-bind", system_path, system_path])
        arguments.extend(["--symlink", "usr/bin", "/bin"])
        for system_file in (
            "/etc/ld.so.cache",
            "/etc/passwd",
            "/etc/group",
            "/etc/nsswitch.conf",
            "/etc/localtime",
        ):
            if Path(system_file).is_file():
                arguments.extend(["--ro-bind", system_file, system_file])
        if Path("/etc/ssl/certs").is_dir():
            arguments.extend(["--ro-bind", "/etc/ssl/certs", "/etc/ssl/certs"])

        arguments.extend(
            [
                "--proc",
                "/proc",
                "--dev",
                "/dev",
                "--tmpfs",
                "/tmp",
                "--dir",
                "/workspace",
                "--ro-bind",
                str(repository_root),
                _SANDBOX_REPOSITORY,
                "--bind",
                str(workspace_root.resolve()),
                _SANDBOX_WORKSPACE,
            ]
        )

        for host_path, sandbox_path in additional_writable_mounts:
            host_path = Path(host_path)
            if host_path.is_symlink():
                raise IsolationError(
                    "Additional writable mount must not be a symlink"
                )
            try:
                host_path = host_path.resolve(strict=True)
            except OSError as exc:
                raise IsolationError(
                    f"Additional writable mount is unavailable: {exc}"
                ) from exc
            if not host_path.is_dir() or not os.access(host_path, os.W_OK):
                raise IsolationError(
                    "Additional writable mount must be a writable directory"
                )
            if host_path.parent != Path("/tmp"):
                raise IsolationError(
                    "Additional writable mounts must be dedicated direct "
                    "children of /tmp"
                )
            if (
                host_path.is_relative_to(repository_root)
                or repository_root.is_relative_to(host_path)
                or host_path.is_relative_to(workspace_root)
                or workspace_root.is_relative_to(host_path)
            ):
                raise IsolationError(
                    "Additional writable mount cannot overlap the repository "
                    "or run workspace"
                )
            sandbox_path_value = Path(sandbox_path)
            if (
                not sandbox_path_value.is_absolute()
                or not sandbox_path_value.is_relative_to(_SANDBOX_WORKSPACE)
                or sandbox_path_value == Path(_SANDBOX_WORKSPACE)
            ):
                raise IsolationError(
                    "Additional writable mount must be inside the run "
                    "workspace"
                )
            arguments.extend(
                ["--bind", str(host_path), str(sandbox_path_value)]
            )

        if virtual_environment is not None:
            arguments.extend(
                [
                    "--dir",
                    "/opt",
                    "--ro-bind",
                    str(virtual_environment),
                    _SANDBOX_VENV,
                ]
            )

        for index, relative in enumerate(PROTECTED_DIRECTORIES):
            source = repository_root / relative
            if source.is_symlink():
                raise IsolationError(
                    f"Protected path cannot be a symlink: {relative}"
                )
            if not source.exists():
                continue
            if not source.is_dir():
                raise IsolationError(
                    f"Protected path must be a real directory: {relative}"
                )
            empty_directory = mask_root / f"protected-{index}"
            empty_directory.mkdir()
            arguments.extend(
                [
                    "--ro-bind",
                    str(empty_directory),
                    str(Path(_SANDBOX_REPOSITORY) / relative),
                ]
            )

        empty_file = mask_root / "empty"
        empty_file.touch()
        empty_file.chmod(0)
        empty_environment_file = mask_root / "empty-environment"
        empty_environment_file.touch()
        for relative in _paths_to_mask(repository_root):
            arguments.extend(
                [
                    "--ro-bind",
                    str(empty_file),
                    str(Path(_SANDBOX_REPOSITORY) / relative),
                ]
            )

        environment_file = repository_root / ".env"
        if environment_file.is_symlink():
            raise IsolationError("Repository .env cannot be a symlink")
        if environment_file.is_file():
            arguments.extend(
                [
                    "--ro-bind",
                    str(empty_environment_file),
                    f"{_SANDBOX_REPOSITORY}/.env",
                ]
            )
        for hidden_directory in (".git", ".venv"):
            source = repository_root / hidden_directory
            if source.is_symlink():
                raise IsolationError(
                    f"Repository {hidden_directory} cannot be a symlink"
                )
            if source.is_dir():
                empty_directory = mask_root / f"hidden-{hidden_directory}"
                empty_directory.mkdir()
                arguments.extend(
                    [
                        "--ro-bind",
                        str(empty_directory),
                        f"{_SANDBOX_REPOSITORY}/{hidden_directory}",
                    ]
                )

        for name, value in child_environment.items():
            arguments.extend(["--setenv", name, value])
        arguments.extend(
            ["--chdir", _SANDBOX_REPOSITORY, "--", *runtime_command]
        )

        try:
            return subprocess.run(
                arguments,
                cwd=tempfile.gettempdir(),
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
                close_fds=True,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise IsolationError(
                f"Cannot establish or complete the isolated process: {exc}"
            ) from exc
