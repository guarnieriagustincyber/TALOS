import pytest
from study_engine.pedagogy.command_parser import (
    CommandType,
    parse_student_command,
    UNIVERSAL_SAFE_COMMANDS,
)


def test_parse_resumen_unidad():
    queries = [
        'RESUMEN UNIDAD 1',
        'resumen de la unidad 2',
        'RESUMEN DEL CAPÍTULO 3',
        'resumen capitulo 4',
        '  RESUMEN UNIDAD U1.2  ',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.RESUMEN_UNIDAD
        assert cmd.expected_format == 'MAPA DE UNIDAD'
        assert cmd.is_structured is True
        assert cmd.max_words == 500
        assert '**MAPA DE UNIDAD**' in cmd.template_instruction


def test_parse_empecemos_tema():
    queries = [
        'EMPECEMOS CON EL TEMA 1.1',
        'empecemos con el tema 2.3',
        'LEÍ EL CAPÍTULO, EMPECEMOS CON EL PUNTO 3.1',
        'LEI CAPITULO EMPECEMOS CON EL PUNTO 4',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.EMPECEMOS_TEMA
        assert cmd.expected_format == 'EXPLICACIÓN DEL TEMA'
        assert cmd.is_structured is True
        assert '**EXPLICACIÓN DEL TEMA**' in cmd.template_instruction


def test_parse_dame_un_ejercicio():
    queries = [
        'DAME UN EJERCICIO',
        'dame ejercicio',
        'quiero un ejercicio',
        'PROPONÉ UN EJERCICIO',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.DAME_UN_EJERCICIO
        assert cmd.expected_format == 'EJERCICIO GUIADO'
        assert cmd.is_structured is True
        assert '**EJERCICIO GUIADO**' in cmd.template_instruction


def test_parse_dame_solucion_completa():
    queries = [
        'DAME LA SOLUCIÓN COMPLETA',
        'dame la solucion completa',
        'SOLUCIÓN COMPLETA',
        'solucion completa',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.DAME_SOLUCION_COMPLETA
        assert cmd.expected_format == 'SOLUCIÓN COMPLETA'
        assert cmd.is_structured is True
        assert '**SOLUCIÓN COMPLETA**' in cmd.template_instruction


def test_parse_traduccion():
    queries = [
        'TRADUCÍ ESTO A C',
        'traduci esto a python',
        'TRADUCÍ A PHP',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.TRADUCCION
        assert cmd.expected_format == 'TRADUCCIÓN'
        assert cmd.is_structured is True
        assert '**TRADUCCIÓN**' in cmd.template_instruction


def test_parse_explicacion_desde_cero():
    queries = [
        'EXPLICÁ COMO SI NO SUPIERA NADA',
        'explica esto como si no supiera nada',
        'EXPLICÁ ESTO COMO SI NO SUPIERA NADA',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.EXPLICACION_DESDE_CERO
        assert cmd.expected_format == 'EXPLICACIÓN DESDE CERO'
        assert cmd.is_structured is True
        assert '**EXPLICACIÓN DESDE CERO**' in cmd.template_instruction


def test_parse_no_entendi():
    queries = [
        'NO ENTENDÍ',
        'no entendi',
        'NO ENTIENDO',
        'OTRA FORMA',
        'reformulá',
        'ME PERDÍ',
    ]
    for q in queries:
        cmd = parse_student_command(q)
        assert cmd is not None, f'Failed for {q}'
        assert cmd.command_type == CommandType.NO_ENTENDI
        assert cmd.expected_format == 'CAMBIO DE ENFOQUE'
        assert cmd.is_structured is True
        assert 'CAMBIO DE ENFOQUE' in cmd.template_instruction


def test_conversational_queries_not_matched():
    queries = [
        '¿Qué es un algoritmo?',
        '¿Por qué el handshake TCP usa 3 pasos?',
        'Tengo una duda con el puntero void*',
        'hola como estas',
        '',
    ]
    for q in queries:
        assert parse_student_command(q) is None


def test_universal_safe_commands_has_all():
    assert 'DAME UN EJERCICIO' in UNIVERSAL_SAFE_COMMANDS
    assert 'DAME LA SOLUCIÓN COMPLETA' in UNIVERSAL_SAFE_COMMANDS
    assert 'RESUMEN UNIDAD' in UNIVERSAL_SAFE_COMMANDS
    assert 'NO ENTENDÍ' in UNIVERSAL_SAFE_COMMANDS
    assert ':solve' in UNIVERSAL_SAFE_COMMANDS
