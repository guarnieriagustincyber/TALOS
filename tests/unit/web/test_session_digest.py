"""Session Digest (Fase 5.4) — memoria de esencia entre sesiones.

Contrato:
- Intentos evaluados se acumulan por sesión en student_state.db.
- generate_session_digest: struggled_kcs (>=2 errores o tracker en lucha),
  mastered_kcs (>=2 aciertos y 0 errores), friction_level coherente.
- El JSON persistido contiene los mismos KCs.
- maybe_inject_session_digest inyecta la directiva UNA vez por sesión.
"""

import json
from types import SimpleNamespace

from study_engine.pedagogy.session_digest import (
    digest_directive,
    generate_session_digest,
    get_latest_digest,
    record_kc_attempt,
)
from study_engine.student.storage import StudentStorage


def test_digest_acumula_fallos_y_aciertos(tmp_path):
    storage = StudentStorage(str(tmp_path / "student.db"))
    student, sess = "agustin", "sess_1"

    # 3 fallos en punteros + 2 aciertos en bucles
    for _ in range(3):
        record_kc_attempt(storage, student, sess, "aritmetica_punteros", correct=False)
    for _ in range(2):
        record_kc_attempt(storage, student, sess, "bucle_do_while", correct=True)

    digest = generate_session_digest(student, sess, storage)
    assert digest["friction_level"] == "high"
    assert "aritmetica_punteros" in digest["struggled_kcs"]
    assert "bucle_do_while" in digest["mastered_kcs"]

    # Persistido en la DB y legible como "última sesión"
    latest = get_latest_digest(storage, student)
    assert latest is not None
    assert latest["struggled_kcs"] == ["aritmetica_punteros"]
    assert "aritmetica_punteros" in json.dumps(latest)  #


def test_digest_struggle_flag_marca_con_un_fallo_si_tracker_activo(tmp_path):
    storage = StudentStorage(str(tmp_path / "s.db"))
    # Un solo error PERO con struggle=True (tracker en lucha) => struggled
    record_kc_attempt(storage, "agustin", "sess", "kc_x", correct=False, struggled=True)
    digest = generate_session_digest("agustin", "sess", storage)
    assert digest["friction_level"] == "high"
    assert digest["struggled_kcs"] == ["kc_x"]


def test_friction_levels():
    storage = StudentStorage(":memory:")
    record_kc_attempt(storage, "s", "sess_a", "kc_a", correct=True)  # 1 acierto, sin errores
    assert generate_session_digest("s", "sess_a", storage)["friction_level"] == "low"

    record_kc_attempt(storage, "s", "sess_b", "kc_b", correct=False)
    assert generate_session_digest("s", "sess_b", storage)["friction_level"] == "medium"


def test_get_latest_digest_none_en_primera_sesion(tmp_path):
    storage = StudentStorage(str(tmp_path / "clean.db"))
    assert get_latest_digest(storage, "agustin") is None


def test_digest_directive_inyecta_una_sola_vez_por_sesion(tmp_path):
    import json
    storage = StudentStorage(str(tmp_path / "s.db"))
    for _ in range(3):
        record_kc_attempt(storage, "agustin", "sess_previa", "kc_hard", correct=False)

    from study_engine.web.routes.chat import _DIGEST_SHOWN, maybe_inject_session_digest

    container = SimpleNamespace(student_storage=storage)
    first = maybe_inject_session_digest(container, "history_nuevo", None)
    assert first is not None and "RESUMEN DE SESIÓN ANTERIOR" in first
    assert "kc_hard" in first
    assert "analogía simple" in first

    # Segundo turno de la MISMA sesión: no repetir
    second = maybe_inject_session_digest(container, "history_nuevo", None)
    assert second is None or "RESUMEN DE SESIÓN ANTERIOR" not in second

    # Sesión distinta: vuelve a inyectar
    other = maybe_inject_session_digest(container, "history_otra", None)
    assert other and "RESUMEN DE SESIÓN ANTERIOR" in other

    _DIGEST_SHOWN.clear()  # no contaminar otros tests
