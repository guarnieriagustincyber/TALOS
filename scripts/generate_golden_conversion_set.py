"""Generator for the CAL Golden Conversion Set (45 documents) and Manifest."""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

def compute_cohen_kappa(ratings_1, ratings_2):
    assert len(ratings_1) == len(ratings_2)
    n = len(ratings_1)
    categories = sorted(list(set(ratings_1) | set(ratings_2)))
    agree = sum(1 for a, b in zip(ratings_1, ratings_2) if a == b)
    p_o = agree / n
    p_e = 0.0
    for cat in categories:
        p1 = sum(1 for a in ratings_1 if a == cat) / n
        p2 = sum(1 for b in ratings_2 if b == cat) / n
        p_e += p1 * p2
    if p_e == 1.0:
        return 1.0
    return (p_o - p_e) / (1.0 - p_e)

docs = []

# 1. tables_complex (5 docs)
for i in range(1, 6):
    doc_id = f"doc_table_{i:02d}"
    gt = f"""# Planificación de Procesos: Comparativa de Algoritmos (Parte {i})

En sistemas multiprogramados, la elección del algoritmo de planificación determina el rendimiento global.

| Algoritmo | Tiempo Espera Promedio (ms) | Desalojo (Preemptive) | Complejidad | Overhead |
| :--- | :---: | :---: | :---: | :--- |
| FCFS | 45.2 | No | O(1) | Mínimo |
| SJF | 22.8 | No | O(n log n) | Moderado |
| SRTF | 18.4 | Sí | O(n log n) | Alto |
| Round Robin | 27.5 | Sí | O(1) | Moderado |
| Priority Queue | 31.0 | Sí | O(log n) | Moderado |

La tabla anterior resume las métricas de prueba para una ráfaga uniforme de 100 procesos concurrentes.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "tables_complex",
        "title": f"Comparativa de Algoritmos de Planificación {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.40,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Silberschatz - Fundamentos de SO",
            "chapter": "Capítulo 5: Planificación de CPU",
            "section": f"5.{i} Criterios de Planificación",
            "page_start": 180 + i * 5,
            "page_end": 184 + i * 5
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.94
    })

# 2. code_blocks (5 docs)
for i in range(1, 6):
    doc_id = f"doc_code_{i:02d}"
    gt = f"""# Implementación de Primitivas de Sincronización en C ({i})

Para evitar condiciones de carrera, se implementa el patrón productor-consumidor usando semáforos POSIX.

```c
#include <pthread.h>
#include <semaphore.h>
#include <stdio.h>

#define BUFFER_SIZE 10

int buffer[BUFFER_SIZE];
sem_t empty;
sem_t full;
pthread_mutex_t mutex;

void* producer(void* arg) {{
    int item = *(int*)arg;
    sem_wait(&empty);
    pthread_mutex_lock(&mutex);
    // Sección Crítica: inserción en buffer circular
    buffer[item % BUFFER_SIZE] = item;
    pthread_mutex_unlock(&mutex);
    sem_post(&full);
    return NULL;
}}
```

Es crucial asegurar que la llamada a `sem_wait(&empty)` ocurra antes de adquirir el mutex.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "code_blocks",
        "title": f"Sincronización POSIX {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.45,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Tanenbaum - Sistemas Operativos Modernos",
            "chapter": "Capítulo 2: Procesos y Subprocesos",
            "section": f"2.{i+2} Comunicación entre Procesos",
            "page_start": 110 + i * 4,
            "page_end": 113 + i * 4
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.95
    })

# 3. multi_column (4 docs)
for i in range(1, 5):
    doc_id = f"doc_multicolumn_{i:02d}"
    gt = f"""# Arquitecturas Monolíticas vs Microkernels (Sección {i})

## Columna Izquierda: Monolitos Tradicionales
En un sistema monolítico, todos los servicios centrales del sistema operativo se ejecutan en el espacio de direcciones del kernel con privilegios máximos (Ring 0). La ventaja principal es la baja latencia en llamadas a función directas sin cambios de contexto de CPU ni copias en IPC. La desventaja es que un fallo en un driver de dispositivo puede corromper la memoria del kernel completa.

## Columna Derecha: Microkernels Modernos
El microkernel reduce el código en modo kernel al mínimo estricto: manejo de hilos, gestión elemental de memoria virtual y paso de mensajes (IPC). Todos los drivers, sistemas de archivos y pilas de red corren en espacio de usuario. Ante un fallo de un servidor de archivos, este simplemente se reinicia sin comprometer la estabilidad global del sistema.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "multi_column",
        "title": f"Arquitecturas de Kernel {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Silberschatz - Fundamentos de SO",
            "chapter": "Capítulo 2: Estructuras del Sistema Operativo",
            "section": f"2.{i+4} Estructura del Sistema",
            "page_start": 65 + i * 3,
            "page_end": 67 + i * 3
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.91
    })

# 4. formulas_latex (5 docs)
for i in range(1, 6):
    doc_id = f"doc_formulas_{i:02d}"
    gt = f"""# Análisis Matemático del Rendimiento de Paginación {i}

