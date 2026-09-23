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
    # ---------------- CWE-120: Buffer Overflow (3 templates) ----------------
    {
        "template_id": "cwe120_strcpy_stack",
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
        "mutation_find": "    strncpy(buffer, input, sizeof(buffer) - 1);\n    buffer[sizeof(buffer) - 1] = '\\0';",
        "mutation_replace": "    strcpy(buffer, input);",
        "must_have_in_buggy": ["strcpy(buffer, input);"],
        "must_lack_in_buggy": ["strncpy(buffer, input, sizeof(buffer) - 1);"],
        "aliases": ["buffer overflow", "desbordamiento de buffer", "desbordamiento de búfer",
                    "cwe-120", "stack smashing", "desborde de búfer", "buffer desbordado"],
        "expected_fix_hint": "usar strncpy/strlcpy con bound + terminador explícito",
    },
    {
        "template_id": "cwe120_gets_stdin",
        "cwe": "CWE-120",
        "kc_family": "entrada_salida_buffer",
        "bug_type": "buffer_overflow_gets",
        "correct": (
            "void leer_nombre(void) {\n"
            "    char buffer[128];\n"
            "    if (fgets(buffer, sizeof(buffer), stdin) != NULL) {\n"
            "        printf(\"Usuario: %s\\n\", buffer);\n"
            "    }\n"
            "}"
        ),
        "mutation_find": "fgets(buffer, sizeof(buffer), stdin)",
        "mutation_replace": "gets(buffer)",
        "must_have_in_buggy": ["gets(buffer)"],
        "must_lack_in_buggy": ["fgets(buffer, sizeof(buffer), stdin)"],
        "aliases": ["buffer overflow", "desbordamiento de buffer", "desbordamiento de búfer",
                    "cwe-120", "gets sin límite", "stack smashing", "desborde de búfer"],
        "expected_fix_hint": "reemplazar gets por fgets especificando sizeof(buffer)",
    },
    {
        "template_id": "cwe120_sprintf_format",
        "cwe": "CWE-120",
        "kc_family": "strings_formato",
        "bug_type": "buffer_overflow_sprintf",
        "correct": (
            "void registrar_evento(const char *tag, const char *msg) {\n"
            "    char log_buf[256];\n"
            "    snprintf(log_buf, sizeof(log_buf), \"[%s] %s\", tag, msg);\n"
            "    puts(log_buf);\n"
            "}"
        ),
        "mutation_find": "snprintf(log_buf, sizeof(log_buf), \"[%s] %s\", tag, msg);",
        "mutation_replace": "sprintf(log_buf, \"[%s] %s\", tag, msg);",
        "must_have_in_buggy": ["sprintf(log_buf, \"[%s] %s\", tag, msg);"],
        "must_lack_in_buggy": ["snprintf(log_buf, sizeof(log_buf)"],
        "aliases": ["buffer overflow", "desbordamiento de buffer", "desbordamiento de búfer",
                    "cwe-120", "sprintf sin acotar", "stack smashing", "desborde de búfer"],
        "expected_fix_hint": "usar snprintf acotado al tamaño del buffer",
    },

    # ---------------- CWE-190: Integer Overflow (3 templates) ----------------
    {
        "template_id": "cwe190_uint_increment",
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
        "mutation_find": "    if (id_actual == UINT_MAX) {\n        return 0;  // wrap explícito y documentado\n    }\n",
        "mutation_replace": "",
        "must_have_in_buggy": ["return id_actual + 1;"],
        "must_lack_in_buggy": ["if (id_actual == UINT_MAX)"],
        "aliases": ["integer overflow", "overflow entero", "wraparound", "desbordamiento entero",
                    "cwe-190", "sobrepasa el máximo", "desborde entero"],
        "expected_fix_hint": "validar id_actual < UINT_MAX antes de incrementar",
    },
    {
        "template_id": "cwe190_malloc_product",
        "cwe": "CWE-190",
        "kc_family": "memoria_enteros",
        "bug_type": "integer_overflow_product",
        "correct": (
            "int *alojar_tabla(size_t filas, size_t cols) {\n"
            "    if (filas > 0 && cols > SIZE_MAX / filas) {\n"
            "        return NULL;  // prevenir desbordamiento en producto\n"
            "    }\n"
            "    return malloc(filas * cols * sizeof(int));\n"
            "}"
        ),
        "mutation_find": "    if (filas > 0 && cols > SIZE_MAX / filas) {\n        return NULL;  // prevenir desbordamiento en producto\n    }\n",
        "mutation_replace": "",
        "must_have_in_buggy": ["return malloc(filas * cols * sizeof(int));"],
        "must_lack_in_buggy": ["SIZE_MAX / filas"],
        "aliases": ["integer overflow", "overflow entero", "wraparound", "desbordamiento entero",
                    "cwe-190", "multiplicación desbordada", "desborde entero"],
        "expected_fix_hint": "comprobar desbordamiento aritmético en el producto antes de malloc",
    },
    {
        "template_id": "cwe190_packet_length_add",
        "cwe": "CWE-190",
        "kc_family": "redes_enteros",
        "bug_type": "integer_overflow_sum",
        "correct": (
            "char *ensamblar_paquete(size_t hdr_len, size_t body_len) {\n"
            "    if (hdr_len > SIZE_MAX - body_len - 1) {\n"
            "        return NULL;  // guarda ante desbordamiento de suma\n"
            "    }\n"
            "    return malloc(hdr_len + body_len + 1);\n"
            "}"
        ),
        "mutation_find": "    if (hdr_len > SIZE_MAX - body_len - 1) {\n        return NULL;  // guarda ante desbordamiento de suma\n    }\n",
        "mutation_replace": "",
        "must_have_in_buggy": ["return malloc(hdr_len + body_len + 1);"],
        "must_lack_in_buggy": ["SIZE_MAX - body_len - 1"],
        "aliases": ["integer overflow", "overflow entero", "wraparound", "desbordamiento entero",
                    "cwe-190", "suma de longitudes desbordada", "desborde entero"],
        "expected_fix_hint": "validar que hdr_len + body_len + 1 no supere SIZE_MAX",
    },

    # ---------------- CWE-362: Race Condition (3 templates) ----------------
    {
        "template_id": "cwe362_counter_mutex",
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
        "mutation_find": "        pthread_mutex_lock(&mtx);\n        contador++;\n        pthread_mutex_unlock(&mtx);",
        "mutation_replace": "        contador++;",
        "must_have_in_buggy": ["contador++;"],
        "must_lack_in_buggy": ["pthread_mutex_lock"],
        "aliases": ["race condition", "condición de carrera", "condicion de carrera",
                    "data race", "cwe-362", "interbloqueo no determinista", "no atómico"],
        "expected_fix_hint": "lock antes de leer/escribir compartida, unlock obligatorio post-uso",
    },
    {
        "template_id": "cwe362_bank_withdraw_toctou",
        "cwe": "CWE-362",
        "kc_family": "concurrencia_sincronizacion",
        "bug_type": "race_condition_toctou",
        "correct": (
            "int debitar_saldo(Cuenta *c, int monto) {\n"
            "    pthread_mutex_lock(&c->lock);\n"
            "    if (c->saldo >= monto) {\n"
            "        c->saldo -= monto;\n"
            "        pthread_mutex_unlock(&c->lock);\n"
            "        return 1;\n"
            "    }\n"
            "    pthread_mutex_unlock(&c->lock);\n"
            "    return 0;\n"
            "}"
        ),
        "mutation_find": "    pthread_mutex_lock(&c->lock);\n    if (c->saldo >= monto) {\n        c->saldo -= monto;\n        pthread_mutex_unlock(&c->lock);\n        return 1;\n    }\n    pthread_mutex_unlock(&c->lock);",
        "mutation_replace": "    if (c->saldo >= monto) {\n        c->saldo -= monto;\n        return 1;\n    }",
        "must_have_in_buggy": ["if (c->saldo >= monto)", "c->saldo -= monto;"],
        "must_lack_in_buggy": ["pthread_mutex_lock(&c->lock);"],
        "aliases": ["race condition", "condición de carrera", "condicion de carrera",
                    "data race", "cwe-362", "toctou", "check-then-act"],
        "expected_fix_hint": "encapsular verificación y débito atómicamente con lock de mutex",
    },
    {
        "template_id": "cwe362_lazy_singleton_init",
        "cwe": "CWE-362",
        "kc_family": "concurrencia_memoria",
        "bug_type": "race_condition_singleton",
        "correct": (
            "Resource *obtener_recurso(void) {\n"
            "    pthread_mutex_lock(&res_mtx);\n"
            "    if (global_res == NULL) {\n"
            "        global_res = inicializar_recurso();\n"
            "    }\n"
            "    pthread_mutex_unlock(&res_mtx);\n"
            "    return global_res;\n"
            "}"
        ),
        "mutation_find": "    pthread_mutex_lock(&res_mtx);\n    if (global_res == NULL) {\n        global_res = inicializar_recurso();\n    }\n    pthread_mutex_unlock(&res_mtx);",
        "mutation_replace": "    if (global_res == NULL) {\n        global_res = inicializar_recurso();\n    }",
        "must_have_in_buggy": ["global_res = inicializar_recurso();"],
        "must_lack_in_buggy": ["pthread_mutex_lock(&res_mtx);"],
        "aliases": ["race condition", "condición de carrera", "condicion de carrera",
                    "data race", "cwe-362", "inicialización no segura", "carrera de hilos"],
        "expected_fix_hint": "usar mutex o pthread_once para garantizar inicialización singleton única",
    },

    # ---------------- CWE-416: Use After Free (3 templates) ----------------
    {
        "template_id": "cwe416_printf_post_free",
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
        "mutation_find": "free(s);\ns = NULL;",
        "mutation_replace": "free(s);\nprintf(\"%s\", s);",
        "must_have_in_buggy": ["printf(\"%s\", s);"],
        "must_lack_in_buggy": ["s = NULL;"],
        "aliases": ["use after free", "use-after-free", "dangling pointer", "puntero colgante",
                    "cwe-416", "uso tras liberar", "uaf"],
        "expected_fix_hint": "poner el puntero a NULL tras free y no usarlo de nuevo",
    },
    {
        "template_id": "cwe416_linked_list_delete",
        "cwe": "CWE-416",
        "kc_family": "estructuras_datos",
        "bug_type": "use_after_free_traversal",
        "correct": (
            "void destruir_lista(Node *cabeza) {\n"
            "    while (cabeza != NULL) {\n"
            "        Node *siguiente = cabeza->next;\n"
            "        free(cabeza);\n"
            "        cabeza = siguiente;\n"
            "    }\n"
            "}"
        ),
        "mutation_find": "        Node *siguiente = cabeza->next;\n        free(cabeza);\n        cabeza = siguiente;",
        "mutation_replace": "        free(cabeza);\n        cabeza = cabeza->next;",
        "must_have_in_buggy": ["free(cabeza);", "cabeza = cabeza->next;"],
        "must_lack_in_buggy": ["Node *siguiente = cabeza->next;"],
        "aliases": ["use after free", "use-after-free", "dangling pointer", "puntero colgante",
                    "cwe-416", "uso tras liberar", "uaf"],
        "expected_fix_hint": "guardar referencia cabeza->next antes de llamar a free(cabeza)",
    },
    {
        "template_id": "cwe416_session_cleanup_field",
        "cwe": "CWE-416",
        "kc_family": "punteros_estructuras",
        "bug_type": "use_after_free_field",
        "correct": (
            "void cerrar_sesion(Session *sesion) {\n"
            "    int uid = sesion->user_id;\n"
            "    free(sesion);\n"
            "    auditar_cierre(uid);\n"
            "}"
        ),
        "mutation_find": "    int uid = sesion->user_id;\n    free(sesion);\n    auditar_cierre(uid);",
        "mutation_replace": "    free(sesion);\n    auditar_cierre(sesion->user_id);",
        "must_have_in_buggy": ["free(sesion);", "auditar_cierre(sesion->user_id);"],
        "must_lack_in_buggy": ["int uid = sesion->user_id;"],
        "aliases": ["use after free", "use-after-free", "dangling pointer", "puntero colgante",
                    "cwe-416", "uso tras liberar", "uaf"],
        "expected_fix_hint": "leer sesion->user_id antes de liberar el bloque con free",
    },
]


