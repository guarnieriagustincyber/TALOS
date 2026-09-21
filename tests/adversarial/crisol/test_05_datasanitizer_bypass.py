"""Test 05: DataSanitizer Bypass Resistance (Fase 7.1 - Red Team Epistémico).

Vector: Obfuscated PII (dotted DNIs, bearer tokens, API keys) injected into prompts.
Invariant: INV-W6-4: DataSanitizer blocks request with fail-closed guarantee; 0 PII leaks to cloud.
"""

import pytest

from study_engine.security.data_sanitizer import DataSanitizer


def test_datasanitizer_blocks_obfuscated_credentials() -> None:
    """Sanitizer catches obfuscated credentials and personal identifiers fail-closed."""
    sanitizer = DataSanitizer()

    test_vectors = [
        ("Mi DNI es 34.567.890 para el acta", "DNI_PUNTEADO"),
        ("Token: ghp_123456789012345678901234567890123456", "GITHUB_PERSONAL_TOKEN"),
        ("Key: AKIAIOSFODNN7EXAMPLE", "AWS_ACCESS_KEY"),
        ("Contacto: usuario.prueba@fadena.defensa.gob.ar", "EMAIL_ADDRESS"),
    ]

    for prompt, expected_pattern in test_vectors:
        res = sanitizer.scrub(prompt)
        assert res.has_pii is True, f"Failed to detect PII in: {prompt}"
        assert expected_pattern in res.detected_patterns


def test_datasanitizer_allows_legitimate_technical_numbers() -> None:
    """Sanitizer does not falsely block technical IP addresses or memory sizes in computer science."""
    sanitizer = DataSanitizer()
    tech_prompt = "Asigno un buffer de 1048576 bytes y una página de 4096 bytes en x86_64"
    res = sanitizer.scrub(tech_prompt)
    assert res.has_pii is False
