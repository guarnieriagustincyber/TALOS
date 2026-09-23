"""Deterministic, ACID-compliant SQLite storage engine for Study Engine knowledge bases."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
import threading
from typing import Generator, Optional, Union


SCHEMA_DDL = """
-- 0. Folders / Collections
CREATE TABLE IF NOT EXISTS folders (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    parent_folder_id TEXT,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE SET NULL,
    UNIQUE(name, parent_folder_id)
);

-- 1. Notebooks / Knowledge Bases
CREATE TABLE IF NOT EXISTS notebooks (
    id TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    subject TEXT,
    curriculum_id TEXT,
    folder_id TEXT NOT NULL DEFAULT 'folder_root',
    created_at TEXT,
    updated_at TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (folder_id) REFERENCES folders(id) ON DELETE RESTRICT,
    UNIQUE(name, folder_id)
);

-- 2. Knowledge Sources
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY NOT NULL,
    sha256 TEXT NOT NULL DEFAULT '',
    manifest_json TEXT NOT NULL DEFAULT '{}',
    source_json TEXT,
    title TEXT NOT NULL,
    author TEXT,
    type TEXT,
    language TEXT NOT NULL DEFAULT 'es',
    role TEXT NOT NULL DEFAULT 'PRIMARY',
    priority INTEGER NOT NULL DEFAULT 1,
    subject TEXT,
    course TEXT,
    phase TEXT,
    chapter TEXT,
    section TEXT,
    page INTEGER,
    created_at TEXT,
    metadata TEXT NOT NULL DEFAULT '{}'
);


-- 3. Association Table between Notebooks and Sources (M:N)
CREATE TABLE IF NOT EXISTS notebook_sources (
    notebook_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    PRIMARY KEY (notebook_id, source_id),
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);

-- 4. Logical Documents
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    path TEXT,
    page_count INTEGER,
    language TEXT NOT NULL DEFAULT 'es',
    created_at TEXT,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);

-- 5. Text Chunks
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY NOT NULL,
    document_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    content TEXT NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    chapter TEXT,
    section TEXT,
    token_count INTEGER,
    pos_index INTEGER NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_sources_sha256 ON sources(sha256);
CREATE INDEX IF NOT EXISTS idx_notebook_sources_source ON notebook_sources(source_id);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_id);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_idx ON chunks(document_id, pos_index);
CREATE INDEX IF NOT EXISTS idx_chunks_source ON chunks(source_id);

-- 6. Lexical Full-Text Search (FTS5) Index on Chunks
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    id UNINDEXED,
    document_id UNINDEXED,
    source_id UNINDEXED,
    content='chunks',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

-- Triggers to keep FTS5 synchronized with chunks table
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content, id, document_id, source_id)
    VALUES (new.rowid, new.content, new.id, new.document_id, new.source_id);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, id, document_id, source_id)
    VALUES ('delete', old.rowid, old.content, old.id, old.document_id, old.source_id);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, id, document_id, source_id)
    VALUES ('delete', old.rowid, old.content, old.id, old.document_id, old.source_id);
    INSERT INTO chunks_fts(rowid, content, id, document_id, source_id)
    VALUES (new.rowid, new.content, new.id, new.document_id, new.source_id);
END;

