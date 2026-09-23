"""Unit tests for Commit 1: streaming citation sanitization and lookahead buffer."""

import json
import pytest
from starlette.testclient import TestClient

from study_engine.pedagogy.citation_validator import CitationValidator, StreamCitationBuffer
from study_engine.web.app import app
from study_engine.web.dependencies import AppContainer, get_container


def test_stream_citation_buffer_invalid_single_and_multi():
    validator = CitationValidator()
    raw_chunks = [{"id": "E1", "citation_id": "E1"}, {"id": "E2", "citation_id": "E2"}]
    buf = StreamCitationBuffer(validator, raw_chunks)

    # Stream containing invalid citation [E5467] across token boundaries
    tokens = ["El ", "concepto ", "según ", "[", "E", "54", "67", "]", " es ", "básico."]
    emitted = []
    for t in tokens:
        emitted.extend(buf.process_token(t))
    emitted.extend(buf.flush())
    out = "".join(emitted)

    assert "[E5467]" not in out
    assert "[ref. no verificada]" in out
    assert "El concepto según [ref. no verificada] es básico." == out


def test_stream_citation_buffer_valid_retained_intact():
    validator = CitationValidator()
    raw_chunks = [{"id": "E1"}, {"id": "E2"}]
    buf = StreamCitationBuffer(validator, raw_chunks)

    tokens = ["Fuente ", "[", "E1", "]", " confirmada."]
    emitted = []
    for t in tokens:
        emitted.extend(buf.process_token(t))
    emitted.extend(buf.flush())
    out = "".join(emitted)

    assert "[E1]" in out
    assert "[ref. no verificada]" not in out


def test_stream_citation_buffer_multi_citation_valid_and_invalid():
    validator = CitationValidator()
    raw_chunks = [{"id": "E1"}, {"id": "E2"}]
    buf = StreamCitationBuffer(validator, raw_chunks)

    tokens = ["Ver ", "[E1, E5467]", " fin."]
    emitted = []
    for t in tokens:
        emitted.extend(buf.process_token(t))
    emitted.extend(buf.flush())
    out = "".join(emitted)

    assert "[E1, ref. no verificada]" in out
    assert "[E5467]" not in out


def test_stream_citation_buffer_non_citation_bracket_flushes_immediately():
    validator = CitationValidator()
    buf = StreamCitationBuffer(validator, [])

    # Code array indexing: [i] should not stall
    t1 = buf.process_token("arr[")
    assert t1 == ["arr"]  # "[" is buffered as potential prefix
    t2 = buf.process_token("i")
    # "i" cannot follow "[" in a citation grammar prefix, so "[" and "i" flush immediately
    assert t2 == ["[", "i"]
    t3 = buf.process_token("]")
    assert t3 == ["]"]


def test_stream_citation_buffer_code_fence_no_buffering():
    validator = CitationValidator()
    buf = StreamCitationBuffer(validator, [])

    buf.process_token("```python\n")
    # Inside code fence, brackets should not be buffered
    t1 = buf.process_token("arr[")
    assert t1 == ["arr["]
