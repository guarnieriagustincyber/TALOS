"""Lexical indexing and BM25 search engine powered by SQLite FTS5."""

import re
from typing import Dict, List, Optional, Set
import unicodedata

from study_engine.contracts.search import SearchResult
from study_engine.storage.sqlite_engine import SQLiteStorageEngine

_BILINGUAL_MAP: Dict[str, str] = {
    "fallo": "fault", "fallos": "fault",
    "pagina": "page", "paginas": "page",
    "mayor": "major", "mayores": "major",
    "menor": "minor", "menores": "minor",
    "proceso": "process", "procesos": "process",
    "hilo": "thread", "hilos": "thread",
    "bloqueo": "deadlock", "bloqueos": "deadlock", "interbloqueo": "deadlock",
    "condicion": "condition", "condiciones": "condition",
    "carrera": "race", "carreras": "race",
    "memoria": "memory", "compartida": "shared", "planificacion": "schedul",
    "cambio": "switch", "contexto": "context", "seccion": "section", "critica": "critical",
    "exclusion": "exclusion", "mutua": "mutual", "espera": "wait",
    "inversion": "inversion", "prioridad": "priority", "desbordamiento": "overflow",
    "bufer": "buffer", "pila": "stack", "pilas": "stack",
    "puntero": "pointer", "punteros": "pointer", "direccion": "address", "direcciones": "address",
    "registro": "register", "registros": "register", "usuario": "user", "usuarios": "user",
    "nucleo": "kernel", "senal": "signal", "senales": "signal", "tuberia": "pipe", "tuberias": "pipe",
    "archivo": "file", "archivos": "file", "segmento": "segment", "segmentos": "segment",
    "tabla": "table", "tablas": "table", "marco": "frame", "marcos": "frame",
    "reemplazo": "replacement", "asignacion": "allocation", "dinamica": "dynamic", "estatica": "static",
    "ataque": "attack", "ataques": "attack", "vulnerabilidad": "vulnerability", "vulnerabilidades": "vulnerability",
    "mitigacion": "mitigation", "mitigaciones": "mitigation",
    "algoritmo": "algorithm", "algoritmos": "algorithm",
    "reloj": "clock",
    "cerrojo": "lock", "cerrojos": "lock",
    "semaforo": "semaphore", "semaforos": "semaphore",
    "interrupcion": "interrupt", "interrupciones": "interrupt",
    "cola": "queue", "colas": "queue",
    "bloque": "block", "bloques": "block",
    "hebra": "thread", "hebras": "thread",
    "llamada": "call", "llamadas": "call",
    "biblioteca": "library", "bibliotecas": "library",
    "enlazador": "linker", "cargador": "loader",
    "tamano": "size", "longitud": "length",
    "espacio": "space", "espacios": "space",
    "virtual": "virtual", "virtuales": "virtual",
    "red": "network", "redes": "network",
    "servidor": "server", "servidores": "server",
    "cliente": "client", "clientes": "client",
    "descriptor": "descriptor", "descriptores": "descriptor",
    "estado": "state", "estados": "state",
    "concurrente": "concurrent", "concurrencia": "concurrency",
    "sincronizacion": "synchronization",
    "bloqueante": "blocking",
    "inodo": "inode", "inodos": "inode",
    "enlace": "link", "enlaces": "link",
}


