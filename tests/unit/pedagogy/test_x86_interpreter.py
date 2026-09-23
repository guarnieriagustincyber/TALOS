"""Tests unitarios para el micro-intérprete x86-64 y ejercicios de Trace Table (Fase B / A3)."""

import pytest

from study_engine.pedagogy.generated_registry import GeneratedOracleGrader
from study_engine.pedagogy.state_predictor import (
    generate_trace_exercise,
    generate_x86_trace_exercise,
)
from study_engine.pedagogy.x86_interpreter import (
    DEFAULT_RSP,
    MAX_STEPS,
    X86Interpreter,
)


def test_x86_mov_and_32bit_zero_extension():
    interp = X86Interpreter()
    code = """
    mov rax, 0x1122334455667788
    mov eax, 42
    mov rbx, rax
    """
    res = interp.execute_program(code)
    # En x86-64, escribir a eax limpia la mitad superior de rax (zero extension)
    assert res["final_registers"]["rax"] == 42
    assert res["final_registers"]["rbx"] == 42


def test_x86_add_sub_flags():
    interp = X86Interpreter()
    code = """
    mov rax, 10
    mov rbx, 15
    add rax, rbx
    sub rax, 25
    """
    res = interp.execute_program(code)
    assert res["final_registers"]["rax"] == 0
    assert res["final_flags"]["ZF"] == 1
    assert res["final_flags"]["SF"] == 0


def test_x86_cmp_and_conditional_jumps():
    interp = X86Interpreter()
    # Contador descendente con bucle
    code = """
    mov rcx, 3
    mov rax, 0
    bucle:
    add rax, 10
    sub rcx, 1
    cmp rcx, 0
    jg bucle
    """
    res = interp.execute_program(code)
    assert res["final_registers"]["rcx"] == 0
    assert res["final_registers"]["rax"] == 30
    assert res["final_flags"]["ZF"] == 1


def test_x86_push_pop_and_stack_memory():
    interp = X86Interpreter()
    code = """
    mov rax, 0xCAFE
    mov rbx, 0xBABE
    push rax
    push rbx
    pop rcx
    pop rdx
    """
    res = interp.execute_program(code)
    assert res["final_registers"]["rcx"] == 0xBABE
    assert res["final_registers"]["rdx"] == 0xCAFE
    assert res["final_registers"]["rsp"] == DEFAULT_RSP


def test_x86_xor_logic_flags():
    interp = X86Interpreter()
    code = """
    mov rax, 0x1234
    xor rax, rax
    """
    res = interp.execute_program(code)
    assert res["final_registers"]["rax"] == 0
    assert res["final_flags"]["ZF"] == 1
    assert res["final_flags"]["SF"] == 0
    assert res["final_flags"]["OF"] == 0


def test_x86_max_step_limit_loop_infinito():
    interp = X86Interpreter()
    code = """
    mov rax, 0
    inf_loop:
    add rax, 1
    jmp inf_loop
    """
    res = interp.execute_program(code)
    assert res["steps_executed"] == MAX_STEPS
    assert res["terminated_by_limit"] is True
    # 1 mov + 49 * (add + jmp) + 1 add = 100 pasos ejecutados => rax == 50
    assert res["final_registers"]["rax"] == 50


def test_x86_trace_exercise_generation_and_grading():
    ex = generate_x86_trace_exercise("x86_architecture", seed=42)
    assert ex is not None
    assert ex["kind"] == "trace"
    assert "oracle" in ex
    assert ex["oracle"]["type"] == "state_match"

    grader = GeneratedOracleGrader()
    final_state = ex["oracle"]["final_state"]

    # Construir respuesta canónica exacta
    ans_parts = [f"{k}={v}" for k, v in final_state.items()]
    ans = ", ".join(ans_parts)
    eval_res = grader.grade(ans, ex["oracle"])
    assert eval_res["is_correct"] is True

    # Construir respuesta con valores hexadecimales
    hex_parts = [f"{k}={hex(v)}" if isinstance(v, int) else f"{k}={v}" for k, v in final_state.items()]
    eval_hex = grader.grade(", ".join(hex_parts), ex["oracle"])
    assert eval_hex["is_correct"] is True

    # Respuesta errónea
    wrong_parts = [f"{k}={v + 1}" if isinstance(v, int) else f"{k}=wrong" for k, v in final_state.items()]
    eval_bad = grader.grade(", ".join(wrong_parts), ex["oracle"])
    assert eval_bad["is_correct"] is False


def test_generate_trace_dispatch_by_kc_or_arch():
    # Dispatch automático por token en kc_id
    ex_x86 = generate_trace_exercise("arquitectura_x86_registros", seed=10)
    assert "x86-64" in ex_x86["prompt"]

    # Dispatch explícito por parámetro arch
    ex_x86_explicit = generate_trace_exercise("punteros", arch="x86", seed=10)
    assert "x86-64" in ex_x86_explicit["prompt"]

    # Dispatch por defecto a C
    ex_c = generate_trace_exercise("punteros_basico", seed=10)
    assert "int *p = &x;" in ex_c["code"]
