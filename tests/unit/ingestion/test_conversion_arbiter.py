"""Hermetic tests for ConversionArbiter and CAL-1 canonical selection rules."""

import pytest

from study_engine.ingestion.conversion_arbiter import (
    ConversionArbiter,
    DELTA_CANONICAL_THRESHOLD,
    TAU_CONFLICT_THRESHOLD,
)
from study_engine.ingestion.conversion_audit import ConversionAuditReport, ConversionAuditor
from study_engine.ingestion.converters.base import ConversionResult


def _make_sample_result(converter_id: str, content: str) -> ConversionResult:
    return ConversionResult(
        converter_id=converter_id,
        converter_version="1.0.0",
        markdown_content=content,
        tables_count=1 if "|" in content else 0,
        code_blocks_count=1 if "```" in content else 0,
        headers_count=1 if "#" in content else 0,
        tokens_count=len(content.split()),
        page_count=1,
        page_map={1: content},
        has_ocr=False,
        ocr_provenance="none",
        trust_level="verified",
        formulas_detected=False,
        formulas_unextracted=False,
        sha256_output=f"sha256_{converter_id}_" + "0" * 45,
    )


def test_normalized_diff_whitespace_insensitive():
    """Normalized diff ignores superficial spacing and casing."""
    text_a = "# Header One\n\nSome paragraph with   spaces.\n"
    text_b = "# HEADER ONE\nSome paragraph with spaces.\n"

    diff = ConversionArbiter.compute_normalized_diff(text_a, text_b)
    assert diff == 0.0


def test_conflict_detection_when_divergence_exceeds_threshold():
    """When structural divergence > 0.12, CONVERSION_CONFLICT is flagged."""
    text_a = """# Process Synchronization
Producer consumer pattern using semaphores in POSIX.
```c
sem_wait(&empty);
buffer[in] = item;
sem_post(&full);
```
"""
    text_b = """# Completely Different Chapter
Virtual Memory Paging and Demand Paging Algorithms.
The page replacement algorithm chooses victim pages using LRU.
"""
    arbiter = ConversionArbiter()
    prim = _make_sample_result("markitdown", text_a)
    sec = _make_sample_result("anydoc_local", text_b)

    decision = arbiter.arbitrate(prim, sec, expected_pages=1)
    assert decision.conflict_flag is True
    assert decision.conflict is not None
    assert decision.conflict.diff_stat > TAU_CONFLICT_THRESHOLD
    assert decision.conflict.converter_a == "markitdown"
    assert decision.conflict.converter_b == "anydoc_local"


def test_cal1_canonical_selection_rule():
    """CAL-1: In conflict, Canonical = Primary unless sec_score - prim_score >= 0.15."""
    arbiter = ConversionArbiter()

    # Case 1: Primary and secondary are in conflict, but score difference < 0.15 -> Primary is canonical
    text_prim = """# Section 1: Memory Hierarchy
The memory hierarchy consists of registers, L1 cache, L2 cache, L3 cache, and RAM.
| Level | Latency | Size |
| :--- | :--- | :--- |
| L1 | 1 ns | 64 KB |
| RAM | 50 ns | 16 GB |
"""
    text_sec_divergent = """# Section 1: Storage Hierarchy
The storage system has registers, caches, main memory and disk arrays.
| Tier | Speed | Capacity |
| :--- | :--- | :--- |
| Cache | Fast | Small |
| Disk | Slow | Large |
"""
    prim = _make_sample_result("markitdown", text_prim)
    sec = _make_sample_result("anydoc_local", text_sec_divergent)

    decision = arbiter.arbitrate(prim, sec, expected_pages=1)
    assert decision.conflict_flag is True
    # Both have good structure, so score difference is small (< 0.15) -> Primary wins
    assert decision.canonical_result.converter_id == "markitdown"

    # Case 2: Primary has damaged structure (broken table), secondary is clean and exceeds primary by >= 0.15
    broken_prim_text = """# Broken Section
Some description without proper formatting.
| Broken Table Header |
No separator or closing
"""
    clean_sec_text = """# Clean Section
High quality extraction with well-formed table and balanced code.
| Col A | Col B |
| :--- | :--- |
| Val 1 | Val 2 |
```c
int x = 42;
```
"""
    prim_broken = _make_sample_result("markitdown", broken_prim_text)
    sec_clean = _make_sample_result("anydoc_local", clean_sec_text)

    decision_override = arbiter.arbitrate(prim_broken, sec_clean, expected_pages=1)
    assert decision_override.conflict_flag is True
    # Secondary significantly outperforms broken primary (>= 0.15) -> Secondary wins
    assert decision_override.canonical_result.converter_id == "anydoc_local"


def test_cal1_stability_under_epsilon_perturbation():
    """CAL-1 Stability Test: Canonical choice must be immune to +/- 0.02 score perturbations."""
    arbiter = ConversionArbiter()

    text_prim = """# Section: Concurrency
Deadlocks require mutual exclusion, hold and wait, no preemption, and circular wait.
| Condition | Description |
| :--- | :--- |
| Mutual Exclusion | One resource per thread |
| Hold and Wait | Thread holds resource while waiting |
"""
    text_sec = """# Section: Synchronization and Deadlocks
Four Coffman conditions lead to deadlock situations in concurrent environments.
| Requirement | Detail |
| :--- | :--- |
| Mutex | Exclusive access |
| Circular Wait | Cycle in resource allocation graph |
"""
    prim = _make_sample_result("markitdown", text_prim)
    sec = _make_sample_result("anydoc_local", text_sec)

    base_decision = arbiter.arbitrate(prim, sec, expected_pages=1)
    base_canon = base_decision.canonical_result.converter_id

    # Test perturbation: modify delta_canon by +/- 0.02 (simulating +/- epsilon score changes)
    epsilon = 0.02
    arbiter_plus = ConversionArbiter(delta_canon=DELTA_CANONICAL_THRESHOLD + epsilon)
    arbiter_minus = ConversionArbiter(delta_canon=DELTA_CANONICAL_THRESHOLD - epsilon)

    decision_plus = arbiter_plus.arbitrate(prim, sec, expected_pages=1)
    decision_minus = arbiter_minus.arbitrate(prim, sec, expected_pages=1)

    assert decision_plus.canonical_result.converter_id == base_canon
    assert decision_minus.canonical_result.converter_id == base_canon


def test_zero_text_averaging_or_smoothing():
    """Invariants: Candidate texts are preserved 100% intact without blending or smoothing."""
    arbiter = ConversionArbiter()
    text_a = "# Output from Converter A\nOriginal verbatim text A."
    text_b = "# Output from Converter B\nOriginal verbatim text B."

    prim = _make_sample_result("markitdown", text_a)
    sec = _make_sample_result("anydoc_local", text_b)

    decision = arbiter.arbitrate(prim, sec, expected_pages=1)

    assert len(decision.all_candidates) == 2
    assert decision.all_candidates[0].markdown_content == text_a
    assert decision.all_candidates[1].markdown_content == text_b
    assert decision.canonical_result.markdown_content in (text_a, text_b)
