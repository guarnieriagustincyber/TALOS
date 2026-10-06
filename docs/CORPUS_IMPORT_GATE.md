# 🚪 Protocolo del TALOS Corpus Import Gate

**Estado:** Especificación Normativa de Assurance y Protocolo de Ingestión  
**Versión:** 1.1 (CP114-PRE v4.1)  
**Objetivo:** Establecer la barrera de verificación pre-ingesta que impida la degradación de `knowledge_store.db` y `vector_store.db`, garantizando fail-closed, soberanía local y separación entre validación técnica y decisión humana.

---

## 1. Principio Fundamental: Fail-Closed y Separación Validación/Decisión

Ningún archivo proveniente de Google Colab o de un entorno externo puede insertarse directamente en las bases de datos de producción de TALOS.

El Import Gate opera en dos fases desacopladas:
1. **Validación Técnica (`TECHNICAL_VALIDATION`):** Verificación exhaustiva, determinista y automatizada de integridad, contratos y diagnósticos. Emite `PASS` o `FAIL`.
2. **Aceptación Humana (`HUMAN_ACCEPTANCE`):** Revisión explícita del operador humano sobre el informe comparativo. Emite `ACCEPTED` o `REJECTED`.

> **Regla de Oro:**  
> `TECHNICAL_VALIDATION = PASS` **NUNCA** implica `HUMAN_ACCEPTANCE = ACCEPTED`.  
> Una mejora en una métrica sintética o en el benchmark no autoriza automáticamente la mutación de producción. Toda mutación requiere confirmación humana explícita informada.

```text
[Bundle Descargado] ──► [TALOS IMPORT GATE: Validación Técnica]
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                  [FAIL: Abort]        [PASS: Report]
                       │                     │
                       ▼                     ▼
                  FAIL-CLOSED       [Evaluación Humana]
                                             │
                                   ┌─────────┴─────────┐
                                   │                   │
                              [REJECT]              [ACCEPT]
                                   │                   │
                                   ▼                   ▼
                               Descarte       Flujo Staged Commit
```

---

## 2. Los 8 Niveles de Verificación del Gate

```text
NIVEL 1: Integridad Criptográfica de Transporte (checksums.sha256)
   ↓ PASS
NIVEL 2: Conformidad de Esquema Sintáctico (JSONL / JSON schemas)
   ↓ PASS
NIVEL 3: Trazabilidad de Origen y Hash del PDF Canónico (fuentes/)
   ↓ PASS
NIVEL 4: Diagnóstico de Calidad Estructural y Jerárquica (AST)
   ↓ PASS
NIVEL 5: Auditoría de Mutilación Léxica y Detección de Ruido
   ↓ PASS
NIVEL 6: Conformidad de Contrato de Espacio Vectorial (1024d, L2 norm)
   ↓ PASS
NIVEL 7: Retrieval Benchmark Comparativo (Taxonomía CP113-R1)
   ↓ PASS
NIVEL 8: Puerta de Aceptación Humana Explícita
   ↓ ACCEPT
FLUJO DE PERSISTENCIA STAGED Y COORDINADO
```

### Detalle de Verificaciones:

1. **Nivel 1 — Integridad Criptográfica de Transporte:**
   - Calcula el hash SHA-256 de cada archivo del bundle descomprimido y lo compara contra `checksums.sha256`. Si hay discrepancia de un solo byte, se aborta con `TRANSPORT_CORRUPTION`.
2. **Nivel 2 — Conformidad de Esquema:**
   - Valida que cada línea de `chunks.jsonl`, `metadata.jsonl` y `provenance.jsonl` cumpla estrictamente con la especificación de tipos de `talos-corpus-bundle-v1` (campos obligatorios no nulos, `token_count > 0`, etc.).
3. **Nivel 3 — Trazabilidad de Origen y Autoridad Canónica:**
   - Verifica que el campo `source_sha256` coincida exactamente (64 caracteres hex) con el hash del archivo físico custodiado localmente en `fuentes/`. Si el PDF fue modificado o sustituido externamente, se rechaza con `UNAUTHORIZED_SOURCE_MUTATION`.
4. **Nivel 4 — Diagnóstico de Calidad Estructural (AST):**
   - Evalúa métricas diagnósticas de jerarquía documental (`table_structure_rate`, `heading_preservation_rate`, `heading_path_coverage`). No se aplican thresholds arbitrarios como filtro ciego; se registran las métricas empíricas para la decisión humana en el Nivel 8.
