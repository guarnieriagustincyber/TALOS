from study_engine.web.routes.chat import _match_context_kc_id


def _kc_so2():
    return {
        "kc_id": "so2_gestion_procesos_pcb",
        "title": "Unidad 1: Gestión de procesos e hilos: PCB, estados y cambio de contexto",
        "display_name": "Unidad 1: Procesos, hilos, PCB y cambio de contexto",
        "subtopics": [
            "Concepto de proceso vs hilo",
            "Creación de procesos en POSIX",
        ],
        "aliases": [
            "sistemas operativos",
            "gestión de procesos",
            "procesos",
            "unidad 1",
        ],
    }


def test_deictic_followup_matches_kc_from_rewritten_retrieval_query():
    kc_id = _match_context_kc_id(
        [_kc_so2()],
        "¿Y eso por qué?",
        "¿Qué es un proceso en sistemas operativos? ¿Por qué se gestiona así?",
        is_followup=True,
    )

    assert kc_id == "so2_gestion_procesos_pcb"


def test_unrelated_query_does_not_use_retrieval_query_fallback():
    kc_id = _match_context_kc_id(
        [_kc_so2()],
        "¿Y eso por qué?",
        "¿Cómo funciona un motor de combustión interna?",
        is_followup=True,
    )

    assert kc_id is None
