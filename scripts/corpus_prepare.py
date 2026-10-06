#!/usr/bin/env python3
"""
TALOS Corpus Preparation Script (CP114-PRE v4.1).

Discovers source PDFs, computes authoritative SHA-256 hashes, detects duplicates,
enforces strict privacy boundaries (blocking .env, *.db, student_state, secrets),
builds authoritative manifest.json, and stages files in corpus_upload/ for Google Drive / Colab.

Usage:
  python scripts/corpus_prepare.py --pilot
  python scripts/corpus_prepare.py --all
  python scripts/corpus_prepare.py --files "Operating Systems*.pdf" "Fundamentos*.pdf"
"""

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES_DIR = REPO_ROOT / "fuentes"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "corpus_upload"

# Authoritative Pilot Documents (Diverse Representation Spectrum)
PILOT_TARGETS = [
    # Pilot 1: Core OS, Process Tables, State Transitions, Headings, Technical Prosa
    "Operating Systems - Internals and Design Principles 7th.pdf",
    # Pilot 2: Programming Fundamentals, C/C++ Code Blocks, Algorithms, Indentation
    "Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf",
    # Pilot 3: Modular Unit, Short Grounded Benchmark Reference
    "prog_punteros.pdf",
]

# Strict Privacy and Security Blacklist: Under no circumstances can these be staged or processed
FORBIDDEN_SUBSTRINGS = [
    ".env",
    ".db",
    ".sqlite",
    "student_state",
    "secret",
    "token",
    "key",
    "password",
    "credential",
    "cache",
    "mem0",
    ".log",
    "private",
]


def is_sensitive_path(path: Path) -> bool:
    """Check if a path or filename matches any forbidden privacy pattern."""
    path_str = str(path).lower()
    for forbidden in FORBIDDEN_SUBSTRINGS:
        if forbidden in path_str:
            return True
    return False


