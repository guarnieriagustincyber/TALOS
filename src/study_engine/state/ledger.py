"""Implementation of EvidenceLedger for Subsystem S5.2.B.

INVARIANTS:
1. Append-only tamper-evident storage with cryptographic hash chaining.
2. Authoritative persistence via SQLite WAL with atomic BEGIN IMMEDIATE serialization.
3. Strict 3-tier identity hierarchy and formal decision function D(K, R).
4. Committed timestamps are assigned exclusively by ledger (monotonic).
5. Anti-duplication enforced via DuplicateEvidenceError, IdempotentReplayError,
   and InconsistentReplayError.
6. Explicit HistoryCutoffMode for time-travel queries.
7. Crash consistency guaranteed via SQLite WAL journal and atomic transactions.
8. Derived JSONL export; export failures never undo an authoritative commit.
"""

from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import sqlite3
import threading
import tempfile
from typing import List, Optional, Set, Tuple

from study_engine.contracts.epistemology import (
    EpistemologicalAuthority,
    EpistemologicalAuthorityViolationError,
)
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    EvidenceLedgerEntry,
    HistoryCutoffMode,
    IdempotentReplayError,
    InconsistentReplayError,
    LedgerIntegrityReport,
    LedgerIntegrityStatus,
    LedgerIntegrityViolationError,
    NonMonotonicCommitError,
    compute_ledger_entry_hash,
)
from study_engine.state.policy_contracts import EvidenceRecord

_GENESIS_HASH = "0" * 64
logger = logging.getLogger(__name__)


def _extract_evaluation_attempt_id(record: EvidenceRecord) -> str:
    """Extract evaluation attempt identity following the 3-tier hierarchy."""
    if record.metadata and "evaluation_attempt_id" in record.metadata:
        return str(record.metadata["evaluation_attempt_id"])
    if hasattr(record, "evaluation_attempt_id") and getattr(record, "evaluation_attempt_id"):
        return str(getattr(record, "evaluation_attempt_id"))
    return record.record_id


