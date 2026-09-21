"""Lexical indexing and BM25 search engine powered by SQLite FTS5."""

import re
from typing import List, Optional, Set

from study_engine.contracts.search import SearchResult
from study_engine.storage.sqlite_engine import SQLiteStorageEngine

SPANISH_STOPWORDS: Set[str] = {
    # Classical grammatical stopwords
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
    # Conversational / prompt framing stopwords
    "explicame", "explícame", "explicar", "explicacion", "explicación",
    "decime", "décime", "decir", "hola", "saludos", "buenos", "dias", "días",
    "tardes", "noches", "favor", "podrias", "podrías", "podes", "podés",
    "quiero", "saber", "entender", "ayuda", "consulta", "duda", "pregunta",
    "funciona", "funcionan", "funcione", "funcionen", "funcionamiento",
    "seccion", "sección", "secciones", "describe", "describir", "descripción",
    "ocurre", "sucede", "pasa", "exactamente", "paso", "versus", "vs", "cuenta",
    "relaciona", "relacionan", "relación", "genera", "generar"
}


class SQLiteLexicalIndex:
    """High-performance lexical search engine using SQLite FTS5 with Okapi BM25 ranking."""

    def __init__(self, engine: SQLiteStorageEngine):
        self.engine = engine

    MAX_QUERY_CHARS: int = 2000
    MAX_QUERY_TOKENS: int = 100

    def sanitize_query(self, raw_query: str, disjunctive: bool = False) -> str:
        """Sanitize raw user input to prevent FTS5 syntax errors while preserving search semantics.

        - Extracts exact quoted phrases verbatim (e.g. '"buffer overflow"').
        - Filters out Spanish grammatical and conversational stopwords.
        - Preserves alphanumeric / unicode word tokens.
        - Employs disjunctive OR logic when disjunctive=True, or conjunctive AND by default.
        - Enforces length and token limits to prevent DoS attacks.
        """
        if not raw_query or not isinstance(raw_query, str):
            return ""

        bounded_query = raw_query[: self.MAX_QUERY_CHARS]

        # 1. Extract explicit quotes
        quotes = re.findall(r'"([^"]+)"', bounded_query)
        cleaned = re.sub(r'"[^"]+"', " ", bounded_query)

        # 2. Extract words
        words = re.findall(r"\w+\*?", cleaned.lower())
        meaningful = [w for w in words if w not in SPANISH_STOPWORDS and len(w) > 1 and w not in ("and", "or", "not")]

        clauses: List[str] = []
        for q in quotes:
            clean_q = q.strip()
            if clean_q:
                # Wrap each word inside quoted phrase
                phrase_words = [f'"{t}"' for t in re.findall(r"\w+", clean_q)]
                if phrase_words:
                    clauses.append(" ".join(phrase_words))

        if len(meaningful) == 1 and not clauses:
            clauses.append(f'"{meaningful[0]}"*')
        elif len(meaningful) > 1:
            # Deduplicate meaningful terms while preserving order
            seen = set()
            deduped = []
            for m in meaningful[: self.MAX_QUERY_TOKENS]:
                if m not in seen:
                    seen.add(m)
                    deduped.append(m)
            for m in deduped:
                if m.endswith("*"):
                    clauses.append(f'"{m[:-1]}"*')
                else:
                    clauses.append(f'"{m}"*')
        elif not clauses and not meaningful and words:
            # Fallback if query consisted only of short words or stopwords
            for w in words[:5]:
                clauses.append(f'"{w}"')

        if not clauses:
            return ""

        if len(clauses) == 1:
            return clauses[0]

        if disjunctive:
            return " OR ".join(clauses)

        return " ".join(clauses)


    def search(
        self,
        query: str,
        limit: int = 10,
        source_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """Execute BM25 lexical search with optional source and document filtering.

        Args:
            query: Raw search query text.
            limit: Maximum number of results to return (default: 10).
            source_id: Optional filter scoping results to a specific source.
            document_id: Optional filter scoping results to a specific document.

        Returns:
            List[SearchResult]: Deterministically ranked results sorted by score DESC.
        """
        if limit <= 0:
            return []

        sanitized = self.sanitize_query(query, disjunctive=False)
        if not sanitized:
            return []

        clean_source_id = source_id.strip() if source_id and source_id.strip() else None
        clean_doc_id = document_id.strip() if document_id and document_id.strip() else None

        sql = """
        SELECT
            c.id,
            c.document_id,
            c.source_id,
            -bm25(chunks_fts) AS score,
            snippet(chunks_fts, 0, '[MATCH]', '[/MATCH]', '...', 32) AS snippet,
            c.content,
            c.pos_index
        FROM chunks_fts
        JOIN chunks c ON c.rowid = chunks_fts.rowid
        WHERE chunks_fts MATCH ?
          AND (? IS NULL OR c.source_id = ?)
          AND (? IS NULL OR c.document_id = ?)
        ORDER BY score DESC, c.document_id ASC, c.pos_index ASC
        LIMIT ?;
        """

        params = (
            sanitized,
            clean_source_id,
            clean_source_id,
            clean_doc_id,
            clean_doc_id,
            limit,
        )

        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()

        # Fallback to disjunctive OR ranking if multi-term conjunctive search returned 0 results
        if not rows and " " in sanitized:
            disjunctive_query = self.sanitize_query(query, disjunctive=True)
            if disjunctive_query and disjunctive_query != sanitized:
                fallback_params = (
                    disjunctive_query,
                    clean_source_id,
                    clean_source_id,
                    clean_doc_id,
                    clean_doc_id,
                    limit,
                )
                with self.engine.transaction() as conn:
                    cursor = conn.cursor()
                    cursor.execute(sql, fallback_params)
                    rows = cursor.fetchall()

        return [
            SearchResult(
                chunk_id=r[0],
                document_id=r[1],
                source_id=r[2],
                score=float(r[3]),
                snippet=r[4],
                content=r[5],
                index=int(r[6]),
            )
            for r in rows
        ]

    def rebuild(self) -> None:
        """Rebuild the FTS5 inverted index from the underlying chunks table."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild');")

    def count(self) -> int:
        """Return the count of indexed chunks in the FTS5 index."""
        with self.engine.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM chunks_fts;")
            return int(cursor.fetchone()[0])
