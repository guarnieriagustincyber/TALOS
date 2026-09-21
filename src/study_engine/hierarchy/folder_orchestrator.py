"""FolderOrchestrator for managing folder-level coordination without technical authority (Fase 5.7)."""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, cast
from study_engine.contracts.notebook import Notebook


ORGANIZATIONAL_KEYWORDS = {
    "progreso",
    "avance",
    "planificación",
    "planificacion",
    "semana",
    "materias",
    "cuadernos",
    "carpeta",
    "estado",
    "resumen",
    "temas",
    "roadmap",
    "actividad",
    "ultima actividad",
    "última actividad",
    "donde me quede",
    "dónde me quedé",
    "donde quede",
    "dónde quedé",
    "que estaba haciendo",
    "qué estaba haciendo",
    "hola",
    "buenas",
    "buen dia",
    "buen día",
    "buenos dias",
    "buenos días",
    "saludos",
    "inicio",
    "empezar",
    "que tengo",
    "qué tengo",
    "que informacion tenes",
    "qué información tenés",
    "informacion",
    "información",
    "fuentes",
    "bibliografia",
    "bibliografía",
    "pendientes",
    "pendiente",
    "materias tengo",
    "cuadernos tengo",
}

CANONICAL_NOTEBOOKS: Dict[str, Dict[str, Any]] = {
    "fadena-lenguajes": {
        "id": "fadena-lenguajes",
        "name": "Lenguajes de Programación - FADENA 2026",
        "short_name": "Lenguajes de Programación",
        "folder_path": "FADENA / 1er Año / 2do Cuatrimestre",
        "subject": "Lenguajes de Programación",
        "keywords": [
            "lenguajes de programacion", "lenguaje de programacion", "lenguaje de programación",
            "lenguajes de programación", "lenguajes", "programacion c", "programación c",
            "lenguaje c", "c basico", "c básico", "programacion basica", "programación básica"
        ],
        "kc_mapping": {
            "leng_intro_algoritmos": "Introducción a la programación, algoritmos y diagramas de flujo",
            "leng_pseudocodigo_estructurado": "Pseudocódigo: estructuras secuenciales, condicionales y repetitivas",
            "leng_iniciacion_c": "Iniciación en C: del pseudocódigo a código ejecutable",
            "leng_arreglos_lineales": "Algoritmos básicos y arreglos unidimensionales",
            "leng_funciones_modularizacion": "Funciones, parámetros y modularización en C",
        },
        "pending_topics": [
            "Comparativa entre lenguajes estructurados y compilados",
            "Introducción al paradigma orientado a objetos",
            "Encapsulamiento, herencia y polimorfismo",
            "Programación web básica, HTML y procesamiento en PHP",
            "Formularios HTML, procesamiento de peticiones y backend",
        ],
        "default_sources": [
            "Lenguajes de Programación - Clase 1: Pseudocódigo (Cátedra Balestrini / Di Stefano)",
            "Lenguajes de Programación - Clase 2: Codificación en C (Cátedra Balestrini / Di Stefano)",
            "Programación en C para principiantes (Gorka Urrutia Landa)",
            "Introducción a la programación con C (Marzal Varó & Gracia)",
            "The GNU C Reference Manual (Richard Stallman)",
            "Algoritmos y Arreglos Lineales (Cátedra FADENA)",
        ],
    },
    "fadena-so2": {
        "id": "fadena-so2",
        "name": "Sistemas Operativos II - FADENA 2026",
        "short_name": "Sistemas Operativos II",
        "folder_path": "FADENA / 1er Año / 2do Cuatrimestre",
        "subject": "Sistemas Operativos",
        "keywords": [
            "sistemas operativos ii", "sistemas operativos 2", "sistemas operativos",
            "sistema operativo", "so2", "so ii", "so 2", "sistemas operativos y procesos"
        ],
        "kc_mapping": {
            "so2_gestion_procesos_pcb": "Gestión de procesos e hilos: PCB, estados y cambio de contexto",
            "so2_ipc_concurrencia": "Concurrencia, comunicación entre procesos, sincronización y exclusión mutua",
            "so2_planificacion_cpu": "Planificación de CPU: algoritmos y niveles de planificación",
        },
        "pending_topics": [
            "Concurrencia y sincronización: exclusión mutua, semáforos y monitores",
            "Planificación de CPU: algoritmos Round Robin, prioridades y colas multinivel",
            "Interbloqueos: condiciones, prevención y recuperación",
            "Modelos cliente-servidor y sistemas distribuidos",
            "Seguridad operativa: triada CIA, control de acceso y firewalls",
        ],
        "default_sources": [
            "Sistemas Operativos II - Clase 1: Gestión de Procesos (Cátedra Drapañoti)",
            "Sistemas Operativos II - Clase 2: Colas de Planificación (Cátedra Drapañoti)",
            "Operating Systems: Internals and Design Principles 7th Ed (William Stallings)",
            "Sistemas Operativos - Procesos y Ciclo de Vida (Cátedra FADENA)",
            "Sistemas Operativos - Concurrencia e Hilos (Cátedra FADENA)",
            "Sistemas Operativos - Planificación de CPU (Cátedra FADENA)",
        ],
    },
    "fadena-std": {
        "id": "fadena-std",
        "name": "Sistema de Tratamiento de Datos - FADENA 2026",
        "short_name": "Sistema de Tratamiento de Datos",
        "folder_path": "FADENA / 1er Año / 2do Cuatrimestre",
        "subject": "Tratamiento de Datos y Bases de Datos",
        "keywords": [
            "sistema de tratamiento de datos", "tratamiento de datos", "std",
            "bases de datos", "base de datos", "bd"
        ],
        "kc_mapping": {
            "std_intro_datos_sgbd": "Dato, información y arquitectura de SGBD",
            "std_modelo_relacional_er": "Modelos de datos relacionales, álgebra relacional y diseño ER",
            "std_sql_consultas": "SQL: DDL, DML, DQL, JOINs y subconsultas",
        },
        "pending_topics": [
            "Administración de BD, seguridad, concurrencia y transacciones",
            "Formatos semiestructurados (JSON, CSV, XML) y REGEX",
            "Bases de datos NoSQL y teorema CAP",
            "Pipelines de datos, ETL y Big Data",
        ],
        "default_sources": [
            "Sistemas de Tratamiento de Datos - Unidad 1 (Cátedra Pereira/Chamudis/Maidana)",
            "Database Systems 11th Ed (Coronel & Morris)",
            "Fundamentos de Bases de Datos (Silberschatz, Korth & Sudarshan)",
            "Introducción a los Sistemas de BD 7ma Ed (C. J. Date)",
            "Material de Cátedra: Estructuras de Datos y Archivos (FADENA)",
            "Tratamiento de Datos y Formatos (Ramalho)",
        ],
    },
    "fadena-teleco": {
        "id": "fadena-teleco",
        "name": "Infraestructura de Telecomunicaciones - FADENA 2025",
        "short_name": "Infraestructura de Telecomunicaciones",
        "folder_path": "FADENA / 1er Año / 2do Cuatrimestre",
        "subject": "Telecomunicaciones y Redes",
        "keywords": [
            "infraestructura de telecomunicaciones", "telecomunicaciones", "teleco",
            "redes de computadoras", "redes", "red", "networking", "telecom"
        ],
        "kc_mapping": {
            "teleco_transmision_datos": "Transmisión de datos: modos, señales analógicas vs digitales",
            "teleco_parametros_senales": "Parámetros de señales, velocidad de transmisión y espectro",
            "teleco_calculo_enlaces_db": "Cálculo de enlaces: atenuación, potencia, dB y dBm",
        },
        "pending_topics": [
            "Ancho de banda, serie y espectro de Fourier",
            "Transmisión en banda base y codificación de línea",
            "Teoría de la información y teorema de Shannon-Nyquist",
            "Control de errores: BER, Checksum, CRC y ARQ",
            "Modulación analógica y digital (AM, FM, ASK, FSK, PSK, QAM)",
            "Arquitectura de redes: modelos OSI y TCP/IP",
            "Direccionamiento IPv4, subredes, CIDR y VLSM",
        ],
        "default_sources": [
            "Infraestructura de Telecomunicaciones - Unidad 1 (Cátedra Fusario)",
            "Comunicaciones y Redes 7ma Ed (William Stallings)",
            "Comunicaciones y Redes (Castro Lechtaler & Fusario)",
            "Internetworking with TCP/IP Vol 1 (Comer)",
            "Computer Networking: A Top-Down Approach (Kurose & Ross)",
            "Guía de Cátedra Telecomunicaciones 2025 (FADENA)",
        ],
    },
    "fase0-soc": {
        "id": "fase0-soc",
        "name": "Roadmap KASIU TECH v4 - Fase 0",
        "short_name": "Fase 0 - Fundamentos de Ciberdefensa",
        "folder_path": "Roadmap / Fase 0",
        "subject": "Fundamentos de Ciberdefensa y Pensamiento Algorítmico",
        "keywords": [
            "fase 0", "fase0", "roadmap", "kasiu tech", "fundamentos", "soc"
        ],
        "kc_mapping": {
            "aritmetica_punteros": "Aritmética de Punteros y Desplazamiento en Memoria",
            "arrays_direccionamiento_contiguo": "Arreglos y Direccionamiento Contiguo",
            "modularidad_stack_frame": "Modularidad, Funciones y Stack Frame",
        },
        "pending_topics": [
            "Análisis Asintótico y Notación Big-O",
            "Búsqueda Binaria sobre Arreglos Ordenados",
            "Algoritmos de Ordenamiento: Burbuja y Optimización",
        ],
        "default_sources": [
            "Fundamentos de Programación (Luis Joyanes Aguilar)",
            "Think Like a Programmer (V. Anton Spraul)",
            "Código Limpio (Robert C. Martin)",
            "Matemáticas Discretas (Kenneth H. Rosen)",
            "Algoritmos y Estructuras de Datos en Python (Digital)",
            "Data Structures and Algorithms in Python (Goodrich et al.)",
            "Automate the Boring Stuff with Python (Al Sweigart)",
            "Programación - Punteros (Cátedra FADENA)",
        ],
    },
}

