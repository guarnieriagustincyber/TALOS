# TALOS V1.5 — INGESTION INTELLIGENCE LAB
## ESPECIFICACIÓN FORMAL DEL ENRUTADOR CALIBRADO Y CONGELADO (PROBE-1)

**Versión:** 1.0.1-calibrated-frozen  
**Fecha de Congelamiento:** 2026-10-06  
**Fase:** Ingestion Intelligence Lab (v2.0)  
**Experimento:** `PROBE-1: Adaptive Structural Routing`  
**Estado:** `ROUTER_FROZEN_FOR_TEST`  
**Autoridad:** Directiva Canónica v1.0.0-canonical (DEV Calibration)  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE`  

---

## 1. DECLARACIÓN DE CONGELAMIENTO (ROUTER_FREEZE = TRUE)

Por la presente se certifica que la arquitectura, orden de precedencia y parámetros numéricos del **Enrutador Estructural Adaptativo de TALOS V1.5** quedan **estricta e irrevocablemente congelados**.

```text
ROUTER_FREEZE_STATUS       : FROZEN_INMUTABLE
CALIBRATION_SET            : DEV_SET (19 páginas de Joyanes Cap. 2)
TEST_SET_CONTAMINATION     : ZERO (Test nunca consultado)
MODIFICATIONS_PERMITTED    : STRICTLY_PROHIBITED
```

---

## 2. PARÁMETROS NUMÉRICOS CALIBRADOS

| Parámetro | Valor Calibrado | Regla Asociada | Racional Técnico |
|---|:---:|:---|:---|
| $\tau_{\text{grid}}$ | `1.0` | `R1_TABLE_GRID` | Detecta al menos 4 intersecciones ortogonales de líneas de tabla. |
| $\tau_{\text{dwg}}$ | `12` | `R2_VECTOR_FLOWCHART` | Separa limpiamente diagramas de flujo ($\ge 14$) de prosa simple ($\le 5$). |
| $\tau_{\text{overlap}}$ | `TRUE` | `R3_PARALLEL_OVERLAP` | Detecta flujos contiguos paralelos excluyendo texto encerrado en figuras. |
| $\tau_{\text{code}}$ | `0.20` | `R4_STRUCTURED_CODE` | Requiere que al menos el 20% de las líneas contengan sintaxis algorítmica. |
| $\tau_{\text{indent}}$ | `3` | `R4_STRUCTURED_CODE` | Exige sangría jerárquica con al menos 3 bloques desplazados $\ge 18\text{ pt}$. |
| $\tau_{\text{dots}}$ | `3` | `R5_DOT_LEADERS_TOC` | Detecta al menos 3 secuencias de puntos suspensivos que preceden números. |

---

## 3. LÓGICA FORMAL DE DECISIÓN DETERMINISTA (MODEL-FREE)

El router se evalúa en estricto orden de precedencia:

```python
def route_page(features: dict, thresholds: dict = None) -> dict:
    """
    Enrutador Estructural Adaptativo Calibrado y Congelado.
    """
    if thresholds is None:
        thresholds = {
            "tau_grid": 1.0,
            "tau_dwg": 12,
            "tau_code": 0.20,
            "tau_indent": 3,
            "tau_dots": 3
        }

    # R1: Cuadrícula Tabular Ortogonal (Prioridad 1)
    if features.get("table_grid_score", 0.0) >= thresholds["tau_grid"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R1_TABLE_GRID",
            "trigger": f"table_grid_score={features.get('table_grid_score', 0.0):.2f} >= {thresholds['tau_grid']}",
            "priority": 1
        }

    # R2: Trazado Vectorial de Diagramas de Flujo (Prioridad 2)
    if features.get("dwg_count", 0) >= thresholds["tau_dwg"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R2_VECTOR_FLOWCHART",
            "trigger": f"dwg_count={features.get('dwg_count', 0)} >= {thresholds['tau_dwg']}",
            "priority": 2
        }

    # R3: Solapamiento Horizontal Paralelo (Prioridad 3)
    if features.get("parallel_overlap", False):
        return {
            "selected_path": "DOCLING",
            "rule_id": "R3_PARALLEL_OVERLAP",
            "trigger": "parallel_overlap=TRUE",
            "priority": 3
        }

    # R4: Código y Pseudocódigo Anidado (Prioridad 4)
    if (features.get("code_block_density", 0.0) >= thresholds["tau_code"] and
        features.get("indented_blocks", 0) >= thresholds["tau_indent"]):
        return {
            "selected_path": "DOCLING",
            "rule_id": "R4_STRUCTURED_CODE",
            "trigger": f"code_density={features.get('code_block_density', 0.0):.2f} & indent={features.get('indented_blocks', 0)}",
            "priority": 4
        }

    # R5: Líderes de Puntos (Índices y Sumarios) (Prioridad 5)
    if features.get("dot_leader_count", 0) >= thresholds["tau_dots"]:
        return {
            "selected_path": "DOCLING",
            "rule_id": "R5_DOT_LEADERS_TOC",
            "trigger": f"dot_leader_count={features.get('dot_leader_count', 0)} >= {thresholds['tau_dots']}",
            "priority": 5
        }

    # R0: Camino Rápido por Defecto (Prioridad 0)
    return {
        "selected_path": "PYMUPDF",
        "rule_id": "R0_FAST_DEFAULT",
        "trigger": "No complex structural signals detected",
        "priority": 0
    }
```

---

## 4. INVARIANTES DE OPERACIÓN

1. **Determinismo Estricto:** Dados los mismos features $F_1 \dots F_6$, la decisión es $100\%$ determinista y reproducible.
2. **Explicabilidad Total:** Cada decisión emite `rule_id`, `trigger` y `priority`.
3. **Cero Dependencia de Red y Cero Modelos Opacos:** No emplea clasificadores ML, redes neuronales ni embeddings para la decisión de routing.
4. **Presupuesto de Inspección:** La inspección completa de features insume $< 10.0\text{ ms}$ en CPU ordinaria.
