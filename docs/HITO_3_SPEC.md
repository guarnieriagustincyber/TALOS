# ESPECIFICACIÓN TÉCNICA DE CONTRATOS Y PUERTOS — HITO 3
## KASIU / STUDY ENGINE — SUBSISTEMAS S4.3, S5.3 & S4.4

**Estado:** `DRAFT SPECIFICATION — PENDING TECH LEAD REVIEW`  
**Fecha:** 2026-09-06  
**Autor:** Antigravity (Implementador Controlado)  
**Base Normativa:** `PROTOCOLO MAESTRO DE CONTINUACIÓN (Secciones 6 a 20)`  
**Invariantes Centrales:**  
1. `DETERMINISTIC CODE FIRST → AI SECOND`  
2. `LLM ≠ SOURCE OF TRUTH` (El modelo solo propone lenguaje; jamás modifica estado, ledger ni currículum).  
3. `FAIL-CLOSED ABSOLUTO` (Ante rechazo de S4.4, falta de evidencia o nodo no autorizado → Abstención Canónica inmediata; cero bucles de auto-reparación).

---

## 1. REPORTE DE INSPECCIÓN FORENSE: MAPA DE DEPENDENCIAS Y AUTORIDADES

### 1.1. Estado de Autoridad Existente por Directorio

| Subsistema / Directorio | Módulos Clave | Responsabilidad y Autoridad Existente | Estado de Gobernanza |
|---|---|---|---|
| **`src/study_engine/generation/`** | `base.py`<br>`prompts.py`<br>`parser.py`<br>`mock.py`<br>`tutor.py` | • `BaseGenerator`: Protocolo que fuerza a generadores a emitir `RawGenerationResult`.<br>• `PromptAssembler`: Ensamblado determinista de `PromptBundle` respetando la jerarquía de prompts.<br>• `GenerationOutputParser`: **Única autoridad** para validar citas `[E#]` léxicas y emitir `GenerationResponse`.<br>• `StructuredTutor`: Fachada autoritativa que conecta generador + parser sin fabricar respuestas ad-hoc. | **ABIERTO (S4.2/S4.3)**<br>(Sujeto a extensión sin duplicación) |
| **`src/study_engine/llm/`** | `backends.py`<br>`client.py`<br>`exceptions.py` | • `ProviderBackend`: Protocolo para backends (`MockBackend`, `RuleBasedBackend`, `HttpOpenAIBackend`).<br>• `LLMClient`: Implementación de `BaseGenerator` que delega en backend y emite `RawGenerationResult`. | **ABIERTO (S4.3)** |
| **`src/study_engine/audit/`** | `auditor.py`<br>`contracts.py`<br>`engine.py`<br>`nli.py` | • `ForensicAuditor` (S4.4): Evalúa Layer 1 (determinista) y Layer 2 (NLI).<br>• Emite `ForensicAuditReport` con veredictos cerrados (`APPROVED`, `REJECTED_*`, `FLAGGED_UNASSESSED`). | **FROZEN INMUTABLE**<br>(Solo consumo vía contrato) |
| **`src/study_engine/session/`** | `contracts.py`<br>`ports.py`<br>`fsm.py`<br>`orchestrator.py` | • `SessionFSM`: Ciclo de vida estricto de la sesión.<br>• `TurnReceiptStore`: Idempotencia operacional durable por hash canónico de la petición.<br>• `SessionOrchestrator`: Coordinador operacional de turnos. | **ABIERTO (S5.3)**<br>(Requiere refactor de puertos) |

---

### 1.2. Hallazgo Forense de Inspección: `Finding ID: H3-INSPECT-01`

