# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## PROBE-1: ESPECIFICACIÓN DEL ENRUTADOR ADAPTATIVO (C02)

**Versión:** 1.0.1-canonical  
**Fecha:** 2026-10-05  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `SPECIFICATION_FROZEN_PRE_CALIBRATION`  
**Autoridad:** Directiva Canónica v1.0.1 (Controles C01, C02, C10, C11)  
**Aislamiento:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. PRINCIPIOS DE ARQUITECTURA DEL ROUTER

El enrutador estructural adaptativo es un componente de decisión local, determinista, explicable y libre de modelos (*model-free*). Su propósito es despachar cada página $p$ al extractor óptimo:
* **FAST_PATH (`PyMuPDF`):** Para páginas de baja complejidad estructural (prosa homogénea, texto continuo, listas simples).
* **DOCLING_PATH (`Docling v2`):** Para páginas complejas (tablas densas, diagramas de flujo vectoriales, código algorítmico jerárquico o columnas paralelas).

```text
                                 PÁGINA PDF (p)
                                       │
                                       ▼
                       INSPECCIÓN DETERMINISTA RÁPIDA
                           (Features F1 ... F6)
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
        ¿Activa alguna regla R1..R5?                 Ninguna regla
                    │                                     │
                    ▼ (SÍ)                                ▼ (NO)
            DOCLING_PATH (v2)                      FAST_PATH (PyMuPDF)
            [TableFormer / Layout]                 [Texto Continuo / Bloques]
                    │                                     │
                    └──────────────────┬──────────────────┘
                                       ▼
                             SALIDA NORMALIZADA
```

---

## 2. REGLAS PRIORIZADAS DE DECISIÓN

Las reglas se evalúan en estricto orden de precedencia. La primera condición que resulta verdadera determina la escalada a Docling.

```python
def route_page_adaptive(features: dict, thresholds: dict) -> dict:
    """
    Enrutador Estructural Determinista de Página (Model-Free).
    """
    # Regla 1: Cuadrícula Tabular Ortogonal (Tablas Densas)
    if features["table_grid_score"] >= thresholds["tau_grid"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R1_TABLE_GRID",
            "trigger": f"table_grid_score={features['table_grid_score']:.2f} >= {thresholds['tau_grid']}",
            "priority": 1
        }

    # Regla 2: Densidad de Trazado Vectorial (Diagramas de Flujo / Cajas ANSI)
    if features["dwg_count"] >= thresholds["tau_dwg"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R2_VECTOR_FLOWCHART",
            "trigger": f"dwg_count={features['dwg_count']} >= {thresholds['tau_dwg']}",
            "priority": 2
        }

    # Regla 3: Solapamiento Horizontal Paralelo (Columnas paralelas / Código y Flujo)
    if features["parallel_overlap"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R3_PARALLEL_OVERLAP",
            "trigger": "parallel_overlap=TRUE",
            "priority": 3
        }

    # Regla 4: Código y Pseudocódigo Anidado
    if (features["code_block_density"] >= thresholds["tau_code"] and 
        features["indented_blocks"] >= thresholds["tau_indent"]):
        return {
            "selected_path": "DOCLING",
            "rule_id": "R4_STRUCTURED_CODE",
            "trigger": f"code_density={features['code_block_density']:.2f} & indent={features['indented_blocks']}",
            "priority": 4
        }

    # Regla 5: Líderes de Puntos (TOC / Índices Jerárquicos)
    if features["dot_leader_count"] >= thresholds["tau_dots"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R5_DOT_LEADERS_TOC",
            "trigger": f"dot_leader_count={features['dot_leader_count']} >= {thresholds['tau_dots']}",
            "priority": 5
        }

    # Regla 0: Camino Rápido por Defecto
    return {
        "selected_path": "PYMUPDF",
        "rule_id": "R0_FAST_DEFAULT",
        "trigger": "No complex structural signals detected",
        "priority": 0
    }
```

---

## 3. POLÍTICA DE VALORES AUSENTES Y CASOS BORDE

1. **Página en blanco / Sin texto:** Si una página no contiene bloques textuales (`blocks = []`), se asigna a `FAST_PATH` con `R0_FAST_DEFAULT`. No se justifica el gasto computacional de Docling en páginas vacías.
2. **Error en extracción de features:** En caso de excepción no controlada en la inspección de features, el enrutador implementa política **fail-closed hacia calidad**: despacha a `DOCLING_PATH` con `rule_id = R_FAILSAFE_ESCALATION` para garantizar que no se pierda estructura pedagógica.
3. **Valores nulos en geometrías:** Se imputan a cero ($0$) sin abortar la ejecución.

---

## 4. PROTOCOLO DE CONGELAMIENTO (ROUTER_FREEZE)

Conforme al Control C02:
1. El código de la función `route_page_adaptive` y los valores finales de `thresholds` se congelan formalmente tras la calibración exclusiva en `DEV_SET`.
2. Se genera el hash criptográfico SHA-256 del código y del archivo de configuración `router_frozen_config.json`.
3. Una vez generado `ROUTER_FREEZE = TRUE`, queda **prohibida cualquier modificación de los umbrales o reglas**.
4. La evaluación sobre `TEST_SET` se ejecutará estrictamente con este binario/script sellado.

---

## 5. ESQUEMA DE AUDITORÍA Y TRAZABILIDAD (TELEMETRÍA EXPLICABLE)

Cada decisión produce un registro JSON estructurado e inmutable:

```json
{
  "$schema": "https://raw.githubusercontent.com/guarnieriagustincyber/TALOS/main/schemas/probe1_routing_decision.schema.json",
  "page_id": "joyanes_ch02_p080",
  "split": "DEV",
  "decision": {
    "selected_path": "DOCLING",
    "rule_id": "R2_VECTOR_FLOWCHART",
    "trigger": "dwg_count=25 >= 15",
    "priority": 2
  },
  "features_observed": {
    "dwg_count": 25,
    "table_grid_score": 0.0,
    "parallel_overlap": false,
    "code_block_density": 0.05,
    "indented_blocks": 1,
    "dot_leader_count": 0
  },
  "telemetry": {
    "inspection_duration_ms": 4.12,
    "timestamp_iso": "2026-10-05T23:55:00Z"
  }
}
```
