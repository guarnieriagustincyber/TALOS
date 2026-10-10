"""Deterministic programming exercise auditor (Fase 0 y Ciberseguridad).

Evaluates:
1. Python syntax correctness (AST parsing)
2. Formal contract specification (PRE/POST)
3. Mermaid flowchart validity
4. Structured pseudocode with guard clauses
5. Test assertion execution in an isolated process sandbox
6. Big O complexity estimation
7. Clean code principles & type annotations
"""

import ast
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from study_engine.contracts.execution import EnvironmentPolicy
from study_engine.execution.env_sanitizer import build_sanitized_environment
from study_engine.execution.process_manager import run_managed_process_group
from study_engine.pedagogy.auditors.base_auditor import (
    AuditCheck,
    BaseExerciseAuditor,
    ExerciseAuditReport,
)
from study_engine.pedagogy.submission_reader import StudentSubmission

_MAX_EXECUTION_INPUT_BYTES = 1_048_576
_MAX_EXECUTION_OUTPUT_BYTES = 16_384
_EXECUTION_TIMEOUT_SECONDS = 3
_EXECUTION_MEMORY_LIMIT_BYTES = 536_870_912
_EXECUTION_FILE_LIMIT_BYTES = 1_048_576
_MAX_CONCURRENT_AUDITS = 1
_EXECUTION_PROCESS_LIMIT = 1
# One runner keeps aggregate user virtual address space within the per-run cap.
_AUDIT_SLOT_DIRECTORY = (
    Path(tempfile.gettempdir()) / f"talos-auditor-slots-{os.getuid()}"
)


def _acquire_audit_slot() -> Optional[int]:
    """Acquire the single host-local audit slot, or return None when occupied."""
    _AUDIT_SLOT_DIRECTORY.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory_stat = _AUDIT_SLOT_DIRECTORY.lstat()
    if (
        not stat.S_ISDIR(directory_stat.st_mode)
        or directory_stat.st_uid != os.getuid()
        or stat.S_IMODE(directory_stat.st_mode) != 0o700
    ):
        raise OSError("Audit slot directory is not private to the current user.")

    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    for slot in range(_MAX_CONCURRENT_AUDITS):
        lock_path = _AUDIT_SLOT_DIRECTORY / f"slot-{slot}.lock"
        descriptor = os.open(lock_path, flags, 0o600)
        try:
            lock_stat = os.fstat(descriptor)
            if (
                not stat.S_ISREG(lock_stat.st_mode)
                or lock_stat.st_uid != os.getuid()
                or stat.S_IMODE(lock_stat.st_mode) != 0o600
            ):
                raise OSError("Audit slot lock is not a private regular file.")
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return descriptor
        except BlockingIOError:
            os.close(descriptor)
        except OSError:
            os.close(descriptor)
            raise
    return None

_EXECUTION_RUNNER = r"""
import json
import re
import sys

def safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name in ("typing", "math", "socket"):
        return __import__(name, globals, locals, fromlist, level)
    raise ImportError("Import not allowed: " + name)

payload = json.loads(sys.stdin.read())
print("__TALOS_SANDBOX_READY__", flush=True)
safe_globals = {
    "__builtins__": {
        "__build_class__": __build_class__,
        "__import__": safe_import,
        "__name__": "__main__",
        "range": range,
        "len": len,
        "int": int,
        "float": float,
        "str": str,
        "bool": bool,
        "list": list,
        "dict": dict,
        "set": set,
        "tuple": tuple,
        "print": print,
        "open": open,
        "isinstance": isinstance,
        "issubclass": issubclass,
        "min": min,
        "max": max,
        "sum": sum,
        "abs": abs,
        "ord": ord,
        "chr": chr,
        "round": round,
        "all": all,
        "any": any,
        "sorted": sorted,
        "reversed": reversed,
        "enumerate": enumerate,
        "zip": zip,
        "AssertionError": AssertionError,
        "MemoryError": MemoryError,
        "ValueError": ValueError,
        "TypeError": TypeError,
        "IndexError": IndexError,
        "KeyError": KeyError,
        "RecursionError": RecursionError,
        "Exception": Exception,
        "OSError": OSError,
    }
}

try:
    exec(compile(payload["code"], "<student_submission>", "exec"), safe_globals)
except Exception as exc:
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(2)

try:
    exec(compile(payload["tests"], "<student_tests>", "exec"), safe_globals)
except AssertionError as exc:
    print(f"AssertionError: {exc or 'assertion failed'}", file=sys.stderr)
    raise SystemExit(1)
except Exception as exc:
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(2)
"""


