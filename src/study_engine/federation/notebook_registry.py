"""Sovereign Notebook Registry for Federation Subsystem (Phase E4).

Maintains notebook identities, scoped sources, authority references, and enforces
default confinement to active notebook.
"""

from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field


class Notebook(BaseModel):
    """Sovereign educational notebook definition."""

    model_config = ConfigDict(frozen=True)

    notebook_id: str = Field(..., min_length=1, description="Unique notebook identifier")
    name: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    level: str = Field(default="Grado")
    sources: List[str] = Field(default_factory=list, description="Associated source_ids")
    authority_matrix_ref: Dict[str, float] = Field(
        default_factory=dict, description="Topic -> authority weight [0.1, 2.0]"
    )
    is_active: bool = Field(default=True)


DEFAULT_NOTEBOOKS = [
    Notebook(
        notebook_id="fase0-soc",
        name="Roadmap KASIU TECH v4 - Fase 0",
        subject="Programación y Pensamiento Algorítmico",
        level="Fundamentos",
        sources=[
            "src_joyanes_fundamentos",
            "src_spraul_think_like_a_programmer",
            "src_martin_clean_code",
            "src_rosen_matematicas_discretas",
            "src_fadena_prog_punteros",
            "src_sweigart_automate_boring_stuff",
            "src_bel_algoritmos_estructuras_python",
            "src_goodrich_dsa_python",
        ],
        authority_matrix_ref={
            "aritmetica_punteros": 2.0,
            "arrays_direccionamiento_contiguo": 1.8,
            "modularidad_stack_frame": 1.5,
            "parsing_acumuladores": 1.5,
            "clean_code_guard_clauses": 1.5,
            "fisica_ram_asignacion": 1.5,
            "big_o_complejidad": 1.4,
            "busqueda_binaria": 1.3,
            "ordenamiento_burbuja": 1.3,
        },
    ),
    Notebook(
        notebook_id="fadena-lenguajes",
        name="Lenguajes de Programación - FADENA 2026",
        subject="Lenguajes de Programación",
        level="Grado",
        sources=[
            "src_fadena_leng_clase1",
            "src_fadena_leng_clase2",
            "src_urrutia_programacion_c_principiantes",
            "src_marzal_intro_programacion_c",
            "src_stallman_gnu_c_manual",
            "src_fadena_prog_lineales",
            "src_joyanes_fundamentos",
            "src_spraul_think_like_a_programmer",
            "src_fadena_prog_punteros",
            "src_sweigart_automate_boring_stuff",
        ],
        authority_matrix_ref={
            "leng_intro_algoritmos": 2.0,
            "leng_pseudocodigo_estructurado": 1.8,
            "leng_iniciacion_c": 1.8,
            "leng_arreglos_lineales": 1.5,
            "leng_funciones_modularizacion": 1.5,
            "leng_comparativa_paradigmas": 1.3,
            "leng_intro_poo": 1.3,
            "leng_principios_poo": 1.3,
            "leng_intro_web_php": 1.2,
            "leng_formularios_backend": 1.2,
        },
    ),
    Notebook(
        notebook_id="fadena-so2",
        name="Sistemas Operativos II - FADENA 2026",
        subject="Sistemas Operativos",
        level="Grado",
        sources=[
            "src_fadena_so2_clase1",
            "src_fadena_so2_clase2",
            "src_stallings_os_internals_7ed",
            "src_fadena_so_procesos",
            "src_fadena_so_concurrencia",
            "src_fadena_so_planificacion",
            "src_fadena_so_memoria",
            "src_stallings_computer_security",
        ],
        authority_matrix_ref={
            "so2_gestion_procesos_pcb": 2.0,
            "so2_ipc_concurrencia": 1.8,
            "so2_planificacion_cpu": 1.8,
            "so2_interbloqueos_deadlock": 1.5,
            "so2_sistemas_distribuidos": 1.4,
            "so2_seguridad_sistemas": 1.3,
        },
    ),
    Notebook(
        notebook_id="fadena-std",
        name="Sistema de Tratamiento de Datos - FADENA 2026",
        subject="Tratamiento de Datos y Bases de Datos",
        level="Grado",
        sources=[
            "src_fadena_std_unidad1",
            "src_coronel_database_systems_11ed",
            "src_silberschatz_fundamentos_bd",
            "src_date_intro_sistemas_bd_7ed",
            "src_elmasri_navathe_sistemas_bd",
            "src_ramakrishnan_gehrke_dbms",
            "src_marques_bases_de_datos",
            "src_fadena_prog_archivos",
            "src_ramalho_fluent_python",
        ],
        authority_matrix_ref={
            "std_intro_datos_sgbd": 2.0,
            "std_modelo_relacional_er": 1.8,
            "std_sql_consultas": 1.8,
            "std_admin_seguridad_bd": 1.5,
            "std_formatos_regex": 1.5,
            "std_nosql_cap": 1.3,
            "std_tendencias_etl": 1.3,
        },
    ),
    Notebook(
        notebook_id="fadena-teleco",
        name="Infraestructura de Telecomunicaciones - FADENA 2025",
        subject="Telecomunicaciones y Redes",
        level="Grado",
        sources=[
            "src_fadena_teleco_unidad1",
            "src_stallings_comunicaciones_redes_7ed",
            "src_castro_fusario_comunicaciones_redes",
            "src_comer_internetworking_tcpip_v1",
            "src_kurose_computer_networking",
            "src_stallings_computer_security",
            "src_corletti_seguridad_redes",
            "src-guia-2025-c04f44ef",
        ],
        authority_matrix_ref={
            "teleco_transmision_datos": 2.0,
            "teleco_parametros_senales": 1.8,
            "teleco_calculo_enlaces_db": 1.8,
            "teleco_ancho_banda_fourier": 1.5,
            "teleco_banda_base_codificacion": 1.5,
            "teleco_capacidad_shannon": 1.5,
            "teleco_deteccion_errores": 1.4,
            "teleco_modulacion_digital": 1.3,
            "teleco_intro_redes_osi": 1.3,
            "teleco_protocolos_ip_subredes": 1.3,
        },
    ),
    # Aliases y compatibilidad retroactiva con tests existentes
    Notebook(
        notebook_id="fadena-prog",
        name="Programación y Estructuras de Datos (Legacy Alias)",
        subject="Programación",
        level="Grado",
        sources=["src-prog-punteros", "src-prog-lineales", "src-prog-arboles", "src-prog-archivos"],
        authority_matrix_ref={
            "punteros": 1.5,
            "memoria_dinamica": 1.4,
            "arboles": 1.3,
            "archivos_binarios": 1.2,
            "complejidad": 1.1,
        },
    ),
    Notebook(
        notebook_id="fadena-so",
        name="Sistemas Operativos y Procesos (Legacy Alias)",
        subject="Sistemas Operativos",
        level="Grado",
        sources=["src-so-procesos", "src-so-planificacion", "src-so-memoria", "src-so-concurrencia"],
        authority_matrix_ref={
            "procesos": 1.5,
            "memoria_virtual": 1.5,
            "concurrencia": 1.4,
            "semaforos": 1.3,
            "buffer_overflow": 1.2,
        },
    ),
    Notebook(
        notebook_id="NB-CYBERSECURITY-V1",
        name="Seguridad Informática y Redes",
        subject="Seguridad",
        level="Grado",
        sources=[
            "src_kurose_computer_networking",
            "src_stallings_computer_security",
            "src_rosen_matematicas_discretas",
        ],
        authority_matrix_ref={
            "sockets_tcp": 1.5,
            "buffer_overflow": 1.5,
            "hashing_sha256": 1.4,
            "race_conditions": 1.3,
        },
    ),
]