def _fts_phrase_for_symbol(symbol: str) -> str:
    """Escapa y construye una frase FTS5 exacta para identificadores técnicos con guiones bajos (Enmienda E-HF4)."""
    clean = symbol.strip("()[]{};,").replace('"', '""')
    parts = [p for p in clean.replace("_", " ").split() if p]
    if not parts:
        return ""
    phrase = " ".join(parts)
    return f'"{phrase}"'

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
    "explicame", "explícame", "explicar", "explicacion", "explicación", "explicá",
    "decime", "décime", "decir", "hola", "saludos", "buenos", "dias", "días",
    "tardes", "noches", "favor", "podrias", "podrías", "podes", "podés",
    "quiero", "saber", "entender", "ayuda", "consulta", "duda", "pregunta",
    "funciona", "funcionan", "funcione", "funcionen", "funcionamiento",
    "seccion", "sección", "secciones", "describe", "describir", "descripción",
    "ocurre", "sucede", "pasa", "exactamente", "paso", "versus", "vs", "cuenta",
    "relaciona", "relacionan", "relación", "genera", "generar",
    "opina", "opinas", "opinás", "opinan", "opinar", "opinion", "opinión",
    # Interrogatives & prompt framing
    "como", "cómo", "cual", "cuál", "cuales", "cuáles", "cuando", "cuándo",
    "donde", "dónde", "cuanto", "cuánto", "detalla", "detallá", "detallar",
    "contrasta", "contrastá", "contrastar", "define", "definir", "definición",
    "formalmente", "contexto", "respecto", "implicancia", "implicancias",
    "concepto", "conceptos", "mecanismo", "mecanismos", "fundamento", "fundamentos",
    "perspectiva", "estándar", "términos", "parámetro", "parámetros",
    "ejemplo", "ejemplos", "bibliografía", "canónica", "canónico",
    "problema", "resuelve", "resolver", "utiliza", "sirve", "usar", "diferencia", "diferencias",
    # Additional conversational, question wrapping & structural words
    "principales", "principal", "recursos", "recurso", "comparten", "comparte", "compartir",
    "tiempo", "tiempos", "vida", "velocidad", "existen", "existe", "existencia",
    "diseño", "sistemas", "sistema", "computación", "analíticamente", "disyuntivas", "elegir",
    "concretos", "concreto", "reales", "real", "programa", "programas", "código", "máquina",
    "nivel", "valores", "posibles", "retorno", "devuelve", "recibe", "firma",
    "casos", "caso", "situación", "situaciones", "modo", "modos", "término",
    "operaciones", "operación", "síncrono", "asíncrono", "frente", "entre",
    "cuantos", "cuántos", "cuanta", "cuánta", "cuantas", "cuántas",
    "quien", "quién", "quienes", "quiénes",
    "hacer", "hace", "hacen", "hizo", "hacía", "haciendo", "hecho",
    "maneja", "manejan", "manejar", "afecta", "afectan", "permite", "permiten", "utilizan", "sirven",
    "consiste", "trata", "muestra", "muestran", "mostrame", "dame", "escribí", "escribime",
    "mecánica", "mecanica", "física", "fisica", "papel", "juega", "juegan", "rol",
    "consecuencia", "consecuencias",
    "dos", "tres", "cuatro", "cinco", "primer", "primera", "segundo", "segunda", "tercer", "tercero", "tercera",
    "ano", "anos", "año", "años", "buenos", "aires", "ciudad", "calcula", "calcular", "calculo",
    "directamente", "completo", "completa", "listo", "exacto", "exacta",
    "trade", "offs", "tradeoff", "tradeoffs",
    # Question wrappers, verbs and framing terms
    "detalle", "detalles", "sintaxis", "comportamiento", "comportamientos",
    "opera", "operan", "operar", "operando", "exactos", "exactas",
    "programacion", "programación", "operativo", "operativos",
    "tipo", "tipos", "informacion", "información",
    "almacena", "almacenan", "almacenar",
    "produce", "producen", "producir", "producirse",
    "etapas", "etapa", "ejecuta", "ejecutan", "ejecutar",
    "nuevo", "nueva", "nuevos", "nuevas",
    "reemplazar", "reemplaza", "reemplazan",
    "construir", "construye", "construyen",
    "punto", "vista", "compará", "compara", "comparar",
    "arquitectonica", "arquitectónicas", "arquitectónico", "arquitectónicos",
    "él", "ella", "ellos", "ellas", "imagen", "imágenes",
    "paso", "pasos", "posix", "linux", "realiza", "realizan", "realizar",
    "estandar", "manera", "forma",
    "básica", "basica", "básicas", "basicas", "básico", "basico", "básicos", "basicos",
    "general", "generales"
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
                # Wrap each word inside quoted phrase escaping internal double quotes
                phrase_words = [f'"{t.replace(chr(34), chr(34) + chr(34))}"' for t in re.findall(r"\w+", clean_q)]
                if phrase_words:
                    clauses.append(" ".join(phrase_words))

        seen = set()
        deduped = []
        for m in meaningful[: self.MAX_QUERY_TOKENS]:
            if m not in seen:
                seen.add(m)
                deduped.append(m)

        for m in deduped:
            base = m[:-1] if m.endswith("*") else m
            if "_" in base:
                # Enmienda E-HF4: frase FTS5 exacta para identificadores técnicos con guiones bajos
                phrase = _fts_phrase_for_symbol(base)
                if phrase:
                    clauses.append(phrase)
                # Estrictamente NO expandir como bilingüe identificadores de código (E-HF4)
            elif len(base) >= 5:
                clean_base = base.replace('"', '""')
                clauses.append(f'"{clean_base}"*')
                if disjunctive:
                    unacc = "".join(c for c in unicodedata.normalize("NFD", base) if unicodedata.category(c) != "Mn")
                    en_term = _BILINGUAL_MAP.get(unacc)
                    if en_term and en_term != base and en_term not in seen:
                        seen.add(en_term)
                        clauses.append(f'"{en_term}"*' if len(en_term) >= 5 else f'"{en_term}"')
            else:
                clean_base = base.replace('"', '""')
                clauses.append(f'"{clean_base}"')
                if disjunctive:
                    unacc = "".join(c for c in unicodedata.normalize("NFD", base) if unicodedata.category(c) != "Mn")
                    en_term = _BILINGUAL_MAP.get(unacc)
                    if en_term and en_term != base and en_term not in seen:
                        seen.add(en_term)
                        clauses.append(f'"{en_term}"*' if len(en_term) >= 5 else f'"{en_term}"')

        if not clauses and not meaningful and words:
            # Fallback if query consisted only of short words or stopwords
            for w in words[:5]:
                clean_w = w.replace('"', '""')
                clauses.append(f'"{clean_w}"')

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
