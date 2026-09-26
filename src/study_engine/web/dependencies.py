"""Dependency injection and service container for the Study Engine Web API (Hito 10).

Manages singleton lifecycle for:
- CurriculumRegistry
- StudyLoopController
- EvidenceLedger
- StateEngine
- Sovereign SessionOrchestrator
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import sys

logger = logging.getLogger(__name__)
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

# Ensure project root is in sys.path so scripts.* imports resolve in all runtimes
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.generation.tutor import StructuredTutor
from study_engine.llm.backends import HttpOpenAIBackend
from study_engine.llm.client import LLMClient
from study_engine.llm.gemini_backend import GeminiBackend
from study_engine.llm.offline_oracle import OfflinePedagogicalBackend
from study_engine.roadmap.contracts import CurricularRoadmap, DependencyType
from study_engine.session.adapters import StructuredTutorAdapter
from study_engine.session.orchestrator import SessionOrchestrator
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.state_contracts import StudentState
from scripts.experiments.run_study_loop_v1 import StudyLoopExperimentRunner


def generate_mermaid_roadmap(
    roadmap: CurricularRoadmap,
    student_state: StudentState,
) -> str:
    """Generate deterministic Mermaid.js graph markup with semantic node styling."""
    lines: List[str] = ["graph TD"]

    # 1. Nodes with state-driven CSS classes
    for node_id, node in roadmap.nodes.items():
        node_state = student_state.get_node_state(node_id)
        raw_status = (
            node_state.status.value
            if node_state and hasattr(node_state.status, "value")
            else (str(node_state.status) if node_state else "LOCKED")
        )
        css_class = raw_status.lower()
        clean_title = node.title.replace('"', "'")
        lines.append(f'  {node_id}["{clean_title}"]:::{css_class}')

    # 2. Edges representing hard and soft prerequisites
    for dep in roadmap.dependencies:
        if dep.dependency_type == DependencyType.HARD:
            lines.append(f"  {dep.source_node_id} --> {dep.target_node_id}")
        else:
            lines.append(f"  {dep.source_node_id} -.-> {dep.target_node_id}")

    # 3. Class definitions with Tailwind palette colors
    lines.append("  classDef assessed_proficient fill:#2563eb,stroke:#1d4ed8,color:#ffffff,stroke-width:2px;")
    lines.append("  classDef available fill:#059669,stroke:#047857,color:#ffffff,stroke-width:2px;")
    lines.append("  classDef in_progress fill:#d97706,stroke:#b45309,color:#ffffff,stroke-width:2px;")
    lines.append("  classDef locked fill:#4b5563,stroke:#374151,color:#9ca3af,stroke-width:1px;")

    return "\n".join(lines)


class AppContainer:
    """Application dependency container wiring KASIU core components for the web server."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        working_dir: Optional[Path] = None,
        use_mock: bool = False,
    ) -> None:
        self.repo_root = (repo_root or Path.cwd()).resolve()
        self.working_dir = working_dir or (self.repo_root / "data" / "web_state")
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.use_mock = use_mock

        self._load_dotenv()
        self._init_core_pipeline()
        self._init_local_routing()
        self._init_llm_subsystems()
        self._init_student_services()
        self._init_pedagogy_services()
        self._init_dialogue_and_session()

    def _load_dotenv(self) -> None:
        """Ensure .env is loaded if present."""
        env_path = self.repo_root / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    clean_k = k.strip()
                    clean_v = v.strip().strip("'\"")
                    if clean_k not in os.environ and clean_v:
                        os.environ[clean_k] = clean_v

    def _init_core_pipeline(self) -> None:
        """Initialize core pipeline via authoritative runner."""
        runner = StudyLoopExperimentRunner(
            repo_root=self.repo_root,
            working_dir=self.working_dir,
        )
        self.controller, self.context = runner.initialize_pipeline()
        self.orchestrator: SessionOrchestrator = self.controller.orchestrator
        self.ledger: EvidenceLedger = self.context["ledger"]
        self.curriculum_registry: CurriculumRegistry = self.context["registry"]
        self.knowledge_store = self.context["store"]

        from study_engine.config import settings
        from study_engine.retrieval.fabric import RetrievalFabricLite
        from study_engine.retrieval.reranker import (
            DeterministicLocalReranker,
            JinaReranker,
            LocalONNXReranker,
        )

        if settings.enable_local_neural_reranker:
            reranker = LocalONNXReranker(
                model_path=settings.local_reranker_model_path,
                tokenizer_path=settings.local_reranker_tokenizer_path,
                fallback=(
                    JinaReranker(api_key=settings.jina_api_key, model=settings.jina_rerank_model)
                    if settings.jina_api_key
                    else DeterministicLocalReranker()
                ),
            )
        elif settings.jina_api_key:
            reranker = JinaReranker(api_key=settings.jina_api_key, model=settings.jina_rerank_model)
        else:
            reranker = DeterministicLocalReranker()

        self.retrieval_fabric = RetrievalFabricLite(
            store=self.knowledge_store,
            reranker=reranker,
        )

    def _init_local_routing(self) -> None:
        """Configure LocalOrchestrator and SemanticRouter (Fase 5.5 & 5.7)."""
        from study_engine.tutor.local_orchestrator import LocalOrchestrator
        from study_engine.tutor.semantic_router import SemanticRouter
        from study_engine.hierarchy.scope_resolver import ScopeResolver
        from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator

        self.scope_resolver = ScopeResolver(self.knowledge_store)
        self.folder_orchestrator = FolderOrchestrator(
            folder_id="folder_root",
            knowledge_store=self.knowledge_store,
            ledger=self.ledger,
        )

        if self.use_mock:
            from study_engine.llm.backends import MockBackend
            mock_loc = MockBackend(canned_text="¡Hola! Soy KASIU.")
            self.controller.local_orchestrator = LocalOrchestrator(local_backend=mock_loc)
            self.controller.semantic_router = None
        else:
            self.controller.local_orchestrator = LocalOrchestrator()
            self.controller.semantic_router = SemanticRouter()

    def _init_llm_subsystems(self) -> None:
        """Configure LLM Pool, Router, and authoritative provider.

        ARCHITECTURE: Multi-Provider Fallback Cascade
        ─────────────────────────────────────────────
        Instead of a static ``if/elif`` chain that picks one provider at
        startup and an single-level CircuitBreakerBackend, we now use a
        ``MultiFallbackBackend`` that tries providers in latency order at
        *call time*, with a per-provider asyncio timeout.

        Provider order (measured, 2026-09-25):
          Tier 1 — <1.5s:   Groq qwen3.8-27b (~1.1s)
          Tier 2 — 1-3s:    Xkiro cohere/command-r-plus (~1.5s)
          Tier 3 — 2-10s:   Gemini gemini-3.5-flash-lite (when healthy)
          Tier 4 — ~22s:    NVIDIA NIM nemotron-3.5-lightning (reasoning trace)
          Tier 5 — offline: OfflinePedagogicalBackend (handled inside MultiFallbackBackend)

        Skipped providers (billing/quota exhausted, confirmed 2026-09-25):
          - Cerebras  → HTTP 402 (billing required)
          - OpenAI    → HTTP 429 (no credits)
          - SambaNova → not tested / not in active tier
          - Cloudflare → API token too short (likely placeholder)
        """
        from study_engine.llm.quota_manager import QuotaManager
        from study_engine.llm.sanitizer import DataSanitizer
        from study_engine.llm.router import TalosLLMRouter
        from study_engine.llm.multi_fallback import MultiFallbackBackend
        from study_engine.llm.providers import (
            AbstractLLMProvider,
            CerebrasProvider,
            SambaNovaProvider,
            NvidiaProvider,
            CloudflareProvider,
            OllamaProvider,
            MockProvider,
        )

        self.quota_manager = QuotaManager(db_path=self.working_dir / "quotas.db")
        self.sanitizer = DataSanitizer()

        # TalosLLMRouter: retained for /api/llm-pool/health endpoint only
        pool_providers: Dict[str, AbstractLLMProvider] = {
            "nvidia": NvidiaProvider(),
            "cerebras": CerebrasProvider(),
            "sambanova": SambaNovaProvider(),
            "cloudflare": CloudflareProvider(),
            "ollama": OllamaProvider(),
        }
        if self.use_mock:
            pool_providers["mock"] = MockProvider(name="mock")

        self.llm_router = TalosLLMRouter(
            providers=pool_providers,
            sanitizer=self.sanitizer,
            quota_manager=self.quota_manager,
        )

        # ── Key extraction ─────────────────────────────────────────────
        groq_key       = (os.getenv("GROQ_API_KEY") or "").strip()
        xkiro_key      = (os.getenv("XKIRO_API_KEY") or "").strip()
        gemini_key     = (os.getenv("GEMINI_API_KEY") or "").strip()
        sambanova_key  = (os.getenv("SAMBANOVA_API_KEY") or "").strip()
        cf_api_token   = (os.getenv("CLOUDFLARE_API_TOKEN") or "").strip()   # token real (cfut_...)
        cf_account_id  = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
        cf_worker_url  = (os.getenv("CLOUDFLARE_WORKER_URL") or "").strip()
        cf_worker_key  = (os.getenv("CLOUDFLARE_API_KEY") or "").strip()     # token del Worker proxy
        nvidia_key     = (os.getenv("NVIDIA_API_KEY") or "").strip()
        # Keys confirmed billing/quota problems — kept for future re-activation:
        # cerebras_key = (os.getenv("CEREBRAS_API_KEY") or "").strip()
        # openai_key   = (os.getenv("OPENAI_API_KEY") or "").strip()

        # ── Build ordered provider list ────────────────────────────────
        # Each entry: (display_name, backend_instance)
        # Only append a provider if its key passes basic format validation.
        ordered_providers = []

        if self.use_mock:
            from study_engine.llm.backends import ReplayMockBackend
            ordered_providers.append(("replay_mock", ReplayMockBackend()))
        else:
            # Tier 1 — Gemini (sin límite ITPM estricto, ideal para prompts de TALOS ~7k tokens)
            # TALOS genera prompts de ~7k tokens (system socrático 11k chars + chunks + query),
            # lo que siempre excede el límite de 7.000 ITPM de Groq free-tier → Gemini va primero.
            if gemini_key and len(gemini_key) > 15 and not gemini_key.startswith("<"):
                gem_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
                ordered_providers.append((
                    f"gemini:{gem_model}",
                    GeminiBackend(
                        api_key=gemini_key,
                        model_name=gem_model,
                        timeout_seconds=20.0,
                    ),
                ))

                # Tier 1b — Gemma 4 (misma key de Google AI Studio, sin costo adicional)
                for gemma_model in [
                    os.getenv("GEMMA_MODEL", "gemma-4-31b-it"),
                    "gemma-4-26b-a4b-it",
                ]:
                    ordered_providers.append((
                        f"google:{gemma_model}",
                        GeminiBackend(
                            api_key=gemini_key,
                            model_name=gemma_model,
                            timeout_seconds=16.0,
                        ),
                    ))

            # Tier 2 — Cloudflare Workers AI (API directa, llama-3.3-70b-instruct-fp8-fast)
            # 16s timeout: el modelo 70B tarda >8s con prompts largos
            if cf_api_token and cf_account_id:
                from study_engine.llm.backends import CloudflareDirectBackend
                cf_model = os.getenv("CLOUDFLARE_CF_MODEL", "@cf/meta/llama-3.3-70b-instruct-fp8-fast")
                ordered_providers.append((
                    f"cloudflare-direct:{cf_model}",
                    CloudflareDirectBackend(
                        account_id=cf_account_id,
                        api_token=cf_api_token,
                        model=cf_model,
                        timeout_seconds=16.0,
                    ),
                ))

            # Tier 3 — Xkiro (~1.5s measured)
            if xkiro_key and len(xkiro_key) > 10 and not xkiro_key.startswith("<"):
                xkiro_model = os.getenv("XKIRO_MODEL", "cohere/command-r-plus-08-2024")
                ordered_providers.append((
                    f"xkiro:{xkiro_model}",
                    HttpOpenAIBackend(
                        api_key=xkiro_key,
                        base_url=os.getenv("XKIRO_BASE_URL", "https://api.xkiro.com/v1"),
                        default_model=xkiro_model,
                        timeout_seconds=12.0,
                    ),
                ))

            # Tier 4 — Cloudflare Worker proxy (llama-3.1-8b-fast-v2 via Worker propio)
            if cf_worker_url and cf_worker_url.startswith("https://") and cf_worker_key:
                from study_engine.llm.backends import CloudflareWorkerBackend
                ordered_providers.append((
                    "cloudflare-worker:llama-3.1-8b-fast-v2",
                    CloudflareWorkerBackend(
                        worker_url=cf_worker_url,
                        api_key=cf_worker_key,
                        timeout_seconds=12.0,
                    ),
                ))

            # Tier 5 — SambaNova (Meta-Llama-3.3-70B-Instruct)
            if sambanova_key and len(sambanova_key) > 10:
                sn_model = os.getenv("SAMBANOVA_MODEL", "Meta-Llama-3.3-70B-Instruct")
                ordered_providers.append((
                    f"sambanova:{sn_model}",
                    HttpOpenAIBackend(
                        api_key=sambanova_key,
                        base_url=os.getenv("SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1"),
                        default_model=sn_model,
                        timeout_seconds=16.0,
                    ),
                ))

            # Tier 6 — Groq (al final: límite 7.000 ITPM free-tier, siempre excedido por TALOS)
            # Útil como último recurso si todos los demás fallan.
            if groq_key and groq_key.startswith("gsk_"):
                groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
                ordered_providers.append((
                    f"groq:{groq_model}",
                    HttpOpenAIBackend(
                        api_key=groq_key,
                        base_url="https://api.groq.com/openai/v1",
                        default_model=groq_model,
                        timeout_seconds=6.0,
                    ),
                ))

            # Tier 7 — NVIDIA NIM (~22s TTFT on reasoning models, word-replay path)
            if nvidia_key and nvidia_key.startswith("nvapi-"):
                nvidia_model = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
                ordered_providers.append((
                    f"nvidia:{nvidia_model}",
                    HttpOpenAIBackend(
                        api_key=nvidia_key,
                        base_url=os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"),
                        default_model=nvidia_model,
                        timeout_seconds=30.0,
                    ),
                ))

            # Cerebras (PENDIENTE BILLING: HTTP 402) — descomentar para reactivar:
            # cerebras_key = (os.getenv("CEREBRAS_API_KEY") or "").strip()
            # if cerebras_key and cerebras_key.startswith("csk-"):
            #     ...

        # MultiFallbackBackend con timeouts específicos por proveedor
        multi_backend = MultiFallbackBackend(
            providers=ordered_providers if ordered_providers else [("offline_oracle_stub", OfflinePedagogicalBackend())],
            timeout_per_provider=12.0,
        )

        llm_client = LLMClient(backend=multi_backend)
        tutor = StructuredTutor(generator=llm_client)
        tutor_adapter = StructuredTutorAdapter(tutor)
        self.orchestrator.tutor_port = tutor_adapter

        # Expose provider metadata for health / status endpoints
        if ordered_providers:
            first_name = ordered_providers[0][0]
            self.provider_name = first_name.split(":")[0]
            self.model_name = first_name.split(":", 1)[-1] if ":" in first_name else first_name
        else:
            self.provider_name = "offline_oracle"
            self.model_name = "talos-pedagogical-oracle-v1"

        self.llm_backend = multi_backend


    def _init_student_services(self) -> None:
        """Configure Student cognitive layer services (Phase E3)."""
        from study_engine.student.storage import StudentStorage
        from study_engine.student.bkt_tracker import BKTTracker
        from study_engine.student.spaced_repetition import SpacedRepetitionScheduler
        from study_engine.student.readiness_probe import ReadinessProbe
        from study_engine.student.pedagogical_memory import PedagogicalMemoryTracker
        from study_engine.student.memory_extractor import PedagogicalMemoryExtractor

        db_path = ":memory:" if self.use_mock else (self.working_dir / "student_state.db")
        self.student_storage = StudentStorage(db_path)

        # Parámetros BKT configurables (config/bkt_params.json): modo estricto
        # (ningún intento incorrecto sube P(L) por sí solo).
        from study_engine.student.bkt_tracker import load_bkt_params
        self.bkt_tracker = BKTTracker(self.student_storage, default_params=load_bkt_params())

        from study_engine.pedagogy.exercise_service import StruggleTracker
        self.struggle_tracker = StruggleTracker()

        from study_engine.pedagogy.generated_registry import GeneratedExerciseRegistry
        self.generated_registry = GeneratedExerciseRegistry(self.student_storage)
        self.spaced_scheduler = SpacedRepetitionScheduler(self.student_storage)
        self.pedagogical_memory_tracker = PedagogicalMemoryTracker(self.student_storage)
        self.pedagogical_memory_extractor = PedagogicalMemoryExtractor(self.pedagogical_memory_tracker)

        from study_engine.student.preference_tracker import PreferenceTracker
        from study_engine.student.learning_patterns import LearningPatternsTracker
        from study_engine.memory.session_memory import SessionMemoryManager
        from study_engine.memory.mem0_manager import Mem0Manager

        self.preference_tracker = PreferenceTracker(self.student_storage)
        self.learning_patterns = LearningPatternsTracker(self.student_storage)

        from study_engine.memory.session_history import SessionHistory
        from study_engine.memory.session_briefing import SessionBriefingGenerator

        # SessionHistory persistente (archivo, no :memory:) compartido por el
        # briefing y por la capa episódica de Mem0; si SessionMemoryManager no
        # recibe uno, cae a un SessionHistory() en :memory: y los turnos se
        # pierden al reiniciar el backend.
        self.session_history = SessionHistory(db_path)
        self.session_memory = SessionMemoryManager(
            student_storage=self.student_storage,
            session_history=self.session_history,
        )
        self.mem0_manager = Mem0Manager(
            student_storage=self.student_storage,
            preference_tracker=self.preference_tracker,
            learning_patterns=self.learning_patterns,
            session_memory=self.session_memory,
        )
        from study_engine.pedagogy.memory.store import CognitiveProfileStore
        from study_engine.pedagogy.memory.injector import ProfileInjector
        from study_engine.pedagogy.memory.extractor import CognitiveExtractor

        self.cognitive_profile_store = CognitiveProfileStore(db_path)
        self.profile_injector = ProfileInjector(self.cognitive_profile_store)
        self.cognitive_extractor = CognitiveExtractor(self.cognitive_profile_store)

        self.session_briefing_generator = SessionBriefingGenerator(
            bkt_tracker=self.bkt_tracker,
            sm2_scheduler=self.spaced_scheduler,
            session_history=self.session_history,
            student_storage=self.student_storage,
            cognitive_profile_store=self.cognitive_profile_store,
        )

        def _get_node_prereqs(node_id: str) -> List[str]:
            roadmap = self.get_roadmap()
            return [
                dep.source_node_id
                for dep in roadmap.dependencies
                if dep.target_node_id == node_id
            ]

        self.readiness_probe = ReadinessProbe(
            bkt=self.bkt_tracker,
            get_prerequisites_fn=_get_node_prereqs,
        )

    def _init_pedagogy_services(self) -> None:
        """Configure Pedagogical vertical slice services."""
        from study_engine.audit.auditor import ForensicAuditor
        from study_engine.federation.notebook_registry import NotebookRegistry
        from study_engine.pedagogy.bridge import ObservationBridge
        from study_engine.pedagogy.concept_builder import ConceptPacketBuilder
        from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler
        from study_engine.pedagogy.exercise_store import ExerciseStore
        from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
        from study_engine.pedagogy.orchestrator import PedagogicalOrchestrator

        self.notebook_registry = NotebookRegistry()
        self._seed_curriculum_tree(self.knowledge_store, self.notebook_registry)
        self.evidence_assembler = MultiSourceEvidenceAssembler(knowledge_store=self.knowledge_store)
        self.concept_builder = ConceptPacketBuilder()
        self.forensic_auditor = ForensicAuditor()
        self.auditor = self.forensic_auditor  # Fix 0.2: Expose auditor alias for chat and dialogue
        self.exercise_store = ExerciseStore()
        self.mc_grader = MultiChoiceGrader()
        self.exact_grader = ExactMatchGrader()
        self.observation_bridge = ObservationBridge(bkt_tracker=self.bkt_tracker)
        self.pedagogical_orchestrator = PedagogicalOrchestrator(
            notebook_registry=self.notebook_registry,
            evidence_assembler=self.evidence_assembler,
            concept_builder=self.concept_builder,
            forensic_auditor=self.forensic_auditor,
            exercise_store=self.exercise_store,
            bkt_tracker=self.bkt_tracker,
        )

        # Fase 5.1: KCs manuales (tabla notebook_kcs) fundidos con el catálogo
        # JSON canónico; el orquestador/matcher/BKT ven el syllabus completo.
        from study_engine.curriculum.kc_admin import KCAdminStore, merge_manual_kcs

        self.kc_admin = KCAdminStore(self.knowledge_store.engine)
        try:
            merge_manual_kcs(
                self.pedagogical_orchestrator._kc_catalog,
                self.kc_admin.catalog_dump(),
            )
        except Exception as kc_err:
            logger.warning("No se pudieron fundir KCs manuales al boot: %s", kc_err)

    def _init_dialogue_and_session(self) -> None:
        """Configure Socratic Dialogue Engine and Unified Study Session Orchestrator."""
        from study_engine.pedagogy.dialogue_policy import DialoguePolicy
        from study_engine.pedagogy.dialogue_state import DialogueStateTracker
        from study_engine.pedagogy.dialogue_engine import DialogueEngine
        from study_engine.session.study_session_orchestrator import StudySessionOrchestrator
        from study_engine.session.progression_policy import ProgressionPolicy
        from study_engine.session.opening_brief_builder import OpeningBriefBuilder

        self.dialogue_policy = DialoguePolicy()
        self.dialogue_state_tracker = DialogueStateTracker()
        self.dialogue_engine = DialogueEngine(
            dialogue_policy=self.dialogue_policy,
            state_tracker=self.dialogue_state_tracker,
            exercise_selector=self.exercise_store,
            forensic_auditor=self.forensic_auditor,
        )

        self.progression_policy = ProgressionPolicy()
        self.opening_brief_builder = OpeningBriefBuilder(self.progression_policy)
        self.study_session_orchestrator = StudySessionOrchestrator(
            notebook_registry=self.notebook_registry,
            pedagogical_orchestrator=self.pedagogical_orchestrator,
            student_storage=self.student_storage,
            progression_policy=self.progression_policy,
            opening_brief_builder=self.opening_brief_builder,
        )

    def _seed_curriculum_tree(self, store: Any, reg: Any) -> None:
        """Idempotently register canonical folders and notebooks in KnowledgeStore."""
        from study_engine.hierarchy.folder import Folder
        from study_engine.contracts.notebook import Notebook

        now = datetime.now(timezone.utc)
        if hasattr(store, "contains_folder") and not store.contains_folder("folder_root"):
            try:
                store.create_folder(
                    Folder(id="folder_root", name="Root Workspace", parent_folder_id=None, created_at=now, updated_at=now)
                )
            except Exception:
                pass

        canonical_folders = [
            ("fadena", "FADENA", "folder_root"),
            ("fadena_1ano", "1er Año", "fadena"),
            ("fadena_1ano_2cuat", "2do Cuatrimestre", "fadena_1ano"),
            ("roadmap", "Roadmap", "folder_root"),
            ("roadmap_fase0", "Fase 0", "roadmap"),
        ]
        for fid, fname, pid in canonical_folders:
            if hasattr(store, "contains_folder") and not store.contains_folder(fid):
                try:
                    store.create_folder(
                        Folder(id=fid, name=fname, parent_folder_id=pid, created_at=now, updated_at=now)
                    )
                except Exception:
                    pass

        nb_folder_map = {
            "fase0-soc": "roadmap_fase0",
            "fadena-lenguajes": "fadena_1ano_2cuat",
            "fadena-so2": "fadena_1ano_2cuat",
            "fadena-std": "fadena_1ano_2cuat",
            "fadena-teleco": "fadena_1ano_2cuat",
        }

        existing_sources = set()
        try:
            with store.engine.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT source_id FROM sources;")
                existing_sources = {r[0] for r in cursor.fetchall()}
        except Exception:
            pass

        if hasattr(reg, "list_notebooks") and hasattr(store, "contains_notebook"):
            bridge_params = []
            for nb in reg.list_notebooks():
                folder_id = nb_folder_map.get(nb.notebook_id, "folder_root")
                valid_sources = [s for s in nb.sources if s in existing_sources]
                if not store.contains_notebook(nb.notebook_id):
                    try:
                        nb_obj = Notebook(
                            id=nb.notebook_id,
                            name=nb.name,
                            description=nb.subject,
                            subject=nb.subject,
                            curriculum_id="fadena_v1",
                            folder_id=folder_id,
                            sources=valid_sources,
                            created_at=now,
                            updated_at=now,
                            metadata={},
                        )
                        store.create_notebook(nb_obj)
                    except Exception:
                        pass
                else:
                    for src_id in valid_sources:
                        bridge_params.append((nb.notebook_id, src_id))

            if bridge_params:
                try:
                    with store.engine.transaction() as conn:
                        cur = conn.cursor()
                        cur.executemany(
                            "INSERT OR IGNORE INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
                            bridge_params,
                        )
                except Exception:
                    pass

    def get_roadmap(self) -> CurricularRoadmap:
        """Access the authoritative active curricular roadmap."""
        return self.orchestrator.roadmap

    def get_current_student_state(self) -> StudentState:
        """Derive the pure, sovereign student state from the current ledger."""
        now = datetime.now(timezone.utc)
        return self.orchestrator._derive_state(now)


import threading

_container: Optional[AppContainer] = None
_container_lock = threading.Lock()


def get_container() -> AppContainer:
    """FastAPI dependency provider for AppContainer singleton."""
    global _container
    if _container is None:
        with _container_lock:
            if _container is None:
                _container = AppContainer()
    return _container


def set_container(container: AppContainer) -> None:
    """Explicitly set or override container (used by tests)."""
    global _container
    with _container_lock:
        _container = container