5. **Nivel 5 — Blindaje contra Mutilación Léxica y Ruido:**
   - Escaneo de límites: detecta y cuantifica palabras partidas con guiones residuales al final o fragmentos léxicos mutilados al inicio de los chunks.
   - Escaneo de ruido: detecta encabezados móviles repetitivos de página filtrados al texto.
6. **Nivel 6 — Conformidad de Contrato de Espacio Vectorial:**
   - Verifica que cada vector serializado tenga exactamente 1024 dimensiones, norma L2 igual a $1.0 \pm 10^{-4}$, y que no contenga valores `NaN` o `Inf`.
7. **Nivel 7 — Retrieval Benchmark Comparativo (Cadena CP113-R1):**
   - Evalúa las consultas de control bajo la taxonomía canónica:
     $$\text{Query} \longrightarrow \text{Hit} \longrightarrow \text{Relevant Evidence} \longrightarrow \text{Sufficient Evidence} \longrightarrow \text{Grounded Response}$$
   - Registra por separado la tasa de acierto (Hit), relevancia, suficiencia y fundamentación, así como deltas A/B respecto al baseline histórico.
   - **Regla:** Un delta positivo en retrieval NO genera aprobación automática; constituye evidencia diagnóstica para la revisión humana.
8. **Nivel 8 — Aprobación Humana Explícita:**
   - El Import Gate emite un `import_audit_report.json` que consolida los resultados técnicos de los niveles 1 al 7.
   - La persistencia productiva permanece bloqueada hasta que el operador ejecute la acción de confirmación explícita (ej. `python scripts/corpus_import.py --bundle ... --confirm`).

---

## 3. Protocolo de Persistencia Staged y Coordinado (Arquitectura Multi-Base)

`knowledge_store.db` y `vector_store.db` son dos archivos SQLite completamente independientes. Por diseño de SQLite, **no existe una única transacción ACID nativa compartida entre dos archivos de base de datos no adjuntos**.

Para garantizar atomicidad a nivel de aplicación sin riesgo de estados intermedios o corruptos, la persistencia se implementa mediante un protocolo **Staged Two-Phase Workflow**:

```text
[1. VALIDATE] ──► [2. STAGE] ──► [3. PREPARE] ──► [4. COMMIT/REPLACE] ──► [5. VERIFY]
       │                 │              │                   │                   │
   (Fallo)           (Fallo)        (Fallo)             (Fallo)             (Fallo)
       ▼                 ▼              ▼                   ▼                   ▼
    ABORT             ABORT          ABORT              ROLLBACK            ROLLBACK
  (Sin cambios)    (Limpieza)     (Limpieza)       (Restaurar backup)  (Restaurar backup)
```

### Fases del Protocolo:

1. **VALIDATE (Lectura pura):**
   - Verificación completa de los Niveles 1 a 8. Bases de datos productivas en modo estrictamente `READ-ONLY`.
2. **STAGE (Área de ensayo temporal):**
   - Creación de copias temporales (`.staging/knowledge_store.db`, `.staging/vector_store.db`).
   - Aplicación de las inserciones de chunks y vectores en el área de staging.
   - Cada base temporal se opera bajo su respectiva transacción SQLite (`BEGIN IMMEDIATE` ... `COMMIT`).
3. **PREPARE (Snapshot de respaldo inmutable):**
   - Creación de snapshots de seguridad de las bases productivas actuales:
     - `data/web_state/knowledge_store.db.bak_<timestamp>`
     - `data/web_state/vector_store.db.bak_<timestamp>`
   - Registro de sumas SHA-256 de los respaldos.
4. **COMMIT / REPLACE (Sustitución atómica por archivo):**
   - Reemplazo atómico de los archivos productivos utilizando `os.replace()` (llamada a nivel de sistema operativo `rename(2)` que es atómica en sistemas POSIX).
   - Secuencia de reemplazo: primero `knowledge_store.db`, luego `vector_store.db`.
   - Si ocurre una excepción en cualquiera de los reemplazos, se activa inmediatamente el procedimiento de restauración desde los snapshots `.bak`.
5. **VERIFY (Auditoría post-commit):**
   - Verificación de integridad SQLite (`PRAGMA integrity_check`) sobre ambos archivos productivos sustituidos.
   - Verificación de consistencia referencial cruzada (cada vector en `vector_store.db` debe corresponder a un chunk válido en `knowledge_store.db`).
   - Si la verificación falla: reversión automática inmediata a los snapshots y fail-closed.

---

## 4. Estado de Implementación en CP114-PRE v4.1

- El script de importación `scripts/corpus_import.py` **NO** se ejecutará durante este checkpoint.
- Las bases de datos de producción permanecen en `READ-ONLY`.
- Ninguna base de datos ni archivo en `data/web_state/` será modificado.
