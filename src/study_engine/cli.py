"""TALOS CLI — ciclo de ingestión incremental vía Colab (offload de embeddings).

Comandos:

- ``talos export-pending``  → chunks sin vector (LEFT JOIN knowledge vs vector
  store) hacia ``data/colab/pending_<ts>.jsonl`` con el contract embebido.
- ``talos sync-vectors <archivo>`` → valida formato + contract + dim y hace
  INSERT OR REPLACE de los vectores nuevos en UNA sola transacción
  (atómico + idempotente).
- ``talos verify-index`` → pendientes == 0, integrity_check en ambas DBs y
  3 queries de control (in-scope / OOD / coloquial) con top-1 para vigilar
  el umbral MIN_VECTOR_SIMILARITY (0.87).

Invariables:
- Nunca re-procesar vectores existentes (solo INSERT de lo que falta).
- vector_store.db existente es de solo-sumado: la PK compuesta
  (chunk_id, notebook_id) hace el sync naturalmente idempotente.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_DB = REPO_ROOT / "data" / "web_state" / "knowledge_store.db"
DEFAULT_VECTOR_DB = REPO_ROOT / "data" / "web_state" / "vector_store.db"
DEFAULT_COLAB_DIR = REPO_ROOT / "data" / "colab"
DEFAULT_CONTRACT_PATH = DEFAULT_COLAB_DIR / "embedding_contract.json"

PENDING_SCHEMA = "talos-pending-v1"
VECTORS_SCHEMA = "talos-vectors-v1"

# Queries de control para verify-index (notebook fase0-soc).
CONTROL_QUERIES = [
    ("in_scope", "fase0-soc", "¿cómo uso malloc y free sin leaks?"),
    ("ood", "fase0-soc", "¿Cuál es la mejor receta de pasta con ajo?"),
    ("coloquial", "fase0-soc", "¿Cómo se llama cuando un proceso espera demasiado por un recurso?"),
]


# ---------------------------------------------------------------------------
# Contract
# ---------------------------------------------------------------------------

def load_contract(path: Optional[Path] = None) -> Dict[str, Any]:
    """Carga el embedding contract versionado (fuente de verdad del espacio vectorial)."""
    p = path or DEFAULT_CONTRACT_PATH
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _contract_matches(local: Dict[str, Any], remote: Dict[str, Any]) -> List[str]:
    """Devuelve la lista de campos del contract que difieren (vacía si coincide)."""
    fields = ("model_id", "provider_id", "dimensions", "max_length", "normalize_l2", "prefixes")
    return [f for f in fields if local.get(f) != remote.get(f)]


# ---------------------------------------------------------------------------
# export-pending
# ---------------------------------------------------------------------------

def _pending_pairs(
    knowledge_db: Path,
    vector_db: Path,
    dimensions: int = 1024,
) -> List[Tuple[str, str, str]]:
    """Chunks con notebook asignado que aún no tienen embedding (dim=1024).

    Solo cuentan como 'cubiertos' los vectores con dimensions = 1024: los
    vectores legacy de dimensiones anteriores NO habilitan la ruta
    vectorial real y deben re-computarse.
    """
    con = sqlite3.connect(f"file:{knowledge_db}?mode=ro", uri=True)
    try:
        con.execute(f"ATTACH DATABASE 'file:{vector_db}?mode=ro' AS vec")
        rows = con.execute(
            """
            SELECT c.id, ns.notebook_id, c.content
            FROM chunks c
            JOIN notebook_sources ns ON ns.source_id = c.source_id
            LEFT JOIN vec.chunk_embeddings ve
                ON ve.chunk_id = c.id AND ve.notebook_id = ns.notebook_id
               AND ve.dimensions = ?
            WHERE ve.chunk_id IS NULL
            ORDER BY ns.notebook_id, c.id;
            """,
            (dimensions,),
        ).fetchall()
    finally:
        con.close()
    return [(r[0], r[1], r[2] or "") for r in rows]


def export_pending(
    knowledge_db: Path = DEFAULT_KNOWLEDGE_DB,
    vector_db: Path = DEFAULT_VECTOR_DB,
    out_dir: Path = DEFAULT_COLAB_DIR,
    contract_path: Optional[Path] = None,
) -> Tuple[Path, int]:
    """Exporta los chunks pendientes a pending_<ts>.jsonl. Devuelve (path, count)."""
    contract = load_contract(contract_path)
    dims = int(contract.get("dimensions", 1024))
    pairs = _pending_pairs(Path(knowledge_db), Path(vector_db), dimensions=dims)

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"pending_{ts}.jsonl"

    meta = {
        "_meta": {
            "schema": PENDING_SCHEMA,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "contract": contract,
            "count": len(pairs),
        }
    }
    with out_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False) + "\n")
        for chunk_id, notebook_id, text in pairs:
            fh.write(
                json.dumps(
                    {"chunk_id": chunk_id, "notebook_id": notebook_id, "text": text},
                    ensure_ascii=False,
                )
                + "\n"
            )
    return out_path, len(pairs)


# ---------------------------------------------------------------------------
# sync-vectors
# ---------------------------------------------------------------------------

def _parse_vectors_file(path: Path, contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Lee y valida TODO el archivo antes de tocar la DB (fail-fast, nada parcial)."""
    dim = int(contract["dimensions"])
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    records: List[Dict[str, Any]] = []
    meta_checked = False
    for lineno, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{lineno}: JSON inválido ({exc})") from exc

        if "_meta" in obj:
            meta = obj["_meta"]
            if meta.get("schema") != VECTORS_SCHEMA:
                raise ValueError(f"{path}: schema '{meta.get('schema')}' != '{VECTORS_SCHEMA}'")
            remote_contract = meta.get("contract")
            if remote_contract is not None:
                diffs = _contract_matches(contract, remote_contract)
                if diffs:
                    raise ValueError(
                        f"{path}: contract incompatible en campos {diffs} — "
                        "los vectores vendrían de un espacio de embedding distinto."
                    )
            meta_checked = True
            continue

        chunk_id = obj.get("chunk_id")
        notebook_id = obj.get("notebook_id")
        vector = obj.get("vector")
        if not chunk_id or not notebook_id:
            raise ValueError(f"{path}:{lineno}: falta chunk_id o notebook_id")
        if not isinstance(vector, list) or len(vector) != dim:
            raise ValueError(
                f"{path}:{lineno}: vector con dim {len(vector) if isinstance(vector, list) else 'n/a'} != {dim}"
            )
        if any((not isinstance(v, (int, float))) or v != v for v in vector):
            raise ValueError(f"{path}:{lineno}: vector con valores no finitos")
        records.append({"chunk_id": chunk_id, "notebook_id": notebook_id, "vector": [float(v) for v in vector]})
    return records