* **Finding ID:** `H3-INSPECT-01`
* **Severidad:** `DESIGN WEAKNESS & AUTHORITY DUPLICATION`
* **Ubicación:** `src/study_engine/session/orchestrator.py:107-109` y `438-470`
* **Descripción del Defecto:**
  En la implementación actual de `SessionOrchestrator`, los hooks para retrieval, generación y auditoría fueron definidos como funciones tipadas de manera ad-hoc:
  ```python
  retrieval_fn: Optional[Callable[[str, str], Optional[str]]] = None,
  generation_fn: Optional[Callable[[str, str], str]] = None,
  audit_fn: Optional[Callable[[str, str], Tuple[str, bool]]] = None,
  ```
  Esto presenta tres violaciones graves del *Principio de No Duplicación de Autoridad*:
  1. `retrieval_fn` espera un `Optional[str]` plano en lugar de interactuar con el `RetrievalService` y el `Epistemic Gatekeeper` certificado en el Hito 2.
  2. `generation_fn` omite `GenerationRequest`, `PackagedContext`, `GenerationOutputParser` y `CitationManifest`, devolviendo texto sin validar con un fallback hardcodeado (`f"Feedback for turn {self.current_turn_index}..."`).
  3. `audit_fn` no consume `ForensicAuditInput` ni `ForensicAuditor`, y ante rechazo (`is_approved == False`) levanta una excepción no controlada (`raise AuditRejectionError`) en lugar de materializar la política obligatoria de **Abstención Canónica Inmediata (Fail-Closed)** en el ciclo de vida del turno.
* **Impacto en Hito 3:** Impide la trazabilidad de citas `[E#]`, desconecta el Epistemic Gatekeeper e introduce riesgo de fallos no controlados.
* **Propuesta de Remediación en Especificación:**
  Deprecar los argumentos `retrieval_fn`, `generation_fn` y `audit_fn` en favor de **Puertos Tipados formales (`typing.Protocol`)**: `RetrievalPort`, `TutorPort` y `AuditPort`. Sustituir la excepción de rechazo por la emisión soberana de `TurnActionType.ABSTENTION` con `SessionResultStatus.ABSTAINED` y preservación de la traza de auditoría.

---

## 2. CONTRATOS DEL GENERADOR (HITO 3.1)

Los contratos respetan Pydantic v2 (`frozen=True, extra="forbid"`).

```python
from enum import Enum
from typing import Any, Dict, Optional, Tuple
from pydantic import ConfigDict, Field
from study_engine.contracts.base import BaseContract
from study_engine.contracts.evidence_engine import PackagedContext
from study_engine.contracts.generation import GenerationMode, TokenUsage


class GenerationProfile(BaseContract):
    """Configuración pedagógica y operativa inmutable para una generación."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    profile_id: str = Field(..., min_length=1, description="Identificador del perfil")
    mode: GenerationMode = Field(
        default=GenerationMode.EXPLANATION,
        description="Modo pedagógico cerrado (EXPLANATION, SOCRATIC_TUTOR, etc.)",
    )
    language: str = Field(
        default="es",
        min_length=2,
        max_length=5,
        description="Código ISO de idioma obligatorio",
    )
    strict_citations: bool = Field(
        default=True,
        description="Si es True, toda afirmación fáctica requiere cita [E#]",
    )
    max_output_tokens: int = Field(
        default=500,
        gt=0,
        description="Límite superior de tokens para la respuesta",
    )
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Temperatura de muestreo (0.0 para reproducibilidad determinista)",
    )


class GenerationRequest(BaseContract):
    """Solicitud autoritativa de generación con contexto empaquetado hermético."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    request_id: str = Field(..., min_length=1, description="Identificador único de solicitud")
    student_id: str = Field(..., min_length=1, description="ID del estudiante")
    node_id: str = Field(..., min_length=1, description="Nodo curricular al que se acota la sesión")
    notebook_id: str = Field(..., min_length=1, description="Cuaderno curricular soberano")
    query: str = Field(..., min_length=1, description="Pregunta o consulta del estudiante")
    packaged_context: PackagedContext = Field(
        ..., description="Contexto empaquetado hermético del Hito 2 con CitationManifest"
    )
    profile: GenerationProfile = Field(
        ..., description="Perfil pedagógico inmutable"
    )


class GenerationResult(BaseContract):
    """Resultado crudo de generación con trazabilidad criptográfica de prompts y contexto."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    raw_content: str = Field(..., min_length=1, description="Texto crudo generado por el backend")
    prompt_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 canónico del prompt ensamblado",
    )
    context_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 canónico del PackagedContext",
    )
    model_name: str = Field(..., min_length=1, description="Nombre exacto del modelo/backend ejecutor")
    latency_ms: float = Field(..., ge=0.0, description="Latencia de generación en milisegundos")
    tokens_used: Optional[TokenUsage] = Field(
        default=None, description="Telemetría de tokens consumidos"
    )
    generator_abstained: bool = Field(
        default=False, description="Indica si el generador declaró abstención explícita"
    )
```

