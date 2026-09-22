"""Tipo 2 (Fase 6): Depuración Adversaria (BugSpotter).

La base de código del material canónico contiene código correcto. Aquí se
aplican MUTACIONES CONTROLADAS verificables sobre plantillas correctas, con
taxonomía CWE explícita:

- CWE-120: Classic Buffer Overflow (strcpy sin bound sobre array fijo)
- CWE-190: Integer Overflow (incremento sin guarda sobre límite)
- CWE-362: Race Condition (contador compartido sin mutex)
- CWE-416: Use After Free (uso de puntero post-free)

Cada plantilla declara: código correcto, mutación (buscar/reemplazar), línea
del bug y la clase CWE que el estudiante debe identificar. El grader acepta
alias ("buffer overflow", "desbordamiento de búfer", "stack smashing", ...):

- La mutación es genuina (string replace sobre el código correcto, no
  escribir el buggy a mano): se demuestra en tests comparando ambos.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Plantillas correctas + mutaciones controladas
# ---------------------------------------------------------------------------

_BUG_BANK: List[Dict[str, Any]] = [
    {
        "cwe": "CWE-120",
        "kc_family": "punteros_memoria",
        "bug_type": "buffer_overflow",
        "correct": (
            "void procesar_datos(const char *input) {\n"
            "    char buffer[64];\n"
            "    strncpy(buffer, input, sizeof(buffer) - 1);\n"
            "    buffer[sizeof(buffer) - 1] = '\\0';\n"
            "    printf(\"Datos: %s\\n\", buffer);\n"
            "}"
        ),
        # Mutación: reemplazar copia acotada por strcpy sin guarda
        "mutation_find": "    strncpy(buffer, input, sizeof(buffer) - 1);\n    buffer[sizeof(buffer) - 1] = '\\0';",
        "mutation_replace": "    strcpy(buffer, input);",
        "must_have_in_buggy": ["strcpy(buffer, input);"],
        "must_lack_in_buggy": ["strncpy(buffer, input, sizeof(buffer) - 1);"],
        "aliases": ["buffer overflow", "desbordamiento de buffer", "desbordamiento de búfer",
                    "cwe-120", "stack smashing", "desborde de búfer", "buffer desbordado"],
        "expected_fix_hint": "usar strncpy/strlcpy con bound + terminador explícito",
    },
    {
        "cwe": "CWE-190",
        "kc_family": "aritmetica_enteros",
        "bug_type": "integer_overflow",
        "correct": (
            "unsigned int siguiente_id(unsigned int id_actual) {\n"
            "    if (id_actual == UINT_MAX) {\n"
            "        return 0;  // wrap explícito y documentado\n"
            "    }\n"
            "    return id_actual + 1;\n"
            "}"
        ),
        # Mutación: quitar la guarda contra wraparound
        "mutation_find": "    if (id_actual == UINT_MAX) {\n        return 0;  // wrap explícito y documentado\n    }\n",
        "mutation_replace": "",
        "must_have_in_buggy": ["return id_actual + 1;"],
        "must_lack_in_buggy": ["if (id_actual == UINT_MAX)"],
        "aliases": ["integer overflow", "overflow entero", "wraparound", "desbordamiento entero",
                    "cwe-190", "sobrepasa el máximo", "desborde entero"],
        "expected_fix_hint": "validar id_actual < UINT_MAX antes de incrementar",
    },
    {
        "cwe": "CWE-362",
        "kc_family": "concurrencia",
        "bug_type": "race_condition",
        "correct": (
            "pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER;\n"
            "int contador = 0;\n\n"
            "void *worker(void *arg) {\n"
            "    for (int i = 0; i < N; i++) {\n"
            "        pthread_mutex_lock(&mtx);\n"
            "        contador++;\n"
            "        pthread_mutex_unlock(&mtx);\n"
            "    }\n"
            "    return NULL;\n"
            "}"
        ),
        # Mutación: quitar el lock/unlock del critical section
        "mutation_find": "        pthread_mutex_lock(&mtx);\n        contador++;\n        pthread_mutex_unlock(&mtx);",
        "mutation_replace": "        contador++;",
        "must_have_in_buggy": ["contador++;"],
        "must_lack_in_buggy": ["pthread_mutex_lock"],
        "aliases": ["race condition", "condición de carrera", "condicion de carrera",
                    "data race", "cwe-362", "interbloqueo no determinista", "no atómico"],
        "expected_fix_hint": "lock antes de leer/escribir compartida, unlock obligatorio post-uso",
    },
    {
        "cwe": "CWE-416",
        "kc_family": "punteros_memoria",
        "bug_type": "use_after_free",
        "correct": (
            "char *s = malloc(16);\n"
            "strncpy(s, \"datos\", 15);\n"
            "procesar(s);\n"
            "free(s);\n"
            "s = NULL;"
        ),
        # Mutación: usar el puntero después del free (sin NULL-out)
        "mutation_find": "free(s);\ns = NULL;",
        "mutation_replace": "free(s);\nprintf(\"%s\", s);",
        "must_have_in_buggy": ["printf(\"%s\", s);"],
        "must_lack_in_buggy": ["s = NULL;"],
        "aliases": ["use after free", "use-after-free", "dangling pointer", "puntero colgante",
                    "cwe-416", "uso tras liberar", "uaf"],
        "expected_fix_hint": "poner el puntero a NULL tras free y no usarlo de nuevo",
    },
]


def generate_debugging_exercise(
    kc_id: str,
    bug_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Genera un ejercicio de depuración adversaria con mutación controlada.

    Si ``bug_type`` se indica (p.ej. 'buffer_overflow'), fuerza ese tipo; si
    es None, se elige el primero cuya familia matchee el kc_id.
    """
    chosen: Optional[Dict[str, Any]] = None
    if bug_type:
        chosen = next((b for b in _BUG_BANK if b["bug_type"] == bug_type), None)
    else:
        kc_low = (kc_id or "").lower()
        for tpl in _BUG_BANK:
            fam = tpl["kc_family"]
            if any(tok in kc_low for tok in fam.split("_")):
                chosen = tpl
                break
        if chosen is None and _BUG_BANK:
            chosen = _BUG_BANK[0]

    if chosen is None:
        return None

    # Mutación controlada verificable: buggy = correcta con mutation_find
    # reemplazado por mutation_replace; se verifican presencias y ausencias.
    buggy = chosen["correct"].replace(chosen["mutation_find"], chosen["mutation_replace"])
    assert buggy != chosen["correct"], f"{chosen['cwe']}: la mutación no cambió el código."
    for must in chosen.get("must_have_in_buggy", []):
        assert must in buggy, f"{chosen['cwe']}: falta '{must}' en el código buggy."
    for absent in chosen.get("must_lack_in_buggy", []):
        assert absent not in buggy, f"{chosen['cwe']}: sigue presente '{absent}' en el buggy."

    ex_id = "gen_bug_" + hashlib.sha256(
        (kc_id + chosen["cwe"] + chosen["bug_type"]).encode()
    ).hexdigest()[:12]

    prompt = (
        "### Depuración Adversaria (BugSpotter)\n\n"
        f"Analizá esta función y encontrá la vulnerabilidad:\n\n"
        f"```c\n{buggy}\n```\n\n"
        "### Tu respuesta debe cubrir:\n"
        "1. Qué clase de vulnerabilidad es (CWE o nombre común).\n"
        "2. Cómo la explotaría un atacante (vector).\n"
        "3. El parche mínimo.\n"
    )

    return {
        "exercise_id": ex_id,
        "kind": "debugging",
        "kc_ids": [kc_id],
        "prompt": prompt,
        "oracle": {
            "type": "bug_class",
            "cwe": chosen["cwe"],
            "accept": chosen["aliases"],
        },
        "difficulty": "avanzado",
        # metadata extra (no parte del oracle pero sí del dict persistido)
        "bug_type": chosen["bug_type"],
        "buggy_code": buggy,
    }
