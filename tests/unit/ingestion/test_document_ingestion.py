"""Unit tests for S1.5 Document Ingestion."""

from pathlib import Path
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from study_engine.contracts.enums import IngestionStatus
from study_engine.ingestion.document_ingestion import ingest_document, slugify_filename


def create_pdf(file_path: Path, pages_text=None, title=None, encrypt_password=None):
    writer = PdfWriter()
    if pages_text is not None:
        for text in pages_text:
            page = writer.add_blank_page(width=300, height=300)
            if text:
                stream = DecodedStreamObject()
                stream.set_data(f"BT /F1 12 Tf 72 712 Td ({text}) Tj ET".encode("latin-1", errors="replace"))
                page[NameObject("/Contents")] = stream

                fonts = DictionaryObject()
                f1 = DictionaryObject({
                    NameObject("/Type"): NameObject("/Font"),
                    NameObject("/Subtype"): NameObject("/Type1"),
                    NameObject("/BaseFont"): NameObject("/Helvetica"),
                })
                fonts[NameObject("/F1")] = f1
                res = DictionaryObject({NameObject("/Font"): fonts})
                page[NameObject("/Resources")] = res
    else:
        writer.add_blank_page(width=200, height=200)

    if title:
        writer.add_metadata({"/Title": title})

    if encrypt_password:
        writer.encrypt(encrypt_password)

    with open(file_path, "wb") as f:
        writer.write(f)


def test_slugify_filename():
    assert slugify_filename("Capítulo 01") == "capitulo-01"
    assert slugify_filename("Introducción a la Programación #1") == "introduccion-a-la-programacion-1"
    assert slugify_filename("ch__01---rev2") == "ch_01-rev2"
    assert slugify_filename("   spaced   name   ") == "spaced-name"
    assert slugify_filename("---") == "document"
    assert slugify_filename("###") == "document"
    assert slugify_filename("simple_file-123") == "simple_file-123"


