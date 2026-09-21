"""Canonical test payloads for Study Engine domain contracts.

These payloads represent minimal and full valid data structures
derived strictly from docs/01-SPEC-V1.0.md.
"""

from datetime import datetime, timezone
from typing import Any, Dict

CANONICAL_TIMESTAMP = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)
CANONICAL_TIMESTAMP_ISO = "2026-09-01T12:00:00Z"

CANONICAL_NOTEBOOK_MINIMAL: Dict[str, Any] = {
    "id": "fase_0_programacion",
    "name": "Fase 0 - Programación",
}

CANONICAL_NOTEBOOK_FULL: Dict[str, Any] = {
    "id": "materia_redes",
    "name": "Redes de Computadoras",
    "description": "Cuaderno de estudio para la materia Redes de Computadoras",
    "subject": "Redes",
    "sources": ["stallings-redes-7e", "tanenbaum-redes-5e"],
    "metadata": {"university": "FADENA", "year": 2026},
    "created_at": CANONICAL_TIMESTAMP,
    "updated_at": CANONICAL_TIMESTAMP,
}

CANONICAL_SOURCE_MINIMAL: Dict[str, Any] = {
    "source_id": "joyanes-fp-4e",
    "title": "Fundamentos de Programación",
}

CANONICAL_SOURCE_FULL: Dict[str, Any] = {
    "source_id": "joyanes-fp-4e",
    "title": "Fundamentos de Programación: Algoritmos, Estructura de Datos y Objetos",
    "author": "Luis Joyanes Aguilar",
    "type": "book",
    "language": "es",
    "role": "PRIMARY",
    "priority": 1,
    "subject": "Programación",
    "course": "Fase-0",
    "phase": "Fase-0",
    "chapter": "Capítulo 1",
    "section": "1.4",
    "page": 24,
    "metadata": {"publisher": "McGraw-Hill", "edition": "4ta"},
}

CANONICAL_DOCUMENT_MINIMAL: Dict[str, Any] = {
    "id": "doc-joyanes-ch1",
    "source_id": "joyanes-fp-4e",
    "title": "Capítulo 1 - Algoritmos y Programas",
}

CANONICAL_DOCUMENT_FULL: Dict[str, Any] = {
    "id": "doc-joyanes-ch1",
    "source_id": "joyanes-fp-4e",
    "title": "Capítulo 1 - Algoritmos y Programas",
    "content": "Un algoritmo es un conjunto de pasos lógicos y secuenciales...",
    "path": "Fase-0/Joyanes/capitulo_01.pdf",
    "page_count": 38,
    "language": "es",
    "metadata": {"file_size_bytes": 1048576, "checksum": "e3b0c442"},
    "created_at": CANONICAL_TIMESTAMP,
}

CANONICAL_CHUNK_MINIMAL: Dict[str, Any] = {
    "id": "chunk-joyanes-1-1",
    "document_id": "doc-joyanes-ch1",
    "source_id": "joyanes-fp-4e",
    "content": "Un algoritmo debe ser preciso, definido y finito.",
}

CANONICAL_CHUNK_FULL: Dict[str, Any] = {
    "id": "chunk-joyanes-1-1",
    "document_id": "doc-joyanes-ch1",
    "source_id": "joyanes-fp-4e",
    "content": "Un algoritmo debe ser preciso, definido y finito.",
    "page_start": 4,
    "page_end": 5,
    "chapter": "Capítulo 1",
    "section": "1.2 Concepto de Algoritmo",
    "token_count": 120,
    "index": 0,
    "metadata": {"parser": "pdfplumber", "strategy": "sliding_window"},
}

CANONICAL_EVIDENCE_MINIMAL: Dict[str, Any] = {
    "id": "ev-001",
    "claim": "Todo algoritmo requiere precisión y finitud según Joyanes.",
    "status": "SUPPORTED",
}

CANONICAL_EVIDENCE_FULL: Dict[str, Any] = {
    "id": "ev-001",
    "claim": "Todo algoritmo requiere precisión y finitud según Joyanes.",
    "status": "SUPPORTED",
    "content": "Las características de un algoritmo son: precisión, definición, finitud.",
    "source_id": "joyanes-fp-4e",
    "document_id": "doc-joyanes-ch1",
    "chunk_id": "chunk-joyanes-1-1",
    "page": 4,
    "confidence": 0.98,
    "metadata": {"verification_rule": "strict_grounding"},
}

CANONICAL_STUDENT_STATE_MINIMAL: Dict[str, Any] = {
    "student_id": "student-agustin-01",
}