class ProgrammingExerciseAuditor(BaseExerciseAuditor):
    """Auditor for programming tasks across Fase 0 and systems engineering."""

    @staticmethod
    def _clean_code(text: str) -> str:
        """Strip markdown fences if code text contains them."""
        m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        return text.strip()

    def audit(self, submission: StudentSubmission) -> ExerciseAuditReport:
        checks: List[AuditCheck] = []
        observations: List[str] = []

        code_text = submission.get_code_block("python", index=0)
        if not code_text and submission.has_section("codigo_python"):
            code_text = self._clean_code(submission.get_section("codigo_python"))

        # 1. Syntax check
        parsed_ast: Optional[ast.AST] = None
        if not code_text.strip():
            checks.append(AuditCheck("syntax", False, "No se encontró bloque de código Python ejecutable."))
        else:
            try:
                parsed_ast = ast.parse(code_text)
                checks.append(AuditCheck("syntax", True, "Sintaxis Python válida."))
            except SyntaxError as err:
                checks.append(AuditCheck("syntax", False, f"Error de sintaxis en línea {err.lineno}: {err.msg}"))

        # 2. Formal Contract check
        contract_text = (
            submission.get_section("contrato_formal")
            or submission.get_section("contrato")
            or submission.get_section("contrato_y_precondiciones")
        )
        if not contract_text:
            checks.append(AuditCheck("contract", False, "Falta la sección de Contrato Formal (PRE/POST)."))
        else:
            has_pre = bool(re.search(r"\bPRE\b", contract_text, re.IGNORECASE))
            has_post = bool(re.search(r"\bPOST\b", contract_text, re.IGNORECASE))
            if has_pre and has_post:
                checks.append(AuditCheck("contract", True, "Contrato Formal con precondiciones y postcondiciones explícitas."))
            else:
                checks.append(AuditCheck("contract", False, "El contrato formal debe especificar claramente tanto 'PRE:' como 'POST:'."))

        # 3. Mermaid Flowchart check
        mermaid_text = submission.get_code_block("mermaid") or submission.get_section("diagrama_de_flujo")
        if not mermaid_text:
            checks.append(AuditCheck("diagram", False, "Falta el Diagrama de Flujo en formato Mermaid.", severity="WARNING"))
        else:
            has_flow = any(token in mermaid_text.lower() for token in ["flowchart", "graph td", "graph lr"])
            if has_flow:
                checks.append(AuditCheck("diagram", True, "Diagrama de flujo Mermaid válido y estructurado."))
            else:
                checks.append(AuditCheck("diagram", False, "Diagrama Mermaid debe iniciar con 'flowchart TD' o 'graph TD'.", severity="WARNING"))

        # 4. Pseudocode check
        pseudocode_text = (
            submission.get_section("pseudocodigo")
            or submission.get_section("pseudocodigo_estructurado")
        )
        if not pseudocode_text:
            checks.append(AuditCheck("pseudocode", False, "Falta el diseño algorítmico en Pseudocódigo.", severity="WARNING"))
        else:
            has_structure = any(token in pseudocode_text.upper() for token in ["FUNCION", "FUNCIÓN", "SI", "MIENTRAS", "PARA", "RETORNAR"])
            if has_structure:
                checks.append(AuditCheck("pseudocode", True, "Pseudocódigo estructurado con palabras clave en español."))
            else:
                checks.append(AuditCheck("pseudocode", False, "El pseudocódigo debe usar estructuras de control claras (SI, MIENTRAS, RETORNAR).", severity="WARNING"))

        # 5. Type Annotations & Clean Code check
        if parsed_ast:
            func_defs = [n for n in ast.walk(parsed_ast) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if not func_defs:
                checks.append(AuditCheck("type_hints", False, "No se detectaron definiciones de funciones estructuradas.", severity="WARNING"))
            else:
                missing_hints = False
                for fn in func_defs:
                    for arg in fn.args.args:
                        if arg.arg != "self" and not arg.annotation:
                            missing_hints = True
                    if not fn.returns:
                        missing_hints = True

                if missing_hints:
                    checks.append(AuditCheck("type_hints", False, "Faltan Type Hints en parámetros o valor de retorno.", severity="WARNING"))
                    observations.append("Recomendación: Agregar anotaciones de tipo completas (ej: `def f(x: int) -> bool:`)")
                else:
                    checks.append(AuditCheck("type_hints", True, "Funciones con Type Hints completos y explícitos."))

        # 6. Big O Complexity estimation
        if parsed_ast:
            loop_depth = self._calculate_max_loop_depth(parsed_ast)
            if loop_depth == 0:
                est_complexity = "O(1)"
            elif loop_depth == 1:
                est_complexity = "O(n)"
            elif loop_depth == 2:
                est_complexity = "O(n^2)"
            else:
                est_complexity = f"O(n^{loop_depth})"
            checks.append(AuditCheck("complexity", True, f"Complejidad asintótica estimada: {est_complexity}", severity="INFO"))

        # 7. Deterministic Test Assertion Runner
        test_text = submission.get_code_block("python", index=1)
        if not test_text and submission.has_section("tests"):
            test_text = self._clean_code(submission.get_section("tests"))

        audit_execution_blocked = False
        if not test_text:
            checks.append(AuditCheck("tests", False, "No se encontraron casos de prueba o aserciones de test."))
        else:
            test_res = self._execute_tests_safe(code_text, test_text)
            if test_res["success"]:
                checks.append(AuditCheck("tests", True, f"Tests unitarios ejecutados exitosamente ({test_res['assertions_count']} aserciones aprobadas)."))
            elif test_res["execution_status"] == "concurrency_limit":
                audit_execution_blocked = True
                checks.append(
                    AuditCheck(
                        "tests",
                        False,
                        "Límite de auditorías simultáneas alcanzado; reintentá la verificación.",
                    )
                )
            else:
                checks.append(AuditCheck("tests", False, f"Falla en tests: {test_res['error']}"))

        # Compute Score
        total_evaluable = [c for c in checks if c.severity in ("ERROR", "WARNING")]
        passed_evaluable = [c for c in total_evaluable if c.passed]
        score = round((len(passed_evaluable) / len(total_evaluable) * 100.0), 1) if total_evaluable else 0.0
        is_passed = (
            not audit_execution_blocked
            and score >= 70.0
            and all(c.passed for c in checks if c.name == "syntax")
        )

        # BKT Update — with content-hash idempotency guard
        target_kc = submission.metadata.get("kc_id") or submission.exercise_id
        content_hash = hashlib.sha256(
            (submission.raw_content or "").encode("utf-8", errors="replace")
        ).hexdigest()
        if audit_execution_blocked:
            bkt_updated, p_before, p_after = False, None, None
        else:
            bkt_updated, p_before, p_after = self.update_bkt_if_eligible(
                target_kc, is_passed, score, content_hash=content_hash
            )

        return ExerciseAuditReport(
            exercise_id=submission.exercise_id,
            notebook_id=submission.metadata.get("notebook_id", "fase0-soc"),
            score=score,
            passed=is_passed,
            checks=checks,
            bkt_updated=bkt_updated,
            p_L_before=p_before,
            p_L_after=p_after,
            observations=observations,
            next_exercise=self._recommend_next_exercise(submission.exercise_id),
        )

    def _calculate_max_loop_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        max_d = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.For, ast.While)):
                d = self._calculate_max_loop_depth(child, current_depth + 1)
                if d > max_d:
                    max_d = d
            else:
                d = self._calculate_max_loop_depth(child, current_depth)
                if d > max_d:
                    max_d = d
        return max_d

    def _execute_tests_safe(self, code_str: str, test_str: str) -> Dict[str, Any]:
        """Execute student code in a mandatory Linux process and namespace sandbox."""
        payload = json.dumps({"code": code_str, "tests": test_str})
        if len(payload.encode("utf-8")) > _MAX_EXECUTION_INPUT_BYTES:
            return {
                "success": False,
                "assertions_count": 0,
                "error": "Execution input exceeds the 1 MiB limit.",
                "execution_status": "input_limit",
            }

        bubblewrap = shutil.which("bwrap")
        prlimit = shutil.which("prlimit")
        python_executable = Path(sys.executable).resolve()
        if (
            bubblewrap is None
            or prlimit is None
            or not python_executable.is_relative_to("/usr")
            or os.getuid() == 0
        ):
            return {
                "success": False,
                "assertions_count": 0,
                "error": "Required Linux sandbox infrastructure or unprivileged execution identity is unavailable.",
                "execution_status": "infrastructure_error",
            }

        sandbox_command = [
            bubblewrap,
            "--unshare-all",
            "--die-with-parent",
            "--uid",
            str(os.getuid()),
            "--gid",
            str(os.getgid()),
            "--ro-bind",
            "/usr",
            "/usr",
            "--ro-bind",
            "/lib",
            "/lib",
            "--ro-bind",
            "/lib64",
            "/lib64",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            "--tmpfs",
            "/tmp",
            "--dir",
            "/workspace",
            "--tmpfs",
            "/workspace",
            "--chdir",
            "/workspace",
            prlimit,
            f"--as={_EXECUTION_MEMORY_LIMIT_BYTES}",
            "--cpu=5:6",
            f"--fsize={_EXECUTION_FILE_LIMIT_BYTES}",
            f"--nproc={_EXECUTION_PROCESS_LIMIT}:{_EXECUTION_PROCESS_LIMIT}",
            "--",
            str(python_executable),
            "-I",
            "-c",
            _EXECUTION_RUNNER,
        ]
        command = sandbox_command
        environment = build_sanitized_environment(
            EnvironmentPolicy(allowed_names=()),
            host_env={},
        )

        try:
            slot_descriptor = _acquire_audit_slot()
        except OSError as exc:
            return {
                "success": False,
                "assertions_count": 0,
                "error": f"Audit concurrency control unavailable: {exc}",
                "execution_status": "infrastructure_error",
            }
        if slot_descriptor is None:
            return {
                "success": False,
                "assertions_count": 0,
                "error": "Maximum concurrent programming audits reached.",
                "execution_status": "concurrency_limit",
            }

        try:
            try:
                outcome = run_managed_process_group(
                    cmd=command,
                    cwd="/",
                    env=environment,
                    timeout_seconds=_EXECUTION_TIMEOUT_SECONDS,
                    max_output_bytes=_MAX_EXECUTION_OUTPUT_BYTES,
                    stdin_payload=payload,
                )
            except OSError as exc:
                return {
                    "success": False,
                    "assertions_count": 0,
                    "error": f"Sandbox infrastructure error: {exc}",
                    "execution_status": "infrastructure_error",
                }
        finally:
            os.close(slot_descriptor)

        error = outcome.streams.stderr.strip() or None
        if outcome.streams.truncated:
            error = f"{error or 'Execution output'} (truncated at {_MAX_EXECUTION_OUTPUT_BYTES} bytes)"
        sandbox_started = outcome.streams.stdout.startswith("__TALOS_SANDBOX_READY__")
        if not sandbox_started:
            execution_status = "infrastructure_error"
            error = error or "Sandbox process failed before starting the execution runner."
        elif outcome.timed_out:
            execution_status = "timeout"
        elif outcome.exit_code == 0:
            execution_status = "pass"
        elif outcome.exit_code == 1:
            execution_status = "assertion_failure"
        elif outcome.exit_code == 2:
            execution_status = "runtime_error"
        else:
            execution_status = "infrastructure_error"
            error = error or "Sandbox process exited unexpectedly."

        assert_count = len(re.findall(r"\bassert\b", test_str))
        return {
            "success": execution_status == "pass",
            "assertions_count": max(1, assert_count) if execution_status == "pass" else 0,
            "error": error,
            "execution_status": execution_status,
            "output_bytes_captured": outcome.streams.bytes_captured,
            "output_bytes_discarded": outcome.streams.bytes_discarded,
            "output_truncated": outcome.streams.truncated,
        }

    def _recommend_next_exercise(self, current_id: str) -> Optional[str]:
        cur = current_id.lower()
        if "ej_01" in cur:
            return "ej_02_pin_seguro"
        elif "ej_02" in cur:
            return "ej_03_calculo_direccion"
        elif "ej_07" in cur or "octeto" in cur:
            return "ej_08_aritmetica_punteros"
        return None