def generate_debugging_exercise(
    kc_id: str,
    bug_type: Optional[str] = None,
    template_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Genera un ejercicio de depuración adversaria con mutación controlada.

    Si ``template_id`` se indica, se elige esa plantilla exacta.
    Si ``bug_type`` se indica (p.ej. 'buffer_overflow' o 'CWE-120'), se filtra por tipo o CWE.
    Si es None, se elige del conjunto cuya familia matchee el kc_id de forma determinista.
    """
    chosen: Optional[Dict[str, Any]] = None
    if template_id:
        chosen = next((b for b in _BUG_BANK if b.get("template_id") == template_id), None)
    elif bug_type:
        bt_low = bug_type.lower()
        candidates = [
            b for b in _BUG_BANK
            if b["bug_type"] == bug_type
            or b["bug_type"].startswith(bug_type + "_")
            or b["cwe"].lower() == bt_low
            or b.get("template_id") == bug_type
        ]
        if candidates:
            # Determinismo según hash de kc_id si hay múltiples candidatos
            idx = int(hashlib.sha256(kc_id.encode()).hexdigest(), 16) % len(candidates)
            # Si uno coincide exactamente con bug_type, priorizarlo
            exact = next((c for c in candidates if c["bug_type"] == bug_type), None)
            chosen = exact or candidates[idx]
    else:
        kc_low = (kc_id or "").lower()
        matching = [
            tpl for tpl in _BUG_BANK
            if any(tok in kc_low for tok in tpl["kc_family"].split("_"))
        ]
        if matching:
            idx = int(hashlib.sha256(kc_id.encode()).hexdigest(), 16) % len(matching)
            chosen = matching[idx]
        elif _BUG_BANK:
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