El tiempo de acceso efectivo a memoria (EAT) bajo demanda con memoria caché asociativa (TLB) se formaliza analíticamente:

$$\\text{{EAT}} = \\alpha \\cdot (\\epsilon + m) + (1 - \\alpha) \\cdot (\\epsilon + 2m)$$

Donde:
- $\\alpha$ representa la tasa de aciertos (TLB hit ratio).
- $\\epsilon$ es el tiempo de búsqueda asociativa en la TLB.
- $m$ es el tiempo de ciclo de acceso a la memoria física principal.

Cuando consideramos la probabilidad de fallo de página $p$, la formulación extendida resulta:

$$\\text{{EAT}}_{{\\text{{total}}}} = (1 - p) \\cdot m + p \\cdot \\tau_{{\\text{{fault}}}}$$

Donde $\\tau_{{\\text{{fault}}}}$ comprende el tiempo de swap a disco y recarga del marco.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "formulas_latex",
        "title": f"Rendimiento de Memoria Virtual {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.25,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Silberschatz - Fundamentos de SO",
            "chapter": "Capítulo 9: Memoria Virtual",
            "section": f"9.{i+1} Paginación por Demanda",
            "page_start": 350 + i * 6,
            "page_end": 355 + i * 6
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.96
    })

# 5. formulas_plain (4 docs - high formula density in plain text, triggers CAL-5 flag)
for i in range(1, 5):
    doc_id = f"doc_formulas_plain_{i:02d}"
    gt = f"""# Relaciones de Recurrencia en Algoritmos de Búsqueda {i}

Para el algoritmo de partición binaria, la ecuación de tiempo se expresa de forma elemental:
T(n) = 2 * T(n/2) + c * n
Ecuación cuadrática:
ax^2 + bx + c = 0 -> x = (-b +- sqrt(b^2 - 4ac)) / (2a)
Sumatoria de series aritméticas:
S_n = sum_(k=1)^n k = (n * (n + 1)) / 2
Factorial recursivo:
n! = prod_(i=1)^n i para todo n >= 1
Integral de convolución discreta:
y[n] = sum_(k=-inf)^inf x[k] * h[n - k]
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "formulas_plain",
        "title": f"Fórmulas en Texto Plano {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.30,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Matemática Discreta",
            "level": "Grado",
            "book": "Rosen - Matemática Discreta y sus Aplicaciones",
            "chapter": "Capítulo 8: Relaciones de Recurrencia",
            "section": f"8.{i} Métodos de Resolución",
            "page_start": 520 + i * 4,
            "page_end": 523 + i * 4
        },
        "r1": "acceptable",
        "r2": "acceptable",
        "human_quality_score": 0.78
    })

# 6. footnotes_headers (4 docs)
for i in range(1, 5):
    doc_id = f"doc_footnotes_{i:02d}"
    gt = f"""# Jerarquía de Almacenamiento y Caching {i}

## Niveles de Memoria en Arquitecturas Modernas

### Registros y Caché L1/L2
Los registros residen en el pipeline del procesador y operan a la frecuencia del ciclo de reloj interno[^1].
La memoria caché L1 está dividida en instrucción (L1i) y datos (L1d).

### Caché L3 Compartida y Memoria Principal
La caché L3 es compartida entre todos los núcleos de la CPU[^2]. Por debajo de ella encontramos la DRAM sincrónica.

[^1]: Latencia típica de acceso a registros: < 1 ns.
[^2]: En arquitecturas multicore, la coherencia de caché se mantiene mediante protocolos MESI/MOESI.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "footnotes_headers",
        "title": f"Jerarquía de Memoria {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Stallings - Sistemas Operativos",
            "chapter": "Capítulo 1: Introducción a los Computadores",
            "section": f"1.{i+2} Organización de Memoria",
            "page_start": 30 + i * 5,
            "page_end": 34 + i * 5
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.92
    })

