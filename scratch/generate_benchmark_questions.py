import json
from pathlib import Path

categories_spec = [
    {
        "category": "explicit_response",
        "name": "Respuesta explícita",
        "count": 20,
        "prefix": "Q0",
        "start": 1,
        "expected_behavior": "answer_with_citations",
        "dimensions": ["evidence_precision", "citation_correctness", "long_context_retrieval", "ttft", "conversational_naturalness"],
        "queries": [
            ("¿Qué es starvation en el algoritmo de scheduling Shortest Job First (SJF)?", ["Silberschatz", "Tanenbaum"], "Postergación indefinida de procesos largos ante la llegada continua de procesos cortos."),
            ("¿Cuál es la diferencia entre un proceso y un hilo a nivel de espacio de direcciones?", ["Silberschatz"], "Los hilos comparten el mismo espacio de direcciones y recursos del proceso, mientras que cada proceso tiene memoria aislada."),
            ("¿Qué función cumple el Translation Lookaside Buffer (TLB) en la paginación?", ["Silberschatz", "Patterson"], "Caché de hardware de alta velocidad que almacena mapeos virtuales a físicos recientes para evitar accesos a la tabla de páginas en memoria."),
            ("¿Qué es un puntero en lenguaje C según Kernighan & Ritchie?", ["Kernighan & Ritchie"], "Una variable que contiene la dirección de memoria de otra variable."),
            ("¿Cuáles son las 4 condiciones de Coffman necesarias para que ocurra un interbloqueo (deadlock)?", ["Silberschatz", "Tanenbaum"], "Exclusión mutua, retención y espera, no apropiación, y espera circular."),
            ("¿En qué consiste la técnica de Copy-on-Write (COW) durante la llamada fork()?", ["Silberschatz", "Love"], "Padre e hijo comparten páginas físicas en solo lectura hasta que alguno escribe, duplicando solo en ese instante."),
            ("¿Cuál es el propósito del registro Program Counter (PC) en la CPU?", ["Tanenbaum", "Patterson"], "Almacena la dirección de memoria de la próxima instrucción a ejecutar por el procesador."),
            ("¿Qué es una interrupción por software o trampa (trap) en un sistema operativo?", ["Silberschatz"], "Instrucción ejecutada por software que transfiere el control al kernel en modo privilegiado."),
            ("¿Qué diferencia existe entre fragmentación interna y fragmentación externa en memoria?", ["Silberschatz"], "Interna: espacio desperdiciado dentro de un marco o bloque asignado. Externa: espacio libre total suficiente pero no contiguo."),
            ("¿Qué garantiza la exclusión mutua en una sección crítica?", ["Silberschatz", "Dijkstra"], "Que a lo sumo un solo proceso o hilo pueda estar ejecutando código en la sección crítica simultáneamente."),
            ("¿Cómo opera el algoritmo Round Robin y qué rol juega el quantum de tiempo?", ["Silberschatz", "Tanenbaum"], "Asigna la CPU a cada proceso por un lapso fijo (quantum) de forma cíclica y expropiativa."),
            ("¿Qué representa el inodo (inode) en un sistema de archivos UNIX?", ["Bach", "Silberschatz"], "Estructura de datos que almacena metadatos y punteros a bloques de datos de un archivo, excluyendo su nombre."),
            ("¿Qué es el fenómeno de anomalía de Belady en reemplazo de páginas?", ["Silberschatz"], "Caso en algoritmos como FIFO donde aumentar los marcos de memoria física produce más fallos de página."),
            ("¿Cómo funciona una variable de condición (condition variable) en monitores?", ["Silberschatz", "Hoare"], "Permite a un hilo suspenderse atómicamente cediendo el cerrojo hasta ser despertado por signal/broadcast."),
            ("¿Qué diferencia a una llamada al sistema (syscall) de una llamada a función ordinaria?", ["Silberschatz", "Tanenbaum"], "Syscall cambia el nivel de privilegio de usuario a kernel mediante un trap en hardware; llamada ordinaria opera en el mismo nivel."),
            ("¿Qué almacena el stack frame o registro de activación durante una llamada recursiva?", ["Kernighan & Ritchie", "Patterson"], "Dirección de retorno, parámetros, registros preservados y variables locales de la invocación."),
            ("¿Qué es el Thrashing (hiperpaginación) en un sistema con memoria virtual?", ["Silberschatz"], "Estado donde el sistema pasa más tiempo paginando páginas entre disco y memoria que ejecutando instrucciones."),
            ("¿Cuál es el principio de localidad temporal y espacial en jerarquía de memoria?", ["Patterson & Hennessy"], "Temporal: datos accedidos recientemente tenderán a accederse pronto. Espacial: datos contiguos a los accedidos tenderán a usarse pronto."),
            ("¿Qué es un semáforo contador de Dijkstra y cuáles son sus operaciones atómicas?", ["Dijkstra", "Silberschatz"], "Variable entera manipulada exclusivamente mediante operaciones atómicas wait/P (decremento) y signal/V (incremento)."),
            ("¿Qué es el modo dual de operación (usuario vs kernel) y cómo previene accesos indebidos?", ["Silberschatz"], "Modo de hardware que restringe instrucciones privilegiadas e inspecciona accesos a memoria según el bit de modo.")
        ]
    },
    {
        "category": "distributed_response",
        "name": "Respuesta distribuida",
        "count": 20,
        "prefix": "Q0",
        "start": 21,
        "expected_behavior": "answer_with_citations",
        "dimensions": ["evidence_precision", "citation_correctness", "long_context_retrieval", "ttft", "conversational_naturalness"],
        "queries": [
            ("¿Cómo se manejan los page faults a lo largo de todo el flujo desde la excepción MMU hasta el reemplazo de disco?", ["Silberschatz"], "Secuencia completa de trap, verificación de validez en PCB, búsqueda de marco libre, E/S de disco, actualización de tabla y reanudación."),
            ("¿Cómo evoluciona el ciclo de vida de un proceso desde su creación hasta su terminación en el PCB?", ["Silberschatz", "Tanenbaum"], "Transiciones New -> Ready -> Running -> Waiting -> Terminated y limpieza de recursos."),
            ("¿Cómo interactúan el planificador de corto, mediano y largo plazo en sistemas multiprogramados?", ["Silberschatz"], "Largo: grado de multiprogramación; Mediano: swapping de procesos; Corto: asignación inmediata de CPU."),
            ("¿Cómo se propaga una señal POSIX desde el emisor kernel hasta el manejador de usuario?", ["Love", "Stevens"], "Generación, marcado en PCB, entrega al retorno al espacio de usuario y ejecución en stack frame ad-hoc."),
            ("¿Cómo se construye la jerarquía de tablas de páginas multinivel para ahorrar espacio en 64 bits?", ["Silberschatz", "Patterson"], "Paginación en 4 o 5 niveles dividiendo la dirección virtual en offsets de página, asignando solo tablas activas."),
            ("¿Cómo se sincronizan las entradas de directorio y los bloques de datos al escribir en disco?", ["Silberschatz", "Bach"], "Estructuración de journaling o escrituras síncronas/asíncronas garantizando integridad del metadata."),
            ("¿Cómo se implementa el paso de mensajes sincrónico versus asincrónico en sistemas distribuidos?", ["Coulouris", "Tanenbaum"], "Sincrónico bloquea remitente y receptor (rendezvous); asincrónico utiliza buffers intermedios desacoplados."),
            ("¿Cómo colaboran el hardware de paginación y el sistema operativo para implementar memoria compartida?", ["Silberschatz"], "Mapeo de las mismas entradas de tabla de páginas virtuales de distintos procesos al mismo marco físico."),
            ("¿Cómo se detectan y resuelven los ciclos en un grafo de asignación de recursos (RAG)?", ["Silberschatz"], "Búsqueda de ciclos determinista con algoritmos de grafos y terminación/expropiación de procesos seleccionados."),
            ("¿Cómo se gestiona el buffer caché del sistema de archivos y cuándo se realiza flush a almacenamiento persistente?", ["Bach", "Love"], "Páginas dirty en caché sincronizadas por demonios de kernel periódicamente o ante fsync."),
            ("¿Cómo interactúan las interrupciones de hardware con la máscara de interrupciones de la CPU?", ["Tanenbaum"], "Deshabilitación transitoria en secciones críticas de kernel o delegación en controladores APIC."),
            ("¿Cómo opera el algoritmo de banquero de Dijkstra en un entorno con múltiples tipos de recursos?", ["Dijkstra", "Silberschatz"], "Verificación previa de estado seguro comparando matrices Allocation, Max, Need y vector Available."),
            ("¿Cómo se implementa la memoria virtual paginada por demanda (demand paging) desde el boot hasta ejecución?", ["Silberschatz"], "Carga perezosa de páginas sólo cuando el proceso genera el primer fallo de página sobre la dirección."),
            ("¿Cómo maneja el kernel la conmutación de contexto (context switch) a nivel de registros y mapas de memoria?", ["Silberschatz", "Tanenbaum"], "Guardado de registros de CPU en PCB, recarga de CR3/puntero de página, y restauración del nuevo estado."),
            ("¿Cómo se organizan los niveles de consistencia en sistemas de archivos con journaling (ext4/XFS)?", ["Love", "Silberschatz"], "Modos journal (datos + metadata), ordered (metadata tras datos) y writeback (sin orden estricto)."),
            ("¿Cómo interactúa el garbage collection con la compactación de memoria en runtimes modernos?", ["Jones", "Silberschatz"], "Fase mark-sweep para identificar vivos y reubicación de punteros en compactación para eliminar fragmentación."),
            ("¿Cómo se estructuran los permisos de acceso mediante listas de control de acceso (ACL) y capacidades?", ["Silberschatz"], "ACLs vinculan sujetos a objetos en el recurso; capacidades son llaves intransferibles en posesión del sujeto."),
            ("¿Cómo se sincronizan los buffers de entrada/salida mediante DMA (Direct Memory Access)?", ["Tanenbaum", "Patterson"], "El controlador DMA transfiere bloques a RAM directamente e interrumpe a la CPU al finalizar la ráfaga."),
            ("¿Cómo se coordina el algoritmo de reloj (clock algorithm) con los bits de referencia y modificación?", ["Silberschatz"], "Puntero circular que evalúa bit de referencia: si es 1 lo apaga y avanza; si es 0 selecciona la página para reemplazo."),
            ("¿Cómo se gestiona el árbol de procesos en UNIX ante la terminación prematura de un padre (huérfanos y zombis)?", ["Stevens", "Silberschatz"], "Huérfanos son adoptados por init/systemd (PID 1); zombis retienen PCB hasta que el padre invoca wait().")
        ]
    },
    {
        "category": "cross_source",
        "name": "Cross-source",
        "count": 20,
        "prefix": "Q0",
        "start": 41,
        "expected_behavior": "synthesize_multiple_sources",
        "dimensions": ["evidence_precision", "citation_correctness", "cross_source_recall", "long_context_retrieval", "conversational_naturalness"],
        "queries": [
            ("Compará Tanenbaum vs Silberschatz en scheduling por lotes versus interactivo", ["Tanenbaum", "Silberschatz"], "Tanenbaum enfatiza throughput y turnaround en batch vs respuesta en interactivo; Silberschatz unifica la jerarquía multinivel."),
            ("Compará Silberschatz vs Stallings respecto a la prevención versus detección de deadlocks", ["Silberschatz", "Stallings"], "Silberschatz prioriza algoritmos de detección con grafos; Stallings formaliza negación de condiciones de Coffman."),
            ("Contrastá la definición de microkernel en Tanenbaum (Minix) frente a kernel monolítico en Linux según Bovet & Cesati", ["Tanenbaum", "Bovet & Cesati"], "Tanenbaum traslada drivers y servidores a espacio de usuario; Bovet enfatiza rendimiento y espacio único de Linux."),
            ("¿Qué diferencias de terminología existen entre Tanenbaum y Silberschatz al describir reemplazo de páginas Aging vs LRU aproximado?", ["Tanenbaum", "Silberschatz"], "Tanenbaum detalla registros de envejecimiento por software; Silberschatz describe bit de referencia y algoritmo de reloj."),
            ("Compará la explicación de pasaje de parámetros por valor y por referencia entre Kernighan & Ritchie y Stroustrup", ["Kernighan & Ritchie", "Stroustrup"], "K&R en C solo admite pasaje por valor (emulado con punteros); Stroustrup en C++ formaliza referencias nativas (&)."),
            ("Contrastá cómo Silberschatz y Tanenbaum clasifican hilos de usuario (ULT) frente a hilos de kernel (KLT)", ["Silberschatz", "Tanenbaum"], "Tanenbaum detalla ventajas de conmutación rápida sin kernel; Silberschatz analiza bloqueo de todo el proceso ante syscalls bloqueantes."),
            ("Compará las estructuras de inodos presentadas en Bach (Design of the UNIX OS) frente a Silberschatz", ["Bach", "Silberschatz"], "Bach detalla inodos en disco vs inodos en memoria central; Silberschatz ofrece modelo conceptual generalizado."),
            ("¿Qué discrepancias prácticas existen entre Tanenbaum y Patterson & Hennessy sobre la penalización por fallo de TLB?", ["Tanenbaum", "Patterson & Hennessy"], "Patterson evalúa impacto en CPI de hardware; Tanenbaum analiza gestión por software en arquitecturas RISC."),
            ("Compará el tratamiento de memoria compartida en POSIX vs modelo de memoria distribuida en Coulouris", ["Silberschatz", "Coulouris"], "POSIX asume memoria compartida física local; Coulouris formaliza RPC y DSM con consistencia de copias."),
            ("Contrastá la semántica de monitores de Hoare vs monitores de Mesa según Silberschatz y Tanenbaum", ["Silberschatz", "Tanenbaum"], "Hoare: signal cede la CPU inmediatamente al despertado; Mesa: el hilo que señala continúa y el despertado reevalúa en while."),
            ("Compará la taxonomía de fallos de red en Lamport frente a Tanenbaum en sistemas distribuidos", ["Lamport", "Tanenbaum"], "Lamport clasifica fallos bizantinos y orden causal; Tanenbaum clasifica caídas por timeout y particiones de red."),
            ("Contrastá la definición de sección crítica en Dijkstra (1965) frente a formalizaciones algebraicas contemporáneas", ["Dijkstra", "Raynal"], "Dijkstra plantea propiedades operativas con semáforos; modelos formales prueban invariantes de safety y liveness."),
            ("Compará la implementación del Spinlock en multiprocesadores según Love vs Silberschatz", ["Love", "Silberschatz"], "Love detalla deshabilitación de preemption local en Linux; Silberschatz presenta test-and-set abstracto."),
            ("Contrastá cómo abordan el problema de inversión de prioridad Tanenbaum vs Liu & Layland", ["Tanenbaum", "Liu & Layland"], "Tanenbaum describe herencia de prioridad básica; Liu & Layland analizan protocolo de techo de prioridad para garantías hard real-time."),
            ("Compará esquemas de asignación contigua vs enlazada vs indexada en Silberschatz vs Stallings", ["Silberschatz", "Stallings"], "Ambos coinciden en ventajas del indexado (inodo), Silberschatz profundiza en soporte para acceso directo."),
            ("¿Qué diferencias de perspectiva existen entre Tanenbaum y Stevens sobre sockets UNIX vs TCP/IP?", ["Tanenbaum", "Stevens"], "Stevens brinda tratamiento exhaustivo de la API de red; Tanenbaum contextualiza sockets dentro del modelo de capas OSI/Internet."),
            ("Compará el manejo de memoria en C según K&R con el modelo de memoria de Rust según Matsakis", ["Kernighan & Ritchie", "Matsakis"], "K&R requiere gestión manual libre de tipos; Rust impone ownership, borrowing y lifetimes verificadas en compilación."),
            ("Contrastá la semántica de fork() y exec() descrita por Rochkind frente a la especificación POSIX moderna", ["Rochkind", "Stevens"], "Rochkind documenta la génesis en UNIX V7; estándares POSIX agregan flags de herencia de descriptores y cloexec."),
            ("Compará el algoritmo de panadería de Lamport con el de Peterson para N procesos según Silberschatz vs Raynal", ["Silberschatz", "Raynal"], "Peterson requiere 2 procesos (extendible jerárquicamente); Lamport Bakery admite N procesos asignando números de turno crecientes."),
            ("Contrastá cómo clasifican ataques de buffer overflow en Aleph One vs guías de seguridad contemporáneas", ["Aleph One", "Silberschatz"], "Aleph One detalla sobreescritura de EIP en stack; defensas modernas incluyen canaries, ASLR y DEP/NX bit.")
        ]
    },
    {
        "category": "contradictions",
        "name": "Contradicciones",
        "count": 10,
        "prefix": "Q0",
        "start": 61,
        "expected_behavior": "disprove_premise_or_expose_conflict",
        "dimensions": ["evidence_precision", "citation_correctness", "cross_source_recall", "conversational_naturalness"],
        "queries": [
            ("¿En qué se contradicen estos autores sobre la sobrecarga (overhead) de rendimiento en microkernels vs kernels monolíticos?", ["Tanenbaum", "Bovet"], "Tanenbaum sostiene que IPC optimizado es insignificante; partidarios de kernels monolíticos demuestran sobrecosto de context switch."),
            ("¿Existe discrepancia en las fuentes sobre si los hilos comparten el puntero de pila (stack pointer)?", ["Silberschatz", "Kernighan & Ritchie"], "No se comparte; cada hilo posee su propia pila y registro SP, aunque comparten el heap y datos globales."),
            ("¿Qué desacuerdo existe sobre si el algoritmo de Peterson funciona directamente en hardware multicore contemporáneo sin barreras de memoria?", ["Silberschatz", "Love"], "En hardware moderno reordena lecturas/escrituras (out-of-order), requiriendo memory barriers para ser correcto."),
            ("¿Contradicen las fuentes la obligatoriedad de expulsión en la cuarta condición de Coffman?", ["Silberschatz", "Tanenbaum"], "La condición de 'no apropiación' es estricta: los recursos asignados no pueden ser quitados por la fuerza."),
            ("¿Discrepan los autores sobre la equivalencia funcional entre semáforos binarios y mutexes con ownership?", ["Silberschatz", "Love"], "Un mutex exige que solo el hilo que tomó el cerrojo pueda liberarlo; un semáforo binario puede ser liberado por cualquier hilo."),
            ("¿Se contradicen los textos sobre si la fragmentación interna es posible en sistemas con segmentación pura?", ["Silberschatz"], "La segmentación pura sólo produce fragmentación externa; la interna sólo ocurre si los segmentos son paginados."),
            ("¿Existe contradicción sobre si un proceso zombi consume recursos de memoria además de una entrada en la tabla de procesos?", ["Silberschatz", "Stevens"], "No consume memoria de código ni datos; únicamente retiene la entrada de su PCB y código de salida."),
            ("¿Qué discrepancia existe sobre el impacto de la paginación invertida en el tiempo de búsqueda sin hash anchor?", ["Silberschatz"], "Búsqueda lineal en tabla invertida es prohibitiva (O(M)); se requiere tabla hash obligatoria para mantener rendimiento."),
            ("¿Contradicen los autores la conveniencia de usar polling activo frente a interrupciones en buses de ultra alta velocidad?", ["Silberschatz", "Tanenbaum"], "En interfaces de ultra alta tasa (100GbE, NVMe), el polling programado supera a las interrupciones al evitar saturación de CPU."),
            ("¿Existe conflicto en las fuentes sobre la definición de starvation frente a deadlock?", ["Silberschatz"], "Deadlock es bloqueo mutuo circular irreversible sin intervención; starvation es retraso indefinido con posibilidad teórica de avance.")
        ]
    },
    {
        "category": "absent_information",
        "name": "Información ausente",
        "count": 10,
        "prefix": "Q0",
        "start": 71,
        "expected_behavior": "abstain",
        "dimensions": ["abstention", "evidence_precision", "ttft", "conversational_naturalness"],
        "queries": [
            ("¿Qué dice el libro sobre algoritmos de compresión cuántica en sistemas operativos qubits?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Cómo especifica el material la configuración del hypervisor VMware ESXi 8.0 en clústeres vSAN?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Cuál es la postura del autor respecto al lenguaje Swift para programación de drivers en iOS?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Cómo recomienda el texto afinar el garbage collector ZGC de Java 21 para latencias submilimétricas?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Qué instrucciones da el manual sobre la instalación de firmware UEFI en microcontroladores ESP32?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Qué análisis presenta el libro sobre redes neuronales generativas transformers dentro del kernel?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Cómo resuelve el texto el protocolo de consenso Raft en hardware neuromórfico?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Cuál es la recomendación del capítulo sobre despliegues de Kubernetes en clústeres multi-cloud?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Qué parámetros de optimización sugiere el texto para bases de datos vectoriales con HNSW?", [], "Información ausente del corpus; el sistema debe abstenerse."),
            ("¿Cómo explica el autor la síntesis de silicio para aceleradores TPU de quinta generación?", [], "Información ausente del corpus; el sistema debe abstenerse.")
        ]
    },
    {
        "category": "trick_questions",
        "name": "Preguntas capciosas",
        "count": 10,
        "prefix": "Q0",
        "start": 81,
        "expected_behavior": "disprove_premise",
        "dimensions": ["evidence_precision", "citation_correctness", "conversational_naturalness", "learning_adaptation"],
        "queries": [
            ("¿Verdad que los semáforos siempre son más rápidos que los mutex porque no requieren llamadas al kernel?", ["Silberschatz"], "Falsa premisa: ambos utilizan soporte de kernel ante contención; además mutexes en espacio de usuario (futex) son más rápidos."),
            ("¿Es cierto que aumentar la memoria RAM siempre reduce los fallos de página en cualquier algoritmo según Belady?", ["Silberschatz"], "Falsa premisa: la anomalía de Belady demuestra que en FIFO aumentar marcos puede incrementar los fallos de página."),
            ("¿Es correcto afirmar que los hilos de usuario (green threads) aprovechan automáticamente múltiples núcleos de CPU sin soporte del kernel?", ["Silberschatz", "Tanenbaum"], "Falsa premisa: el kernel sólo ve un hilo de ejecución, por lo que todo el proceso se mapea a un único núcleo."),
            ("¿Verdad que la desreferenciación de un puntero nulo (NULL) en C ejecuta el código almacenado en la dirección 0x0000?", ["Kernighan & Ritchie"], "Falsa premisa: genera una excepción de fallo de segmentación (SIGSEGV) en arquitecturas con protección de memoria."),
            ("¿Es verdad que el planificador FCFS (First-Come, First-Served) garantiza el tiempo de espera promedio mínimo?", ["Silberschatz"], "Falsa premisa: SJF demuestra matemáticamente ser óptimo en tiempo de espera promedio; FCFS sufre efecto convoy."),
            ("¿Es cierto que la memoria virtual fue inventada principalmente para acelerar el acceso a los datos de la CPU?", ["Silberschatz"], "Falsa premisa: fue inventada para permitir ejecutar programas más grandes que la memoria física y brindar aislamiento."),
            ("¿Verdad que el interbloqueo (deadlock) y la inanición (starvation) son exactamente el mismo fenómeno con distinto nombre?", ["Silberschatz"], "Falsa premisa: deadlock es un ciclo permanente irreversible; starvation permite que otros avancen mientras uno espera indefinidamente."),
            ("¿Es correcto que la memoria caché L1 es gestionada directamente por el algoritmo de paginación del sistema operativo?", ["Patterson & Hennessy"], "Falsa premisa: la caché L1 es gestionada enteramente por hardware sin intervención del software del SO."),
            ("¿Verdad que un proceso hijo creado con fork() comparte exactamente la misma memoria física modificable que su padre?", ["Silberschatz"], "Falsa premisa: operan en espacios lógicos independientes y con COW la memoria modificable se duplica al escribir."),
            ("¿Es cierto que el bit de validez en la tabla de páginas indica si una página está protegida contra escritura?", ["Silberschatz"], "Falsa premisa: el bit de validez indica si la página está presente en memoria física o en el espacio virtual válido; los permisos son bits separados.")
        ]
    },
    {
        "category": "anaphoric_synthesis",
        "name": "Referencias anafóricas + síntesis",
        "count": 10,
        "prefix": "Q",
        "start": 91,
        "expected_behavior": "resolve_anaphora_and_synthesize",
        "dimensions": ["evidence_precision", "citation_correctness", "session_continuity", "learning_adaptation", "conversational_naturalness"],
        "queries": [
            ("En la sesión anterior analizamos paginación y segmentación. ¿Cómo se relaciona eso que vimos con el manejo del TLB?", ["Silberschatz"], "Conecta la traducción de direcciones previa con la aceleración por hardware del TLB."),
            ("Tomando en cuenta la analogía de los casilleros postales de antes, ¿cómo explicarías la indirección múltiple (**ptr)?", ["Kernighan & Ritchie"], "Extiende la analogía previa a un casillero cuyo mensaje contiene el número de otro casillero."),
            ("¿Cómo impacta ese problema de inanición que mencionaste antes en el diseño de un scheduler con prioridades?", ["Silberschatz"], "Aplica el concepto de starvation para justificar técnicas de envejecimiento (aging) en prioridades."),
            ("Siguiendo con la discusión sobre exclusión mutua, ¿por qué el algoritmo de Peterson no bastaba según lo que vimos?", ["Silberschatz", "Love"], "Sintetiza la falla de Peterson ante reordenamiento en arquitecturas multicore modernas."),
            ("¿Cómo se vincula el fallo de página que explicaste en el capítulo anterior con el concepto de working set?", ["Silberschatz"], "Vincula el costo del page fault con el conjunto de trabajo necesario para evitar thrashing."),
            ("Considerando las fallas de segmentación que revisamos, ¿qué pasa cuando un puntero cruza el límite de buffer?", ["Kernighan & Ritchie", "Aleph One"], "Relaciona la memoria desbordada con la invasión del marco de pila y potencial violación de segmento."),
            ("¿Cómo se relaciona la inversión de prioridad que vimos en Mars Pathfinder con el protocolo de techo de prioridad?", ["Tanenbaum", "Liu & Layland"], "Aplica la lección de Pathfinder para comparar herencia de prioridad vs protocolo de techo."),
            ("Tomando el concepto de inodo que explicamos, ¿cómo se implementa un hard link vs un soft link a partir de eso?", ["Bach", "Silberschatz"], "Hard link referencia el mismo número de inodo; soft link es un inodo separado que contiene la ruta."),
            ("A partir de lo que discutimos sobre semáforos y mutexes, ¿cómo construirías un monitor seguro?", ["Hoare", "Silberschatz"], "Encapsula variables compartidas con mutex de entrada y variables de condición internas."),
            ("Integrando la arquitectura Two-Stage y la memoria de sesiones, ¿cómo asegura TALOS que este razonamiento es continuo?", ["TALOS Architecture"], "Demuestra cómo el Controller determinista y el PersonaNarrator preservan estado mediante SessionBriefing.")
        ]
    }
]

questions = []
for spec in categories_spec:
    cat_id = spec["category"]
    for idx, (q_text, sources, ground_truth) in enumerate(spec["queries"]):
        num = spec["start"] + idx
        qid = f"Q{num:03d}"
        q_item = {
            "id": qid,
            "category": cat_id,
            "category_name": spec["name"],
            "query": q_text,
            "expected_behavior": spec["expected_behavior"],
            "relevant_sources": sources,
            "ground_truth": ground_truth,
            "evaluation_dimensions": spec["dimensions"]
        }
        questions.append(q_item)

assert len(questions) == 100, f"Expected 100 questions, got {len(questions)}"

out_path = Path("benchmark/questions.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(questions, f, indent=2, ensure_ascii=False)

print(f"Successfully generated {len(questions)} questions in {out_path}")