class NotebookRegistry:
    """In-memory thread-safe registry enforcing notebook isolation boundaries."""

    def __init__(self, initial_notebooks: Optional[List[Notebook]] = None) -> None:
        self._notebooks: Dict[str, Notebook] = {}
        self._lock = threading.Lock()

        seeds = initial_notebooks if initial_notebooks is not None else DEFAULT_NOTEBOOKS
        for nb in seeds:
            self._notebooks[nb.notebook_id] = nb

    def register_notebook(self, notebook: Notebook) -> None:
        """Register or update a notebook."""
        with self._lock:
            self._notebooks[notebook.notebook_id] = notebook

    def get_notebook(self, notebook_id: str) -> Optional[Notebook]:
        """Retrieve notebook by ID."""
        with self._lock:
            return self._notebooks.get(notebook_id.strip())

    def list_notebooks(self) -> List[Notebook]:
        """List all active notebooks."""
        with self._lock:
            return list(self._notebooks.values())

    def validate_notebook_scope(self, notebook_id: str) -> bool:
        """Verify if a notebook ID is formally registered and active."""
        with self._lock:
            nb = self._notebooks.get(notebook_id.strip())
            return nb is not None and nb.is_active

    def get_sources_for_notebook(self, notebook_id: str) -> Set[str]:
        """Return all source_ids associated with a notebook."""
        with self._lock:
            nb = self._notebooks.get(notebook_id.strip())
            return set(nb.sources) if nb else set()

    def get_authority_weight(self, notebook_id: str, topic: str) -> float:
        """Retrieve topic authority weight for a notebook (default 1.0, clamped [0.1, 2.0])."""
        with self._lock:
            nb = self._notebooks.get(notebook_id.strip())
            if not nb:
                return 1.0
            weight = nb.authority_matrix_ref.get(topic.lower().strip(), 1.0)
            return max(0.1, min(2.0, weight))
