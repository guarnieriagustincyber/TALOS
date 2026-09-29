# Gate 2 — Revisión semántica propuesta de GS2-SYN-018…020

**Estado:** propuesta técnica; pendiente de aceptación explícita.  
**Fecha:** 2026-09-28  
**Grupo:** `sintaxis_codigo` / `pipe` / `retrieval_citation`.

## Distinciones semánticas del lote

Los qrels mezclan tres usos distintos de “pipe”:

1. La tubería IPC de Unix entre procesos, descrita en *Operating Systems:
   Internals and Design Principles*, p. 305.
2. El operador de shell `|` para encadenar comandos, en *Seguridad en Redes*,
   pp. 197–198.
3. La metáfora de un *pipe* de red/enlace en *Computer Networking: A
   Top-Down Approach*, p. 287.

Solo el primer uso explica la tubería IPC de la pregunta. El operador de shell
es contexto relacionado, pero no equivale a la interfaz `pipe(2)`; el uso
metafórico de redes es irrelevante para este syscall.

## Propuestas por query/qrel

| Consulta | Referencia | Grado histórico | Propuesta | Justificación |
|---|---|---:|---:|---|
| `SYN-018` | `seguridad-en-redes.pdf:p198:c0002` | 3 | **1** | Ejemplo de `ls \| awk`; operador de shell, no interfaz `pipe(2)`. |
| `SYN-018` | `seguridad-en-redes.pdf:p197:c0004` | 2 | **1** | Encadenamiento de comandos en shell, contexto marginal. |
| `SYN-018` | `chk_76e248a62974_305_1` | 1 | **2** | Explica FIFO entre procesos, bloqueo y pipes nombrados/no nombrados; no da la sintaxis de llamada. |
| `SYN-018` | `seguridad-en-redes.pdf:p336:c0003` | 1 | **1** | Mención pasajera de enviar logs a otro programa mediante pipe. |
| `SYN-018` | `Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf:p287:c0000` | 1 | **0** | “Pipe” es una metáfora de capacidad de enlace de red. |
| `SYN-019` | `seguridad-en-redes.pdf:p198:c0002` | 3 | **1** | Ejemplo de pipeline de shell, no explica el mecanismo POSIX/Linux. |
| `SYN-019` | `seguridad-en-redes.pdf:p197:c0004` | 2 | **1** | Explica `|` y el orden de ejecución del shell, no la syscall. |
| `SYN-019` | `seguridad-en-redes.pdf:p336:c0003` | 1 | **1** | Solo identifica una ruta hacia otro programa. |
| `SYN-019` | `chk_76e248a62974_305_1` | 1 | **2** | Evidencia sustantiva de operación IPC, aunque no cubre el contrato completo de API. |
| `SYN-019` | `Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf:p287:c0000` | 1 | **0** | Metáfora de transporte/capacidad de red, fuera del concepto pedido. |
| `SYN-020` | `seguridad-en-redes.pdf:p198:c0002` | 3 | **1** | El ejemplo de shell no aporta parámetros ni retornos de `pipe(2)`. |
| `SYN-020` | `seguridad-en-redes.pdf:p197:c0004` | 2 | **1** | Trata el operador del shell, no el contrato de la API. |
| `SYN-020` | `seguridad-en-redes.pdf:p336:c0003` | 1 | **0** | Mención pasajera sin datos de interfaz. |
| `SYN-020` | `chk_76e248a62974_305_1` | 1 | **1** | Describe el mecanismo, pero no los parámetros exactos ni valores de retorno. |
| `SYN-020` | `Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf:p287:c0000` | 1 | **0** | Uso metafórico en redes; sin información de `pipe(2)`. |

## Cobertura diagnóstica de facetas (umbral ≥2)

- **SYN-018:** el pasaje de sistemas operativos cubre el comportamiento IPC;
  queda descubierta la faceta de sintaxis/interfaz de la syscall. La sintaxis
  del operador de shell no satisface esa faceta.
- **SYN-019:** el pasaje de sistemas operativos respalda sustantivamente las
  dos facetas operativas separadas: mecanismo FIFO entre procesos y
  comportamiento de bloqueo/uso compartido. No se interpreta esto como
  cobertura de una firma o contrato de retorno de `pipe(2)`, que la consulta
  no pide explícitamente.
- **SYN-020:** quedan descubiertas las facetas de parámetros y valores de
  retorno. Ninguno de los cinco pasajes cubre esas dimensiones.

Esta separación es diagnóstica y acotada a la pregunta: el helper no adjudica
independencia, suficiencia canónica ni validez de la consulta.

## Fuentes e independencia

Hay tres `source_id`, pero los dos ejemplos de shell y la mención sobre logs
provienen de *Seguridad en Redes*. Solo *Operating Systems* proporciona
evidencia sustantiva del comportamiento de una tubería IPC, y la ocurrencia de
Kurose es una metáfora ajena al tema. Cinco qrels no representan cinco
evidencias independientes ni cinco fuentes pertinentes.

## Estado decisional y límites

Las quince propuestas permanecen no canónicas. Las decisiones de consulta y
qrel canónicas siguen vacías; no se alteraron golden set, qrels históricos,
registro explícito ni ACL. La revisión se limitó a los quince pares existentes
y a los cinco pasajes únicos leídos desde SQLite en modo solo lectura. No se
buscó evidencia de reemplazo ni se ejecutó retrieval.

El [JSON detallado](./gate2_v2400_review_batch_syn_018_020_adjudication_2026-09-28.json)
incluye textos de consulta, facetas analíticas, decisión y justificación por
referencia, y los diagnósticos de cobertura.
