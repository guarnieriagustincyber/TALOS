"""Tipo 3 (Fase 6): Predicción de estado (Trace-Tables).

Genera un mini-programa C sobre enteros + punteros y SIMULA la traza
determinísticamente. El oráculo es el estado final computado por el
simulador — idéntico a ejecutar el código real para este subconjunto de C.

Ops soportadas (subconjunto determinista):
    int x = <lit>;
    int *p = &x;
    x = x <op> <lit>;
    *p = *p <op> <lit>;   (escribe sobre x vía puntero)

El usuario debe predecir el estado final: valor de x, de *p, y a quién
apunta p (simbólico).
"""

from __future__ import annotations

import hashlib
import random
from typing import Any, Dict, List, Optional, Tuple

_OPS = ["+", "-"]


def _simulate(ops: List[Tuple[str, str, Any]], var_names: List[str]) -> Dict[str, int]:
    """Simula la traza sobre el mini-lenguaje. ops: (dst, op, src)."""
    state: Dict[str, Any] = {}
    pointers: Dict[str, str] = {}

    def resolve(ref: str, state: Dict[str, Any]) -> int:
        if ref.startswith("*"):
            target = pointers[ref[1:]]
            return state[target]
        return int(state[ref])

    def assign(target: str, value: int) -> None:
        if target.startswith("*"):
            pointee = pointers[target[1:]]
            state[pointee] = value
        else:
            state[target] = value

    for dst, op, src in ops:
        if op == ":=":  # literal/assign
            assign(dst, int(src))
        elif op == ":@":  # pointer to var
            pointers[dst[1:] if dst.startswith("*") else dst] = state[f"&{src}"] = src
        else:
            current = resolve(dst, state)
            val = int(src)
            result = current + val if op == "+" else current - val
            assign(dst, result)

    out: Dict[str, int] = {}
    for name, value in state.items():
        if name.startswith("&"):
            continue
        out[name] = value
    for ptr, target in pointers.items():
        out[f"*{ptr}"] = out[target]
        out[f"{ptr}_apunta_a"] = target
    return out


def generate_trace_exercise(
    kc_id: str,
    seed: Optional[int] = None,
    n_mutations: int = 2,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """Genera un ejercicio de predicción de estado con oráculo determinista."""
    rng = random.Random(seed)

    x0 = rng.randint(3, 17)
    ops: List[Tuple[str, str, Any]] = [
        ("x", ":=", x0),
        ("p", ":@", "x"),  # int *p = &x
    ]
    # Elegir mutaciones uniformes entre directa (x) e indirecta (*p)
    descs: List[str] = []
    for _ in range(n_mutations):
        dst = rng.choice(["x", "*p"])
        op = rng.choice(_OPS)
        val = rng.randint(1, 9)
        ops.append((dst, op, val))
        descs.append(f"    {dst} = {dst} {op} {val};")

    final = _simulate(ops, ["x", "p"])
    code_lines = [
        f"int x = {x0};",
        "int *p = &x;",
        *descs,
    ]
    code = "\n".join(code_lines)

    prompt = (
        "### Predicción de Estado (Trace-Table)\n\n"
        "Simulá mentalmente este fragmento:\n\n"
        f"```c\n{code}\n```\n\n"
        "**Respondé en formato `x=<valor>, *p=<valor>, p apunta a <var>`** "
        "(el oráculo compara valores con su variable; no valores sueltos)"
    )

    ex_id = "gen_trace_" + hashlib.sha256((kc_id + "|" + code).encode()).hexdigest()[:12]

    return {
        "exercise_id": ex_id,
        "kind": "trace",
        "kc_ids": [kc_id],
        "prompt": prompt,
        "oracle": {
            "type": "state_match",
            "final_state": {
                "x": final["x"],
                "*p": final["*p"],
            },
            "symbolic_fields": ["p_apunta_a"],
            "initial_state": {"x": x0, "p": "&x"},
        },
        "difficulty": difficulty or "basico",
        "code": code,
        "solution_trace": final,
    }
