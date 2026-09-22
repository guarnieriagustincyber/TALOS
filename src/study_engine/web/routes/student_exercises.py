"""FastAPI routes for local student exercises (VSCode + TALOS Auditor).

Enables local file-based workflow:
1. Student writes solution in VSCode (data/student_submissions/{notebook}/{unit}/ej_XX.md).
2. Student clicks 'Verificar' in TALOS.
3. TALOS deterministically reads the file from disk, audits code/contracts/diagrams,
   updates BKT state, and returns forensic feedback.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from study_engine.pedagogy.auditors import (
    ExerciseAuditReport,
    get_auditor_for_notebook,
)
from study_engine.pedagogy.submission_reader import SubmissionReader
from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/student/exercises", tags=["Student Exercises"])

BASE_SUBMISSIONS_DIR = Path("data/student_submissions").resolve()
REPORTS_DIR = BASE_SUBMISSIONS_DIR / ".reports"


class ExerciseSummaryDto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    exercise_id: str
    title: str
    notebook_id: str
    unit_or_tramo: str
    relative_path: str
    absolute_path: str
    file_exists: bool
    status: str  # "PENDING", "SUBMITTED", "VERIFIED", "NEEDS_REVISION"
    last_score: Optional[float] = None
    last_verified_at: Optional[str] = None


class ExerciseDetailDto(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    exercise_id: str
    title: str
    notebook_id: str
    unit_or_tramo: str
    relative_path: str
    absolute_path: str
    template_type: str
    template_content: str
    file_exists: bool
    current_content: Optional[str] = None
    vscode_command: str


class VerifyExerciseRequest(BaseModel):
    custom_path: Optional[str] = None


def _get_template_for_notebook(notebook_id: str) -> Tuple[str, str]:
    templates_dir = BASE_SUBMISSIONS_DIR / "templates"
    nb = notebook_id.lower()
    if "so2" in nb or "operativo" in nb:
        t_file = templates_dir / "template_so.md"
        t_type = "so"
    elif "teleco" in nb or "redes" in nb:
        t_file = templates_dir / "template_telecom.md"
        t_type = "telecom"
    elif "sye" in nb or "sociedad" in nb or "estado" in nb:
        t_file = templates_dir / "template_fadena.md"
        t_type = "fadena"
    else:
        t_file = templates_dir / "template_programming.md"
        t_type = "programming"

    content = t_file.read_text(encoding="utf-8") if t_file.exists() else ""
    return t_type, content


def _find_submission_file(exercise_id: str, notebook_id: Optional[str] = None) -> Optional[Path]:
    """Locate submission file on disk by exercise_id across subdirectories."""
    # Check direct match with .md extension
    filename = exercise_id if exercise_id.endswith(".md") else f"{exercise_id}.md"

    if notebook_id:
        nb_dir = BASE_SUBMISSIONS_DIR / notebook_id
        if nb_dir.exists():
            matches = list(nb_dir.glob(f"**/{filename}"))
            if matches:
                return matches[0]

    # Global search within submissions dir
    matches = list(BASE_SUBMISSIONS_DIR.glob(f"**/{filename}"))
    if matches:
        return matches[0]
    return None


@router.get("", response_model=List[ExerciseSummaryDto])
def list_exercises(
    notebook_id: Optional[str] = Query(None, description="Filtrar por ID de cuaderno"),
    unit: Optional[str] = Query(None, description="Filtrar por tramo o unidad"),
) -> List[ExerciseSummaryDto]:
    """List available and submitted exercises from filesystem and catalog."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    results: List[ExerciseSummaryDto] = []

    # Scan submissions directory
    search_dir = BASE_SUBMISSIONS_DIR / notebook_id if notebook_id else BASE_SUBMISSIONS_DIR
    if not search_dir.exists():
        return []

    # Find all .md files excluding templates and reports
    md_files = [
        f for f in search_dir.glob("**/*.md")
        if "templates" not in f.parts and ".reports" not in f.parts
    ]

    for f in md_files:
        rel = f.relative_to(BASE_SUBMISSIONS_DIR)
        parts = rel.parts
        nb_id = parts[0] if len(parts) > 1 else (notebook_id or "fase0-soc")
        unit_str = parts[1] if len(parts) > 2 else "tramo1"
        ex_id = f.stem

        if unit and unit.lower() not in unit_str.lower():
            continue

        # Check for cached report
        report_file = REPORTS_DIR / f"{ex_id}.json"
        last_score = None
        last_ver = None
        current_status = "SUBMITTED"

        if report_file.exists():
            try:
                rep_data = json.loads(report_file.read_text(encoding="utf-8"))
                last_score = rep_data.get("score")
                last_ver = rep_data.get("timestamp")
                current_status = "VERIFIED" if rep_data.get("passed") else "NEEDS_REVISION"
            except Exception:
                pass

        results.append(
            ExerciseSummaryDto(
                exercise_id=ex_id,
                title=ex_id.replace("_", " ").title(),
                notebook_id=nb_id,
                unit_or_tramo=unit_str,
                relative_path=str(rel),
                absolute_path=str(f),
                file_exists=True,
                status=current_status,
                last_score=last_score,
                last_verified_at=last_ver,
            )
        )

    return results


class GenerateMultiKcRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    kc_ids: List[str] = Field(..., min_length=2, max_length=4)
    difficulty: Optional[str] = None


@router.post("/generate/multi-kc", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_multi_kc_exercise(
    payload: GenerateMultiKcRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Genera un ejercicio multi-KC (composición causal) y lo persiste."""
    from study_engine.pedagogy.exercise_compiler import compose_multi_kc_exercise

    catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    exercise = compose_multi_kc_exercise(
        list(payload.kc_ids), difficulty=payload.difficulty, catalog=catalog
    )
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay plantilla de composición para ese conjunto de KCs.",
        )
    container.generated_registry.save(exercise)
    return exercise


class GenerateDebugRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    kc_id: str = Field(..., min_length=1)
    bug_type: Optional[str] = Field(
        default=None,
        description="buffer_overflow|integer_overflow|race_condition|use_after_free (auto si no se indica)",
    )


@router.post("/generate/debugging", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_debugging_exercise_ep(
    payload: GenerateDebugRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Genera un ejercicio de depuración adversaria (código con bug inyectado)."""
    from study_engine.pedagogy.bug_generator import generate_debugging_exercise

    exercise = generate_debugging_exercise(payload.kc_id, bug_type=payload.bug_type)
    if exercise is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No hay plantilla de bug para ese KC/tipo.",
        )
    container.generated_registry.save(exercise)
    return exercise


class GenerateTraceRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    kc_id: str = Field(..., min_length=1)
    n_mutations: int = Field(default=2, ge=1, le=6)
    difficulty: Optional[str] = None


@router.post("/generate/trace", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def generate_trace_exercise_ep(
    payload: GenerateTraceRequest,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Genera un ejercicio de predicción de estado (trace-table) determinista."""
    from study_engine.pedagogy.state_predictor import generate_trace_exercise

    exercise = generate_trace_exercise(
        payload.kc_id, n_mutations=payload.n_mutations, difficulty=payload.difficulty
    )
    container.generated_registry.save(exercise)
    return exercise


@router.get("/available", response_model=Dict[str, Any])
def get_available_exercises(
    notebook_id: str = Query(..., description="ID del cuaderno"),
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Ejercicios QUALIFIABLE disponibles para los KCs del cuaderno (Fase 5.1).

    Conecta con el ExerciseStore certificado (fail-closed: solo QUALIFIABLE).
    Matchea por kc_id exacto contra el catálogo efectivo del cuaderno, o por
    prefijo ``{notebook_id}-`` para catálogos namespaced legados.
    """
    clean_id = notebook_id.strip()
    kc_catalog = getattr(container.pedagogical_orchestrator, "_kc_catalog", {})
    nb_entry = kc_catalog.get(clean_id, {}) if isinstance(kc_catalog, dict) else {}
    nb_kcs = {k.get("kc_id") for k in nb_entry.get("kcs", []) if isinstance(k, dict)}

    items: List[Dict[str, Any]] = []
    store = getattr(container, "exercise_store", None)
    if store is not None:
        for ex in store.list_all():
            if not ex.is_presentable():
                continue
            if nb_kcs and ex.kc_id not in nb_kcs and not ex.kc_id.startswith(f"{clean_id}-"):
                continue
            items.append({
                "exercise_id": ex.exercise_id,
                "kc_id": ex.kc_id,
                "title": (ex.prompt or "")[:80],
                "type": getattr(ex.exercise_type, "value", str(ex.exercise_type)),
                "difficulty": None,  # el certificado no lleva dificultad hoy
            })
    return {"notebook_id": clean_id, "total": len(items), "exercises": items}


@router.get("/{exercise_id}", response_model=ExerciseDetailDto)
def get_exercise_detail(
    exercise_id: str,
    notebook_id: Optional[str] = Query(None),
) -> ExerciseDetailDto:
    """Retrieve exercise metadata, recommended template, and local path for VSCode."""
    file_path = _find_submission_file(exercise_id, notebook_id)

    if file_path and file_path.exists():
        rel = file_path.relative_to(BASE_SUBMISSIONS_DIR)
        parts = rel.parts
        nb_id = parts[0] if len(parts) > 1 else (notebook_id or "fase0-soc")
        unit_str = parts[1] if len(parts) > 2 else "tramo1"
        content = file_path.read_text(encoding="utf-8")
        exists = True
        abs_path = str(file_path)
    else:
        nb_id = notebook_id or "fase0-soc"
        unit_str = "tramo1"
        filename = exercise_id if exercise_id.endswith(".md") else f"{exercise_id}.md"
        file_path = BASE_SUBMISSIONS_DIR / nb_id / unit_str / filename
        rel = file_path.relative_to(BASE_SUBMISSIONS_DIR)
        content = None
        exists = False
        abs_path = str(file_path)

    template_type, template_content = _get_template_for_notebook(nb_id)

    return ExerciseDetailDto(
        exercise_id=exercise_id,
        title=exercise_id.replace("_", " ").title(),
        notebook_id=nb_id,
        unit_or_tramo=unit_str,
        relative_path=str(rel),
        absolute_path=abs_path,
        template_type=template_type,
        template_content=template_content,
        file_exists=exists,
        current_content=content,
        vscode_command=f"code {abs_path}",
    )


@router.post("/{exercise_id}/verify", response_model=Dict[str, Any])
def verify_exercise(
    exercise_id: str,
    req: Optional[VerifyExerciseRequest] = None,
    container: AppContainer = Depends(get_container),
) -> Dict[str, Any]:
    """Audit local student exercise file from disk and update BKT cognitive state."""
    if req and req.custom_path:
        target_path = Path(req.custom_path)
    else:
        target_path = _find_submission_file(exercise_id)

    if not target_path or not target_path.exists():
        expected_path = target_path or (BASE_SUBMISSIONS_DIR / f"{exercise_id}.md")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Archivo de ejercicio '{exercise_id}.md' no encontrado en el disco local.\n"
                f"Crealo en: {expected_path}\n"
                f"Podés crearlo desde tu terminal con: code {expected_path}"
            ),
        )

    # 1. Parse submission with deterministic reader
    reader = SubmissionReader()
    try:
        submission = reader.parse(target_path)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Error al parsear el archivo Markdown: {str(exc)}",
        )

    # 2. Select domain auditor
    notebook_id = submission.metadata.get("notebook_id", "fase0-soc")
    auditor = get_auditor_for_notebook(notebook_id, bkt_tracker=container.bkt_tracker)

    # 3. Execute deterministic audit
    report = auditor.audit(submission)

    # 4. Save report in local storage for history
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"{exercise_id}.json"
    report_dict = report.to_dict()
    report_file.write_text(json.dumps(report_dict, indent=2, ensure_ascii=False), encoding="utf-8")

    return report_dict