### 2.1. Especificación del `MockBackend` con Replay Determinista

Para garantizar que los tests unitarios y de regresión se ejecuten en aislamiento hermético (sin red y sin variabilidad estocástica):
1. **Fórmula de Identidad de Replay:**  
   $$\text{ReplayKey} = \text{SHA-256}(\text{query} \parallel \text{node\_id} \parallel \text{context\_hash} \parallel \text{profile\_id})$$
2. **Invariante:**  
   $\text{Misma Solicitud} + \text{Mismo Contexto} + \text{Mismo Fixture} \Longrightarrow \text{Mismo Output Idéntico}$
3. **Mapeo Explícito por Entorno:**  
   La selección del backend se gobernará por la variable de entorno `STUDY_ENGINE_LLM_BACKEND`:
   * Valores válidos: `"mock"`, `"rule-based"`, `"http-openai"`.
   * Prohibido `"AUTO"`. Prohibido fallback silencioso entre proveedores.
   * Default en entorno de pruebas: `"mock"`.

---

## 3. PUERTOS DEL SESSION ORCHESTRATOR (HITO 3.2)

Se establecen protocolos tipados para desacoplar el orquestador de las implementaciones concretas, garantizando el respeto al perímetro congelado y la no duplicación de autoridad.

```python
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from study_engine.audit.contracts import ForensicAuditReport
from study_engine.contracts.generation import GenerationResponse
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.curriculum.registry import CurriculumRegistry


@runtime_checkable
class RetrievalPort(Protocol):
    """Puerto soberano de recuperación con filtrado curricular a priori."""

    def retrieve_evidence(
        self,
        query: str,
        node_id: str,
        registry: CurriculumRegistry,
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Recupera candidatos aplicando el Epistemic Gatekeeper sobre la matriz curricular."""
        ...


@runtime_checkable
class TutorPort(Protocol):
    """Puerto de generación pedagógica controlada y parseo determinista."""

    def generate_tutoring(
        self,
        request: GenerationRequest,
    ) -> GenerationResponse:
        """Genera respuesta y la valida mediante GenerationOutputParser."""
        ...


@runtime_checkable
class AuditPort(Protocol):
    """Puerto de auditoría forense S4.4 (Layer 1 determinista + Layer 2 NLI)."""

    def audit_response(
        self,
        request: GenerationRequest,
        response: GenerationResponse,
    ) -> ForensicAuditReport:
        """Audita la respuesta generada contra el contexto empaquetado hermético."""
        ...
```

### 3.1. Contratos de Solicitud y Resultado de Sesión

