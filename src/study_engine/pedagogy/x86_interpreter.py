"""Micro-intérprete x86-64 determinista en Python puro (Fase B / Tipo 3).

Soporta el conjunto nuclear de 8 instrucciones para ejercicios de Trace Tables:
- MOV dst, src
- ADD dst, src
- SUB dst, src
- XOR dst, src
- CMP op1, op2
- PUSH src
- POP dst
- Saltos: JMP, JE/JZ, JNE/JNZ, JG, JL (y JGE, JLE)

Características:
- Registros de 64 bits (rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp, r8-r15)
- Subregistros de 32 bits (eax, ebx, ecx, edx, esi, edi, ebp, esp) con zero-extension
- Flags: ZF (Zero), SF (Sign), OF (Overflow)
- Stack de memoria plana hacia abajo desde DEFAULT_RSP = 0x7FFFFFFFE000
- Límite estricto de MAX_STEPS = 100 para evitar bucles infinitos
- Generación de tabla de traza paso a paso (step-by-step trace table)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple, Union

DEFAULT_RSP = 0x7FFFFFFFE000
MAX_STEPS = 100

REG64 = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
         "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15")

REG32_MAP = {
    "eax": "rax", "ebx": "rbx", "ecx": "rcx", "edx": "rdx",
    "esi": "rsi", "edi": "rdi", "ebp": "rbp", "esp": "rsp",
    "r8d": "r8", "r9d": "r9", "r10d": "r10", "r11d": "r11",
    "r12d": "r12", "r13d": "r13", "r14d": "r14", "r15d": "r15",
}

_MASK64 = 0xFFFFFFFFFFFFFFFF
_SIGN64 = 1 << 63
_MASK32 = 0xFFFFFFFF
_SIGN32 = 1 << 31


class X86Interpreter:
    """Micro-intérprete x86-64 determinista."""

    def __init__(self, initial_registers: Optional[Dict[str, int]] = None) -> None:
        self.registers: Dict[str, int] = {r: 0 for r in REG64}
        self.registers["rsp"] = DEFAULT_RSP
        self.registers["rbp"] = DEFAULT_RSP
        if initial_registers:
            for k, v in initial_registers.items():
                self.set_register(k, v)

        self.flags: Dict[str, int] = {"ZF": 0, "SF": 0, "OF": 0}
        self.memory: Dict[int, int] = {}  # byte-addressed flat memory
        self.trace: List[Dict[str, Any]] = []
        self.step_count = 0

    def get_register(self, name: str) -> int:
        name_low = name.lower()
        if name_low in REG32_MAP:
            parent = REG32_MAP[name_low]
            return self.registers[parent] & _MASK32
        if name_low in self.registers:
            return self.registers[name_low] & _MASK64
        raise ValueError(f"Registro desconocido: {name}")

    def set_register(self, name: str, value: int) -> None:
        name_low = name.lower()
        if name_low in REG32_MAP:
            parent = REG32_MAP[name_low]
            # En x86-64, escribir a subregistro de 32 bits limpia los 32 bits altos (zero-extension)
            self.registers[parent] = value & _MASK32
            return
        if name_low in self.registers:
            self.registers[name_low] = value & _MASK64
            return
        raise ValueError(f"Registro desconocido: {name}")

    def read_mem(self, addr: int, size: int = 8) -> int:
        val = 0
        for i in range(size):
            b = self.memory.get(addr + i, 0)
            val |= (b << (8 * i))
        return val

    def write_mem(self, addr: int, value: int, size: int = 8) -> None:
        for i in range(size):
            self.memory[addr + i] = (value >> (8 * i)) & 0xFF

    def _parse_mem_operand(self, op: str) -> Tuple[int, int]:
        """Devuelve (dirección_efectiva, tamaño_bytes)."""
        op_low = op.lower().strip()
        size = 8
        if "dword ptr" in op_low:
            size = 4
        elif "qword ptr" in op_low:
            size = 8

        match = re.search(r"\[\s*([a-z0-9]+)\s*(?:([+-])\s*([0-9a-fx]+))?\s*\]", op_low)
        if not match:
            raise ValueError(f"Operando de memoria inválido: {op}")
        base_reg = match.group(1)
        base_addr = self.get_register(base_reg)
        sign = match.group(2)
        offset_str = match.group(3)
        offset = 0
        if offset_str:
            offset = int(offset_str, 0)
            if sign == "-":
                offset = -offset
        return (base_addr + offset) & _MASK64, size

    def eval_operand(self, op: str, default_size: int = 8) -> int:
        op_str = op.strip()
        if op_str.startswith("[") or "ptr [" in op_str.lower():
            addr, size = self._parse_mem_operand(op_str)
            return self.read_mem(addr, size=size)
        op_low = op_str.lower()
        if op_low in self.registers or op_low in REG32_MAP:
            return self.get_register(op_low)
        # Inmediato (decimal o hex)
        return int(op_str, 0)

    def write_dest(self, dst: str, value: int, default_size: int = 8) -> None:
        dst_str = dst.strip()
        if dst_str.startswith("[") or "ptr [" in dst_str.lower():
            addr, size = self._parse_mem_operand(dst_str)
            self.write_mem(addr, value, size=size)
        else:
            self.set_register(dst_str, value)

    def _determine_size(self, op1: str, op2: Optional[str] = None) -> int:
        for op in (op1, op2):
            if not op:
                continue
            op_low = op.strip().lower()
            if "dword ptr" in op_low or op_low in REG32_MAP:
                return 4
        return 8

    def _set_flags_add(self, a: int, b: int, res: int, size: int) -> None:
        mask = _MASK32 if size == 4 else _MASK64
        sign_bit = _SIGN32 if size == 4 else _SIGN64
        a_val = a & mask
        b_val = b & mask
        r_val = res & mask

        self.flags["ZF"] = 1 if r_val == 0 else 0
        self.flags["SF"] = 1 if (r_val & sign_bit) != 0 else 0
        a_sign = (a_val & sign_bit) != 0
        b_sign = (b_val & sign_bit) != 0
        r_sign = (r_val & sign_bit) != 0
        self.flags["OF"] = 1 if (a_sign == b_sign and a_sign != r_sign) else 0

    def _set_flags_sub(self, a: int, b: int, res: int, size: int) -> None:
        mask = _MASK32 if size == 4 else _MASK64
        sign_bit = _SIGN32 if size == 4 else _SIGN64
        a_val = a & mask
        b_val = b & mask
        r_val = res & mask

        self.flags["ZF"] = 1 if r_val == 0 else 0
        self.flags["SF"] = 1 if (r_val & sign_bit) != 0 else 0
        a_sign = (a_val & sign_bit) != 0
        b_sign = (b_val & sign_bit) != 0
        r_sign = (r_val & sign_bit) != 0
        self.flags["OF"] = 1 if (a_sign != b_sign and a_sign != r_sign) else 0

    def _set_flags_logic(self, res: int, size: int) -> None:
        mask = _MASK32 if size == 4 else _MASK64
        sign_bit = _SIGN32 if size == 4 else _SIGN64
        r_val = res & mask
        self.flags["ZF"] = 1 if r_val == 0 else 0
        self.flags["SF"] = 1 if (r_val & sign_bit) != 0 else 0
        self.flags["OF"] = 0

    def execute_program(self, asm_code: str) -> Dict[str, Any]:
        """Ejecuta un bloque de código ensamblador y retorna la traza completa."""
        lines = [line.strip() for line in asm_code.splitlines()]
        instructions: List[Tuple[str, List[str], str]] = []
        labels: Dict[str, int] = {}

        for line in lines:
            cleaned = re.split(r"[;#/]", line)[0].strip()
            if not cleaned:
                continue

            if ":" in cleaned:
                lbl, rest = cleaned.split(":", 1)
                labels[lbl.strip().lower()] = len(instructions)
                cleaned = rest.strip()
                if not cleaned:
                    continue

            parts = cleaned.split(None, 1)
            mnemonic = parts[0].upper()
            args = [a.strip() for a in parts[1].split(",")] if len(parts) > 1 else []
            instructions.append((mnemonic, args, cleaned))

        pc = 0
        self.step_count = 0
        self.trace = []

        while pc < len(instructions) and self.step_count < MAX_STEPS:
            mnemonic, args, raw_line = instructions[pc]
            next_pc = pc + 1

            if mnemonic == "MOV":
                dst, src = args[0], args[1]
                size = self._determine_size(dst, src)
                val = self.eval_operand(src, default_size=size)
                self.write_dest(dst, val, default_size=size)

            elif mnemonic == "ADD":
                dst, src = args[0], args[1]
                size = self._determine_size(dst, src)
                mask = _MASK32 if size == 4 else _MASK64
                v1 = self.eval_operand(dst, default_size=size)
                v2 = self.eval_operand(src, default_size=size)
                res = (v1 + v2) & mask
                self._set_flags_add(v1, v2, res, size)
                self.write_dest(dst, res, default_size=size)

            elif mnemonic == "SUB":
                dst, src = args[0], args[1]
                size = self._determine_size(dst, src)
                mask = _MASK32 if size == 4 else _MASK64
                v1 = self.eval_operand(dst, default_size=size)
                v2 = self.eval_operand(src, default_size=size)
                res = (v1 - v2) & mask
                self._set_flags_sub(v1, v2, res, size)
                self.write_dest(dst, res, default_size=size)

            elif mnemonic == "CMP":
                op1, op2 = args[0], args[1]
                size = self._determine_size(op1, op2)
                mask = _MASK32 if size == 4 else _MASK64
                v1 = self.eval_operand(op1, default_size=size)
                v2 = self.eval_operand(op2, default_size=size)
                res = (v1 - v2) & mask
                self._set_flags_sub(v1, v2, res, size)

            elif mnemonic == "XOR":
                dst, src = args[0], args[1]
                size = self._determine_size(dst, src)
                mask = _MASK32 if size == 4 else _MASK64
                v1 = self.eval_operand(dst, default_size=size)
                v2 = self.eval_operand(src, default_size=size)
                res = (v1 ^ v2) & mask
                self._set_flags_logic(res, size)
                self.write_dest(dst, res, default_size=size)

            elif mnemonic == "PUSH":
                src = args[0]
                val = self.eval_operand(src, default_size=8)
                rsp = (self.get_register("rsp") - 8) & _MASK64
                self.set_register("rsp", rsp)
                self.write_mem(rsp, val, size=8)

            elif mnemonic == "POP":
                dst = args[0]
                rsp = self.get_register("rsp")
                val = self.read_mem(rsp, size=8)
                self.set_register("rsp", (rsp + 8) & _MASK64)
                self.write_dest(dst, val, default_size=8)

            elif mnemonic == "JMP":
                target = args[0].lower()
                if target in labels:
                    next_pc = labels[target]

            elif mnemonic in ("JE", "JZ"):
                if self.flags["ZF"] == 1:
                    target = args[0].lower()
                    if target in labels:
                        next_pc = labels[target]

            elif mnemonic in ("JNE", "JNZ"):
                if self.flags["ZF"] == 0:
                    target = args[0].lower()
                    if target in labels:
                        next_pc = labels[target]

            elif mnemonic == "JG":
                if self.flags["ZF"] == 0 and (self.flags["SF"] == self.flags["OF"]):
                    target = args[0].lower()
                    if target in labels:
                        next_pc = labels[target]

            elif mnemonic == "JL":
                if self.flags["SF"] != self.flags["OF"]:
                    target = args[0].lower()
                    if target in labels:
                        next_pc = labels[target]

            elif mnemonic == "JGE":
                if self.flags["SF"] == self.flags["OF"]:
                    target = args[0].lower()
                    if target in labels:
                        next_pc = labels[target]

            elif mnemonic == "JLE":
                if self.flags["ZF"] == 1 or (self.flags["SF"] != self.flags["OF"]):
                    target = args[0].lower()
                    if target in labels:
                        next_pc = labels[target]

            else:
                raise ValueError(f"Instrucción no soportada por el micro-intérprete: {mnemonic}")

            self.step_count += 1
            entry = {
                "step": self.step_count,
                "pc": pc,
                "instruction": raw_line,
                "registers": {r: self.registers[r] for r in ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp")},
                "flags": dict(self.flags),
            }
            self.trace.append(entry)
            pc = next_pc

        return {
            "steps_executed": self.step_count,
            "terminated_by_limit": (self.step_count >= MAX_STEPS),
            "final_registers": {r: self.registers[r] for r in ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp")},
            "final_flags": dict(self.flags),
            "trace": self.trace,
        }
