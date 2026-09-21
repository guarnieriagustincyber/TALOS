# Golden Set v1 — Casos conocidos

Documento vivo de casos de calibración. Cada caso fija el comportamiento
esperado para distinguir falla real de diseño. Creado en `feat(f3)`
(commit a369786) como base del slice `feat(eval)`.

## CASO K1: queries de SO en notebook fase0-soc

Ejemplo: "¿Cómo funciona el scheduling SJF?", "¿Y si dos procesos empatan en burst?"

- **Comportamiento esperado:** retrieval grounded con citas reales +
  `bkt_context.fallback=true` (kc_id null, p_L=0.5).
- **NO es un fallo:** el catálogo KC de fase0-soc contiene los 8 tramos de
  programación/punteros; no hay KCs de sistemas operativos. El fallback
  honesto expone el desajuste catálogo↔corpus (pendiente: KCs de SO).
- **Métrica:** groundedness y citas válidas. **No** medir exactitud de kc_id.

## CASO K2: queries de programación/punteros en fase0-soc

Ejemplo: "¿cómo uso malloc y free sin leaks?"

- **Comportamiento esperado:** `bkt_context.fallback=false` con `kc_id`
  correcto (`aritmetica_punteros`) y p_L real del KC.
- **Métrica:** además de groundedness, exactitud del `kc_id` matcheado
  (medir como accuracy sobre el golden set).

## Regla general

Un turno sin KC matcheable debe ser *visible* como tal
(`fallback=true`), nunca atribuido silenciosamente a otro KC
(el viejo fallback `kcs_list[0]` se eliminó en F3 por mentiroso).
