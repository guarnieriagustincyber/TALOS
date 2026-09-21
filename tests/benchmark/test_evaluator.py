"""Test suite for Adversarial Benchmark Evaluator vs NotebookLM (Ola 6, Fase 6.4).

6 tests requeridos:
1. test_evaluator_loads_100_questions           -> Carga correctamente las 100 preguntas de questions.json
2. test_evaluator_classifies_categories         -> Clasifica preguntas en categorías correctas
3. test_evaluator_runs_deterministic_dimensions -> Ejecuta las 7 dimensiones deterministas por código
4. test_evaluator_runs_subjective_dimensions    -> Ejecuta las 3 dimensiones subjetivas con Judge LLM/rúbrica
5. test_report_generator_produces_valid_report  -> Produce reporte Markdown válido y JSON estructurado
6. test_retirement_criteria_evaluation          -> Evalúa correctamente el criterio de retiro (>=8/10)
"""

from pathlib import Path
import pytest

from benchmark.evaluator import BenchmarkEvaluator, BenchmarkRunResult, DIMENSION_SPECS
from benchmark.report_generator import BenchmarkReportGenerator


def test_evaluator_loads_100_questions() -> None:
    """1. BenchmarkEvaluator successfully loads exactly 100 adversarial questions."""
    evaluator = BenchmarkEvaluator()
    assert len(evaluator.questions) == 100
    assert evaluator.questions[0]["id"] == "Q001"
    assert evaluator.questions[-1]["id"] == "Q100"
    for q in evaluator.questions:
        assert "query" in q
        assert "category" in q
        assert "expected_behavior" in q


def test_evaluator_classifies_categories() -> None:
    """2. Evaluator partitions questions into the required pedagogical categories."""
    evaluator = BenchmarkEvaluator()
    cats = evaluator.get_questions_by_category()

    # Verify counts match the distribution in Condition 2
    assert len(cats["explicit_response"]) == 20
    assert len(cats["distributed_response"]) == 20
    assert len(cats["cross_source"]) == 20
    assert len(cats["contradictions"]) == 10
    assert len(cats["absent_information"]) == 10
    assert len(cats["trick_questions"]) == 10
    assert len(cats["anaphoric_synthesis"]) == 10


def test_evaluator_runs_deterministic_dimensions() -> None:
    """3. Evaluator executes the 7 deterministic dimensions with code authority."""
    evaluator = BenchmarkEvaluator()

    det_dimensions = [
        "evidence_precision",
        "citation_correctness",
        "abstention",
        "cross_source_recall",
        "long_context_retrieval",
        "ttft",
        "session_continuity",
    ]

    for dim_key in det_dimensions:
        res = evaluator.evaluate_deterministic_dimension(dim_key)
        assert res.dimension == dim_key
        assert res.authority == "deterministic"
        assert res.sample_count > 0
        assert isinstance(res.talos_score, (float, int))
        assert isinstance(res.passed, bool)


def test_evaluator_runs_subjective_dimensions() -> None:
    """4. Evaluator executes the 3 subjective dimensions with Judge LLM / Rubric authority."""
    evaluator = BenchmarkEvaluator()

    subj_dimensions = [
        "conversational_naturalness",
        "multimodal_understanding",
        "learning_adaptation",
    ]

    for dim_key in subj_dimensions:
        res = evaluator.evaluate_subjective_dimension(dim_key)
        assert res.dimension == dim_key
        assert res.authority == "llm_judge"
        assert res.sample_count > 0
        assert isinstance(res.talos_score, (float, int))
        assert isinstance(res.passed, bool)


def test_report_generator_produces_valid_report(tmp_path: Path) -> None:
    """5. ReportGenerator produces compliant Markdown report and structured JSON."""
    evaluator = BenchmarkEvaluator()
    run_result = evaluator.run_full_benchmark()

    generator = BenchmarkReportGenerator(output_dir=tmp_path)
    md_report = generator.generate_report(run_result)

    # Verify Markdown elements
    assert "# 📊 REPORTE DE EVALUACIÓN BENCHMARK ADVERSARIAL" in md_report
    assert "Matriz Comparativa por Dimensión" in md_report
    assert "Distribución de las 100 Preguntas por Categoría" in md_report
    assert "Análisis de las Cláusulas de Retiro de NotebookLM" in md_report
    assert "Dictamen Final de Retiro" in md_report

    # Verify files created on disk
    assert (tmp_path / "evaluation_report.md").exists()
    assert (tmp_path / "benchmark_results.json").exists()


def test_retirement_criteria_evaluation() -> None:
    """6. Retirement criterion is correctly authorized when >= 8 of 10 dimensions pass."""
    evaluator = BenchmarkEvaluator()
    run_result = evaluator.run_full_benchmark()

    assert run_result.total_dimensions == 10
    assert run_result.dimensions_passed >= 8
    assert run_result.retirement_authorized is True
    assert "AUTORIZADO" in run_result.summary
