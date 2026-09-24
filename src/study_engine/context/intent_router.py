"""Three-layer Intent & Context Router (Ola 5, Fase 5.2).

Determines epistemic intent and required context depth for notebook interactions.

Capas:
- Capa 1: Heurísticas deterministas (ContextHeuristics, confianza >= 0.90, 0 llamadas LLM).
- Capa 2: Clasificador ligero (Groq 8B o mock clasificador JSON-constrained si Capa 1 no alcanza).
- Capa 3: Fallback determinista seguro:
    - len(query.split()) > 12 palabras -> DEEP
    - len(query.split()) <= 12 palabras -> NORMAL

INVARIANTES:
1. INV-W5-3: El router NUNCA decide KCs, transiciones pedagógicas ni maestría de BKT.
2. MULTIMODAL es ortogonal a depth (no es un cuarto nivel).
3. suggested_provider es Optional[str], el router no hardcodea proveedores finales (eso lo decide el Model Registry en Fase 5.3).
"""

import json
import logging
from typing import Any, Optional
from study_engine.context.heuristics import ContextHeuristics
from study_engine.context.routing_decision import RoutingDecision

logger = logging.getLogger(__name__)


class IntentRouter:
    """Three-stage intent and context router."""

    def __init__(
        self,
        classifier_backend: Optional[Any] = None,
        confidence_threshold: float = 0.90,
    ) -> None:
        self.classifier_backend = classifier_backend
        self.confidence_threshold = confidence_threshold

    async def route(
        self,
        query: str,
        *,
        has_multimodal_asset: bool = False,
        active_kc_id: Optional[str] = None,
        has_active_exercise: bool = False,
    ) -> RoutingDecision:
        """Route query through the 3-layer architecture."""
        q = (query or "").strip()

        # =========================================================================
        # CAPA 1: Heurísticas deterministas (0 llamadas LLM)
        # =========================================================================
        decision, confidence = ContextHeuristics.evaluate(
            q,
            has_multimodal_asset=has_multimodal_asset,
            active_kc_id=active_kc_id,
            has_active_exercise=has_active_exercise,
        )
        if decision is not None and confidence >= self.confidence_threshold:
            logger.debug("IntentRouter Capa 1 hit: %s (confidence=%.2f)", decision.depth, confidence)
            return decision

        # =========================================================================
        # CAPA 2: Clasificador ligero (Groq 8B / Classifier backend si provisto)
        # =========================================================================
        if self.classifier_backend is not None:
            try:
                classified_decision = await self._classify_with_llm(
                    q,
                    has_multimodal_asset=has_multimodal_asset,
                    active_kc_id=active_kc_id,
                )
                if classified_decision is not None:
                    logger.debug("IntentRouter Capa 2 hit: %s", classified_decision.depth)
                    return classified_decision
            except Exception as exc:
                logger.warning("IntentRouter Capa 2 failed, falling through to Capa 3: %s", exc)

        # =========================================================================
        # CAPA 3: Default seguro determinista
        # =========================================================================
        words = q.split()
        if len(words) > 12:
            return RoutingDecision(
                depth="DEEP",
                requires_multimodal=has_multimodal_asset,
                requires_multi_source=False,
                requires_long_context=True,
                max_context_tokens=16000,
                cloud_allowed=True,
                suggested_provider=None,
                explanation="Fallback Capa 3: Query extensa (>12 palabras) sin heurística específica -> DEEP context.",
            )

        return RoutingDecision(
            depth="NORMAL",
            requires_multimodal=has_multimodal_asset,
            requires_multi_source=False,
            requires_long_context=False,
            max_context_tokens=5000,
            cloud_allowed=True,
            suggested_provider=None,
            explanation="Fallback Capa 3: Query corta (<=12 palabras) sin heurística específica -> NORMAL focal context.",
        )

    async def _classify_with_llm(
        self,
        query: str,
        *,
        has_multimodal_asset: bool,
        active_kc_id: Optional[str],
    ) -> Optional[RoutingDecision]:
        """Prompt light classifier constrained to JSON."""
        prompt = (
            "Eres el clasificador de profundidad de contexto epistémico de TALOS.\n"
            "Clasifica la consulta del usuario en una de tres profundidades:\n"
            "- NORMAL: pregunta puntual, focal, conceptual o de un único tema.\n"
            "- DEEP: análisis profundo de un capítulo, sección, desglose o demostración.\n"
            "- GLOBAL: síntesis de todo el libro, comparación entre múltiples fuentes o panorama general.\n\n"
            f'Consulta: "{query}"\n'
            "Responde estrictamente en JSON con este formato:\n"
            '{"depth": "NORMAL"|"DEEP"|"GLOBAL", "requires_multi_source": true|false, "explanation": "..."}'
        )
        if hasattr(self.classifier_backend, "ainvoke"):
            raw_res = await self.classifier_backend.ainvoke(prompt)
        elif hasattr(self.classifier_backend, "generate_json"):
            raw_res = await self.classifier_backend.generate_json(prompt)
        elif callable(self.classifier_backend):
            import asyncio
            raw_res = await asyncio.to_thread(self.classifier_backend, prompt)
        else:
            return None

        if isinstance(raw_res, str):
            data = json.loads(raw_res)
        elif isinstance(raw_res, dict):
            data = raw_res
        else:
            return None

        depth = str(data.get("depth", "NORMAL")).upper()
        if depth not in ("NORMAL", "DEEP", "GLOBAL"):
            depth = "NORMAL"

        requires_multi_source = bool(data.get("requires_multi_source", depth == "GLOBAL"))
        requires_long_context = depth in ("DEEP", "GLOBAL")
        max_tokens = 40000 if depth == "GLOBAL" else (16000 if depth == "DEEP" else 5000)

        return RoutingDecision(
            depth=depth,  # type: ignore[arg-type]
            requires_multimodal=has_multimodal_asset,
            requires_multi_source=requires_multi_source,
            requires_long_context=requires_long_context,
            max_context_tokens=max_tokens,
            cloud_allowed=True,
            suggested_provider=None,
            explanation=f"Capa 2 Classifier: {data.get('explanation', 'LLM classification')}",
        )
