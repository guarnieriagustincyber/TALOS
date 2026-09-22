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

HIGH_MASTERY_THRESHOLD = 0.7

# Banca determinista de composiciones. Cada plantilla define:
# - prompt: enunciado socrático (medio, no da la solución)
# - oracle: cobertura de conceptos obligatorios para el grader
# Los kc_ids canónicos del catálogo guían la composición; la banca se indexa
# por familias semánticas (no por ids exactos) para escalar cuando el usuario
# cargue KCs manuales.
_COMPOSE_BANK: List[Dict[str, Any]] = [
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
    return [t for t in _re.findall(r"[a-z]{3,}", (text or "").lower())]


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
