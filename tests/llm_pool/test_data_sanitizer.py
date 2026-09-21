"""Unit tests for DataSanitizer Outbound Border Control (Fase 5.9 / Pilar 3)."""

from study_engine.llm.sanitizer import DataSanitizer, SensitiveDataLeakError


def test_data_sanitizer_ipv4_detection():
    sanitizer = DataSanitizer()
    text_with_ip = "Connecting to remote database at 192.168.1.45:5432"
    assert sanitizer.is_sensitive(text_with_ip) is True
    findings = sanitizer.find_sensitive_items(text_with_ip)
    assert any(cat == "ipv4" and "192.168.1.45" in match for cat, match in findings)

    public_ip_text = "Server deployed on 203.0.113.195"
    assert sanitizer.is_sensitive(public_ip_text) is True


def test_data_sanitizer_ipv6_detection():
    sanitizer = DataSanitizer()
    text = "Host address 2001:0db8:85a3:0000:0000:8a2e:0370:7334 is listening"
    assert sanitizer.is_sensitive(text) is True
    findings = sanitizer.find_sensitive_items(text)
    assert any(cat == "ipv6" for cat, _ in findings)


def test_data_sanitizer_system_paths():
    sanitizer = DataSanitizer()
    linux_text = "Check configuration in /etc/passwd or /etc/shadow"
    assert sanitizer.is_sensitive(linux_text) is True

    home_path = "Personal key located at /home/agustin/.ssh/id_rsa"
    assert sanitizer.is_sensitive(home_path) is True

    win_path = r"Executable found at C:\Windows\System32\calc.exe"
    assert sanitizer.is_sensitive(win_path) is True


def test_data_sanitizer_credentials_and_tokens():
    sanitizer = DataSanitizer()

    # AWS Key
    aws_text = "Use key AKIAIOSFODNN7EXAMPLE for S3 backup"
    assert sanitizer.is_sensitive(aws_text) is True

    # Bearer Token
    bearer_text = "Authorization: Bearer abcd1234efgh5678ijkl9012mnop3456"
    assert sanitizer.is_sensitive(bearer_text) is True

    # JWT Token
    jwt_text = "Token eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    assert sanitizer.is_sensitive(jwt_text) is True

    # Private key header
    key_text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQ..."
    assert sanitizer.is_sensitive(key_text) is True

    # Password assignment
    pwd_text = "database_password = super_secret_pass_123"
    assert sanitizer.is_sensitive(pwd_text) is True


def test_data_sanitizer_email_detection():
    sanitizer = DataSanitizer()
    email_text = "Send confirmation to developer.admin@corp-internal.com"
    assert sanitizer.is_sensitive(email_text) is True
    findings = sanitizer.find_sensitive_items(email_text)
    assert any(cat == "email" for cat, _ in findings)


def test_data_sanitizer_innocuous_inputs():
    sanitizer = DataSanitizer()
    innocuous = [
        "Explain how memory pointers work in C.",
        "What is the difference between an array and a linked list?",
        "def bubble_sort(arr):\n    for i in range(len(arr)):\n        pass",
        "Algorithm complexity is O(n log n).",
        "Version 2.5 of the library was released in 2024.",
    ]
    for text in innocuous:
        assert sanitizer.is_sensitive(text) is False, f"False positive on: {text}"


def test_data_sanitizer_scrub_method():
    sanitizer = DataSanitizer()
    prompt = "Explain quicksort"
    context = "Source code file: /etc/hosts"
    p, c, is_sensitive = sanitizer.scrub(prompt, context)
    assert p == prompt
    assert c == context
    assert is_sensitive is True
