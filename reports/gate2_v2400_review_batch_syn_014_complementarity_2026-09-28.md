# Gate 2 — Complementariedad propuesta para GS2-SYN-014 (`execve`)

**Estado:** propuesta técnica; pendiente de aceptación del usuario.  
**Fecha:** 2026-09-28  
**Consulta:** «Explicame en detalle la sintaxis y comportamiento de execve en
programación de sistemas».

## Candidato al caso inverso

La consulta tiene dos referencias históricas que, leídas en contexto, parecen
cubrir dimensiones diferentes:

- `hacking-etico-carlos-tori.pdf:p258:c0000`, de Carlos Tori, ofrece un
  ejemplo concreto con ruta del ejecutable, `argv` y `envp`. El contexto es un
  rootkit; se propone grado **2** por la forma de invocación, no por aprobar
  ese uso.
- `chk_0aa9aa4cc0b2_373_1`, de William Stallings, explica reemplazo de la
  imagen del programa y preparación de argumentos/entorno hasta la llamada al
  sistema. Su contexto es shellcode; se propone grado **2** por aportar
  comportamiento complementario, no como referencia POSIX completa.

Los autores y libros son distintos, lo que hace plausible la independencia
documental. Ambos pasajes, sin embargo, comparten un contexto de seguridad;
la autoría independiente no demuestra por sí sola independencia intelectual.

## Suficiencia respecto de esta query y su `expected`

La consulta pide **sintaxis y comportamiento**; su `expected` incluye las
referencias de Tori y Stallings p. 373/p. 620, y la nota exige una coincidencia
canónica `execve` en el top 3.

| Requisito de la query | Evidencia | Estado |
|---|---|---|
| Sintaxis de invocación | Tori muestra `execve` con ruta, `argv` y `envp`. | Cubierto |
| Comportamiento central | Stallings explica el reemplazo/carga de la imagen, argumentos/entorno y comienzo del nuevo programa. | Cubierto |
| Identificador estricto `execve` | Ambas fuentes contienen la llamada por nombre. | Cubierto |

Con ese alcance, se propone que el conjunto es **suficiente para las facetas
centrales que esta query declara**, pendiente de aceptación del usuario. No se
afirma que sea una referencia neutral exhaustiva de POSIX ni que cubra firma
completa o valores de retorno; esos requisitos pertenecen a la variante
`SYN-016`, no a esta pregunta. El contexto de seguridad es una limitación de
encuadre, pero no deja sin cubrir una faceta explícita de esta query.

## Evaluación del resto de referencias de esta consulta

| Referencia | Grado propuesto | Motivo |
|---|---:|---|
| `chk_0aa9aa4cc0b2_620_1` | **2** | Explica carga del ejecutable en un nuevo espacio de direcciones e inicio de ejecución; mismo libro/autor que el pasaje de p. 373, así que es apoyo adicional, no otra fuente independiente. |
| `chk_0aa9aa4cc0b2_380_1` | **0** | Mención en una lista, sin sintaxis ni semántica. |
| `Computer_Security_Stallings_3rd_Ed.pdf:p820:c0001` | **0** | Entrada de índice solamente. |

## Relevancia, independencia, complementariedad y suficiencia

- **Relevancia individual:** dos pasajes alcanzan grado propuesto 2; un
  pasaje del mismo libro añade conducta del proceso; las otras referencias
  son una mención y una entrada de índice.
- **Independencia:** los dos pasajes de grado 2 proceden de autores y obras
  diferentes. Es independencia de procedencia aparente, no prueba concluyente
  de independencia intelectual; ambos pertenecen a literatura de seguridad.
- **Complementariedad:** un pasaje aporta la forma de invocación; el otro,
  reemplazo de imagen y preparación de argumentos/entorno.
- **Suficiencia del conjunto:** propuesta **suficiente para sintaxis +
  comportamiento central de SYN-014**, pendiente de aceptación; no significa
  cobertura exhaustiva de API/POSIX ni de los requisitos más estrictos de
  SYN-016.

## Autoridad

La decisión de consulta sigue pendiente y los cinco qrels históricos siguen
`PENDING`. Los grados y decisiones aquí son propuestas: no modifican el
registro explícito, el golden set, los qrels ni la ACL. No se ejecutó
retrieval.

El [JSON detallado](./gate2_v2400_review_batch_syn_014_complementarity_2026-09-28.json)
incluye autores, alcance por referencia, límites y evaluación de independencia.
El caso se conserva también como fixture ejecutable de referencia en
[gate2_syn_014_facet_coverage.json](../tests/fixtures/gate2_syn_014_facet_coverage.json);
la función de resumen de cobertura y sus pruebas verifican el mapeo de
evidencia con grado propuesto ≥2 a cada faceta. Ese cálculo no adjudica
independencia, complementariedad ni estado canónico.

La prueba de generalización se complementa con la fixture diagnóstica de
[`GS2-CMP-011`](../tests/fixtures/gate2_cmp_011_facet_coverage.json): el
candidato de semáforo (grado 2) cubre su faceta, mientras que el candidato
de mutex (grado 1) no alcanza el umbral para propiedad del hilo. Ambos chunks
pertenecen a la misma fuente; la fixture no los presenta como corroboración
independiente ni crea decisiones nuevas.