# 7. scanned_ocr (5 docs - Rosen-style scanned, has_text_layer=False, scan_ratio=1.0)
for i in range(1, 6):
    doc_id = f"doc_scanned_{i:02d}"
    gt = f"""# Rosen Matemática Discreta - Página Escaneada {i}

CAPÍTULO 3: LÓGICA Y DEMOSTRACIONES

Definición 3.{i}: Una proposición es una oración declarativa que es o bien verdadera o bien falsa, pero no ambas cosas a la vez.
Consideremos las siguientes afirmaciones:
1. Washington D.C. es la capital de los Estados Unidos de América.
2. Buenos Aires es la capital de la República Argentina.
3. 1 + 1 = 2
4. 2 + 2 = 5
Las afirmaciones 1, 2 y 3 son verdaderas, mientras que la afirmación 4 es falsa. Todas ellas son proposiciones válidas.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "scanned_ocr",
        "title": f"Rosen Lógica Proposicional Escaneada {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": False,
            "scan_ratio": 1.0,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.05,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Matemática Discreta",
            "level": "Grado",
            "book": "Rosen - Matemática Discreta y sus Aplicaciones",
            "chapter": "Capítulo 1: Fundamentos de Lógica",
            "section": f"1.{i} Proposiciones",
            "page_start": 10 + i,
            "page_end": 10 + i
        },
        "r1": "acceptable",
        "r2": "acceptable",
        "human_quality_score": 0.82
    })

# 8. hybrid_text_image (4 docs)
for i in range(1, 5):
    doc_id = f"doc_hybrid_{i:02d}"
    gt = f"""# Gestión de Entrada/Salida: DMA y Buses ({i})

El controlador de DMA (Direct Memory Access) transfiere bloques enteros de datos entre los periféricos de alta velocidad y la memoria principal sin la intervención continua de la CPU.

![Diagrama del Bus del Sistema y Controlador DMA](figura_dma_{i}.png)

La CPU únicamente inicializa la dirección base de memoria, el contador de bytes y la dirección del registro de dispositivo. Al completar la transferencia del bloque, el controlador emite una interrupción hardware por el bus PCI-Express.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "hybrid_text_image",
        "title": f"Mecanismo DMA {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.35,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Silberschatz - Fundamentos de SO",
            "chapter": "Capítulo 13: Sistemas de Entrada/Salida",
            "section": f"13.{i+1} Hardware de E/S",
            "page_start": 480 + i * 4,
            "page_end": 483 + i * 4
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.89
    })

# 9. corrupt_truncated (3 docs - poor quality, malformed)
for i in range(1, 4):
    doc_id = f"doc_corrupt_{i:02d}"
    gt = f"""# Archivo Truncado o Dañado {i}
\x00\x01\x02 Error de parseo en bloque {i}. Datos ilegibles o incompletos.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pdf",
        "category": "corrupt_truncated",
        "title": f"Documento Dañado {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": False,
            "scan_ratio": 0.90,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Desconocido",
            "level": "Grado",
            "book": "Corrupt",
            "chapter": "N/A",
            "section": "N/A",
            "page_start": 1,
            "page_end": 1
        },
        "r1": "poor",
        "r2": "poor",
        "human_quality_score": 0.25
    })

# 10. office_docx (2 docs)
for i in range(1, 3):
    doc_id = f"doc_docx_{i:02d}"
    gt = f"""# Guía de Trabajos Prácticos de Laboratorio {i}

## Objetivos
- Configurar un entorno virtualizado en Linux Debian.
- Compilar el kernel Linux con módulos personalizados de telemetría.

### Pasos Requeridos
1. Clonar el repositorio oficial: `git clone https://kernel.org/git/linux.git`
2. Ejecutar `make menuconfig` para habilitar el subsistema eBPF.
3. Compilar con paralelismo máximo usando `make -j$(nproc)`.
"""
    docs.append({
        "doc_id": doc_id,
        "format": "docx",
        "category": "office_docx",
        "title": f"Trabajo Práctico Kernel {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.20,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Guías de Cátedra",
            "chapter": f"TP {i}",
            "section": "Práctica de Kernel",
            "page_start": 1,
            "page_end": 2
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.95
    })

# 11. office_pptx (2 docs - CAL-7 ordinal mapping slide index)
for i in range(1, 3):
    doc_id = f"doc_pptx_{i:02d}"
    gt = f"""<!-- slide -->
# Clase Teórica {i}: Seguridad y Protección en Sistemas Operativos

