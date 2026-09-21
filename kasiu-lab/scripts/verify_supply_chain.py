#!/usr/bin/env python3
"""
KASIU v0.3.0 - Supply-Chain Integrity & Lockfile Verifier
Audita la integridad de binarios locales (Tailwind CLI) y verifica que package.json no contenga rangos dinámicos.
"""

import json
import hashlib
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIR = BASE_DIR / "ui"
TAILWIND_BIN = UI_DIR / "bin" / "tailwindcss"
PACKAGE_JSON = UI_DIR / "package.json"

EXPECTED_TAILWIND_SHA256 = "dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a"

def verify_package_json():
    if not PACKAGE_JSON.exists():
        print("[-] Error: package.json no encontrado en ui/")
        return False
    
    with open(PACKAGE_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    invalid_deps = []
    for dep_type in ["dependencies", "devDependencies"]:
        deps = data.get(dep_type, {})
        for name, version in deps.items():
            if version.startswith("^") or version.startswith("~") or version == "*" or "x" in version:
                invalid_deps.append((name, version))
    
    if invalid_deps:
        print("[!] VIOLACIÓN DE SUPPLY-CHAIN: Se detectaron dependencias no congeladas (rangos dinámicos):")
        for name, ver in invalid_deps:
            print(f"  - {name}: {ver}")
        return False
    
    print("[+] OK: package.json contiene exclusivamente versiones congeladas (pinned).")
    return True

def verify_tailwind_binary():
    if not TAILWIND_BIN.exists():
        print("[-] Error: Binario Tailwind Standalone CLI no encontrado en ui/bin/tailwindcss")
        return False
    
    hasher = hashlib.sha256()
    with open(TAILWIND_BIN, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    
    digest = hasher.hexdigest()
    if EXPECTED_TAILWIND_SHA256 and digest != EXPECTED_TAILWIND_SHA256:
        print(f"[!] VIOLACIÓN DE INTEGRIDAD: SHA-256 no coincide. Esperado: {EXPECTED_TAILWIND_SHA256}, Obtenido: {digest}")
        return False
    print(f"[+] SHA-256 Tailwind Standalone CLI verificado: {digest}")
    return True

def main():
    print("=== KASIU SUPPLY-CHAIN INTEGRITY CHECK ===")
    pkg_ok = verify_package_json()
    bin_ok = verify_tailwind_binary()
    
    if pkg_ok and bin_ok:
        print("=== VERIFICACIÓN COMPLETADA SIN ANOMALÍAS ===")
        sys.exit(0)
    else:
        print("=== VERIFICACIÓN FALLIDA ===")
        sys.exit(1)

if __name__ == "__main__":
    main()
