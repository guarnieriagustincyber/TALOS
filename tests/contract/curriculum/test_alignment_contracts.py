"""Contract tests for Subsystem S5.4 Curricular Alignment Matrix.

INVARIANTS:
1. Immutability: all models are strictly frozen (extra='forbid').
2. Page bounds: page_start <= page_end, both >= 1.
3. Cryptographic integrity: canonical_matrix_id must match deterministic SHA-256.
4. Fail-closed: node key in alignments dict must match alignment.node_id.
"""

import pytest
from pydantic import ValidationError

from study_engine.curriculum.alignment_contracts import (
    CurricularAlignmentMatrix,
    CurricularDocumentScope,
    CurricularNodeAlignment,
    compute_canonical_matrix_id,
)


def test_document_scope_valid() -> None:
    """Valid document scope instantiates correctly."""
    scope = CurricularDocumentScope(
        document_id="prog_punteros.pdf",
        page_start=1,
        page_end=15,
        is_primary=True,
    )
    assert scope.document_id == "prog_punteros.pdf"
    assert scope.page_start == 1
    assert scope.page_end == 15
    assert scope.is_primary is True


def test_document_scope_invalid_page_boundaries() -> None:
    """page_end < page_start raises ValidationError."""
    with pytest.raises(ValidationError, match="page_end .* must be >= page_start"):
        CurricularDocumentScope(
            document_id="prog_punteros.pdf",
            page_start=15,
            page_end=10,
        )


def test_document_scope_zero_or_negative_page() -> None:
    """page_start < 1 or page_end < 1 raises ValidationError."""
    with pytest.raises(ValidationError):
        CurricularDocumentScope(
            document_id="prog_punteros.pdf",
            page_start=0,
            page_end=10,
        )


def test_document_scope_immutability() -> None:
    """Fields cannot be mutated after instantiation."""
    scope = CurricularDocumentScope(
        document_id="prog_punteros.pdf",
        page_start=1,
        page_end=15,
    )
    with pytest.raises(ValidationError):
        scope.page_start = 5  # type: ignore[misc]


def test_node_alignment_valid() -> None:
    """Node alignment with valid scopes instantiates correctly."""
    scope1 = CurricularDocumentScope(
        document_id="so_memoria.pdf",
        page_start=1,
        page_end=12,
        is_primary=True,
    )
    scope2 = CurricularDocumentScope(
        document_id="prog_punteros.pdf",
        page_start=10,
        page_end=20,
        is_primary=False,
    )
    alignment = CurricularNodeAlignment(
        node_id="SEC-03-MEM-MGMT",
        allowed_documents=(scope1, scope2),
    )
    assert alignment.node_id == "SEC-03-MEM-MGMT"
    assert len(alignment.allowed_documents) == 2


def test_node_alignment_empty_documents_rejected() -> None:
    """Node alignment without documents is rejected."""
    with pytest.raises(ValidationError):
        CurricularNodeAlignment(
            node_id="SEC-03-MEM-MGMT",
            allowed_documents=(),
        )


def test_compute_canonical_matrix_id_determinism() -> None:
    """Hash calculation is strictly deterministic and invariant to dictionary insertion order."""
    scope1 = CurricularDocumentScope(
        document_id="prog_punteros.pdf", page_start=1, page_end=10
    )
    scope2 = CurricularDocumentScope(
        document_id="so_procesos.pdf", page_start=1, page_end=10
    )

    align_a = {
        "NODE-A": CurricularNodeAlignment(
            node_id="NODE-A", allowed_documents=(scope1,)
        ),
        "NODE-B": CurricularNodeAlignment(
            node_id="NODE-B", allowed_documents=(scope2,)
        ),
    }

    align_b = {
        "NODE-B": CurricularNodeAlignment(
            node_id="NODE-B", allowed_documents=(scope2,)
        ),
        "NODE-A": CurricularNodeAlignment(
            node_id="NODE-A", allowed_documents=(scope1,)
        ),
    }

    hash_a = compute_canonical_matrix_id("M1", "R1", "1.0.0", align_a)
    hash_b = compute_canonical_matrix_id("M1", "R1", "1.0.0", align_b)

    assert hash_a == hash_b
    assert len(hash_a) == 64


def test_compute_canonical_matrix_id_sensitivity() -> None:
    """Changing page range or document changes the hash."""
    scope1 = CurricularDocumentScope(
        document_id="prog_punteros.pdf", page_start=1, page_end=10
    )
    scope2 = CurricularDocumentScope(
        document_id="prog_punteros.pdf", page_start=1, page_end=11
    )

    align1 = {
        "NODE-A": CurricularNodeAlignment(
            node_id="NODE-A", allowed_documents=(scope1,)
        )
    }
    align2 = {
        "NODE-A": CurricularNodeAlignment(
            node_id="NODE-A", allowed_documents=(scope2,)
        )
    }

    hash1 = compute_canonical_matrix_id("M1", "R1", "1.0.0", align1)
    hash2 = compute_canonical_matrix_id("M1", "R1", "1.0.0", align2)

    assert hash1 != hash2


def test_matrix_hash_validation_failure() -> None:
    """Tampered or incorrect canonical_matrix_id is rejected on construction."""
    scope = CurricularDocumentScope(
        document_id="prog_punteros.pdf", page_start=1, page_end=10
    )
    alignments = {
        "NODE-A": CurricularNodeAlignment(
            node_id="NODE-A", allowed_documents=(scope,)
        )
    }
    fake_hash = "0" * 64

    with pytest.raises(ValidationError, match="canonical_matrix_id mismatch"):
        CurricularAlignmentMatrix(
            matrix_id="M1",
            roadmap_id="R1",
            version="1.0.0",
            alignments=alignments,
            canonical_matrix_id=fake_hash,
        )


def test_matrix_key_mismatch_rejected() -> None:
    """Alignment dictionary key differing from node_id is rejected."""
    scope = CurricularDocumentScope(
        document_id="prog_punteros.pdf", page_start=1, page_end=10
    )
    alignments = {
        "WRONG-KEY": CurricularNodeAlignment(
            node_id="NODE-A", allowed_documents=(scope,)
        )
    }
    correct_hash = compute_canonical_matrix_id("M1", "R1", "1.0.0", alignments)

    with pytest.raises(ValidationError, match="Alignment key .* does not match node_id"):
        CurricularAlignmentMatrix(
            matrix_id="M1",
            roadmap_id="R1",
            version="1.0.0",
            alignments=alignments,
            canonical_matrix_id=correct_hash,
        )