@router.get("/{exercise_id}/report", response_model=Dict[str, Any])
def get_exercise_report(exercise_id: str) -> Dict[str, Any]:
    """Retrieve the latest audit report for a given exercise."""
    report_file = REPORTS_DIR / f"{exercise_id}.json"
    if not report_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No hay reporte previo de auditoría para '{exercise_id}'. Hacé click en 'Verificar' primero.",
        )
    return json.loads(report_file.read_text(encoding="utf-8"))


@router.post("/{exercise_id}/init-template", response_model=ExerciseDetailDto)
def init_exercise_template(
    exercise_id: str,
    notebook_id: Optional[str] = Query(None),
    unit: Optional[str] = Query(None),
) -> ExerciseDetailDto:
    """Initialize exercise markdown file on disk from template if not already present."""
    file_path = _find_submission_file(exercise_id, notebook_id)
    nb_id = notebook_id or "fase0-soc"
    unit_str = unit or "tramo1"

    if not file_path or not file_path.exists():
        filename = exercise_id if exercise_id.endswith(".md") else f"{exercise_id}.md"
        file_path = BASE_SUBMISSIONS_DIR / nb_id / unit_str / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        template_type, template_content = _get_template_for_notebook(nb_id)
        content = template_content.replace("[nombre_del_ejercicio]", exercise_id.replace("_", " ").title())
        file_path.write_text(content, encoding="utf-8")

    return get_exercise_detail(exercise_id, nb_id)

