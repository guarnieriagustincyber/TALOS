#!/usr/bin/env python3
"""Auditoría forense del código KASIU."""
import subprocess
from pathlib import Path

def run_command(cmd, description):
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr[:500]}")

def main():
    print("🩺 AUDITORÍA FORENSE DE KASIU")
    print(f"Directorio: {Path.cwd()}")
    
    # 1. Git status
    run_command("git status --short", "Git Status - Archivos modificados")
    
    # 2. Archivos más grandes
    run_command(
        "find src/study_engine/ -name '*.py' -type f -exec wc -l {} \\; | sort -rn | head -10",
        "Archivos más grandes (candidatos a dividir)"
    )
    
    # 3. Duplicados
    run_command(
        "grep -rn '^def ' src/study_engine/ --include='*.py' | awk -F: '{print $3}' | sort | uniq -c | sort -rn | head -10",
        "Funciones con nombres duplicados"
    )
    
    # 4. Complejidad
    run_command(
        ".venv/bin/radon cc src/study_engine/ -a -s --total-average 2>/dev/null | tail -5",
        "Complejidad ciclomática promedio"
    )
    
    # 5. Cobertura
    run_command(
        ".venv/bin/pytest tests/unit/ -q --cov=src/study_engine --cov-report=term 2>&1 | tail -20",
        "Cobertura de tests"
    )
    
    # 6. Seguridad
    run_command(
        "grep -rn 'api_key\\|password\\|secret' src/study_engine/ --include='*.py' | grep -v 'os.getenv\\|environ' | head -5",
        "Secretos hardcodeados"
    )
    
    print("\n" + "="*60)
    print("✅ AUDITORÍA COMPLETADA")
    print("="*60)

if __name__ == "__main__":
    main()
