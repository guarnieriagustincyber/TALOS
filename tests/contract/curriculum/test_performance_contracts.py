"""Contract tests for PerformanceLevel (S5.4)."""

import pytest
from enum import IntEnum
from study_engine.curriculum.performance_contracts import PerformanceLevel


def test_performance_level_is_int_enum() -> None:
    """HG-S5.4-O1: Inherits from IntEnum for deterministic ordinality."""
    assert issubclass(PerformanceLevel, IntEnum)
    assert issubclass(PerformanceLevel, int)


def test_performance_level_exact_domain_and_no_aliases() -> None:
    """Verify exactly 4 distinct levels without aliases."""
    assert len(PerformanceLevel) == 4
    assert set(PerformanceLevel) == {
        PerformanceLevel.N1_INSUFFICIENT,
        PerformanceLevel.N2_BASIC,
        PerformanceLevel.N3_COMPETENT,
        PerformanceLevel.N4_EXCELLENT,
    }
    values = [lvl.value for lvl in PerformanceLevel]
    assert values == [1, 2, 3, 4]
    assert len(set(values)) == 4


def test_performance_level_ordinal_comparisons() -> None:
    """Verify strict ordinal comparisons matching expectations."""
    n1 = PerformanceLevel.N1_INSUFFICIENT
    n2 = PerformanceLevel.N2_BASIC
    n3 = PerformanceLevel.N3_COMPETENT
    n4 = PerformanceLevel.N4_EXCELLENT

    assert n1 < n2 < n3 < n4
    assert n4 > n3 > n2 > n1
    assert n3 >= n2
    assert n3 >= n3
    assert n2 <= n3
    assert n1 <= n4
    assert n1 != n2
    assert n3 == PerformanceLevel.N3_COMPETENT


def test_deterministic_sorting() -> None:
    """Verify arbitrary collections sort deterministically."""
    unsorted = [
        PerformanceLevel.N4_EXCELLENT,
        PerformanceLevel.N1_INSUFFICIENT,
        PerformanceLevel.N3_COMPETENT,
        PerformanceLevel.N2_BASIC,
    ]
    sorted_levels = sorted(unsorted)
    assert sorted_levels == [
        PerformanceLevel.N1_INSUFFICIENT,
        PerformanceLevel.N2_BASIC,
        PerformanceLevel.N3_COMPETENT,
        PerformanceLevel.N4_EXCELLENT,
    ]


def test_label_and_description() -> None:
    """Verify short labels and descriptive strings."""
    assert PerformanceLevel.N1_INSUFFICIENT.label == "N1"
    assert PerformanceLevel.N2_BASIC.label == "N2"
    assert PerformanceLevel.N3_COMPETENT.label == "N3"
    assert PerformanceLevel.N4_EXCELLENT.label == "N4"

    for lvl in PerformanceLevel:
        assert len(lvl.description) > 10


def test_from_label_parsing() -> None:
    """Verify parsing from standard labels."""
    assert (
        PerformanceLevel.from_label("n1")
        == PerformanceLevel.N1_INSUFFICIENT
    )
    assert (
        PerformanceLevel.from_label("N2")
        == PerformanceLevel.N2_BASIC
    )
    assert (
        PerformanceLevel.from_label(" N3 ")
        == PerformanceLevel.N3_COMPETENT
    )
    assert (
        PerformanceLevel.from_label("N4")
        == PerformanceLevel.N4_EXCELLENT
    )

    with pytest.raises(ValueError, match="Invalid performance level label"):
        PerformanceLevel.from_label("N5")

    with pytest.raises(ValueError, match="Invalid performance level label"):
        PerformanceLevel.from_label("PASS")