TECHNICAL_EXPLANATION_INDICATORS = [
    "cómo funciona", "como funciona",
    "cómo se implementa", "como se implementa",
    "explicame", "explícame", "explicar", "explica",
    "por qué se produce", "por que se produce", "porque se produce",
    "escribí un código", "escribi un codigo", "escribir código", "escribir codigo",
    "implementar", "implementá",
    "segmentation fault", "malloc", "calloc", "free",
    "árboles binarios", "arboles binarios", "balanceo avl",
    "deadlock", "algoritmo del banquero", "round robin",
    "diferencia entre", "código para", "codigo para",
    "cómo calcular", "como calcular", "calcular enlace",
]


class FolderOrchestrator:
    """Read-only orchestrator for conversations and aggregated metrics at the folder level.

    INVARIANTS & CONSTRAINTS:
    - Strictly read-only: does not mutate notebooks, state, or the evidence ledger.
    - Zero technical authority: does not teach or explain technical syllabus content.
    - Zero citation authority: does not emit [E#] citations.
    - Cross-notebook isolation: does not mix document chunks or sources across notebooks.
    - Deterministic query routing: uses keyword rules and cognitive state inspection.
    """

    def __init__(
        self,
        folder_id: str,
        knowledge_store: Any,
        ledger: Optional[Any] = None,
        student_storage: Optional[Any] = None,
    ) -> None:
        self.folder_id = folder_id.strip()
        self.knowledge_store = knowledge_store
        self.ledger = ledger
        self.student_storage = student_storage

        # Guarantee read-only contract flags
        self.mutation_allowed: bool = False
        self.execution_allowed: bool = False
        self.epistemic_authority: bool = False

    def list_notebooks(self) -> List[Notebook]:
        """Return all notebooks belonging to this folder, or all active notebooks if root."""
        if hasattr(self.knowledge_store, "list_notebooks"):
            try:
                all_nbs = cast(List[Notebook], self.knowledge_store.list_notebooks())
            except Exception:
                all_nbs = []
        else:
            all_nbs = []

        if self.folder_id in ("folder_root", "root_global"):
            if all_nbs:
                return all_nbs
            return [nb for nb in all_nbs if getattr(nb, "folder_id", "folder_root") == self.folder_id]

        if hasattr(self.knowledge_store, "list_notebooks_in_folder"):
            return cast(List[Notebook], self.knowledge_store.list_notebooks_in_folder(self.folder_id))

        return [nb for nb in all_nbs if getattr(nb, "folder_id", "folder_root") == self.folder_id]

    def get_aggregated_progress(self, student_id: str) -> Dict[str, Any]:
        """Compute read-only aggregated progress metrics across all notebooks in the folder."""
        notebooks = self.list_notebooks()
        nb_ids = [nb.id for nb in notebooks]

        total_notebooks = len(notebooks)
        total_entries = 0
        nodes_mastered: List[str] = []

        if self.ledger is not None:
            # Query ledger for records belonging to this student and folder
            if hasattr(self.ledger, "get_all_records"):
                all_records = list(self.ledger.get_all_records())
            else:
                all_records = [
                    getattr(e, "record", None)
                    for e in getattr(self.ledger, "_entries", [])
                    if getattr(e, "record", None) is not None
                ]

            student_records = [
                r for r in all_records
                if r is not None
                and r.student_id == student_id
                and (
                    (getattr(r, "metadata", {}) or {}).get("folder_id") == self.folder_id
                    or (self.folder_id in ("folder_root", "root_global") and not (getattr(r, "metadata", {}) or {}).get("folder_id"))
                )
            ]
            total_entries = len(student_records)
            nodes_mastered = sorted(list(set(r.node_id for r in student_records)))

        return {
            "folder_id": self.folder_id,
            "student_id": student_id,
            "total_notebooks": total_notebooks,
            "notebook_ids": nb_ids,
            "total_evidence_entries": total_entries,
            "nodes_recorded": nodes_mastered,
            "read_only": True,
        }

    def suggest_study_plan(self, student_id: str) -> Dict[str, Any]:
        """Suggest an ordered study roadmap across notebooks in this folder (read-only)."""
        notebooks = self.list_notebooks()
        if not notebooks:
            return {
                "folder_id": self.folder_id,
                "suggested_notebook_id": None,
                "message": "No hay cuadernos cargados en esta carpeta.",
            }

        first_nb = notebooks[0]
        return {
            "folder_id": self.folder_id,
            "suggested_notebook_id": first_nb.id,
            "suggested_notebook_name": first_nb.name,
            "plan_sequence": [nb.id for nb in notebooks],
            "message": f"Te sugerimos comenzar o continuar con el cuaderno '{first_nb.name}'.",
        }

    def _get_bkt_states(self) -> Dict[str, Dict[str, Any]]:
        """Fetch real BKT cognitive states if available."""
        if self.student_storage is not None and hasattr(self.student_storage, "get_all_bkt_states"):
            try:
                states = self.student_storage.get_all_bkt_states()
                return {
                    kc_id: {
                        "kc_id": s.kc_id,
                        "p_L": s.p_L,
                        "attempts": s.attempts,
                        "last_update": s.last_update,
                    }
                    for kc_id, s in states.items()
                }
            except Exception:
                pass

        db_candidates = [
            Path("data/web_state/student_state.db"),
            Path("data/student/student_state.db"),
        ]
        for cand in db_candidates:
            if cand.exists():
                try:
                    conn = sqlite3.connect(str(cand))
                    cur = conn.cursor()
                    cur.execute("SELECT kc_id, p_L, attempts, last_update FROM bkt_states")
                    rows = cur.fetchall()
                    conn.close()
                    return {
                        r[0]: {
                            "kc_id": r[0],
                            "p_L": r[1],
                            "attempts": r[2],
                            "last_update": r[3],
                        }
                        for r in rows
                    }
                except Exception:
                    pass
        return {}

    def _get_sources_for_notebook(self, notebook_id: str) -> List[str]:
        """Fetch real sources associated with notebook from knowledge_store."""
        if hasattr(self.knowledge_store, "list_notebook_sources"):
            try:
                sources = self.knowledge_store.list_notebook_sources(notebook_id)
                titles = []
                for s in sources:
                    title = None
                    if isinstance(getattr(s, "metadata", None), dict):
                        title = s.metadata.get("title")
                    elif hasattr(getattr(s, "metadata", None), "title"):
                        title = getattr(s.metadata, "title", None)
                    if not title and hasattr(s, "manifest") and hasattr(s.manifest, "filename"):
                        title = s.manifest.filename
                    if title:
                        titles.append(title)
                if titles:
                    return titles
            except Exception:
                pass

        spec = CANONICAL_NOTEBOOKS.get(notebook_id)
        if spec:
            return list(spec.get("default_sources", []))
        return []

    def _detect_target_notebook(self, query_lower: str) -> Optional[Dict[str, Any]]:
        """Identify if a specific canonical notebook is referenced in the query."""
        for nb_id, spec in CANONICAL_NOTEBOOKS.items():
            for kw in spec["keywords"]:
                if kw in query_lower:
                    return spec
        return None

    def _is_technical_explanation_query(self, query_lower: str) -> bool:
        """Determine if query is requesting code, technical implementation or conceptual teaching."""
        return any(ind in query_lower for ind in TECHNICAL_EXPLANATION_INDICATORS)

    def _get_all_notebook_source_counts(self) -> Dict[str, int]:
        """Batch fetch source counts for all notebooks using a single transaction."""
        counts: Dict[str, int] = {}
        if hasattr(self.knowledge_store, "engine"):
            try:
                with self.knowledge_store.engine.transaction() as conn:
                    cur = conn.cursor()
                    cur.execute(
                        "SELECT notebook_id, count(source_id) FROM notebook_sources GROUP BY notebook_id;"
                    )
                    counts = dict(cur.fetchall())
            except Exception:
                pass
        return counts

    def _format_greeting(self, bkt_states: Dict[str, Any]) -> str:
        # Build dynamic source counts per notebook in batch
        counts = self._get_all_notebook_source_counts()
        nb_lines = []
        for nb_id, spec in CANONICAL_NOTEBOOKS.items():
            count = counts.get(nb_id)
            if count is None or count == 0:
                count = len(spec.get("default_sources", []))
            nb_lines.append(f"- **{spec['short_name']}** (`{nb_id}`): {count} fuentes.")

        # Build dynamic BKT summary
        bkt_lines = []
        for nb_id, spec in CANONICAL_NOTEBOOKS.items():
            for kc_id, kc_desc in spec.get("kc_mapping", {}).items():
                bkt = bkt_states.get(kc_id, {})
                p_L = bkt.get("p_L")
                if p_L is not None:
                    pct = int(round(p_L * 100))
                    if pct >= 85:
                        bkt_lines.append(f"- **{kc_desc}**: **{pct}%** (Dominado ✅)")
                    elif pct >= 60:
                        bkt_lines.append(f"- **{kc_desc}**: **{pct}%** (En consolidación 📈)")
                    else:
                        bkt_lines.append(f"- **{kc_desc}**: **{pct}%** (Laguna detectada ⚠️)")

        bkt_summary = "\n".join(bkt_lines) if bkt_lines else "- Sin evaluaciones registradas. Todos los temas comienzan desde cero."

        nb_summary = "\n".join(nb_lines)
        total_nbs = len(CANONICAL_NOTEBOOKS)

        return (
            f"¡Hola Agustín! Entorno de estudio configurado con **{total_nbs} cuadernos canónicos**:\n\n"
            f"{nb_summary}\n\n"
            f"📊 **Estado cognitivo actual (BKT)**:\n"
            f"{bkt_summary}\n\n"
            "Podés seleccionar un cuaderno o formular una consulta conceptual específica para comenzar."
        )

    def _format_activity(self, bkt_states: Dict[str, Any]) -> str:
        # Dynamic: show notebooks with BKT data, or inform no activity yet
        active_kcs = []
        for nb_id, spec in CANONICAL_NOTEBOOKS.items():
            for kc_id, kc_desc in spec.get("kc_mapping", {}).items():
                bkt = bkt_states.get(kc_id, {})
                p_L = bkt.get("p_L")
                if p_L is not None:
                    pct = int(round(p_L * 100))
                    active_kcs.append((spec["short_name"], kc_desc, pct))

        if not active_kcs:
            return (
                "📍 **Actividad registrada**:\n\n"
                "No hay sesiones de estudio ni actividad con evaluaciones registradas todavía. "
                "Abrí un cuaderno en el panel lateral para comenzar tu primera sesión."
            )

        lines = "\n".join(
            f"- **{nb}** → {kc}: **{pct}%**" for nb, kc, pct in active_kcs
        )
        return (
            "📍 **Temas con actividad y evaluación registrada**:\n\n"
            f"{lines}\n\n"
            "Podés abrir cualquier cuaderno en el panel lateral para continuar estudiando."
        )

    def _format_all_notebooks_overview(self, bkt_states: Dict[str, Any]) -> str:
        icons = ["💻", "⚙️", "🗄️", "📡", "🛡️"]
        nb_blocks = []
        for i, (nb_id, spec) in enumerate(CANONICAL_NOTEBOOKS.items()):
            icon = icons[i % len(icons)]
            sources = self._get_sources_for_notebook(nb_id)
            source_names = ", ".join(f"*{s}*" for s in spec.get("default_sources", [])[:4])

            # BKT status for this notebook
            kc_mapping = spec.get("kc_mapping", {})
            kc_lines = []
            for kc_id, kc_desc in kc_mapping.items():
                bkt = bkt_states.get(kc_id, {})
                p_L = bkt.get("p_L")
                if p_L is not None:
                    pct = int(round(p_L * 100))
                    if pct >= 85:
                        kc_lines.append(f"{kc_desc}: **{pct}%** ✅")
                    elif pct >= 60:
                        kc_lines.append(f"{kc_desc}: **{pct}%** 📈")
                    else:
                        kc_lines.append(f"{kc_desc}: **{pct}%** ⚠️")

            if kc_lines:
                cognitive = "; ".join(kc_lines)
            else:
                cognitive = "Sin evaluaciones registradas ⏳"

            pending = spec.get("pending_topics", [])
            pending_count = len(pending)

            block = (
                f"{i+1}. {icon} **{spec['name']}** (`{nb_id}`)\n"
                f"   - **Ubicación**: `{spec['folder_path']}`\n"
                f"   - **Fuentes ({len(sources)})**: {source_names}.\n"
                f"   - **Estado Cognitivo**: {cognitive}. {pending_count} temas pendientes."
            )
            nb_blocks.append(block)

        total_nbs = len(CANONICAL_NOTEBOOKS)
        nb_text = "\n\n".join(nb_blocks)

        return (
            "📚 **Estructura Curricular y Cuadernos Disponibles**:\n\n"
            f"Tenés **{total_nbs} cuadernos canónicos** organizados en tu árbol de navegación:\n\n"
            f"{nb_text}\n\n"
            "¿Querés consultar el avance detallado de alguno de estos cuadernos o comenzar a estudiar?"
        )

    def _format_notebook_briefing(self, spec: Dict[str, Any], bkt_states: Dict[str, Any]) -> str:
        nb_id = spec["id"]
        sources = self._get_sources_for_notebook(nb_id)
        kc_mapping = spec.get("kc_mapping", {})
        pending = spec.get("pending_topics", [])

        mastery_lines = []
        for kc_id, kc_desc in kc_mapping.items():
            bkt = bkt_states.get(kc_id, {})
            p_L = bkt.get("p_L")
            attempts = bkt.get("attempts", 0)
            if p_L is not None:
                pct = int(round(p_L * 100))
                if pct >= 85:
                    status = f"**{pct}%** (Dominado ✅ · {attempts} intentos)"
                elif pct >= 60:
                    status = f"**{pct}%** (En consolidación 📈 · {attempts} intentos)"
                else:
                    status = f"**{pct}%** (Laguna detectada · Remediación activa ⚠️ · {attempts} intentos)"
                mastery_lines.append(f"- {kc_desc} (`{kc_id}`): {status}")

        if not mastery_lines:
            mastery_summary = "- Aún no tenés evaluaciones registradas en este cuaderno (Temas listos para iniciar ⏳)."
        else:
            mastery_summary = "\n".join(mastery_lines)

        pending_summary = "\n".join(f"- ⏳ {t}" for t in pending)
        sources_summary = "\n".join(f"- 📖 {s}" for s in sources[:6])

        return (
            f"📘 **Cuaderno: {spec['name']}** (`{nb_id}`)\n"
            f"- **Ubicación**: `{spec['folder_path']}`\n"
            f"- **Materia / Área**: {spec['subject']}\n\n"
            f"📚 **Fuentes Curriculares Vinculadas ({len(sources)})**:\n"
            f"{sources_summary}\n\n"
            f"📊 **Estado Cognitivo (BKT)**:\n"
            f"{mastery_summary}\n\n"
            f"🎯 **Temas del Programa Pendientes**:\n"
            f"{pending_summary}\n\n"
            f"¿Querés trabajar en alguno de estos temas? Podés abrir el cuaderno **{spec['short_name']}** "
            f"en el panel lateral para iniciar el diálogo socrático o resolver ejercicios evaluativos."
        )

    def _format_notebook_progress(self, spec: Dict[str, Any], bkt_states: Dict[str, Any]) -> str:
        kc_mapping = spec.get("kc_mapping", {})
        pending = spec.get("pending_topics", [])

        mastery_lines = []
        has_remediation = False
        remediation_kc = None
        for kc_id, kc_desc in kc_mapping.items():
            bkt = bkt_states.get(kc_id, {})
            p_L = bkt.get("p_L")
            attempts = bkt.get("attempts", 0)
            if p_L is not None:
                pct = int(round(p_L * 100))
                if pct >= 85:
                    status = f"**{pct}%** de maestría (Dominado ✅ · {attempts} intentos)"
                elif pct >= 60:
                    status = f"**{pct}%** de maestría (En consolidación 📈 · {attempts} intentos)"
                else:
                    status = f"**{pct}%** de maestría (Laguna detectada · Remediación activa ⚠️ · {attempts} intentos)"
                    has_remediation = True
                    remediation_kc = kc_desc
                mastery_lines.append(f"- {kc_desc} (`{kc_id}`): {status}")

        if not mastery_lines:
            mastery_summary = "- No hay evaluaciones registradas en este cuaderno. Todos los temas están disponibles para iniciar."
        else:
            mastery_summary = "\n".join(mastery_lines)

        pending_summary = "\n".join(f"- ⏳ {t}" for t in pending)

        rec = (
            f"Te recomiendo abrir el cuaderno **{spec['short_name']}** en la barra lateral para resolver la remediación de {remediation_kc} antes de avanzar."
            if has_remediation
            else f"Podés ingresar al cuaderno **{spec['short_name']}** en la barra lateral para avanzar con los temas pendientes."
        )

        return (
            f"📊 **Balance de Avance y Temas Pendientes: {spec['name']}**\n"
            f"- **Ubicación en árbol**: `{spec['folder_path']}`\n\n"
            f"📈 **Nodos Evaluados (BKT)**:\n"
            f"{mastery_summary}\n\n"
            f"⏳ **Temas Pendientes en el Programa**:\n"
            f"{pending_summary}\n\n"
            f"🎯 **Recomendación Pedagógica**:\n{rec}"
        )

    def _format_general_progress(self, bkt_states: Dict[str, Any]) -> str:
        if self.folder_id not in ("folder_root", "root_global"):
            notebooks = self.list_notebooks()
            nb_names = ", ".join(f"'{nb.name}'" for nb in notebooks) or "ninguno registrado"
            return (
                f"Esta es una consulta organizativa sobre el estado o avance de la carpeta '{self.folder_id}'. "
                f"Contiene {len(notebooks)} cuaderno(s): {nb_names}."
            )

        # Dynamic: build progress from all notebooks' kc_mappings
        progress_lines = []
        lowest_kc = None
        lowest_pct = 101
        for nb_id, spec in CANONICAL_NOTEBOOKS.items():
            kc_mapping = spec.get("kc_mapping", {})
            has_bkt = False
            for kc_id, kc_desc in kc_mapping.items():
                bkt = bkt_states.get(kc_id, {})
                p_L = bkt.get("p_L")
                if p_L is not None:
                    pct = int(round(p_L * 100))
                    has_bkt = True
                    if pct >= 85:
                        progress_lines.append(f"• **{kc_desc}**: **{pct}%** (Dominado ✅ · {spec['short_name']})")
                    elif pct >= 60:
                        progress_lines.append(f"• **{kc_desc}**: **{pct}%** (En consolidación 📈 · {spec['short_name']})")
                    else:
                        progress_lines.append(f"• **{kc_desc}**: **{pct}%** (Laguna detectada ⚠️ · {spec['short_name']})")
                    if pct < lowest_pct:
                        lowest_pct = pct
                        lowest_kc = (kc_desc, spec['short_name'])
            if not has_bkt:
                progress_lines.append(f"• **{spec['short_name']}**: Pendiente de ejercitación ⏳")

        progress_text = "\n".join(progress_lines)
        total_nbs = len(CANONICAL_NOTEBOOKS)

        if lowest_kc and lowest_pct < 60:
            hint = f"🎯 **Próximo hito sugerido**: Resolver la laguna en **{lowest_kc[1]}** sobre {lowest_kc[0]} antes de avanzar."
        else:
            hint = "🎯 **Próximo hito sugerido**: Abrí un cuaderno en el panel lateral para comenzar tu primera sesión de estudio."

        return (
            "📊 **Balance Global de Avance Curricular y Roadmap**:\n\n"
            f"Tu plan de estudio integra **{total_nbs} cuadernos canónicos**:\n\n"
            f"{progress_text}\n\n"
            f"{hint}"
        )

    def route_query(self, query: str) -> Dict[str, Any]:
        """Determine whether query is folder-organizational or technical (Deterministic).

        Uses deterministic keyword rules and curricular inspection:
        - If query matches technical explanation requests -> delegates to notebook scope.
        - If query is organizational, greeting, progress, or notebook inquiry -> handled at folder level.
        """
        query_lower = query.lower().strip()
        bkt_states = self._get_bkt_states()

        # 1. Technical explanation query check (zero epistemic authority at folder level)
        if self._is_technical_explanation_query(query_lower):
            target_spec = self._detect_target_notebook(query_lower)
            nb_suggestion = target_spec["id"] if target_spec else None
            nb_name = target_spec["name"] if target_spec else "el cuaderno correspondiente"
            return {
                "action": "delegate_to_notebook",
                "suggested_notebook_id": nb_suggestion,
                "message": (
                    f"Esta pregunta parece técnica. Como orquestador de carpetas mantengo estricto "
                    f"aislamiento epistémico y cero autoridad técnica. Para analizar el tema en profundidad "
                    f"con las fuentes bibliográficas y el diálogo socrático, te sugiero abrir {nb_name} en el panel lateral."
                ),
            }

        # 2. Check if a specific notebook is mentioned
        target_spec = self._detect_target_notebook(query_lower)
        if target_spec is not None:
            is_progress_query = any(
                p in query_lower
                for p in ("avance", "progreso", "pendiente", "pendientes", "estado", "falta", "quedo", "quedó", "como voy", "cómo voy", "nota", "maestria", "maestría")
            )
            if is_progress_query:
                msg = self._format_notebook_progress(target_spec, bkt_states)
            else:
                msg = self._format_notebook_briefing(target_spec, bkt_states)

            return {
                "action": "folder_response",
                "handler": "get_aggregated_progress",
                "suggested_notebook_id": target_spec["id"],
                "message": msg,
            }

        # 3. Check greetings
        if any(g in query_lower for g in ("hola", "buenas", "buen dia", "buen día", "buenos dias", "buenos días", "saludos", "inicio", "empezar")):
            return {
                "action": "folder_response",
                "handler": "get_aggregated_progress",
                "message": self._format_greeting(bkt_states),
            }

        # 4. Check activity / where left off
        if any(a in query_lower for a in ("actividad", "donde me quede", "dónde me quedé", "donde quede", "dónde quedé", "que estaba haciendo", "qué estaba haciendo", "ultima actividad", "última actividad")):
            return {
                "action": "folder_response",
                "handler": "get_aggregated_progress",
                "message": self._format_activity(bkt_states),
            }

        # 5. Check progress / planning / roadmap
        if any(p in query_lower for p in ("progreso", "avance", "planificación", "planificacion", "semana")):
            return {
                "action": "folder_response",
                "handler": "get_aggregated_progress",
                "message": self._format_general_progress(bkt_states),
            }

        # 6. Check all notebooks / overview
        if any(o in query_lower for o in ("cuadernos", "materias", "que informacion tenes", "qué información tenés", "carpeta", "resumen", "roadmap", "que tengo", "qué tengo", "temas", "informacion", "información", "fuentes", "bibliografia", "bibliografía")):
            return {
                "action": "folder_response",
                "handler": "get_aggregated_progress",
                "message": self._format_all_notebooks_overview(bkt_states),
            }

        # 7. Fallback: query assumed technical -> delegate to notebook
        return {
            "action": "delegate_to_notebook",
            "suggested_notebook_id": None,
            "message": "Esta pregunta parece técnica. ¿En qué cuaderno querés trabajar?",
        }
