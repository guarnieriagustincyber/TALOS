"""Tipo 1 (Fase 6): Ejercicios Multi-KC — Composición Causal.

Combina KCs que el estudiante domina por separado pero le cuestan juntos.
Generación determinista (banco de composiciones con oracle propio).

Selección:
  - select_multi_kc_candidates(): KCs con p_L >= HIGH_MASTERY_THRESHOLD
    (individual) como operandos, preferentemente incluyendo alguno con
    historial de fricción en el último session digest.
  - compose_multi_kc_exercise(kc_ids): construye el enunciado desde la
    banca de plantillas; oracle keyword-coverage (determinista).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

HIGH_MASTERY_THRESHOLD = 0.6

# Banca determinista de composiciones. Cada plantilla define:
# - family: tags conceptuales para matching con el catálogo
# - required_kcs: cantidad mínima de KCs coincidentes
# - title: nombre del ejercicio
# - prompt: enunciado socrático
# - oracle: oráculo determinista con test suite / cobertura requerida y solución de referencia
# - difficulty: nivel pedagógico
_COMPOSE_BANK: List[Dict[str, Any]] = [
    # Familia 1 (3 KCs): Punteros + Gestión de Memoria Heap + Concurrencia (Race Condition / Mutex)
    {
        "family": ["concurrencia", "mutex", "race", "hilo", "hilos", "compartido", "shared"],
        "required_kcs": 2,
        "title": "Buffer compartido dinámico con sincronización mutex",
        "prompt": (
            "Escribí en C una función `char *get_or_create_shared_buffer(char **shared_ptr, size_t size, pthread_mutex_t *mtx)` "
            "donde múltiples hilos acceden a un buffer compartido en el heap. La función debe proteger el acceso al puntero con el mutex, "
            "verificar si `*shared_ptr` es NULL antes de reservar con `malloc(size)`, manejar la falla de reserva, y liberar el lock "
            "en todos los caminos de ejecución. Además: explicá cómo y cuándo debe liberarse la memoria con `free` al finalizar el programa.\n\n"
            "Oráculo esperado: mutex_lock + malloc + null_check + mutex_unlock + free del caller."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "mutex_lock", "accept": ["pthread_mutex_lock", "lock", "bloqueo", "adquirir mutex", "mutex"]},
                {"name": "malloc", "accept": ["malloc", "heap", "reserva dinámica", "reserva"]},
                {"name": "null_check", "accept": ["null", "null-check", "si es nulo", "verificar"]},
                {"name": "mutex_unlock", "accept": ["pthread_mutex_unlock", "unlock", "desbloquear", "liberar mutex"]},
                {"name": "free", "accept": ["free", "liberar memoria", "cleanup"]},
            ],
            "reference_solution": (
                "char *get_or_create_shared_buffer(char **shared_ptr, size_t size, pthread_mutex_t *mtx) {\n"
                "    pthread_mutex_lock(mtx);\n"
                "    if (*shared_ptr == NULL) {\n"
                "        *shared_ptr = (char *)malloc(size);\n"
                "    }\n"
                "    char *res = *shared_ptr;\n"
                "    pthread_mutex_unlock(mtx);\n"
                "    return res;\n"
                "}\n"
                "// El caller o destructor del programa debe invocar free(*shared_ptr) tras pthread_join."
            ),
        },
        "difficulty": "avanzado",
    },
    # Familia 2 (2-3 KCs): Estructuras de Datos Lineales (Pilas/Colas) + Punteros + Frontera/Underflow
    {
        "family": ["pila", "pilas", "cola", "colas", "underflow"],
        "required_kcs": 2,
        "title": "Operación pop segura en pila dinámica enlazada",
        "prompt": (
            "Escribí en C la función `int stack_pop(Node **top_ptr, int *out_val)` para una estructura de pila enlazada "
            "(`struct Node { int val; struct Node *next; }`). La función debe validar la precondición de pila vacía retornando -1 "
            "si `*top_ptr == NULL` (guarda de underflow), extraer el valor del nodo tope en `*out_val`, actualizar `*top_ptr` al "
            "siguiente nodo (`top->next`), y liberar (`free`) el nodo desapilado. Explicá cómo tu guarda evita la desreferenciación "
            "de puntero nulo y previene memory leaks."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "empty_guard", "accept": ["null", "vacia", "vacía", "underflow", "top == null", "*top_ptr == null", "!*top_ptr"]},
                {"name": "extract_value", "accept": ["out_val", "valor", "val", "*out_val"]},
                {"name": "update_top", "accept": ["next", "siguiente", "*top_ptr = temp->next", "top = top->next", "temp->next"]},
                {"name": "free_node", "accept": ["free", "liberar", "libera el nodo", "free(temp)"]},
            ],
            "reference_solution": (
                "int stack_pop(Node **top_ptr, int *out_val) {\n"
                "    if (!top_ptr || !*top_ptr) return -1;\n"
                "    Node *temp = *top_ptr;\n"
                "    *out_val = temp->val;\n"
                "    *top_ptr = temp->next;\n"
                "    free(temp);\n"
                "    return 0;\n"
                "}"
            ),
        },
        "difficulty": "intermedio",
    },
    # Familia 3 (2-3 KCs): Arquitectura x86-64 / ABI + Stack Frame + Funciones
    {
        "family": ["x86", "x86_64", "ensamblador", "assembly", "abi", "prologo", "prólogo", "stack", "frame"],
        "required_kcs": 2,
        "title": "Prólogo de función y convención ABI System V x86-64",
        "prompt": (
            "Escribí en ensamblador x86-64 el prólogo y epílogo canónico de una función `int suma(int a, int b)` según la convención "
            "ABI System V x86-64. La función recibe argumentos en `%edi` y `%esi`, debe preservar `%rbp` en el stack, establecer el stack frame, "
            "sumar los argumentos colocando el resultado en `%eax`, restaurar `%rbp` y retornar con `ret`."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "push_rbp", "accept": ["push %rbp", "pushq %rbp", "push rbp", "preservar rbp"]},
                {"name": "mov_rsp_rbp", "accept": ["mov %rsp, %rbp", "movq %rsp, %rbp", "mov rbp, rsp", "mov rsp, rbp"]},
                {"name": "registers_args", "accept": ["%edi", "%esi", "edi", "esi", "rdi", "rsi"]},
                {"name": "return_rax", "accept": ["%eax", "%rax", "eax", "rax", "retorno en eax"]},
                {"name": "epilogue_ret", "accept": ["pop %rbp", "popq %rbp", "pop rbp", "leave", "ret", "retq"]},
            ],
            "reference_solution": (
                "suma:\n"
                "    pushq %rbp\n"
                "    movq %rsp, %rbp\n"
                "    movl %edi, %eax\n"
                "    addl %esi, %eax\n"
                "    popq %rbp\n"
                "    ret\n"
            ),
        },
        "difficulty": "intermedio",
    },
    # Familia 4 (2 KCs): Aritmética de Punteros + Arrays + Off-by-one
    {
        "family": ["subindice", "subíndice", "corchetes", "frontera", "off-by-one"],
        "required_kcs": 2,
        "title": "Búsqueda en rango con aritmética de punteros y guardas de frontera",
        "prompt": (
            "Escribí en C una función `int *find_in_range(int *start, int *end, int target)` que busque un entero en un array contiguo "
            "utilizando exclusivamente aritmética de punteros (sin indexación `[]`). La función debe avanzar con `start++` mientras `start < end`, "
            "devolviendo el puntero al elemento coincidente o `NULL` si no se encuentra. Justificá por qué la guarda `start < end` evita el off-by-one."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "pointer_arithmetic", "accept": ["start++", "p++", "*start", "aritmética de punteros", "indirección"]},
                {"name": "boundary_check", "accept": ["start < end", "p < end", "guarda", "límite", "frontera"]},
                {"name": "target_match", "accept": ["*start == target", "*p == target", "coincidencia", "target"]},
                {"name": "null_fallback", "accept": ["return null", "null", "no encontrado"]},
            ],
            "reference_solution": (
                "int *find_in_range(int *start, int *end, int target) {\n"
                "    while (start < end) {\n"
                "        if (*start == target) return start;\n"
                "        start++;\n"
                "    }\n"
                "    return NULL;\n"
                "}"
            ),
        },
        "difficulty": "basico",
    },
    # Plantillas preexistentes conservadas por compatibilidad
    {
        "family": ["punteros", "memoria", "malloc", "puntero"],
        "required_kcs": 2,
        "title": "Copia profunda con heap manual",
        "prompt": (
            "Escribí en C una función `char *dup_deep(const char *src, const char *fallback)` "
            "que devuelva una copia profunda de `src` reservada con malloc. Si `src` es NULL, "
            "la copia debe ser de `fallback`. Luego: explicá dónde y cuándo se libera la memoria "
            "y qué pasa si el caller olvida el free. Sin usar strdup.\n\n"
            "Oráculo esperado: malloc + copy + condición NULL + free del caller."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "malloc", "accept": ["malloc", "reserva", "heap"]},
                {"name": "copia", "accept": ["copia", "copy", "deep copy", "copia profunda", "memcpy", "strcpy"]},
                {"name": "null_handling", "accept": ["null", "null-check", "si es nulo", "fallback"]},
                {"name": "free", "accept": ["free", "liberar", "libera"]},
            ],
        },
        "difficulty": "intermedio",
    },
    {
        "family": ["bucle", "array", "lista", "estructura", "lineal"],
        "required_kcs": 2,
        "title": "Acumulación con guard de borde",
        "prompt": (
            "Escribí una función que recorra un array de enteros con un bucle y devuelva "
            "el índice del primer elemento que supera un umbral, o -1 si ninguno lo supera. "
            "Después: justificá por qué tu guarda de frontera evita el off-by-one en el caso "
            "de array vacío y array unitario.\n\n"
            "Oráculo esperado: índice correcto y explicación del invariante de borde."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "indice", "accept": ["indice", "índice", "posicion", "posición"]},
                {"name": "umbral", "accept": ["umbral", "threshold", "supera"]},
                {"name": "borde", "accept": ["borde", "frontera", "off-by-one", "vacio", "vacío"]},
                {"name": "menos_uno", "accept": ["-1", "no encontrado", "ninguno"]},
            ],
        },
        "difficulty": "basico",
    },
    {
        "family": ["concurrencia", "proceso", "hilo", "semaforo", "mutex", "race"],
        "required_kcs": 2,
        "title": "Contador compartido con race",
        "prompt": (
            "Tenés dos hilos que incrementan un contador global compartido N veces cada uno. "
            "Escribí el escenario mínimo en C (con pthreads) donde el resultado final no es 2N "
            "por una race condition. Luego, reescribí el critical section protegido con un mutex "
            "y explicá qué invariante restaura.\n\n"
            "Oráculo esperado: identificación del read-modify-write atómico roto + mutex correctamente "
            "colocado (lock antes de la lectura, unlock después de la escritura)."
        ),
        "oracle": {
            "type": "keyword_coverage",
            "min_coverage": 0.75,
            "required": [
                {"name": "race", "accept": ["race", "condicion de carrera", "condición de carrera", "interleaving"]},
                {"name": "mutex", "accept": ["mutex", "lock", "exclusion mutua", "exclusión mutua"]},
                {"name": "seccion_critica", "accept": ["seccion critica", "sección crítica", "critical section"]},
                {"name": "resultado", "accept": ["2n", "2*n", "duplicar", "contador"]},
            ],
        },
        "difficulty": "avanzado",
    },
]


def re_vocab(text: str) -> List[str]:
    """Tokens del identificador/título para matching con familias de plantillas."""
    import re as _re
    return [t for t in _re.findall(r"[a-z0-9]{3,}", (text or "").lower())]


def _template_for(kc_ids: List[str], catalog: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Elige la mejor plantilla del banco para el conjunto de KCs."""
    vocab: set = set()
    for kc in kc_ids:
        vocab.update(re_vocab(kc))
        if catalog:
            for entry in catalog.values():
                if isinstance(entry, dict):
                    for kc in entry.get("kcs", []):
                        if kc.get("kc_id") in kc_ids:
                            vocab.update(re_vocab(kc.get("title", "") + " " + " ".join(kc.get("subtopics", []) or [])))
    best = None
    best_score = 0
    for t in _COMPOSE_BANK:
        score = sum(1 for fam in t["family"] if fam in vocab)
        if score >= t["required_kcs"] and score > best_score:
            best = t
            best_score = score
    return best


