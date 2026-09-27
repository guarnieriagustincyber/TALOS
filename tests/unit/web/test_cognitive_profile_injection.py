from unittest.mock import Mock

from study_engine.config import CANONICAL_STUDENT_ID
from study_engine.web.routes.chat import _build_cognitive_profile_block


def test_cognitive_profile_uses_canonical_student_id():
    injector = Mock()
    injector.build_injection_block.return_value = "<student_cognitive_profile />"

    result = _build_cognitive_profile_block(injector, "kc-processes")

    assert result == "<student_cognitive_profile />"
    injector.build_injection_block.assert_called_once_with(
        student_id=CANONICAL_STUDENT_ID,
        active_kc="kc-processes",
    )


def test_cognitive_profile_errors_are_logged_and_return_empty(caplog):
    injector = Mock()
    injector.build_injection_block.side_effect = RuntimeError("profile store unavailable")

    assert _build_cognitive_profile_block(injector, None) == ""
    assert "Error building cognitive profile block" in caplog.text
