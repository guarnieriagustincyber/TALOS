from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class EvaluationStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    ABSTAINED = "ABSTAINED"


class AssertionCheck(BaseModel):
    id: str
    description: str
    passed: bool
    error_detail: Optional[str] = None


class PracticeEvaluateRequest(BaseModel):
    task_id: str
    file_path: str = Field(..., description="Ruta absoluta o relativa al script local")
    command: str = Field(default=":eval")


class PracticeEvaluateResponse(BaseModel):
    task_id: str
    status: EvaluationStatus
    assertions: List[AssertionCheck]
    assertions_passed: int
    assertions_total: int
    execution_time_ms: float
    stdout: str
    stderr: str
    ledger_block_hash: Optional[str] = Field(None, description="Digest SHA-256 emitido por el Ledger tras aprobación")
    ledger_timestamp: Optional[str] = None