class EvidenceLedger:
    """Tamper-evident authoritative append-only ledger for immutable evidence recording."""

    def __init__(self, file_path: Optional[Path] = None) -> None:
        self._lock = threading.RLock()
        self._file_path = Path(file_path) if file_path else None
        self._entries: List[EvidenceLedgerEntry] = []
        self._seen_record_ids: Set[str] = set()
        self._seen_assessment_digests: Set[str] = set()
        self._tip_hash: str = _GENESIS_HASH
        self.export_pending = False

        if self._file_path:
            if self._file_path.suffix == ".jsonl":
                self._jsonl_path: Optional[Path] = self._file_path
                self._db_path: Optional[Path] = self._file_path.with_suffix(".db")
            elif self._file_path.suffix == ".db":
                self._db_path = self._file_path
                self._jsonl_path = self._file_path.with_suffix(".jsonl")
            else:
                self._db_path = self._file_path.with_suffix(".db")
                self._jsonl_path = self._file_path.with_suffix(".jsonl")

            existed = self._db_path.exists()
            if self._jsonl_path.exists() and not existed:
                # Validate for diagnostics, but never bootstrap a DB from an export.
                self._read_jsonl(self._jsonl_path)
                raise LedgerIntegrityViolationError("JSONL exists without authoritative SQLite; import blocked.")
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(
                str(self._db_path),
                timeout=30.0,
                check_same_thread=False,
                isolation_level=None,
            )
            if existed and self._conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_ledger'"
            ).fetchone() is None:
                self._conn.close()
                raise LedgerIntegrityViolationError("Existing SQLite has no authoritative ledger table.")
            self._conn.execute("PRAGMA journal_mode = WAL;")
            self._conn.execute("PRAGMA synchronous = NORMAL;")
            self._conn.execute("PRAGMA busy_timeout = 30000;")
        else:
            self._db_path = None
            self._jsonl_path = None
            self._conn = sqlite3.connect(
                ":memory:",
                check_same_thread=False,
                isolation_level=None,
            )
            self._conn.execute("PRAGMA synchronous = NORMAL;")

        self._init_db_schema()

        if self._file_path:
            try:
                self._load_from_storage()
            except Exception:
                self._conn.close()
                raise

    def _init_db_schema(self) -> None:
        """Initialize authoritative SQLite schema."""
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_ledger (
                    entry_index INTEGER PRIMARY KEY,
                    record_id TEXT NOT NULL UNIQUE,
                    student_id TEXT NOT NULL,
                    node_id TEXT NOT NULL,
                    evaluation_attempt_id TEXT NOT NULL,
                    assessment_digest TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    parent_entry_hash TEXT NOT NULL,
                    entry_hash TEXT NOT NULL UNIQUE,
                    committed_at TEXT NOT NULL,
                    UNIQUE(student_id, node_id, evaluation_attempt_id)
                );
                """
            )
            self._conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_assessment_digest ON evidence_ledger(assessment_digest);"
            )

    @property
    def total_entries(self) -> int:
        """Return total number of committed entries in ledger."""
        with self._lock:
            if self._db_path and self._db_path.exists():
                cur = self._conn.cursor()
                cur.execute("SELECT COUNT(*) FROM evidence_ledger")
                return cur.fetchone()[0]
            return len(self._entries)

    @property
    def tip_hash(self) -> str:
        """Return hash of the latest entry or genesis hash if empty."""
        with self._lock:
            if self._db_path and self._db_path.exists():
                cur = self._conn.cursor()
                cur.execute(
                    "SELECT entry_hash FROM evidence_ledger ORDER BY entry_index DESC LIMIT 1"
                )
                row = cur.fetchone()
                return row[0] if row else _GENESIS_HASH
            return self._tip_hash

    def has_assessment_digest(self, digest: str) -> bool:
        """Check if an assessment digest has already been committed to ledger.

        Read-only public query method for preflight replay detection.
        Does not mutate caches, does not reserve the digest, pure query.
        """
        if not digest:
            return False
        with self._lock:
            if digest in self._seen_assessment_digests:
                return True
            cur = self._conn.cursor()
            cur.execute(
                "SELECT 1 FROM evidence_ledger WHERE assessment_digest = ? LIMIT 1",
                (digest,),
            )
            found = cur.fetchone() is not None
            if found:
                self._seen_assessment_digests.add(digest)
            return found

    def _ensure_entries_synced(self) -> None:
        """Sync in-memory cache from database if updated by another instance or process."""
        if not self._db_path or not self._db_path.exists():
            return
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM evidence_ledger")
        db_count = cur.fetchone()[0]
        if db_count == len(self._entries):
            return

        self._set_entries(self._read_sqlite())

    def _set_entries(self, entries: List[EvidenceLedgerEntry]) -> None:
        self._entries = entries
        self._seen_record_ids = {entry.record.record_id for entry in entries}
        self._seen_assessment_digests = {
            entry.record.assessment_digest for entry in entries if entry.record.assessment_digest
        }
        self._tip_hash = entries[-1].entry_hash if entries else _GENESIS_HASH

    def _validate_entries(self, entries: List[EvidenceLedgerEntry]) -> None:
        seen_ids: Set[str] = set()
        seen_digests: Set[str] = set()
        seen_keys: Set[Tuple[str, str, str]] = set()
        parent = _GENESIS_HASH
        previous_commit = None
        for index, entry in enumerate(entries):
            line_num = index + 1
            if entry.entry_index != index:
                raise LedgerIntegrityViolationError(
                    f"Non-sequential entry_index {entry.entry_index} (expected {index}) at line {line_num}."
                )
            if entry.record.record_id in seen_ids:
                raise DuplicateEvidenceError(f"Duplicate record_id '{entry.record.record_id}' found at line {line_num}.")
            key = (entry.record.student_id, entry.record.node_id, _extract_evaluation_attempt_id(entry.record))
            if key in seen_keys:
                raise DuplicateEvidenceError(f"Duplicate evaluation attempt found at line {line_num}.")
            digest = entry.record.assessment_digest
            if digest and digest in seen_digests:
                raise DuplicateEvidenceError(f"Duplicate assessment_digest '{digest}' found at line {line_num}.")
            if entry.record.authority_id != EpistemologicalAuthority.EVIDENCE_POLICY:
                raise EpistemologicalAuthorityViolationError("Ledger entry lacks EVIDENCE_POLICY authority.")
            if entry.parent_entry_hash != parent:
                raise LedgerIntegrityViolationError(f"Broken hash chain at line {line_num}.")
            expected = compute_ledger_entry_hash(
                entry.entry_index, entry.parent_entry_hash, entry.record, entry.committed_at,
            )
            if entry.entry_hash != expected:
                raise LedgerIntegrityViolationError(f"Tampered entry_hash at line {line_num}.")
            if previous_commit is not None and entry.committed_at < previous_commit:
                raise NonMonotonicCommitError(f"Non-monotonic commit at line {line_num}.")
            seen_ids.add(entry.record.record_id)
            seen_keys.add(key)
            if digest:
                seen_digests.add(digest)
            parent, previous_commit = entry.entry_hash, entry.committed_at

    def _read_jsonl(self, path: Path) -> List[EvidenceLedgerEntry]:
        entries = []
        with path.open("r", encoding="utf-8") as stream:
            for line_num, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    entries.append(EvidenceLedgerEntry.model_validate_json(line))
                except Exception as exc:
                    raise LedgerIntegrityViolationError(f"Corrupted entry at line {line_num} in '{path}'.") from exc
        self._validate_entries(entries)
        return entries

    def _read_sqlite(self) -> List[EvidenceLedgerEntry]:
        rows = self._conn.execute(
            """SELECT entry_index, record_id, student_id, node_id, evaluation_attempt_id,
                      assessment_digest, parent_entry_hash, entry_hash, committed_at, payload_json
               FROM evidence_ledger ORDER BY entry_index"""
        ).fetchall()
        entries = []
        for row in rows:
            try:
                entry = EvidenceLedgerEntry.model_validate_json(row[9])
            except Exception as exc:
                raise LedgerIntegrityViolationError(f"Corrupted SQLite entry at index {row[0]}.") from exc
            expected = (
                entry.entry_index, entry.record.record_id, entry.record.student_id,
                entry.record.node_id, _extract_evaluation_attempt_id(entry.record),
                entry.record.assessment_digest or "", entry.parent_entry_hash,
                entry.entry_hash, entry.committed_at.isoformat(),
            )
            if row[:9] != expected:
                raise LedgerIntegrityViolationError(f"SQLite identity/payload mismatch at index {row[0]}.")
            entries.append(entry)
        self._validate_entries(entries)
        return entries

    def _check_projection(self, path: Path, entries: List[EvidenceLedgerEntry]) -> bool:
        """Accept a matching projection or prefix, never repair discrepant bytes."""
        if not path.exists():
            return False
        exported = self._read_jsonl(path)
        if len(exported) > len(entries) or exported != entries[:len(exported)]:
            raise LedgerIntegrityViolationError(f"JSONL conflicts with authoritative SQLite: '{path}'.")
        return len(exported) == len(entries)

    def _load_from_storage(self) -> None:
        """Recover SQLite commits; inspect JSONL without importing or repairing it."""
        assert self._file_path is not None
        with self._lock:
            # Same reservation as exporters/writers: snapshot and file cannot race.
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                entries = self._read_sqlite()
                self.export_pending = not self._check_projection(self._jsonl_path, entries)
                self._set_entries(entries)
                self._conn.execute("COMMIT")
            finally:
                if self._conn.in_transaction:
                    self._conn.execute("ROLLBACK")

    def append_record(
        self,
        record: EvidenceRecord,
        override_committed_at: Optional[datetime] = None,
    ) -> EvidenceLedgerEntry:
        """Append a new EvidenceRecord to the authoritative ledger.

        Enforces the formal Decision Function D(K, R):
        - If K not in DB -> COMMIT_OK
        - If K in DB and R_in == R_stored -> IdempotentReplayError (IDEMPOTENT_ACK)
        - If K in DB and R_in != R_stored -> InconsistentReplayError (Fail-Closed)

        Args:
            record: The EvidenceRecord to commit.
            override_committed_at: Used strictly in deterministic tests.

        Returns:
            The committed EvidenceLedgerEntry. JSONL failure sets export_pending
            and is logged without reporting a failed SQLite insertion.

        Raises:
            DuplicateEvidenceError: If record_id or assessment_digest is duplicated.
            IdempotentReplayError: If exact attempt (K, R) is re-submitted.
            InconsistentReplayError: If attempt K has divergent outcome digest R' != R.
            NonMonotonicCommitError: If committed_at is earlier than previous.
        """
        # 0. Strict runtime type enforcement
        if not isinstance(record, EvidenceRecord):
            raise TypeError(
                f"Only EvidenceRecord can be committed to the EvidenceLedger, "
                f"got {type(record).__name__}."
            )

        # 0b. Strict epistemological authority verification
        if record.authority_id != EpistemologicalAuthority.EVIDENCE_POLICY:
            raise EpistemologicalAuthorityViolationError(
                f"EvidenceLedger only commits records with authority "
                f"'{EpistemologicalAuthority.EVIDENCE_POLICY.value}', "
                f"got '{record.authority_id.value}'."
            )

        eval_attempt_id = _extract_evaluation_attempt_id(record)
        student_id = record.student_id
        node_id = record.node_id
        incoming_digest = record.assessment_digest or ""

        with self._lock:
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                cur = self._conn.cursor()

                # 1. Evaluate Decision Function D(K, R) against authoritative SQLite state
                cur.execute(
                    """
                    SELECT entry_index, record_id, assessment_digest, payload_json
                    FROM evidence_ledger
                    WHERE student_id = ? AND node_id = ? AND evaluation_attempt_id = ?
                    """,
                    (student_id, node_id, eval_attempt_id),
                )
                row_k = cur.fetchone()

                if row_k is not None:
                    stored_digest = row_k[2]
                    self._conn.execute("ROLLBACK")
                    if stored_digest == incoming_digest:
                        raise IdempotentReplayError(
                            f"Idempotent replay detected: attempt '{eval_attempt_id}' for student "
                            f"'{student_id}' on node '{node_id}' already committed with identical digest '{incoming_digest}'."
                        )
                    else:
                        raise InconsistentReplayError(
                            f"Inconsistent replay detected: attempt '{eval_attempt_id}' for student "
                            f"'{student_id}' on node '{node_id}' already committed with digest '{stored_digest}', "
                            f"incoming attempt has divergent digest '{incoming_digest}'."
                        )

                # 2. Check record_id uniqueness
                cur.execute(
                    "SELECT 1 FROM evidence_ledger WHERE record_id = ?",
                    (record.record_id,),
                )
                if cur.fetchone() is not None:
                    self._conn.execute("ROLLBACK")
                    raise DuplicateEvidenceError(
                        f"EvidenceRecord with record_id '{record.record_id}' already committed to ledger."
                    )

                # 3. Check assessment_digest uniqueness (if non-empty)
                if incoming_digest:
                    cur.execute(
                        "SELECT 1 FROM evidence_ledger WHERE assessment_digest = ?",
                        (incoming_digest,),
                    )
                    if cur.fetchone() is not None:
                        self._conn.execute("ROLLBACK")
                        raise DuplicateEvidenceError(
                            f"EvidenceRecord with assessment_digest '{incoming_digest}' already committed to ledger."
                        )

                # 4. Monotonicity validation & parent hash linking
                cur.execute(
                    "SELECT entry_index, entry_hash, committed_at FROM evidence_ledger ORDER BY entry_index DESC LIMIT 1"
                )
                last_row = cur.fetchone()
                committed_at = override_committed_at or datetime.now(timezone.utc)

                if last_row is not None:
                    last_index, last_hash, last_commit_iso = last_row
                    last_committed = datetime.fromisoformat(last_commit_iso)
                    if committed_at < last_committed:
                        self._conn.execute("ROLLBACK")
                        raise NonMonotonicCommitError(
                            f"New committed_at '{committed_at}' is earlier than "
                            f"last entry committed_at '{last_committed}'."
                        )
                    entry_index = last_index + 1
                    parent_entry_hash = last_hash
                else:
                    entry_index = 0
                    parent_entry_hash = _GENESIS_HASH

                # 5. Hash chaining computation
                entry_hash = compute_ledger_entry_hash(
                    entry_index=entry_index,
                    parent_entry_hash=parent_entry_hash,
                    record=record,
                    committed_at=committed_at,
                )

                entry = EvidenceLedgerEntry(
                    entry_index=entry_index,
                    record=record,
                    parent_entry_hash=parent_entry_hash,
                    entry_hash=entry_hash,
                    committed_at=committed_at,
                )

                # 6. Physical atomic insertion in SQLite
                cur.execute(
                    """
                    INSERT INTO evidence_ledger (
                        entry_index, record_id, student_id, node_id, evaluation_attempt_id,
                        assessment_digest, payload_json, parent_entry_hash, entry_hash, committed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_index,
                        record.record_id,
                        student_id,
                        node_id,
                        eval_attempt_id,
                        incoming_digest,
                        entry.model_dump_json(),
                        parent_entry_hash,
                        entry_hash,
                        committed_at.isoformat(),
                    ),
                )

                # SQLite alone confirms the operation; JSONL is never published before it.
                self._conn.execute("COMMIT")

            except (DuplicateEvidenceError, IdempotentReplayError, InconsistentReplayError, NonMonotonicCommitError):
                raise
            except Exception:
                try:
                    self._conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise

            # A post-commit projection failure cannot report a failed insertion.
            try:
                self._set_entries(self._read_sqlite())
                if self._jsonl_path:
                    self.export_jsonl()
            except Exception:
                self.export_pending = True
                logger.exception("Ledger commit confirmed at index %s; JSONL export pending.", entry.entry_index)
            return entry

    append_evidence = append_record

    def export_jsonl(self, target_path: Optional[Path] = None) -> Path:
        """Publish a confirmed snapshot atomically, serialized across SQLite writers."""
        out_path = Path(target_path) if target_path else self._jsonl_path
        if not out_path:
            raise ValueError("No target path specified for export_jsonl.")
        if self._db_path and out_path.resolve() in {
            Path(str(self._db_path) + suffix).resolve() for suffix in ("", "-wal", "-shm")
        }:
            raise ValueError("An export cannot overwrite authoritative SQLite.")
        canonical = self._jsonl_path is not None and out_path.resolve() == self._jsonl_path.resolve()
        with self._lock:
            if canonical:
                self.export_pending = True
            temporary = None
            try:
                # Build/sync the temporary without holding SQLite's writer reservation.
                entries = self._read_sqlite()
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=out_path.parent,
                    prefix=f".{out_path.name}.", suffix=".tmp", delete=False,
                ) as stream:
                    temporary = Path(stream.name)
                    for entry in entries:
                        stream.write(entry.model_dump_json() + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                # Lock order: RLock -> SQLite. Fence stale snapshots before publication.
                self._conn.execute("BEGIN IMMEDIATE")
                latest = self._conn.execute(
                    "SELECT entry_index, entry_hash FROM evidence_ledger ORDER BY entry_index DESC LIMIT 1"
                ).fetchone()
                cutoff = (entries[-1].entry_index, entries[-1].entry_hash) if entries else None
                if latest != cutoff:
                    raise RuntimeError("Export snapshot superseded; export remains pending.")
                self._check_projection(out_path, entries)
                os.replace(temporary, out_path)
                directory = os.open(out_path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(directory)
                finally:
                    os.close(directory)
                self._conn.execute("COMMIT")
                self._set_entries(entries)
                if canonical:
                    self.export_pending = False
            finally:
                if self._conn.in_transaction:
                    self._conn.execute("ROLLBACK")
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
        return out_path

    def get_history_for_node(
        self,
        node_id: str,
        as_of_time: Optional[datetime] = None,
        cutoff_mode: HistoryCutoffMode = HistoryCutoffMode.COMMIT_TIME,
    ) -> Tuple[EvidenceRecord, ...]:
        """Return chronological sequence of records for a specific node."""
        with self._lock:
            self._ensure_entries_synced()
            results: List[EvidenceRecord] = []
            for entry in self._entries:
                if entry.record.node_id != node_id:
                    continue

                if as_of_time is not None:
                    if cutoff_mode == HistoryCutoffMode.COMMIT_TIME:
                        if entry.committed_at > as_of_time:
                            continue
                    elif cutoff_mode == HistoryCutoffMode.EVENT_TIME:
                        if entry.record.timestamp > as_of_time:
                            continue

                results.append(entry.record)

            return tuple(results)

    def get_all_records(
        self,
        as_of_time: Optional[datetime] = None,
        cutoff_mode: HistoryCutoffMode = HistoryCutoffMode.COMMIT_TIME,
    ) -> Tuple[EvidenceRecord, ...]:
        """Return all records across all nodes up to cutoff."""
        with self._lock:
            self._ensure_entries_synced()
            results: List[EvidenceRecord] = []
            for entry in self._entries:
                if as_of_time is not None:
                    if cutoff_mode == HistoryCutoffMode.COMMIT_TIME:
                        if entry.committed_at > as_of_time:
                            continue
                    elif cutoff_mode == HistoryCutoffMode.EVENT_TIME:
                        if entry.record.timestamp > as_of_time:
                            continue

                results.append(entry.record)

            return tuple(results)

    def get_entry_by_index(self, index: int) -> Optional[EvidenceLedgerEntry]:
        """Retrieve entry at exact index or None if out of bounds."""
        with self._lock:
            self._ensure_entries_synced()
            if 0 <= index < len(self._entries):
                return self._entries[index]
            return None

    def get_cutoff_tip_hash(
        self,
        as_of_time: Optional[datetime] = None,
        cutoff_mode: HistoryCutoffMode = HistoryCutoffMode.COMMIT_TIME,
    ) -> str:
        """Return hash of the last entry matching cutoff, or genesis if none."""
        with self._lock:
            self._ensure_entries_synced()
            last_hash = _GENESIS_HASH
            for entry in self._entries:
                if as_of_time is not None:
                    if cutoff_mode == HistoryCutoffMode.COMMIT_TIME:
                        if entry.committed_at > as_of_time:
                            continue
                    elif cutoff_mode == HistoryCutoffMode.EVENT_TIME:
                        if entry.record.timestamp > as_of_time:
                            continue
                last_hash = entry.entry_hash
            return last_hash

    def verify_integrity(self) -> LedgerIntegrityReport:
        """Verify cryptographic hash chain integrity across all entries."""
        with self._lock:
            self._ensure_entries_synced()
            if not self._entries:
                return LedgerIntegrityReport(
                    status=LedgerIntegrityStatus.VALID,
                    total_entries=0,
                    valid_entries=0,
                    tip_hash=_GENESIS_HASH,
                    details="Empty ledger is valid.",
                )

            seen_ids: Set[str] = set()
            expected_parent = _GENESIS_HASH

            for idx, entry in enumerate(self._entries):
                if entry.entry_index != idx:
                    return LedgerIntegrityReport(
                        status=LedgerIntegrityStatus.CORRUPTED_ENTRY,
                        total_entries=len(self._entries),
                        valid_entries=idx,
                        first_invalid_index=idx,
                        details=f"Index mismatch at {idx}: found {entry.entry_index}.",
                    )

                if entry.record.record_id in seen_ids:
                    return LedgerIntegrityReport(
                        status=LedgerIntegrityStatus.DUPLICATE_EVIDENCE_ID,
                        total_entries=len(self._entries),
                        valid_entries=idx,
                        first_invalid_index=idx,
                        details=f"Duplicate record_id '{entry.record.record_id}' at index {idx}.",
                    )
                seen_ids.add(entry.record.record_id)

                if idx == 0 and entry.parent_entry_hash != _GENESIS_HASH:
                    return LedgerIntegrityReport(
                        status=LedgerIntegrityStatus.GENESIS_MISMATCH,
                        total_entries=len(self._entries),
                        valid_entries=0,
                        first_invalid_index=0,
                        details=f"Genesis parent '{entry.parent_entry_hash}' is not all zeros.",
                    )

                if idx > 0 and entry.parent_entry_hash != expected_parent:
                    return LedgerIntegrityReport(
                        status=LedgerIntegrityStatus.HASH_CHAIN_BROKEN,
                        total_entries=len(self._entries),
                        valid_entries=idx,
                        first_invalid_index=idx,
                        details=(
                            f"Hash chain broken at index {idx}: declared parent "
                            f"'{entry.parent_entry_hash}' != '{expected_parent}'."
                        ),
                    )

                computed = compute_ledger_entry_hash(
                    entry_index=entry.entry_index,
                    parent_entry_hash=entry.parent_entry_hash,
                    record=entry.record,
                    committed_at=entry.committed_at,
                )
                if entry.entry_hash != computed:
                    return LedgerIntegrityReport(
                        status=LedgerIntegrityStatus.HASH_CHAIN_BROKEN,
                        total_entries=len(self._entries),
                        valid_entries=idx,
                        first_invalid_index=idx,
                        details=(
                            f"Tampered content at index {idx}: declared "
                            f"'{entry.entry_hash}' != computed '{computed}'."
                        ),
                    )

                if idx > 0:
                    prev_commit = self._entries[idx - 1].committed_at
                    if entry.committed_at < prev_commit:
                        return LedgerIntegrityReport(
                            status=LedgerIntegrityStatus.NON_MONOTONIC_COMMIT,
                            total_entries=len(self._entries),
                            valid_entries=idx,
                            first_invalid_index=idx,
                            details=(
                                f"Non-monotonic commit at index {idx}: "
                                f"{entry.committed_at} < {prev_commit}."
                            ),
                        )

                expected_parent = entry.entry_hash

            return LedgerIntegrityReport(
                status=LedgerIntegrityStatus.VALID,
                total_entries=len(self._entries),
                valid_entries=len(self._entries),
                tip_hash=self._entries[-1].entry_hash,
                details=f"Ledger verified with {len(self._entries)} entries.",
            )

    def close(self) -> None:
        """Close SQLite database connection safely."""
        with self._lock:
            if hasattr(self, "_conn") and self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass

    def __del__(self) -> None:
        self.close()
