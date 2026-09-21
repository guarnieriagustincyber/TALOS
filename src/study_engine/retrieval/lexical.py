import re
import time
from typing import List, Optional, Set
from study_engine.contracts.retrieval import (
    RetrievalDiagnostics,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
    ScoredCandidate,
)
from study_engine.storage.knowledge_store import KnowledgeStore

SPANISH_STOPWORDS: Set[str] = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "cómo",
    "con", "contra", "cual", "cuales", "cuál", "cuáles", "cuando", "cuándo",
    "de", "del", "desde", "donde", "dónde", "durante", "e", "el", "ella", "ellas",
    "ello", "ellos", "en", "entre", "era", "erais", "eran", "eras", "eres", "es",
    "esa", "esas", "ese", "eso", "esos", "esta", "estaba", "estabais", "estaban",
    "estabas", "estad", "estada", "estadas", "estado", "estados", "estais",
    "estamos", "estando", "estar", "estaremos", "estará", "estarán", "estarás",
    "estaré", "estaréis", "estaría", "estaríais", "estaríamos", "estarían",
    "estarías", "estas", "este", "estemos", "esto", "estos", "estoy", "estuve",
    "estuviera", "estuvierais", "estuvieran", "estuvieras", "estuvieron",
    "estuviese", "estuvieseis", "estuviesen", "estuvieses", "estuvimos",
    "estuviste", "estuvisteis", "estuvo", "fue", "fuera", "fuerais", "fueran",
    "fueras", "fueron", "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos",
    "fuiste", "fuisteis", "ha", "habéis", "había", "habíais", "habíamos",
    "habían", "habías", "han", "has", "hasta", "hay", "haya", "hayamos",
    "hayan", "hayas", "hayáis", "he", "hemos", "hube", "hubiera", "hubierais",
    "hubieran", "hubieras", "hubieron", "hubiese", "hubieseis", "hubiesen",
    "hubieses", "hubimos", "hubiste", "hubisteis", "hubo", "la", "las", "le",
    "les", "lo", "los", "me", "mi", "mis", "mía", "mías", "mío", "míos",
    "mucho", "muchos", "muy", "más", "mas", "mí", "nada", "ni", "no", "nos",
    "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o",
    "os", "otra", "otras", "otro", "otros", "para", "pero", "poco", "por",
    "porque", "que", "qué", "quien", "quienes", "quién", "quiénes", "se",
    "sea", "seamos", "sean", "seas", "sentid", "sentida", "sentidas", "sentido",
    "sentidos", "ser", "seremos", "será", "serán", "serás", "seré", "seréis",
    "sería", "seríais", "seríamos", "serían", "serías", "seáis", "siente",
    "sin", "sintiendo", "sobre", "sois", "somos", "son", "soy", "su", "sus",
    "suya", "suyas", "suyo", "suyos", "sí", "también", "tambien", "tanto",
    "te", "tendremos", "tendrá", "tendrán", "tendrás", "tendré", "tendréis",
    "tendría", "tendríais", "tendríamos", "tendrían", "tendrías", "tened",
    "tenemos", "tenga", "tengamos", "tengan", "tengas", "tengo", "tengáis",
    "tenida", "tenidas", "tenido", "tenidos", "teniendo", "tenéis", "tenía",
    "teníais", "teníamos", "tenían", "tenías", "ti", "tiene", "tienen",
    "tienes", "todo", "todos", "tu", "tus", "tuve", "tuviera", "tuvierais",
    "tuvieran", "tuvieras", "tuvieron", "tuviese", "tuvieseis", "tuviesen",
    "tuvieses", "tuvimos", "tuviste", "tuvisteis", "tuvo", "tuya", "tuyas",
    "tuyo", "tuyos", "tú", "u", "un", "una", "unas", "uno", "unos", "vosotras",
    "vosotros", "vuestra", "vuestras", "vuestro", "vuestros", "y", "ya", "yo",
}


def filter_spanish_stopwords(raw_query: str) -> List[str]:
    """Extract word tokens from query and filter out Spanish stopwords.

    Punctuation marks (¿, ?, ¡, !, etc.) are excluded by token extraction.
    Tokens are matched in lower-case against SPANISH_STOPWORDS.
    """
    if not raw_query or not isinstance(raw_query, str):
        return []
    tokens = re.findall(r"\w+", raw_query)
    return [t for t in tokens if t.lower() not in SPANISH_STOPWORDS]


