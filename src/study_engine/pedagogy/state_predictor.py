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


def generate_x86_trace_exercise(
    kc_id: str,
    seed: Optional[int] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    """Genera un ejercicio de predicción de estado en x86-64 con micro-intérprete."""
    from study_engine.pedagogy.x86_interpreter import X86Interpreter

    rng = random.Random(seed)
    archetype = rng.choice(["arithmetic", "loop", "stack"])

    if archetype == "arithmetic":
        a = rng.randint(5, 20)
        b = rng.randint(2, 8)
        code = (
            f"mov rax, {a}\n"
            f"mov rbx, {b}\n"
            "add rax, rbx\n"
            "sub rbx, 1\n"
            "xor rcx, rcx\n"
            "cmp rax, 20"
        )
        target_vars = ["rax", "rbx", "rcx", "ZF"]

    elif archetype == "loop":
        iters = rng.randint(2, 4)
        step = rng.randint(2, 5)
        code = (
            f"mov rcx, {iters}\n"
            "mov rax, 0\n"
            "loop_body:\n"
            f"add rax, {step}\n"
            "sub rcx, 1\n"
            "cmp rcx, 0\n"
            "jg loop_body"
        )
        target_vars = ["rax", "rcx", "ZF"]

    else:  # stack
        val1 = rng.randint(10, 50)
        val2 = rng.randint(60, 99)
        code = (
            f"mov rax, {val1}\n"
            f"mov rbx, {val2}\n"
            "push rax\n"
            "push rbx\n"
            "pop rax\n"
            "pop rbx"
        )
        target_vars = ["rax", "rbx"]

    interp = X86Interpreter()
    exec_res = interp.execute_program(code)
    final_regs = exec_res["final_registers"]
    final_flags = exec_res["final_flags"]

    final_state: Dict[str, Any] = {}
    for var in target_vars:
        if var in final_regs:
            final_state[var] = final_regs[var]
        elif var in final_flags:
            final_state[var] = final_flags[var]

    fmt_targets = ", ".join(f"{v}=<valor>" for v in target_vars)
    prompt = (
        "### Predicción de Estado x86-64 (Trace-Table)\n\n"
        "Simulá mentalmente la ejecución de este bloque de ensamblador x86-64:\n\n"
        f"```assembly\n{code}\n```\n\n"
        f"**Respondé en formato `{fmt_targets}`** "
        "(podés escribir los valores en decimal o hexadecimal con prefijo `0x`)."
    )

    ex_id = "gen_x86_" + hashlib.sha256((kc_id + "|" + code).encode()).hexdigest()[:12]

    return {
        "exercise_id": ex_id,
        "kind": "trace",
        "kc_ids": [kc_id],
        "prompt": prompt,
        "oracle": {
            "type": "state_match",
            "final_state": final_state,
            "architecture": "x86-64",
        },
        "difficulty": difficulty or "intermedio",
        "code": code,
        "solution_trace": exec_res["trace"],
    }


def generate_trace_exercise(
    kc_id: str,
    seed: Optional[int] = None,
    n_mutations: int = 2,
    difficulty: Optional[str] = None,
    arch: Optional[str] = None,
) -> Dict[str, Any]:
    """Genera un ejercicio de predicción de estado con oráculo determinista."""
    arch_req = (arch or "").lower()
    kc_low = (kc_id or "").lower()
    if arch_req == "x86" or any(tok in kc_low for tok in ("x86", "asm", "assembly", "ensamblador", "abi")):
        return generate_x86_trace_exercise(kc_id, seed=seed, difficulty=difficulty)

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