def select_multi_kc_candidates(
    kc_catalog: Dict[str, Any],
    bkt_tracker: Any,
    min_mastery: float = HIGH_MASTERY_THRESHOLD,
    digest: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Elige los KCs candidatos a combinar.

    Lógica: KCs con p_L >= umbral (dominados por separado) + preferencia por
    los que aparecieron en `struggled_kcs` del último digest (le costaron en
    contexto combinado).
    """
    if not kc_catalog:
        return []
    struggled = set((digest or {}).get("struggled_kcs") or [])
    high: List[str] = []
    seen = set()
    for entry in kc_catalog.values():
        if not isinstance(entry, dict):
            continue
        for kc in entry.get("kcs", []):
            kc_id = kc.get("kc_id")
            if not kc_id or kc_id in seen:
                continue
            try:
                p_l = bkt_tracker.get_state(kc_id).p_L if bkt_tracker else 0.0
            except Exception:
                p_l = 0.0
            if p_l >= min_mastery:
                high.append(kc_id)
                seen.add(kc_id)
    # Los struggled con alta P(L) individual son los candidatos más interesantes
    high.sort(key=lambda k: (k not in struggled, k))
    return high


def compose_multi_kc_exercise(
    kc_ids: List[str],
    difficulty: Optional[str] = None,
    catalog: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Compone un ejercicio multi-KC con oráculo determinista (o None si no aplica)."""
    if not kc_ids:
        return None
    template = _template_for(kc_ids, catalog=catalog)
    if template is None:
        return None
    ex_id = "gen_multikc_" + hashlib.sha256(
        ("|".join(sorted(kc_ids)) + template["title"]).encode()
    ).hexdigest()[:12]
    kcs_label = " + ".join(kc_ids)
    prompt = (
        f"**Ejercicio Multi-KC — {template['title']}**\n\n"
        f"KCs combinados: `{kcs_label}`\n\n"
        f"{template['prompt']}"
    )
    return {
        "exercise_id": ex_id,
        "kind": "multi_kc",
        "kc_ids": list(kc_ids),
        "prompt": prompt,
        "oracle": template["oracle"],
        "difficulty": difficulty or template.get("difficulty"),
        "source": "generated",
    }
