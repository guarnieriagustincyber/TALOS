import pytest

from scripts.benchmark_gate2_retrieval import _concurrency_metrics


def test_concurrency_metrics_distinguish_attempts_and_successes():
    metrics = _concurrency_metrics(request_count=10, errors=2, duration=4.0)

    assert metrics == {
        "requests": 10,
        "successful_requests": 8,
        "errors": 2,
        "error_rate_pct": 20.0,
        "attempt_qps": 2.5,
        "successful_qps": 2.0,
    }


def test_concurrency_metrics_report_zero_error_rate_when_all_succeed():
    metrics = _concurrency_metrics(request_count=6, errors=0, duration=2.0)

    assert metrics["error_rate_pct"] == 0.0
    assert metrics["attempt_qps"] == metrics["successful_qps"] == 3.0


@pytest.mark.parametrize(
    ("request_count", "errors", "duration"),
    [
        (0, 0, 1.0),
        (2, -1, 1.0),
        (2, 3, 1.0),
        (2, 0, 0.0),
    ],
)
def test_concurrency_metrics_reject_invalid_measurements(
    request_count, errors, duration
):
    with pytest.raises(ValueError):
        _concurrency_metrics(request_count, errors, duration)
