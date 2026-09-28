from pathlib import Path


WEB_STATIC = Path(__file__).parents[3] / "src" / "study_engine" / "web" / "static" / "js"


def test_chat_ui_uses_canonical_sse_endpoint_and_not_legacy_turn_route():
    chat_source = (WEB_STATIC / "chat.js").read_text(encoding="utf-8")

    assert 'fetch("/api/chat/query"' in chat_source
    assert "text/event-stream" in chat_source
    assert "getReader()" in chat_source
    assert 'event.event_type === "audit_verdict"' in chat_source
    assert "recent_turns: recentTurns" in chat_source
    assert "evidence_provenance" in chat_source
    assert "evidence-provenance" in chat_source
    assert "/api/session/turn/conceptual" not in chat_source


def test_chat_session_start_does_not_call_retired_session_endpoint():
    dag_source = (WEB_STATIC / "dag.js").read_text(encoding="utf-8")

    assert "/api/session/start" not in dag_source
    assert "Chat.createSessionId()" in dag_source