def sync_vectors(
    vectors_jsonl: Path,
    vector_db: Path = DEFAULT_VECTOR_DB,
    knowledge_db: Path = DEFAULT_KNOWLEDGE_DB,
    contract_path: Optional[Path] = None,
    batch_size: int = 5000,
) -> Dict[str, int]:
    """Inserta vectores nuevos en UNA transacción streaming (idempotente y memory-safe para archivos multi-GB)."""
    import struct
    from study_engine.retrieval.vector_store import SQLiteVectorStore

    contract = load_contract(contract_path)
    dim = int(contract["dimensions"])
    model_id = contract["model_id"]
    provider_id = contract["provider_id"]

    # chunk_id -> source_id (la FK semántica del embedding hacia el corpus)
    kcon = sqlite3.connect(f"file:{knowledge_db}?mode=ro", uri=True)
    try:
        src_map = {r[0]: r[1] for r in kcon.execute("SELECT id, source_id FROM chunks")}
    finally:
        kcon.close()

    # Asegurar inicialización de schema e índices en el vector store
    vstore = SQLiteVectorStore(vector_db)
    vstore.close()

    vcon = sqlite3.connect(str(vector_db))
    vcon.execute("PRAGMA journal_mode = WAL;")
    vcon.execute("PRAGMA synchronous = NORMAL;")
    vcon.execute("PRAGMA busy_timeout = 30000;")

    # Identificar existentes para clasificar inserted vs updated
    existing_keys = {
        (r[0], r[1])
        for r in vcon.execute(
            "SELECT chunk_id, notebook_id FROM chunk_embeddings WHERE dimensions = ?",
            (dim,),
        )
    }

    inserted = 0
    updated = 0
    total_synced = 0

    vcon.execute("BEGIN TRANSACTION;")
    try:
        batch = []
        meta_checked = False

        with open(vectors_jsonl, "r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{vectors_jsonl}:{lineno}: JSON inválido ({exc})") from exc

                if "_meta" in obj:
                    meta = obj["_meta"]
                    if meta.get("schema") != VECTORS_SCHEMA:
                        raise ValueError(f"{vectors_jsonl}: schema '{meta.get('schema')}' != '{VECTORS_SCHEMA}'")
                    remote_contract = meta.get("contract")
                    if remote_contract is not None:
                        diffs = _contract_matches(contract, remote_contract)
                        if diffs:
                            raise ValueError(
                                f"{vectors_jsonl}: contract incompatible en campos {diffs} — "
                                "los vectores vendrían de un espacio de embedding distinto."
                            )
                    meta_checked = True
                    continue

                chunk_id = obj.get("chunk_id")
                notebook_id = obj.get("notebook_id")
                vector = obj.get("vector")

                if not chunk_id or not notebook_id:
                    raise ValueError(f"{vectors_jsonl}:{lineno}: falta chunk_id o notebook_id")

                if chunk_id not in src_map:
                    raise ValueError(
                        f"{vectors_jsonl}:{lineno}: chunk_id '{chunk_id}' no existen en knowledge_store. "
                        "Sync abortado: nada fue insertado."
                    )

                if not isinstance(vector, list) or len(vector) != dim:
                    raise ValueError(
                        f"{vectors_jsonl}:{lineno}: vector con dim "
                        f"{len(vector) if isinstance(vector, list) else 'n/a'} != {dim}"
                    )

                if any((not isinstance(v, (int, float))) or v != v for v in vector):
                    raise ValueError(f"{vectors_jsonl}:{lineno}: vector con valores no finitos")

                blob = struct.pack(f"{dim}f", *vector)
                source_id = src_map[chunk_id]
                batch.append((chunk_id, notebook_id, source_id, provider_id, model_id, dim, blob))

                key = (chunk_id, notebook_id)
                if key in existing_keys:
                    updated += 1
                else:
                    inserted += 1
                    existing_keys.add(key)
                total_synced += 1

                if len(batch) >= batch_size:
                    vcon.executemany(
                        """
                        INSERT OR REPLACE INTO chunk_embeddings (
                            chunk_id, notebook_id, source_id, provider_id, model_id, dimensions, vector
                        ) VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        batch,
                    )
                    batch.clear()

            if batch:
                vcon.executemany(
                    """
                    INSERT OR REPLACE INTO chunk_embeddings (
                        chunk_id, notebook_id, source_id, provider_id, model_id, dimensions, vector
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    batch,
                )
                batch.clear()

        if total_synced == 0:
            raise ValueError(f"{vectors_jsonl}: no contiene vectores válidos")

        vcon.commit()
    except Exception:
        vcon.rollback()
        raise
    finally:
        vcon.close()

    pending_after = len(
        _pending_pairs(
            Path(knowledge_db),
            Path(vector_db),
            dimensions=dim,
        )
    )
    return {
        "synced": total_synced,
        "inserted": inserted,
        "updated": updated,
        "pending_after": pending_after,
    }


# ---------------------------------------------------------------------------
# verify-index
# ---------------------------------------------------------------------------

def verify_index(
    knowledge_db: Path = DEFAULT_KNOWLEDGE_DB,
    vector_db: Path = DEFAULT_VECTOR_DB,
    run_control_queries: bool = True,
) -> Dict[str, Any]:
    """Integridad + cobertura + queries de control. Devuelve dict de reporte."""
    report: Dict[str, Any] = {"ok": True, "checks": {}}

    pending = _pending_pairs(Path(knowledge_db), Path(vector_db))
    report["checks"]["pending_chunks"] = len(pending)
    if pending:
        report["ok"] = False

    for name, db in (("knowledge_store", knowledge_db), ("vector_store", vector_db)):
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            con.close()
        report["checks"][f"integrity_{name}"] = integrity
        if integrity != "ok":
            report["ok"] = False

    if run_control_queries:
        control = []
        from study_engine.storage.knowledge_store import KnowledgeStore

        store = KnowledgeStore(Path(knowledge_db))
        for label, notebook_id, query in CONTROL_QUERIES:
            t0 = time.perf_counter()
            results = store.search_hybrid(query=query, notebook_id=notebook_id, limit=6, min_sources=3)
            elapsed_ms = round((time.perf_counter() - t0) * 1000)
            top1 = results[0].score if results else None
            control.append(
                {
                    "label": label,
                    "query": query,
                    "hits": len(results),
                    "top1_score": top1,
                    "ms": elapsed_ms,
                    "gate": "ABSTIENE" if not results else "RESPONDE",
                }
            )
            # Sanidad esperada del gate post-F3/calibración:
            # in_scope y coloquial deben responder; OOD debe abstener.
            expected_respond = label != "ood"
            actually_responds = len(results) > 0
            if actually_responds != expected_respond:
                report["ok"] = False
        report["checks"]["control_queries"] = control

    return report


# ---------------------------------------------------------------------------
# talos kc — gestión de Knowledge Components (Fase 5.2)
# ---------------------------------------------------------------------------

DEFAULT_STUDENT_DB = REPO_ROOT / "data" / "web_state" / "student_state.db"

_DIFFICULTY_MAP = {
    "basic": "basico",
    "intermediate": "intermedio",
    "advanced": "avanzado",
    "basico": "basico",
    "intermedio": "intermedio",
    "avanzado": "avanzado",
}


def _slugify(text: str) -> str:
    import re as _re
    import unicodedata as _ud

    norm = _ud.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    slug = _re.sub(r"[^a-z0-9]+", "_", norm.lower()).strip("_")
    return slug or "kc_manual"


def _open_kc_store(knowledge_db: Path):
    from study_engine.curriculum.kc_admin import KCAdminStore
    from study_engine.storage.sqlite_engine import SQLiteStorageEngine

    return KCAdminStore(SQLiteStorageEngine(Path(knowledge_db)))


def _kc_bkt_status(student_db: Path) -> Dict[str, float]:
    """p_L por kc_id (si existe la DB de estudiante)."""
    import sqlite3 as _sq

    if not Path(student_db).exists():
        return {}
    con = _sq.connect(f"file:{student_db}?mode=ro", uri=True)
    try:
        return {r[0]: r[1] for r in con.execute("SELECT kc_id, p_L FROM bkt_states")}
    except Exception:
        return {}
    finally:
        con.close()


def _kc_status_label(p_l: Optional[float]) -> str:
    if p_l is None:
        return "not_started"
    if p_l >= 0.8:
        return "mastered"
    if p_l >= 0.4:
        return "in_progress"
    return "not_started"


def _cmd_kc_list(args: argparse.Namespace) -> int:
    store = _open_kc_store(Path(args.knowledge_db))
    manual = {k["kc_id"]: k for k in store.list_manual_kcs(args.notebook_id)}

    # Catálogo canónico JSON
    catalog_path = REPO_ROOT / "config" / "notebook_kc_catalog.json"
    json_kcs: List[Dict[str, Any]] = []
    if catalog_path.exists():
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        json_kcs = (data.get(args.notebook_id, {}) or {}).get("kcs", []) or []

    rows: List[Dict[str, Any]] = []
    for kc in json_kcs:
        rows.append({
            "kc_id": kc.get("kc_id", ""),
            "title": kc.get("title") or kc.get("display_name") or "",
            "difficulty": "—",
            "origin": "json",
        })
    rows += [
        {
            "kc_id": k["kc_id"],
            "title": k["title"],
            "difficulty": k.get("difficulty") or "—",
            "origin": k["origin"],
        }
        for k in manual.values()
    ]

    if not rows:
        print(f"No hay KCs definidos para este notebook ('{args.notebook_id}').")
        return 0

    bkt = _kc_bkt_status(Path(args.student_db))
    headers = ("KC_ID", "DIFICULTAD", "ORIGEN", "ESTADO BKT", "TÍTULO")
    widths = [
        min(max([len(headers[i])] + [len(str(r[c])) for r in rows]), 28) + 2
        for i, c in enumerate(("kc_id", "difficulty", "origin"))
    ]

    print(f"KCs de '{args.notebook_id}' ({len(rows)}):")
    for r in rows:
        status = _kc_status_label(bkt.get(r["kc_id"]))
        line = (
            f"  {r['kc_id']:<{widths[0]}} {r['difficulty']:<{widths[1]}} "
            f"{r['origin']:<{widths[2]}} {status:<12} {r['title'][:56]}"
        )
        print(line)
    return 0


def _cmd_kc_add(args: argparse.Namespace) -> int:
    store = _open_kc_store(Path(args.knowledge_db))

    # Validar que el notebook exista
    import sqlite3 as _sq
    con = _sq.connect(f"file:{args.knowledge_db}?mode=ro", uri=True)
    try:
        exists = con.execute("SELECT 1 FROM notebooks WHERE id = ?", (args.notebook_id,)).fetchone()
    finally:
        con.close()
    if not exists:
        print(f"Error: el notebook '{args.notebook_id}' no existe (404).")
        return 1

    difficulty = _DIFFICULTY_MAP.get((args.diff or "").lower()) if args.diff else None
    if args.diff and difficulty is None:
        print(f"Error: dificultad inválida '{args.diff}'. Válidas: basic, intermediate, advanced.")
        return 2

    prereqs = [p.strip() for p in (args.prereq or "").split(",") if p.strip()] or None
    subtopics = [s.strip() for s in (args.subtopics or "").split(",") if s.strip()] or None

    # Catálogo efectivo (JSON + manuales) para dedupe
    catalog_path = REPO_ROOT / "config" / "notebook_kc_catalog.json"
    existing: List[Dict[str, Any]] = []
    if catalog_path.exists():
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        existing = (data.get(args.notebook_id, {}) or {}).get("kcs", []) or []
    existing += store.list_manual_kcs(args.notebook_id)

    from study_engine.curriculum.kc_admin import DuplicateKCError

    kc_id = args.kc_id or _slugify(args.title)
    try:
        rec = store.add_kc(
            notebook_id=args.notebook_id,
            kc_id=kc_id,
            title=args.title,
            prerequisites=prereqs,
            subtopics=subtopics,
            estimated_time=args.time,
            difficulty=difficulty,
            existing_kcs=existing,
        )
    except DuplicateKCError:
        print(f"Error: El KC '{kc_id}' ya existe en este notebook (409).")
        return 4
    except ValueError as exc:
        print(f"Error de validación: {exc}")
        return 2

    print(f"✅ KC '{rec['kc_id']}' agregado exitosamente al notebook '{args.notebook_id}'.")
    return 0


def _cmd_kc_delete(args: argparse.Namespace) -> int:
    store = _open_kc_store(Path(args.knowledge_db))
    deleted = store.delete_manual_kc(args.notebook_id, args.kc_id)
    if deleted:
        print(f"🗑️  KC manual '{args.kc_id}' eliminado de '{args.notebook_id}'.")
        print("   Nota: si el backend está vivo, refrescá o reiniciá para reemerger el catálogo.")
        return 0
    print(
        f"Error: no existe KC manual '{args.kc_id}' en '{args.notebook_id}'. "
        "(Los KCs canónicos del JSON no se pueden borrar por este comando.)"
    )
    return 4




def _cmd_export_pending(args: argparse.Namespace) -> int:
    out_path, count = export_pending(
        knowledge_db=Path(args.knowledge_db),
        vector_db=Path(args.vector_db),
        out_dir=Path(args.out_dir),
    )
    print(f"pendientes: {count}")
    print(f"archivo:    {out_path}")
    if count == 0:
        print("índice completo: no hay chunks sin vector (caso base OK)")
    return 0


def _cmd_sync_vectors(args: argparse.Namespace) -> int:
    try:
        res = sync_vectors(
            vectors_jsonl=Path(args.archivo),
            vector_db=Path(args.vector_db),
            knowledge_db=Path(args.knowledge_db),
        )
    except ValueError as exc:
        print(f"SYNC ABORTADO: {exc}")
        return 2
    print(
        f"sync OK: {res['synced']} vectores "
        f"({res['inserted']} nuevos, {res['updated']} reemplazados) | "
        f"pendientes restantes: {res['pending_after']}"
    )
    return 0


def _cmd_verify_index(args: argparse.Namespace) -> int:
    t0 = time.perf_counter()
    report = verify_index(
        knowledge_db=Path(args.knowledge_db),
        vector_db=Path(args.vector_db),
        run_control_queries=not args.no_control_queries,
    )
    for key, val in report["checks"].items():
        if key == "control_queries":
            for c in val:
                print(
                    f"  control[{c['label']}]: gate={c['gate']} hits={c['hits']} "
                    f"top1={c['top1_score']} ({c['ms']}ms)"
                )
        else:
            print(f"  {key}: {val}")
    print(f"verify-index: {'OK' if report['ok'] else 'FALLO'} ({round((time.perf_counter()-t0)*1000)}ms)")
    return 0 if report["ok"] else 1


# ---------------------------------------------------------------------------
# talos content — unidades curriculares y solucionarios (Slice 6.0.5)
# ---------------------------------------------------------------------------

def _open_knowledge_store(knowledge_db: Path):
    from study_engine.storage.knowledge_store import KnowledgeStore

    store = KnowledgeStore(Path(knowledge_db))
    store.initialize()
    return store


def _open_student_storage(student_db: Path):
    from study_engine.student.storage import StudentStorage

    return StudentStorage(Path(student_db))


def _resolve_content_item(store: Any, ref: str):
    ref_clean = ref.strip()
    # 1. Direct get by exact content_id
    item = store.content_registry.get(ref_clean)
    if item is not None:
        return item

    # 2. Extract reference with known content_ids
    from study_engine.retrieval.reference_extractor import extract_reference

    known_items = store.content_registry.list_all()
    known_ids = [it.content_id for it in known_items]
    res = extract_reference(ref_clean, known_content_ids=known_ids)
    if res and res.content_id:
        item = store.content_registry.get(res.content_id)
        if item is not None:
            return item
        for it in known_items:
            if it.content_id.lower() == res.content_id.lower():
                return it
    return None


def _cmd_content_show(args: argparse.Namespace) -> int:
    store = _open_knowledge_store(Path(args.knowledge_db))
    item = _resolve_content_item(store, args.reference)
    if item is None:
        print(f"Error: Contenido '{args.reference}' no encontrado en el registro.", file=sys.stderr)
        return 1

    chunk_repo = getattr(store, "chunks", None) or getattr(getattr(store, "repositories", None), "chunks", None)
    stmt_chunks, _ = store.content_registry.get_statement_chunks(item.content_id, chunk_repo)

    print("=" * 70)
    print(f"ID: {item.content_id} | Tipo: {item.unit_type.value.upper()} | Estado: {item.status.value.upper()}")
    print(f"Fuente: {item.source_id}")
    print("=" * 70)
    print("\n[ENUNCIADO]:")
    print(item.statement_text)
    if stmt_chunks:
        print("\n[FRAGMENTOS DE CONTENIDO]:")
        for idx, chk in enumerate(stmt_chunks, 1):
            p_str = f"Pág {chk.page_start}" if getattr(chk, "page_start", None) else ""
            print(f"\n--- Fragmento {idx} ({p_str}) [Chunk ID: {chk.id}] ---")
            print(chk.content.strip())
    print("\n" + "=" * 70)
    return 0


def _cmd_content_solution(args: argparse.Namespace) -> int:
    store = _open_knowledge_store(Path(args.knowledge_db))
    item = _resolve_content_item(store, args.reference)
    if item is None:
        print(f"Error: Contenido '{args.reference}' no encontrado en el registro.", file=sys.stderr)
        return 1

    student_storage = _open_student_storage(Path(args.student_db))
    has_attempt = student_storage.has_exercise_attempt(item.content_id)

    if not has_attempt and not args.force:
        print(
            f"ACCESO DENEGADO: No podés ver la solución de '{item.content_id}' sin haber registrado al menos un intento de resolución previo.\n"
            f"Para forzar la visualización (quedará registrado en auditoría), ejecutá:\n"
            f"  talos content solution \"{args.reference}\" --force",
            file=sys.stderr,
        )
        return 2

    # Registrar acceso a solucionario
    student_storage.log_solution_access(
        content_id=item.content_id,
        forced=bool(args.force),
        metadata={"ref_input": args.reference, "has_attempt": has_attempt},
    )

    chunk_repo = getattr(store, "chunks", None) or getattr(getattr(store, "repositories", None), "chunks", None)
    sol_chunks = store.content_registry.get_solution_chunks(item.content_id, chunk_repo)

    print("=" * 70)
    audit_mode = "FORZADO (SIN INTENTO PREVIO)" if (args.force and not has_attempt) else "AUTORIZADO (CON INTENTO PREVIO)"
    print(f"SOLUCIONARIO: {item.content_id} | Acceso: {audit_mode}")
    print(f"Fuente: {item.source_id}")
    print("=" * 70)

    if not sol_chunks:
        print(f"\nNo hay fragmentos de solución registrados en el sistema para '{item.content_id}'.")
    else:
        for idx, chk in enumerate(sol_chunks, 1):
            p_str = f"Pág {chk.page_start}" if getattr(chk, "page_start", None) else ""
            print(f"\n--- Solución Fragmento {idx} ({p_str}) [Chunk ID: {chk.id}] ---")
            print(chk.content.strip())
    print("\n" + "=" * 70)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="talos", description="TALOS CLI — ciclo Colab de embeddings")
    parser.add_argument("--knowledge-db", default=str(DEFAULT_KNOWLEDGE_DB))
    parser.add_argument("--vector-db", default=str(DEFAULT_VECTOR_DB))
    sub = parser.add_subparsers(dest="command", required=True)

    p_exp = sub.add_parser("export-pending", help="Exporta chunks sin vector a data/colab/")
    p_exp.add_argument("--out-dir", default=str(DEFAULT_COLAB_DIR))
    p_exp.set_defaults(func=_cmd_export_pending)

    p_sync = sub.add_parser("sync-vectors", help="Sincroniza vectors_<ts>.jsonl desde Colab")
    p_sync.add_argument("archivo", help="Ruta al vectors_<ts>.jsonl")
    p_sync.set_defaults(func=_cmd_sync_vectors)

    p_ver = sub.add_parser("verify-index", help="Verifica cobertura, integridad y gate de abstención")
    p_ver.add_argument("--no-control-queries", action="store_true", help="Salta las 3 queries de control")
    p_ver.set_defaults(func=_cmd_verify_index)

    # talos kc — gestión de Knowledge Components (Fase 5.2)
    p_kc = sub.add_parser("kc", help="Gestiona Knowledge Components de un notebook")
    p_kc.add_argument("--student-db", default=str(DEFAULT_STUDENT_DB),
                      help="DB de estudiante para estados BKT (solo lectura)")
    kc_sub = p_kc.add_subparsers(dest="kc_command", required=True)

    p_kc_list = kc_sub.add_parser("list", help="Lista KCs de un notebook")
    p_kc_list.add_argument("notebook_id")
    p_kc_list.set_defaults(func=_cmd_kc_list)

    p_kc_add = kc_sub.add_parser("add", help="Agrega un KC manual al notebook")
    p_kc_add.add_argument("notebook_id")
    p_kc_add.add_argument("--title", required=True)
    p_kc_add.add_argument("--kc-id", default=None, help="ID explícito (default: slug del título)")
    p_kc_add.add_argument("--prereq", default=None, help="Prerequisitos separados por coma")
    p_kc_add.add_argument("--subtopics", default=None, help="Subtemas separados por coma")
    p_kc_add.add_argument("--time", type=int, default=None, help="Minutos estimados")
    p_kc_add.add_argument("--diff", default=None, help="basic|intermediate|advanced")
    p_kc_add.set_defaults(func=_cmd_kc_add)

    p_kc_del = kc_sub.add_parser("delete", help="Elimina un KC manual (no borra canónicos JSON)")
    p_kc_del.add_argument("notebook_id")
    p_kc_del.add_argument("kc_id")
    p_kc_del.set_defaults(func=_cmd_kc_delete)

    # talos content — gestión y visualización de unidades del content_registry (Slice 6.0.5)
    p_content = sub.add_parser("content", help="Gestión y visualización de unidades curriculares del content_registry")
    p_content.add_argument("--student-db", default=str(DEFAULT_STUDENT_DB),
                           help="DB de estudiante para verificación y log de intentos")
    content_sub = p_content.add_subparsers(dest="content_command", required=True)

    p_content_show = content_sub.add_parser("show", help="Muestra enunciado y metadatos (filtrado, jamás solucionario)")
    p_content_show.add_argument("reference", help="Referencia textual (ej: 'guia 4 ejercicio 3', 'sec 3.1') o content_id")
    p_content_show.set_defaults(func=_cmd_content_show)

    p_content_solution = content_sub.add_parser("solution", help="Muestra el solucionario si el estudiante ya lo intentó o con --force")
    p_content_solution.add_argument("reference", help="Referencia textual o content_id")
    p_content_solution.add_argument("--force", action="store_true", help="Fuerza la visualización sin intento previo (registrado en auditoría)")
    p_content_solution.set_defaults(func=_cmd_content_solution)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
