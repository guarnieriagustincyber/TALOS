"""Practice evaluation and S6 execution endpoints."""

from enum import Enum
from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt, StrictStr

router = APIRouter(prefix="/api/practice", tags=["Practice"])


class EvaluationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ABSTAINED = "ABSTAINED"
    PRACTICE_UNAVAILABLE = "PRACTICE_UNAVAILABLE"


class AssertionCheck(BaseModel):
    model_config = ConfigDict(strict=True)

    id: StrictStr
    description: StrictStr
    passed: StrictBool
    error_detail: Optional[StrictStr] = None


class PracticeEvaluateRequest(BaseModel):
    model_config = ConfigDict(strict=True)

    task_id: StrictStr
    file_path: StrictStr = Field(..., description="Path to student practice solution")
    command: StrictStr = Field(default=":eval")


class PracticeEvaluateResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    task_id: StrictStr
    status: EvaluationStatus
    assertions: List[AssertionCheck]
    assertions_passed: StrictInt
    assertions_total: StrictInt
    execution_time_ms: StrictFloat
    stdout: StrictStr
    stderr: StrictStr
    ledger_block_hash: Optional[StrictStr] = Field(None, description="SHA-256 ledger block hash")
    ledger_timestamp: Optional[StrictStr] = None


@router.post("/evaluate", response_model=PracticeEvaluateResponse)
async def evaluate_practice(req: PracticeEvaluateRequest) -> PracticeEvaluateResponse:
    """Evaluate practical task submission in S6 isolated sandbox.

    [FIX 2.1]: Retorna PRACTICE_UNAVAILABLE fail-closed indicando honestamente que el
    sandbox de ejecución real S6 no está montado en esta versión, eliminando aserciones simuladas.
    """
    return PracticeEvaluateResponse(
        task_id=req.task_id,
        status=EvaluationStatus.PRACTICE_UNAVAILABLE,
        assertions=[],
        assertions_passed=0,
        assertions_total=0,
        execution_time_ms=0.0,
        stdout="[S6] Sandbox de ejecución real no disponible en esta versión.",
        stderr="",
        ledger_block_hash=None,
        ledger_timestamp=None,
    )
