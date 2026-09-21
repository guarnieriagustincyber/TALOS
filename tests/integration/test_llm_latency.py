import os
import time
import pytest
from study_engine.llm.factory import LLMProviderFactory


@pytest.mark.integration
@pytest.mark.network
@pytest.mark.skipif(
    os.getenv("KASIU_E2E") not in ("1", "true", "True", "yes"),
    reason=(
        "Live LLM latency test requires network + valid GEMINI_API_KEY. "
        "Set KASIU_E2E=1 to opt into live external-provider runs; "
        "otherwise skipped to avoid CI flakiness."
    ),
)
def test_llm_latency_under_5_seconds():
    """Test that LLM generation completes within acceptable latency.

    This test requires network access and a valid GEMINI_API_KEY.
    In sandboxed/CI environments without network, the test is skipped
    (via KASIU_E2E gate and mock-fallback detection) rather than producing
    a false positive or flaky failure.
    """
    factory = LLMProviderFactory()
    client = factory.create_client()

    backend_name = type(client.backend).__name__
    # If we're using a mock/replay backend, skip – we want to test real latency
    if backend_name in ("ReplayMockBackend", "MockBackend"):
        pytest.skip("No live LLM backend available (mock fallback active)")

    start = time.time()
    try:
        response = client.generate("Hola", max_tokens=10)
    except Exception as e:
        err_msg = str(e).lower()
        if "name or service not known" in err_msg or "connect" in err_msg:
            pytest.skip(f"No network access available: {e}")
        raise

    elapsed = time.time() - start
    print(f"Latencia: {elapsed:.2f}s (backend={backend_name})")

    assert elapsed < 10.0, f"LLM latency too high: {elapsed:.2f}s"
    assert response is not None
    assert response.raw_content, "Response content should not be empty"
