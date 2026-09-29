# Gate 2 — Revisión semántica propuesta de GS2-FUN-116…120

**Estado:** propuesta técnica; pendiente de aceptación del usuario.  
**Fecha:** 2026-09-28  
**Grupo:** `fundamentos` / `punteros_dobles` / `retrieval_citation`.

## Evidencia leída

Se leyeron las cinco consultas completas y las dos referencias completas en
SQLite read-only. Ambas existen y sus fuentes figuran actualmente en la ACL
de `NB-SEC-01-C-PTR`, pero la pertenencia a ACL no demuestra relevancia.

- `chk_776399a65bec_105_1` (`Programación en C para Principiantes`, p. 105)
  muestra un parámetro `int*` que recibe la dirección de una variable del
  caller y escribe allí una suma. Es contexto relacionado con modificar datos
  visibles por el caller, pero no demuestra `T**` ni el cambio de la dirección
  almacenada en una variable puntero. El chunk termina al comenzar otro ejemplo.
- `chk_bed831d843c0_440_1` (`Fundamentos de Sistemas de Bases de Datos`,
  p. 440) trata hashing de archivos, cubos de desbordamiento y punteros a
  registros/bloques. La aparición de punteros en ese dominio no cubre el
  concepto de C preguntado.

## Propuestas independientes por par

| Consulta | `…105_1` — parámetro `int*` de salida | `…440_1` — hashing/almacenamiento |
|---|---:|---:|
| `GS2-FUN-116` — uso de `T**` | **1** — contexto relacionado, pero no muestra doble indirección | **0** — contexto semánticamente ajeno |
| `GS2-FUN-117` — explicación formal | **1** — ejemplo de `int*`, no mecanismo formal `T**` | **0** — no explica punteros dobles en C |
| `GS2-FUN-118` — bibliografía canónica de SO | **1** — fuente identificada como introducción a C, además de no mostrar `T**` | **0** — bases de datos/hash; no satisface tema ni encuadre |
| `GS2-FUN-119` — mecanismo y fundamentos | **1** — no cubre doble indirección y el ejemplo siguiente está truncado | **0** — hashing en disco, sin mecanismo de `T**` |
| `GS2-FUN-120` — implicancias de diseño de sistemas | **1** — no desarrolla `T**` ni sus implicancias sistémicas | **0** — uso de punteros en otro dominio, sin apoyo a la consulta |

## Relevancia e independencia

Las referencias proceden de dos fuentes y páginas distintas, pero solo el
pasaje de C es marginalmente adyacente al tema. La diversidad de fuentes no
debe convertirse en “dos evidencias independientes”: la segunda fuente no es
pertinente al objetivo. El grado mide la relevancia de cada chunk para cada
consulta, no la diversidad del conjunto.

## Estado de autoridad

Los grados y decisiones `EXCLUDE_FROM_POSITIVE_QRELS` son propuestas, no
decisiones aceptadas. Las cinco decisiones canónicas de consulta siguen
vacías y los diez pares qrel esperan aceptación; los qrels históricos siguen
`PENDING`. No se modificaron el registro explícito, el dataset, los qrels ni
la ACL, y no se ejecutó retrieval.

El [JSON detallado](./gate2_v2400_review_batch_fun_116_120_adjudication_2026-09-28.json)
conserva el razonamiento independiente de cada par y sus limitaciones.