class LexicalRetriever:
    """Deterministic lexical retriever wrapping S2 SQLite FTS5 search."""

    def __init__(self, store: KnowledgeStore) -> None:
        """Initialize with an active KnowledgeStore instance."""
        if not isinstance(store, KnowledgeStore):
            msg = f"Expected KnowledgeStore, got {type(store).__name__}."
            raise TypeError(msg)
        self.store = store

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        """Execute a lexical search scoped strictly to requested notebook."""
        if not isinstance(request, RetrievalRequest):
            msg = f"Expected RetrievalRequest, got {type(request).__name__}."
            raise TypeError(msg)

        start_time = time.perf_counter()

        # Stopwords filtering and query preprocessing
        filtered_tokens = filter_spanish_stopwords(request.query)
        if not filtered_tokens:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            diagnostics = RetrievalDiagnostics(
                lexical_candidates_count=0,
                dense_candidates_count=None,
                unique_candidates_count=0,
                latencies_ms={
                    "retrieval_ms": elapsed_ms,
                    "lexical_ms": elapsed_ms,
                },
                rejection_reason="QUERY_ALL_STOPWORDS",
            )
            return RetrievalResponse(
                query=request.query,
                notebook_id=request.notebook_id,
                strategy_used=RetrievalStrategy.LEXICAL,
                items=[],
                diagnostics=diagnostics,
            )

        clean_query = " ".join(filtered_tokens)

        # Build stem-prefix query for Spanish inflection fallback
        stemmed_tokens: List[str] = []
        for t in filtered_tokens:
            clean = t.strip()
            if clean.lower().endswith("es") and len(clean) > 4:
                stemmed_tokens.append(f"{clean[:-2]}*")
            elif clean.lower().endswith("s") and len(clean) > 3:
                stemmed_tokens.append(f"{clean[:-1]}*")
            else:
                stemmed_tokens.append(f"{clean}*")
        stemmed_query = " ".join(stemmed_tokens)

        # Handle optional single-source / single-document filters
        direct_source_id: Optional[str] = None
        direct_doc_id: Optional[str] = None
        allowed_source_ids: Optional[Set[str]] = None
        allowed_doc_ids: Optional[Set[str]] = None

        if request.source_ids:
            if len(request.source_ids) == 1:
                direct_source_id = request.source_ids[0]
            else:
                allowed_source_ids = set(request.source_ids)

        if request.document_ids:
            if len(request.document_ids) == 1:
                direct_doc_id = request.document_ids[0]
            else:
                allowed_doc_ids = set(request.document_ids)

        # In S2, search limit is direct SQL LIMIT
        # If multi-filter is present, fetch more to guarantee top_k
        has_multi = allowed_source_ids or allowed_doc_ids
        query_limit = request.top_k * 3 if has_multi else request.top_k

        raw_results = self.store.search(
            query=clean_query,
            notebook_id=request.notebook_id,
            source_id=direct_source_id,
            document_id=direct_doc_id,
            limit=query_limit,
        )

        # If exact token match found 0 results, fall back to Spanish stem-prefix search
        if not raw_results and stemmed_query != clean_query:
            raw_results = self.store.search(
                query=stemmed_query,
                notebook_id=request.notebook_id,
                source_id=direct_source_id,
                document_id=direct_doc_id,
                limit=query_limit,
            )

        filtered_results = raw_results
        if allowed_source_ids:
            filtered_results = [
                r for r in filtered_results
                if r.source_id in allowed_source_ids
            ]
        if allowed_doc_ids:
            filtered_results = [
                r for r in filtered_results
                if r.document_id in allowed_doc_ids
            ]

        # Truncate to top_k

        final_results = filtered_results[: request.top_k]

        items: List[ScoredCandidate] = []
        for idx, r in enumerate(final_results):
            # Note on score: In S2 KnowledgeStore, result.score is
            # `-bm25(chunks_fts)`, which negates SQLite's negative BM25
            # score into a positive float where higher is better.
            items.append(
                ScoredCandidate(
                    chunk_id=r.chunk_id,
                    document_id=r.document_id,
                    source_id=r.source_id,
                    notebook_id=request.notebook_id,
                    rank=idx + 1,
                    score=r.score,
                    lexical_score=r.score,
                    dense_score=None,
                    retrieval_method="lexical",
                    content=r.content,
                    page_start=r.page_start,
                    page_end=r.page_end,
                    pos_index=r.index,
                    metadata={"snippet": r.snippet} if r.snippet else {},
                )
            )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        diagnostics = RetrievalDiagnostics(
            lexical_candidates_count=len(raw_results),
            dense_candidates_count=None,
            unique_candidates_count=len(items),
            latencies_ms={
                "retrieval_ms": elapsed_ms,
                "lexical_ms": elapsed_ms,
            },
        )

        return RetrievalResponse(
            query=request.query,
            notebook_id=request.notebook_id,
            strategy_used=RetrievalStrategy.LEXICAL,
            items=items,
            diagnostics=diagnostics,
        )