def compute_sha256(file_path: Path) -> str:
    """Compute cryptographic SHA-256 of a file in binary blocks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while block := f.read(65536):
            hasher.update(block)
    return hasher.hexdigest()


def scan_source_pdfs(sources_dir: Path) -> List[Path]:
    """Scan and return all unique non-sensitive PDF files under sources directory."""
    if not sources_dir.exists():
        raise FileNotFoundError(f"Sources directory not found: {sources_dir}")

    discovered = []
    for p in sources_dir.rglob("*.pdf"):
        # Privacy filter
        if is_sensitive_path(p):
            print(f"🚨 PRIVACY GUARD: Excluded sensitive path matching blacklist: {p}")
            continue

        if p.suffix.lower() != ".pdf":
            continue

        # Resolve symlinks to avoid ghost or broken paths
        resolved = p.resolve()
        if resolved.exists() and resolved.is_file():
            if is_sensitive_path(resolved):
                print(f"🚨 PRIVACY GUARD: Excluded sensitive symlink target: {resolved}")
                continue
            discovered.append(p)
    return sorted(discovered, key=lambda x: x.name)


def prepare_corpus(
    sources_dir: Path,
    output_dir: Path,
    targets: Optional[List[str]] = None,
    is_pilot: bool = False,
    copy_files: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Prepare manifest and stage files for upload."""
    all_pdfs = scan_source_pdfs(sources_dir)
    if not all_pdfs:
        print(f"❌ No PDF files found in {sources_dir}")
        return {"status": "NO_FILES"}

    # Filter targets
    selected_pdfs: List[Path] = []
    if is_pilot:
        target_names = set(PILOT_TARGETS)
        for p in all_pdfs:
            if p.name in target_names and p not in selected_pdfs:
                selected_pdfs.append(p)
    elif targets:
        for p in all_pdfs:
            for t in targets:
                if fnmatch.fnmatch(p.name, t) or t in p.name:
                    if p not in selected_pdfs:
                        selected_pdfs.append(p)
    else:
        selected_pdfs = all_pdfs

    if not selected_pdfs:
        print("❌ No files matched the requested targets.")
        return {"status": "NO_MATCH"}

    print(f"\n📋 Preparing {len(selected_pdfs)} PDF document(s)...")

    # Hash and metadata extraction
    manifest_sources = []
    seen_hashes: Dict[str, str] = {}
    duplicates: List[Tuple[str, str, str]] = []
    total_bytes = 0

    for pdf_path in selected_pdfs:
        if is_sensitive_path(pdf_path):
            print(f"🚨 PRIVACY GUARD: Blocked file {pdf_path.name}")
            continue

        sha = compute_sha256(pdf_path)
        size = pdf_path.stat().st_size
        total_bytes += size
        
        # Check duplicate content
        if sha in seen_hashes:
            duplicates.append((pdf_path.name, seen_hashes[sha], sha))
            print(f"⚠️  Duplicate detected: '{pdf_path.name}' has same content as '{seen_hashes[sha]}'")
            continue
        seen_hashes[sha] = pdf_path.name

        rel_path = str(pdf_path.relative_to(REPO_ROOT))

        manifest_sources.append({
            "document_id": f"sha256:{sha}",
            "filename": pdf_path.name,
            "relative_source_path": rel_path,
            "sha256": sha,
            "byte_size": size,
            "mime_type": "application/pdf"
        })
        print(f"  ✓ [{size / (1024*1024):5.1f} MB] {pdf_path.name} ({sha[:12]}...)")

    manifest = {
        "schema": "talos-corpus-upload-manifest-v1",
        "created_at": "2026-10-02T19:30:00Z",
        "pipeline_version": "1.5.0-prep",
        "total_documents": len(manifest_sources),
        "total_bytes": total_bytes,
        "is_pilot": is_pilot,
        "sources": manifest_sources,
        "duplicates_skipped": [
            {"filename": d[0], "duplicate_of": d[1], "sha256": d[2]}
            for d in duplicates
        ]
    }

    if dry_run:
        print("\nℹ️  Dry-run active: no files staged to disk.")
        return manifest

    # Staging directory setup
    pdf_stage_dir = output_dir / "pdf"
    if output_dir.exists():
        # Keep clean
        shutil.rmtree(output_dir)
    pdf_stage_dir.mkdir(parents=True, exist_ok=True)

    # Write manifest.json
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Stage files (symlinks by default to save disk space, or copies if requested)
    for s in manifest_sources:
        src = REPO_ROOT / s["relative_source_path"]
        dst = pdf_stage_dir / s["filename"]
        
        # Verify destination name is clean
        if is_sensitive_path(dst):
            raise RuntimeError(f"Refusing to stage sensitive path: {dst}")

        if copy_files:
            shutil.copy2(src, dst)
        else:
            try:
                # Use relative symlink or copy fallback
                dst.symlink_to(src.resolve())
            except OSError:
                shutil.copy2(src, dst)

    # Final privacy verification of staged folder
    for staged_item in output_dir.rglob("*"):
        if staged_item.is_file():
            if is_sensitive_path(staged_item):
                shutil.rmtree(output_dir)
                raise RuntimeError(f"Critical Privacy Violation: sensitive file detected in staging: {staged_item}")
            if staged_item.name != "manifest.json" and staged_item.suffix.lower() != ".pdf":
                shutil.rmtree(output_dir)
                raise RuntimeError(f"Unexpected non-PDF file detected in staging: {staged_item}")

    print(f"\n✅ Staging complete in: {output_dir}")
    print(f"   Manifest: {manifest_path} ({len(manifest_sources)} items)")
    print(f"   PDF Directory: {pdf_stage_dir}")
    print(f"   Total Staged Size: {total_bytes / (1024*1024):.2f} MB")
    print("\n👉 Upload Instructions:")
    print("   Upload the contents of 'corpus_upload/' (manifest.json and pdf/ folder)")
    print("   to your Google Drive folder (e.g. 'TALOS/corpus_upload/').")

    return manifest


def main():
    parser = argparse.ArgumentParser(description="TALOS Corpus Preparation CLI")
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES_DIR), help="Sources directory")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_DIR), help="Output staging directory")
    parser.add_argument("--pilot", action="store_true", help="Stage representative pilot documents only")
    parser.add_argument("--all", action="store_true", help="Stage all discovered PDF documents")
    parser.add_argument("--files", nargs="*", help="Specific filenames or glob patterns to stage")
    parser.add_argument("--copy", action="store_true", help="Copy physical files instead of symlinks")
    parser.add_argument("--dry-run", action="store_true", help="Inspect without modifying filesystem")
    args = parser.parse_args()

    prepare_corpus(
        sources_dir=Path(args.sources),
        output_dir=Path(args.output),
        targets=args.files,
        is_pilot=args.pilot or (not args.all and not args.files),
        copy_files=args.copy,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