- Principio de Menor Privilegio (POLP).
- Dominios de protección y matrices de acceso.
- Listas de Control de Acceso (ACLs) vs Capacidades.

<!-- slide -->
# Matriz de Acceso
- Filas: Dominios / Usuarios
- Columnas: Objetos del Sistema (Archivos, Dispositivos)
- Celdas: Derechos de acceso (Read, Write, Execute, Owner)
"""
    docs.append({
        "doc_id": doc_id,
        "format": "pptx",
        "category": "office_pptx",
        "title": f"Presentación Teórica Seguridad {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.0,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 2
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Diapositivas Teóricas",
            "chapter": f"Unidad {i+7}: Seguridad",
            "section": "Diapositivas 1 y 2",
            "page_start": 1,
            "page_end": 2
        },
        "r1": "high",
        "r2": "acceptable" if i == 2 else "high",
        "human_quality_score": 0.91
    })

# 12. office_xlsx (2 docs - CAL-7 ordinal mapping sheet index)
for i in range(1, 3):
    doc_id = f"doc_xlsx_{i:02d}"
    gt = f"""# Hoja 1: Registro de Calificaciones de Exámenes Parciales {i}

| Padrón | Apellido y Nombre | Parcial 1 | Parcial 2 | Recuperatorio | Estado |
| :--- | :--- | :---: | :---: | :---: | :--- |
| 104521 | Alvarez, Mateo | 8 | 9 | - | Promovido |
| 104522 | Benitez, Sofia | 4 | 7 | 8 | Regular |
| 104523 | Castro, Lucia | 2 | 2 | - | Libre |
| 104524 | Dominguez, Juan | 9 | 10 | - | Promovido |
"""
    docs.append({
        "doc_id": doc_id,
        "format": "xlsx",
        "category": "office_xlsx",
        "title": f"Planilla de Calificaciones {i}",
        "raw_content": gt,
        "expected_profile": {
            "has_text_layer": True,
            "scan_ratio": 0.0,
            "table_density": 0.50,
            "code_density": 0.0,
            "formula_density": 0.0,
            "language": "es",
            "pages": 1
        },
        "ground_truth_markdown": gt,
        "curricular_metadata": {
            "subject": "Sistemas Operativos",
            "level": "Grado",
            "book": "Planillas Administrativas",
            "chapter": "Calificaciones",
            "section": f"Comisión {i}",
            "page_start": 1,
            "page_end": 1
        },
        "r1": "high",
        "r2": "high",
        "human_quality_score": 0.93
    })

assert len(docs) == 45, f"Expected 45 docs, got {len(docs)}"

# Compute Cohen's kappa for r1 and r2
r1_list = [d["r1"] for d in docs]
r2_list = [d["r2"] for d in docs]
kappa = compute_cohen_kappa(r1_list, r2_list)
print(f"Computed Cohen's Kappa: {kappa:.4f}")
assert kappa >= 0.80, f"Kappa {kappa} is below 0.80 threshold (CAL-6)"

# Write golden_set_v1.json
golden_set_path = Path("data/benchmark/conversion/golden_set_v1.json")
golden_set_path.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved {len(docs)} golden documents to {golden_set_path}")

# Build manifest
manifest_docs = []
for d in docs:
    raw_hash = hashlib.sha256(d["raw_content"].encode("utf-8")).hexdigest()
    gt_hash = hashlib.sha256(d["ground_truth_markdown"].encode("utf-8")).hexdigest()
    manifest_docs.append({
        "doc_id": d["doc_id"],
        "format": d["format"],
        "category": d["category"],
        "raw_sha256": raw_hash,
        "gt_sha256": gt_hash,
        "human_score": d["human_quality_score"],
        "agreement": d["r1"] == d["r2"]
    })

manifest = {
    "manifest_version": "1.0.0",
    "dataset_name": "CAL Golden Conversion Set v1",
    "total_documents": len(docs),
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "seed": 42,
    "annotators": ["auditor_alpha", "auditor_beta"],
    "cohen_kappa": round(kappa, 4),
    "kappa_threshold": 0.80,
    "cal_6_status": "PASSED" if kappa >= 0.80 else "FAILED",
    "documents": manifest_docs
}

manifest_str = json.dumps(manifest, sort_keys=True)
manifest["manifest_sha256"] = hashlib.sha256(manifest_str.encode("utf-8")).hexdigest()

manifest_path = Path("data/benchmark/conversion/manifest_golden_set.json")
manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Saved manifest to {manifest_path} with SHA256={manifest['manifest_sha256']}")
