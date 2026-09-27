from study_engine.web.routes.chat import _match_kc_id


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


def test_match_kc_con_alias():
    assert _match_kc_id(
        [_kc_so2()],
        "¿Qué es un proceso en sistemas operativos?",
    ) == "so2_gestion_procesos_pcb"


def test_match_kc_sin_relacion_no_matchea():
    assert _match_kc_id(
        [_kc_so2()],
        "¿Cómo funciona un motor de combustión interna?",
    ) is None


def test_alias_solo_no_alcanza_umbral():
    assert _match_kc_id(
        [_kc_so2()],
        "¿Qué son los sistemas operativos?",
    ) is None
