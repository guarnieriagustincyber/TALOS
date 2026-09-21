#!/usr/bin/env python3
"""LagunaDetector Specificity and Sensitivity Evaluation (F8).

Evaluates 50 synthetic cases (25 true lag, 25 non-lag) to measure:
- Precision
- Recall (Sensitivity)
- Specificity (True Negative Rate)
"""

from typing import Any, Dict, List
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.laguna_detector import LagunaDetector


def build_synthetic_cases() -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []

    # 25 cases with real laguna:
    # Target topic requires prereq, student fails, mastery remains < 0.60
    for i in range(25):
        cases.append({
            "case_id": f"LAG_TRUE_{i}",
            "current_topic": f"TOPIC_{i}",
            "kc_id": f"PREREQ_{i}",
            "is_prereq": True,
            "correct": False,
            "prior_mastery_high": False,
            "has_laguna": True,
        })

    # 25 cases WITHOUT laguna:
    # 10 cases: correct response on prerequisite
    for i in range(10):
        cases.append({
            "case_id": f"LAG_FALSE_CORRECT_{i}",
            "current_topic": f"TOPIC_{i + 25}",
            "kc_id": f"PREREQ_{i + 25}",
            "is_prereq": True,
            "correct": True,
            "prior_mastery_high": False,
            "has_laguna": False,
        })

    # 10 cases: non-prerequisite evaluation (independent topic error)
    for i in range(10):
        cases.append({
            "case_id": f"LAG_FALSE_NONPREREQ_{i}",
            "current_topic": f"TOPIC_{i + 35}",
            "kc_id": f"UNRELATED_{i + 35}",
            "is_prereq": False,
            "correct": False,
            "prior_mastery_high": False,
            "has_laguna": False,
        })

    # 5 cases: high mastery student (> 0.85) slipping on prerequisite (P(L) stays >= 0.60)
    for i in range(5):
        cases.append({
            "case_id": f"LAG_FALSE_SLIP_{i}",
            "current_topic": f"TOPIC_{i + 45}",
            "kc_id": f"PREREQ_{i + 45}",
            "is_prereq": True,
            "correct": False,
            "prior_mastery_high": True,
            "has_laguna": False,
        })

    return cases


def main() -> None:
    cases = build_synthetic_cases()

    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0

    for c in cases:
        tracker = BKTTracker()
        detector = LagunaDetector(bkt=tracker)

        if c["is_prereq"]:
            detector.register_prerequisites(c["current_topic"], {c["kc_id"]})
        else:
            detector.register_prerequisites(c["current_topic"], {f"DIFFERENT_{c['kc_id']}"})

        if c["prior_mastery_high"]:
            for _ in range(8):
                tracker.update(kc_id=c["kc_id"], correct=True)

        interrupt = detector.check_after_exercise(
            kc_id_or_payload=c["kc_id"],
            correct=c["correct"],
            current_topic_id=c["current_topic"],
        )

        detected = interrupt is not None
        actual_lag = c["has_laguna"]

        if actual_lag and detected:
            true_positives += 1
        elif not actual_lag and detected:
            false_positives += 1
        elif not actual_lag and not detected:
            true_negatives += 1
        elif actual_lag and not detected:
            false_negatives += 1

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    specificity = true_negatives / (true_negatives + false_positives) if (true_negatives + false_positives) > 0 else 0.0

    print("==========================================================")
    print("LAGUNADETECTOR METRICS: SPECIFICITY & SENSITIVITY")
    print("==========================================================")
    print(f"Total Cases:     {len(cases)}")
    print(f"True Positives:  {true_positives}/25")
    print(f"False Positives: {false_positives}/25")
    print(f"True Negatives:  {true_negatives}/25")
    print(f"False Negatives: {false_negatives}/25")
    print(f"Precision:   {precision * 100:.2f}%")
    print(f"Recall:      {recall * 100:.2f}%")
    print(f"Specificity: {specificity * 100:.2f}%")

    assert precision >= 0.90, f"Precision {precision:.2%} below 90%"
    assert recall >= 0.90, f"Recall {recall:.2%} below 90%"
    assert specificity >= 0.90, f"Specificity {specificity:.2%} below 90%"
    print("✅ LagunaDetector equilibrado y certificado (Specificity >= 90%)")


if __name__ == "__main__":
    main()