CANONICAL_STUDENT_STATE_FULL: Dict[str, Any] = {
    "student_id": "student-agustin-01",
    "topic": "Algoritmos y Estructuras de Control",
    "status": "developing",
    "understanding": {
        "conceptual": True,
        "application": True,
        "transfer": False,
    },
    "strengths": ["Bucles for", "Condicionales simples"],
    "weaknesses": ["Bucles anidados", "Condición de corte en recursión"],
    "recurring_errors": ["Error off-by-one en condición de parada"],
    "last_evaluation": {"score": 8.0, "passed": True, "date": "2026-09-01"},
    "next_action": {"type": "targeted_exercise", "topic": "Bucles anidados"},
    "metadata": {"total_study_hours": 12.5},
    "updated_at": CANONICAL_TIMESTAMP,
}

CANONICAL_STUDY_PLAN_MINIMAL: Dict[str, Any] = {
    "id": "plan-algoritmos-01",
    "module": "Módulo 1: Algoritmos Básicos",
    "objective": "Comprender la estructura lógica de los algoritmos y su representación.",
}

CANONICAL_STUDY_PLAN_FULL: Dict[str, Any] = {
    "id": "plan-algoritmos-01",
    "student_id": "student-agustin-01",
    "module": "Módulo 1: Algoritmos Básicos",
    "objective": "Comprender la estructura lógica de los algoritmos y su representación.",
    "prerequisites": ["Lógica proposicional básica"],
    "concepts": ["Definición de algoritmo", "Pseudocódigo", "Diagramas de flujo"],
    "sources": ["joyanes-fp-4e", "spraul-think-like-a-programmer"],
    "order": [
        "1. Leer Joyanes Cap 1 (pp. 1-15)",
        "2. Resolver ejercicios de pseudocódigo en Spraul",
        "3. Evaluación conceptual con Tester",
    ],
    "depth": "rigorous",
    "exercises": ["ex-alg-01", "ex-alg-02", "ex-alg-03"],
    "mastery_criteria": "Explicar diferencias entre pseudocódigo y diagrama de flujo y resolver 3 ejercicios sin errores.",
    "metadata": {"estimated_sessions": 3},
    "created_at": CANONICAL_TIMESTAMP,
}

CANONICAL_LLM_REQUEST_MINIMAL: Dict[str, Any] = {
    "request_id": "req-tutor-001",
}

CANONICAL_LLM_REQUEST_FULL: Dict[str, Any] = {
    "request_id": "req-tutor-001",
    "mode": "tutor",
    "system_prompt": "Eres el Tutor socrático de Study Engine. Enseña guiando al estudiante.",
    "messages": [
        {"role": "user", "content": "¿Por qué Joyanes insiste en definir el caso base antes de escribir una función recursiva?"}
    ],
    "context": "Fuente: Joyanes Cap. 5 - Recursividad. Evidencia: 'El caso base evita la recursión infinita...'",
    "temperature": 0.5,
    "max_tokens": 800,
    "stop_sequences": ["<END_OF_TURN>"],
    "model": "gpt-oss-120b",
    "provider": "groq",
    "metadata": {"notebook_id": "fase_0_programacion"},
}

CANONICAL_LLM_RESPONSE_MINIMAL: Dict[str, Any] = {
    "request_id": "req-tutor-001",
    "content": "Joyanes destaca que sin un caso base, la función continuará llamándose indefinidamente hasta desbordar la pila.",
}

CANONICAL_LLM_RESPONSE_FULL: Dict[str, Any] = {
    "request_id": "req-tutor-001",
    "content": "Joyanes destaca que sin un caso base, la función continuará llamándose indefinidamente hasta desbordar la pila.",
    "mode": "tutor",
    "model": "gpt-oss-120b",
    "provider": "groq",
    "tokens_used": {"prompt": 150, "completion": 45, "total": 195},
    "finish_reason": "stop",
    "latency_ms": 240.5,
    "metadata": {"safety_check": "passed"},
}

CANONICAL_EVENT_MINIMAL: Dict[str, Any] = {
    "event_id": "evt-001",
    "event_type": "session_start",
}

CANONICAL_EVENT_FULL: Dict[str, Any] = {
    "event_id": "evt-001",
    "session_id": "sess-study-2026-09-01",
    "event_type": "evaluation_completed",
    "timestamp": CANONICAL_TIMESTAMP,
    "payload": {
        "module": "Módulo 1",
        "score": 9.5,
        "questions_count": 5,
        "mode": "tester",
    },
    "metadata": {"client": "web_chat", "ip_anonymized": True},
}