-- 7. Pedagogical Contracts (Fase 5.8)
CREATE TABLE IF NOT EXISTS pedagogical_contracts (
    notebook_id TEXT PRIMARY KEY NOT NULL,
    persona TEXT NOT NULL,
    base_system_prompt TEXT NOT NULL,
    forbidden_patterns_json TEXT NOT NULL,
    safe_words_json TEXT NOT NULL,
    response_phases_json TEXT NOT NULL,
    required_analogies_json TEXT NOT NULL,
    anti_errors_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

-- 8. Knowledge Components manuales del usuario (Fase 5.1)
-- KCs agregados manualmente por el usuario vía API; se funden con el catálogo
-- JSON canónico (config/notebook_kc_catalog.json) al inicializar el orquestador
-- y tras cada alta (ver curriculum/kc_admin.py).
CREATE TABLE IF NOT EXISTS notebook_kcs (
    notebook_id TEXT NOT NULL,
    kc_id TEXT NOT NULL,
    title TEXT NOT NULL,
    prerequisites_json TEXT NOT NULL DEFAULT '[]',
    subtopics_json TEXT NOT NULL DEFAULT '[]',
    estimated_time_min INTEGER,
    difficulty TEXT,
    origin TEXT NOT NULL DEFAULT 'manual',
    created_at TEXT NOT NULL,
    PRIMARY KEY (notebook_id, kc_id),
    FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
);

-- 9. Content Registry (Slice 6.0.5)
CREATE TABLE IF NOT EXISTS content_registry (
    content_id TEXT PRIMARY KEY NOT NULL,
    source_id TEXT NOT NULL,
    unit_type TEXT NOT NULL,
    statement_text TEXT NOT NULL,
    chunk_ids TEXT NOT NULL,
    solution_chunk_ids TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_content_reg_source ON content_registry(source_id);
CREATE INDEX IF NOT EXISTS idx_content_reg_type ON content_registry(unit_type);
CREATE INDEX IF NOT EXISTS idx_content_reg_status ON content_registry(status);
"""



class SQLiteStorageEngine:
    """Low-level SQLite connection and schema manager for Study Engine knowledge stores."""

    SCHEMA_VERSION: int = 5  # v5: content_registry (Identidad exacta + anti-leakage, Slice 6.0.5)

    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        self.db_path = Path(db_path) if db_path != ":memory:" else ":memory:"
        self._is_memory = self.db_path == ":memory:"
        self._mem_conn: Optional[sqlite3.Connection] = None
        self._thread_local = threading.local()

        if not self._is_memory and isinstance(self.db_path, Path):
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """Create and configure a new SQLite connection with enforced pragmas.

        Enforced Pragmas:
            - foreign_keys = ON: strict referential integrity.
            - recursive_triggers = ON: enables foreign key cascade actions to fire triggers (e.g. FTS5 index synchronization on ON DELETE CASCADE).
            - busy_timeout = 5000: wait up to 5s on locked DB instead of failing immediately.
            - journal_mode = WAL: high-concurrency write-ahead logging (disk DBs only).
            - synchronous = NORMAL: optimal speed with corruption resistance in WAL mode (note: possible loss of last committed transaction on sudden power loss, but preserves database structural integrity).
        """

        if self._is_memory:
            if self._mem_conn is None:
                conn = sqlite3.connect(":memory:", check_same_thread=False)
                conn.execute("PRAGMA foreign_keys = ON;")
                conn.execute("PRAGMA recursive_triggers = ON;")
                conn.execute("PRAGMA busy_timeout = 5000;")
                self._mem_conn = conn
            return self._mem_conn

        persistent = getattr(self._thread_local, "persistent_conn", None)
        if persistent is not None:
            try:
                persistent.execute("SELECT 1;")
            except Exception:
                persistent = None
                self._thread_local.persistent_conn = None

        if persistent is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA recursive_triggers = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            self._thread_local.persistent_conn = conn
            persistent = conn
        return persistent

    def get_schema_version(self) -> int:
        """Retrieve the PRAGMA user_version of the database."""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version;")
        return int(cursor.fetchone()[0])

    def set_schema_version(self, version: int) -> None:
        """Update the PRAGMA user_version of the database."""
        conn = self.connect()
        conn.execute(f"PRAGMA user_version = {int(version)};")

    def initialize_schema(self) -> None:
        """Initialize all domain tables, indexes and record schema version idempotently.

        Applies non-destructive additive migrations for databases created with
        earlier schema versions (e.g. adding ``curriculum_id`` to ``notebooks``).
        """
        conn = self.connect()
        conn.executescript(SCHEMA_DDL)
        conn.commit()
        cursor = conn.cursor()
        cursor.execute("PRAGMA user_version;")
        current_v = int(cursor.fetchone()[0])
        cursor.fetchall()
        cursor.close()

        cur = conn.cursor()
        # --- Additive migrations (idempotent) ---
        if current_v < 2:
            self._migrate_to_v2(cur)

        if current_v < 3:
            self._migrate_to_v3(cur)

        if current_v < 4:
            self._migrate_to_v4(cur)

        if current_v < 5:
            self._migrate_to_v5(cur)

        # Ensure default root folder always exists
        cur.execute(
            """
            INSERT OR IGNORE INTO folders (id, name, parent_folder_id, description, created_at, updated_at)
            VALUES ('folder_root', 'Root Folder', NULL, 'Default root folder for notebooks', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            """
        )

        if current_v < self.SCHEMA_VERSION:
            cur.execute(f"PRAGMA user_version = {self.SCHEMA_VERSION};")

        conn.commit()
        cur.close()

    def _migrate_to_v2(self, cursor: sqlite3.Cursor) -> None:
        """v1 -> v2: add ``curriculum_id`` column to ``notebooks`` if absent."""
        cursor.execute("PRAGMA table_info(notebooks);")
        cols = {row[1] for row in cursor.fetchall()}
        if "curriculum_id" not in cols:
            cursor.execute("ALTER TABLE notebooks ADD COLUMN curriculum_id TEXT;")

    def _migrate_to_v3(self, cursor: sqlite3.Cursor) -> None:
        """v2 -> v3: ensure folders table, provision folder_root, add folder_id and unique indexes."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS folders (
                id TEXT PRIMARY KEY NOT NULL,
                name TEXT NOT NULL,
                parent_folder_id TEXT,
                description TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (parent_folder_id) REFERENCES folders(id) ON DELETE SET NULL,
                UNIQUE(name, parent_folder_id)
            );
            """
        )
        cursor.execute(
            """
            INSERT OR IGNORE INTO folders (id, name, parent_folder_id, description, created_at, updated_at)
            VALUES ('folder_root', 'Root Folder', NULL, 'Default root folder for notebooks', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z');
            """
        )
        cursor.execute("PRAGMA table_info(notebooks);")
        cols = {row[1] for row in cursor.fetchall()}
        if "folder_id" not in cols:
            cursor.execute("ALTER TABLE notebooks ADD COLUMN folder_id TEXT NOT NULL DEFAULT 'folder_root';")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notebooks_folder ON notebooks(folder_id);")
            cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_notebooks_name_folder ON notebooks(name, folder_id);")

    def _migrate_to_v4(self, cursor: sqlite3.Cursor) -> None:
        """v3 -> v4: ensure notebook_kcs table exists."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notebook_kcs (
                notebook_id TEXT NOT NULL,
                kc_id TEXT NOT NULL,
                title TEXT NOT NULL,
                prerequisites_json TEXT NOT NULL DEFAULT '[]',
                subtopics_json TEXT NOT NULL DEFAULT '[]',
                estimated_time_min INTEGER,
                difficulty TEXT,
                origin TEXT NOT NULL DEFAULT 'manual',
                created_at TEXT NOT NULL,
                PRIMARY KEY (notebook_id, kc_id),
                FOREIGN KEY (notebook_id) REFERENCES notebooks(id) ON DELETE CASCADE
            );
            """
        )

    def _migrate_to_v5(self, cursor: sqlite3.Cursor) -> None:
        """v4 -> v5: ensure content_registry table and indexes exist."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS content_registry (
                content_id TEXT PRIMARY KEY NOT NULL,
                source_id TEXT NOT NULL,
                unit_type TEXT NOT NULL,
                statement_text TEXT NOT NULL,
                chunk_ids TEXT NOT NULL,
                solution_chunk_ids TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY (source_id) REFERENCES sources(source_id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_reg_source ON content_registry(source_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_reg_type ON content_registry(unit_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_reg_status ON content_registry(status);")

    @contextmanager
    def transaction(self, mode: str = "IMMEDIATE") -> Generator[sqlite3.Connection, None, None]:
        """Transactional context manager with connection pooling and reentrant nested transactions via savepoints."""
        active_conn = getattr(self._thread_local, "conn", None)
        if active_conn is not None:
            depth = getattr(self._thread_local, "depth", 0) + 1
            self._thread_local.depth = depth
            sp_name = f"sp_{depth}"
            active_conn.execute(f"SAVEPOINT {sp_name};")
            try:
                yield active_conn
                active_conn.execute(f"RELEASE SAVEPOINT {sp_name};")
            except Exception:
                active_conn.execute(f"ROLLBACK TO SAVEPOINT {sp_name};")
                raise
            finally:
                self._thread_local.depth = depth - 1
            return

        conn = self.connect()
        # In WAL mode, DEFERRED transactions permit concurrent readers without taking immediate exclusive lock
        conn.execute(f"BEGIN {mode};")
        self._thread_local.conn = conn
        self._thread_local.depth = 0
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._thread_local.conn = None

    def close(self) -> None:
        """Close open connections if active."""
        if self._is_memory and self._mem_conn is not None:
            self._mem_conn.close()
            self._mem_conn = None
        persistent = getattr(self._thread_local, "persistent_conn", None)
        if persistent is not None:
            try:
                persistent.close()
            except Exception:
                pass
            self._thread_local.persistent_conn = None
