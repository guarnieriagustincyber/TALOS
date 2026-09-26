"""Deterministic programming exercise auditor (Fase 0 y Ciberseguridad).

Evaluates:
1. Python syntax correctness (AST parsing)
2. Formal contract specification (PRE/POST)
3. Mermaid flowchart validity
4. Structured pseudocode with guard clauses
5. Test assertion execution in a safe in-memory execution sandbox
6. Big O complexity estimation
7. Clean code principles & type annotations
"""

import ast
import hashlib
import re
from typing import Any, Dict, List, Optional

from study_engine.pedagogy.auditors.base_auditor import (
    AuditCheck,
    BaseExerciseAuditor,
    ExerciseAuditReport,
)
from study_engine.pedagogy.submission_reader import StudentSubmission


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

        if not test_text:
            checks.append(AuditCheck("tests", False, "No se encontraron casos de prueba o aserciones de test."))
        else:
            test_res = self._execute_tests_safe(code_text, test_text)
            if test_res["success"]:
                checks.append(AuditCheck("tests", True, f"Tests unitarios ejecutados exitosamente ({test_res['assertions_count']} aserciones aprobadas)."))
            else:
                checks.append(AuditCheck("tests", False, f"Falla en tests: {test_res['error']}"))

        # Compute Score
        total_evaluable = [c for c in checks if c.severity in ("ERROR", "WARNING")]
        passed_evaluable = [c for c in total_evaluable if c.passed]
        score = round((len(passed_evaluable) / len(total_evaluable) * 100.0), 1) if total_evaluable else 0.0
        is_passed = score >= 70.0 and all(c.passed for c in checks if c.name == "syntax")

        # BKT Update — with content-hash idempotency guard
        target_kc = submission.metadata.get("kc_id") or submission.exercise_id
        content_hash = hashlib.sha256(
            (submission.raw_content or "").encode("utf-8", errors="replace")
        ).hexdigest()
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
        """Execute test assertions in an isolated in-memory Python scope."""
        combined_source = f"{code_str}\n\n{test_str}"

        def safe_import(name: str, globals=None, locals=None, fromlist=(), level=0):
            if name in ("typing", "math"):
                return __import__(name, globals, locals, fromlist, level)
            raise ImportError(f"Importación de '{name}' no permitida en sandbox de evaluación.")

        safe_globals: Dict[str, Any] = {
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
                "print": lambda *args: None,
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
                "ValueError": ValueError,
                "TypeError": TypeError,
                "IndexError": IndexError,
                "KeyError": KeyError,
                "RecursionError": RecursionError,
                "Exception": Exception,
            }
        }
        try:
            compiled = compile(combined_source, filename="<student_submission>", mode="exec")
            exec(compiled, safe_globals)
            # Count asserts
            assert_count = len(re.findall(r"\bassert\b", test_str))
            return {"success": True, "assertions_count": max(1, assert_count), "error": None}
        except AssertionError as exc:
            return {"success": False, "assertions_count": 0, "error": f"AssertionError: {exc or 'Condición de aserción no satisfecha'}"}
        except Exception as exc:
            return {"success": False, "assertions_count": 0, "error": f"{type(exc).__name__}: {str(exc)}"}

    def _recommend_next_exercise(self, current_id: str) -> Optional[str]:
        cur = current_id.lower()
        if "ej_01" in cur:
            return "ej_02_pin_seguro"
        elif "ej_02" in cur:
            return "ej_03_calculo_direccion"
        elif "ej_07" in cur or "octeto" in cur:
            return "ej_08_aritmetica_punteros"
        return None