```python
class SessionRequest(BaseContract):
    """Petición de interacción enviada por el estudiante al orquestador."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str = Field(..., min_length=1, description="Identificador de sesión")
    student_id: str = Field(..., min_length=1, description="Identificador del estudiante")
    node_id: str = Field(..., min_length=1, description="Nodo curricular foco")
    query: str = Field(..., min_length=1, description="Consulta del estudiante")
    mode: GenerationMode = Field(
        default=GenerationMode.EXPLANATION,
        description="Modo de interacción formativa solicitado",
    )
    turn_index: int = Field(default=0, ge=0, description="Índice secuencial del turno")


class SessionResultStatus(str, Enum):
    """Taxonomía cerrada de estados de respuesta de una sesión."""

    APPROVED = "APPROVED"          # Verificado por S4.4 y admitido
    ABSTAINED = "ABSTAINED"        # Sin evidencia o rechazado por S4.4 (Fail-Closed)
    FAIL_CLOSED = "FAIL_CLOSED"    # Violación de precondición o bloqueo curricular duro


class SessionResult(BaseContract):
    """Resultado final inmutable entregado al alumno y persistido operativamente."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str = Field(..., min_length=1, description="ID de sesión")
    turn_id: str = Field(..., min_length=1, description="ID único del turno procesado")
    node_id: str = Field(..., min_length=1, description="Nodo curricular autorizado")
    status: SessionResultStatus = Field(..., description="Veredicto final de la sesión")
    response_text: str = Field(..., min_length=1, description="Texto de respuesta o aviso de abstención")
    audit_report_id: Optional[str] = Field(
        default=None, description="ID del reporte de auditoría S4.4 asociado"
    )
    abstention_reason: Optional[str] = Field(
        default=None, description="Razón formal de abstención si status != APPROVED"
    )
    audit_trace: Dict[str, Any] = Field(
        default_factory=dict, description="Metadatos forenses inmutables del turno"
    )
```

---

## 4. ESTRUCTURA DE REPLAY FIXTURES (JSON)

Para los tests unitarios herméticos, se establecen dos fixtures canónicos en `data/experiments/hito3/generation_replay.json`:

```json
{
  "fixtures": {
    "fixture_approved_concurrency_01": {
      "replay_key": "a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
      "node_id": "SEC-04-CONCURR",
      "query": "¿Qué es una condición de carrera?",
      "context_hash": "c0ffee0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      "profile_id": "profile_strict_v1",
      "raw_content": "Según se documenta en [E1], una condición de carrera ocurre cuando dos o más procesos acceden a un espacio de memoria compartida sin sincronización apropiada, produciendo resultados dependientes del orden de ejecución.",
      "citations_manifest_expected": ["E1"],
      "expected_audit_verdict": "APPROVED",
      "expected_session_status": "APPROVED"
    },
    "fixture_rejected_hallucination_02": {
      "replay_key": "f0e1d2c3b4a5968778695a4b3c2d1e0f9876543210fedcba9876543210fedcba",
      "node_id": "SEC-04-CONCURR",
      "query": "¿Cómo funciona el algoritmo de Dekker?",
      "context_hash": "c0ffee0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
      "profile_id": "profile_strict_v1",
      "raw_content": "El algoritmo de Dekker utiliza variables de turno y banderas booleanas según [E99], garantizando exclusión mutua perfecta en procesadores cuánticos.",
      "citations_manifest_expected": ["E1"],
      "injected_phantom_citations": ["E99"],
      "expected_audit_verdict": "REJECTED_UNSUPPORTED",
      "expected_session_status": "ABSTAINED",
      "expected_abstention_reason": "Forensic audit S4.4 rejected ungrounded claim or phantom citation [E99]."
    }
  }
}
```

---

## 5. PLAN DE MIGRACIÓN Y PRÓXIMO PASO

Una vez revisado y aprobado este documento por el Tech Lead:
1. Se procederá al **Paso 3 (Implementación Mínima)** del Hito 3.1:
   - Crear adaptadores de configuración de backends en `src/study_engine/llm/`.
   - Implementar el cargador y ejecutor de `generation_replay.json`.
   - Corregir en `SessionOrchestrator` la vulnerabilidad `H3-INSPECT-01` mediante la adopción de los puertos tipados formales.
2. Ejecutar la suite de tests obligatorios (§8 del Protocolo Maestro).
3. Mantener intacto en un 100% el perímetro congelado.