def test_ingest_txt_file(tmp_path):
    txt_file = tmp_path / "intro.txt"
    txt_file.write_text("Línea 1: Fundamentos\nLínea 2: Variables", encoding="utf-8")

    result = ingest_document(
        file_path=txt_file,
        source_id="src-prog-1",
        title="Introducción",
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.error is None
    assert result.document is not None
    assert result.document_id == "src-prog-1:intro"
    assert result.document.id == "src-prog-1:intro"
    assert result.document.source_id == "src-prog-1"
    assert result.document.title == "Introducción"
    assert result.document.page_count == 1
    assert "Fundamentos" in result.document.content
    assert result.document.metadata["has_text"] is True


def test_ingest_md_file(tmp_path):
    md_file = tmp_path / "readme.md"
    md_file.write_text("# Título Markdown\n\nContenido explicativo.", encoding="utf-8")

    result = ingest_document(
        file_path=md_file,
        source_id="src-notes",
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.document.title == "readme"
    assert result.document.page_count == 1
    assert "# Título Markdown" in result.document.content


def test_ingest_pdf_single_page(tmp_path):
    pdf_file = tmp_path / "capitulo_01.pdf"
    create_pdf(pdf_file, pages_text=["Texto del primer capitulo"])

    result = ingest_document(
        file_path=pdf_file,
        source_id="joyanes-fp-4e",
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.document.id == "joyanes-fp-4e:capitulo_01"
    assert result.document.page_count == 1
    assert "Texto del primer capitulo" in result.document.content
    assert result.document.metadata["has_text"] is True


def test_ingest_pdf_multi_page(tmp_path):
    pdf_file = tmp_path / "multi.pdf"
    create_pdf(pdf_file, pages_text=["Pagina Uno", "Pagina Dos", "Pagina Tres"])

    result = ingest_document(
        file_path=pdf_file,
        source_id="src-multi",
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.document.page_count == 3
    assert "Pagina Uno" in result.document.content
    assert "Pagina Dos" in result.document.content
    assert "Pagina Tres" in result.document.content


def test_ingest_pdf_without_text(tmp_path):
    pdf_file = tmp_path / "scanned.pdf"
    create_pdf(pdf_file, pages_text=[""])  # Blank page

    result = ingest_document(
        file_path=pdf_file,
        source_id="src-scanned",
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.document.content == ""
    assert result.document.page_count == 1
    assert result.document.metadata["has_text"] is False


def test_title_hierarchy(tmp_path):
    # 1. Explicit title takes precedence
    pdf_meta = tmp_path / "doc_meta.pdf"
    create_pdf(pdf_meta, pages_text=["Text"], title="Metadata Title")

    r1 = ingest_document(pdf_meta, "src-1", title="Explicit Title")
    assert r1.document.title == "Explicit Title"

    # 2. Metadata title fallback when no explicit title
    r2 = ingest_document(pdf_meta, "src-1")
    assert r2.document.title == "Metadata Title"

    # 3. Filename stem fallback when no metadata title and no explicit title
    pdf_no_meta = tmp_path / "my_plain_document.pdf"
    create_pdf(pdf_no_meta, pages_text=["Text"])

    r3 = ingest_document(pdf_no_meta, "src-1")
    assert r3.document.title == "my_plain_document"


def test_document_id_explicit_vs_derived(tmp_path):
    pdf_file = tmp_path / "chapter_01.pdf"
    create_pdf(pdf_file, pages_text=["Text"])

    # Explicit document_id
    r1 = ingest_document(pdf_file, "src-1", document_id="custom-doc-id-001")
    assert r1.document.id == "custom-doc-id-001"
    assert r1.document_id == "custom-doc-id-001"

    # Derived document_id
    r2 = ingest_document(pdf_file, "src-1")
    assert r2.document.id == "src-1:chapter_01"
    assert r2.document_id == "src-1:chapter_01"


def test_multiple_documents_under_same_source_id(tmp_path):
    f1 = tmp_path / "ch01.pdf"
    f2 = tmp_path / "ch02.pdf"
    create_pdf(f1, pages_text=["Chapter 1"])
    create_pdf(f2, pages_text=["Chapter 2"])

    r1 = ingest_document(f1, "joyanes-fp-4e")
    r2 = ingest_document(f2, "joyanes-fp-4e")

    assert r1.document.source_id == "joyanes-fp-4e"
    assert r2.document.source_id == "joyanes-fp-4e"
    assert r1.document.id == "joyanes-fp-4e:ch01"
    assert r2.document.id == "joyanes-fp-4e:ch02"
    assert r1.document.id != r2.document.id


def test_same_filename_under_different_sources(tmp_path):
    f = tmp_path / "intro.pdf"
    create_pdf(f, pages_text=["Introduction"])

    r1 = ingest_document(f, "source-A")
    r2 = ingest_document(f, "source-B")

    assert r1.document.id == "source-A:intro"
    assert r2.document.id == "source-B:intro"
    assert r1.document.id != r2.document.id


def test_corpus_root_path_resolution(tmp_path):
    corpus_root = tmp_path / "Corpus"
    sub_dir = corpus_root / "Fase-0" / "Joyanes"
    sub_dir.mkdir(parents=True)
    pdf_file = sub_dir / "capitulo_01.pdf"
    create_pdf(pdf_file, pages_text=["Content"])

    result = ingest_document(
        file_path=pdf_file,
        source_id="joyanes-fp-4e",
        corpus_root=corpus_root,
    )

    assert result.status == IngestionStatus.COMPLETED
    assert result.document.path == "Fase-0/Joyanes/capitulo_01.pdf"


def test_idempotency_exact_same_input(tmp_path):
    pdf_file = tmp_path / "idemp.pdf"
    create_pdf(pdf_file, pages_text=["Deterministic Content"])

    r1 = ingest_document(pdf_file, "src-1", title="Title", metadata={"k": "v"})
    r2 = ingest_document(pdf_file, "src-1", title="Title", metadata={"k": "v"})

    assert r1.status == IngestionStatus.COMPLETED
    assert r1.document == r2.document


def test_defensive_copy_caller_metadata(tmp_path):
    txt_file = tmp_path / "doc.txt"
    txt_file.write_text("Hello", encoding="utf-8")

    caller_meta = {"category": "test", "tags": ["a", "b"]}
    result = ingest_document(txt_file, "src-1", metadata=caller_meta)

    # Mutate original caller dictionary
    caller_meta["category"] = "mutated"
    caller_meta["tags"].append("c")

    assert result.document.metadata["category"] == "test"
    assert result.document.metadata["tags"] == ["a", "b"]
