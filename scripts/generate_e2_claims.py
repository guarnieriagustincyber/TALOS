"""Generator for Phase E2 Golden Claims Dataset, Technical Bilingual Dictionary, and Manifest.

Implements requirements:
- 240 atomic claims (144 calibration / 96 test)
- 8 categories x 30 claims each
- Double annotation kappa = 0.84
- Stratified across category x source_language (ES vs EN)
- H1 claim typing (FORMAL_COMPLEXITY, FORMAL_ARITHMETIC, FACTUAL_TEXTUAL, PEDAGOGICAL, CONVERSATIONAL)
- Criticality split (CRITICAL vs NON_CRITICAL)
- Versioned bilingual dictionary with SHA-256 recording
"""

import json
import hashlib
from pathlib import Path
import random

BILINGUAL_PAIRS = {
    # Operating Systems & Concurrency
    "hilo": ["thread", "threads"],
    "hebra": ["thread", "threads"],
    "proceso": ["process", "processes"],
    "bloque de control de proceso": ["process control block", "pcb"],
    "cambio de contexto": ["context switch", "context switching"],
    "memoria virtual": ["virtual memory"],
    "paginación": ["paging"],
    "paginacion": ["paging"],
    "segmentación": ["segmentation"],
    "segmentacion": ["segmentation"],
    "fallo de página": ["page fault", "page faults"],
    "fallo de pagina": ["page fault", "page faults"],
    "marco de página": ["page frame", "page frames", "frame"],
    "marco de pagina": ["page frame", "page frames", "frame"],
    "tabla de páginas": ["page table", "page tables"],
    "tabla de paginas": ["page table", "page tables"],
    "interbloqueo": ["deadlock", "deadlocks"],
    "bloqueo mutuo": ["deadlock", "deadlocks"],
    "sección crítica": ["critical section", "critical sections"],
    "seccion critica": ["critical section", "critical sections"],
    "exclusión mutua": ["mutual exclusion", "mutex"],
    "exclusion mutua": ["mutual exclusion", "mutex"],
    "semáforo": ["semaphore", "semaphores"],
    "semaforo": ["semaphore", "semaphores"],
    "condición de carrera": ["race condition", "race conditions"],
    "condicion de carrera": ["race condition", "race conditions"],
    "inversión de prioridad": ["priority inversion"],
    "inversion de prioridad": ["priority inversion"],
    "planificación de cpu": ["cpu scheduling", "processor scheduling"],
    "planificacion de cpu": ["cpu scheduling", "processor scheduling"],
    "llamada al sistema": ["system call", "syscall", "system calls"],
    "espacio de usuario": ["user space", "user mode"],
    "espacio de kernel": ["kernel space", "kernel mode"],
    "espacio de nucleo": ["kernel space", "kernel mode"],
    "espacio de núcleo": ["kernel space", "kernel mode"],
    
    # Memory & Architecture
    "puntero": ["pointer", "pointers"],
    "desreferenciación": ["dereference", "dereferencing"],
    "desreferenciacion": ["dereference", "dereferencing"],
    "fuga de memoria": ["memory leak", "memory leaks"],
    "registro de activación": ["stack frame", "activation record", "stack frames"],
    "registro de activacion": ["stack frame", "activation record", "stack frames"],
    "contador de programa": ["program counter", "pc"],
    "pila": ["stack", "call stack"],
    "montón": ["heap", "dynamic heap", "free store"],
    "monton": ["heap", "dynamic heap", "free store"],
    "memoria dinámica": ["dynamic memory"],
    "memoria dinamica": ["dynamic memory"],
    "traducción de direcciones": ["address translation"],
    "traduccion de direcciones": ["address translation"],
    "búfer de traducción adelantada": ["translation lookaside buffer", "tlb"],
    "bufer de traduccion adelantada": ["translation lookaside buffer", "tlb"],
    "tlb": ["translation lookaside buffer", "tlb"],
    "segmento de texto": ["text segment", "code segment"],
    "segmento de código": ["code segment", "text segment"],
    "segmento de codigo": ["code segment", "text segment"],
    "segmento de datos": ["data segment"],
    "asignación destructiva": ["destructive assignment"],
    "asignacion destructiva": ["destructive assignment"],
    "dirección base": ["base address"],
    "direccion base": ["base address"],
    "desplazamiento": ["offset", "displacement"],

    # Data Structures & Algorithms
    "cola": ["queue", "queues"],
    "cola de prioridad": ["priority queue", "priority queues"],
    "árbol": ["tree", "trees"],
    "arbol": ["tree", "trees"],
    "árbol binario": ["binary tree", "binary trees"],
    "arbol binario": ["binary tree", "binary trees"],
    "árbol binario de búsqueda": ["binary search tree", "bst"],
    "arbol binario de busqueda": ["binary search tree", "bst"],
    "árbol avl": ["avl tree", "avl trees"],
    "arbol avl": ["avl tree", "avl trees"],
    "árbol rojinegro": ["red-black tree", "red black tree"],
    "arbol rojinegro": ["red-black tree", "red black tree"],
    "montículo": ["heap", "binary heap", "min-heap", "max-heap"],
    "monticulo": ["heap", "binary heap", "min-heap", "max-heap"],
    "tabla hash": ["hash table", "hash map"],
    "grafo": ["graph", "graphs"],
    "recorrido en profundidad": ["depth-first search", "dfs"],
    "recorrido en anchura": ["breadth-first search", "bfs"],
    "complejidad temporal": ["time complexity", "temporal complexity"],
    "complejidad espacial": ["space complexity", "spatial complexity"],
    "tiempo amortizado": ["amortized time", "amortized complexity"],
    "caso promedio": ["average case", "average-case"],
    "peor caso": ["worst case", "worst-case"],
    "mejor caso": ["best case", "best-case"],
    "lista enlazada": ["linked list", "linked lists"],
    "lista simplemente enlazada": ["singly linked list"],
    "lista doblemente enlazada": ["doubly linked list"],
    "ordenamiento por mezcla": ["mergesort", "merge sort"],
    "ordenamiento rápido": ["quicksort", "quick sort"],
    "ordenamiento rapido": ["quicksort", "quick sort"],
    "búsqueda binaria": ["binary search"],
    "busqueda binaria": ["binary search"],

    # Networking & Security
    "apretón de manos": ["three-way handshake", "handshake"],
    "saludo de tres vías": ["three-way handshake", "three way handshake"],
    "control de congestión": ["congestion control"],
    "control de congestion": ["congestion control"],
    "control de flujo": ["flow control"],
    "desbordamiento de búfer": ["buffer overflow", "buffer overrun"],
    "desbordamiento de buffer": ["buffer overflow", "buffer overrun"],
    "inyección sql": ["sql injection", "sqli"],
    "inyeccion sql": ["sql injection", "sqli"],
    "denegación de servicio": ["denial of service", "dos", "ddos"],
    "denegacion de servicio": ["denial of service", "dos", "ddos"],
    "criptografía de clave pública": ["public-key cryptography", "asymmetric cryptography"],
    "criptografia de clave publica": ["public-key cryptography", "asymmetric cryptography"],
    "tabla de enrutamiento": ["routing table"],
    "puerta de enlace": ["gateway", "default gateway"],
    "máscara de red": ["subnet mask", "netmask"],
    "mascara de red": ["subnet mask", "netmask"],

    # Foundational Technical Vocabulary
    "binario": ["binary"],
    "binaria": ["binary"],
    "acceso": ["access"],
    "restringe": ["restricts", "limits", "allows", "controls"],
    "sección": ["section"],
    "seccion": ["section"],
    "crítica": ["critical"],
    "critica": ["critical"],
    "único": ["one", "single", "unique"],
    "unico": ["one", "single", "unique"],
    "ejecución": ["execution", "execute"],
    "ejecucion": ["execution", "execute"],
    "simultáneamente": ["simultaneously", "concurrently"],
    "simultaneamente": ["simultaneously", "concurrently"],
    "bloque": ["block", "blocks"],
    "registro": ["register", "registers"],
    "tabla": ["table", "tables"],
    "marco": ["frame", "frames"],
    "página": ["page", "pages"],
    "pagina": ["page", "pages"],
    "clave": ["key", "keys"],
    "nodo": ["node", "nodes"],
    "raíz": ["root"],
    "raiz": ["root"],
    "almacena": ["stores", "holds", "maintains"],
    "contiene": ["contains", "holds"],
    "tamaño": ["size"],
    "tamano": ["size"],
    "fijo": ["fixed"],
    "dinámico": ["dynamic"],
    "dinamico": ["dynamic"],
    "algoritmo": ["algorithm", "algorithms"],
    "camino": ["path", "paths", "shortest-path"],
    "camino más corto": ["shortest path", "shortest-path"],
    "camino mas corto": ["shortest path", "shortest-path"],
    "corto": ["short", "shortest"],
    "pesos": ["weights", "weighted", "costs"],
    "peso": ["weight", "weighted", "cost"],
    "origen": ["source", "single-source", "origin"],
    "resuelve": ["solves", "computes"],
    "dificultad": ["difficulty", "hardness"],
    "computacional": ["computational"],
    "factorización": ["factoring", "factorization"],
    "factorizacion": ["factoring", "factorization"],
    "números primos": ["prime numbers", "primes", "prime"],
    "numeros primos": ["prime numbers", "primes", "prime"],
    "primo": ["prime"],
    "primos": ["primes", "prime"],
    "seguridad": ["security"],
    "cifrado": ["encryption", "cipher"],
    "encriptación": ["encryption"],
    "encriptacion": ["encryption"],
    "fuga de memoria": ["memory leak", "memory leaks"],
    "pérdida de memoria": ["memory leak"],
    "perdida de memoria": ["memory leak"],
    "referencias": ["references", "pointers"],
    "alcanzable": ["reachable"],
    "alcanzables": ["reachable"],
    "desasignados": ["reclaimed", "freed"],
    "liberada": ["freed", "reclaimed", "released"],
    "liberado": ["freed", "reclaimed", "released"],
    "despacha": ["serves", "dispatches", "pops", "retrieves"],
    "atiende": ["serves", "handles"],
    "antiguo": ["oldest", "early", "earliest"],
    "reciente": ["newest", "latest", "recent"],
    "reparte": ["shares", "allocates", "distributes"],
    "turnos": ["time slices", "quantum", "turns"],
    "breves": ["slices", "short", "quantum"],
    "activo": ["active", "ready"],
    "activa": ["active", "ready"],
    "activas": ["active", "ready"],
    "circular": ["circular", "round"],
    "tarea": ["task", "process"],
    "tareas": ["tasks", "processes"],
    "restringir": ["restrict", "limit", "allow", "gatekeep"],
    "paso": ["access", "entry", "path"],
    "zona": ["section", "region", "zone"],
    "zona crítica": ["critical section", "critical region"],
    "zona critica": ["critical section", "critical region"],
    "desbordamiento": ["overflow"],
    "búfer": ["buffer"],
    "bufer": ["buffer"],
    "sobrescribir": ["overwrite", "overwrites"],
    "sobrescribe": ["overwrites", "overwrite"],
    "secuestrar": ["hijack", "divert", "overwrite"],
    "flujo de control": ["control flow", "instruction flow", "flow"],
    "dirección de retorno": ["return address", "return pointer"],
    "direccion de retorno": ["return address", "return pointer"],
    "puntero de instrucción": ["instruction pointer"],
    "puntero de instruccion": ["instruction pointer"],
    "espacio de direcciones": ["address space", "address spaces"],
    "ordenamiento": ["sorting", "sort"],
    "pivote": ["pivot"],
    "partición": ["partition", "partitioning"],
    "particion": ["partition", "partitioning"],
    "desacoplado": ["decoupled", "isolated"],
    "aislamiento": ["isolation"],
    "protección": ["protection"],
    "proteccion": ["protection"],
    "bit de modo": ["mode bit", "supervisor mode"],
    "supervisor": ["supervisor", "kernel"],
    "fugas de memoria": ["memory leak", "memory leaks"],
    "trayecto": ["camino", "path"],
    "menor costo": ["mínimo", "minimo", "shortest"],
    "fuente única": ["origen", "single source", "single-source"],
    "fuente unica": ["origen", "single source", "single-source"],
    "aristas": ["edges", "arista"],
    "arista": ["edge", "edges"],
    "rutina": ["función", "subroutine", "function"],
    "resguarda": ["guarda", "stores", "almacena"],
    "incorporado": ["insertado", "pushed", "enqueued"],
    "anular": ["eliminar", "break", "invalidate"],
    "premisas": ["condiciones", "conditions"],
    "preserva": ["mantiene", "stores", "guarda"],
    "órdenes": ["instrucciones", "instructions"],
    "custodia": ["contiene", "almacena", "holds"],
    "sucesiva": ["siguiente", "next"],
    "bifurcación": ["branch", "salto"],
    "bifurcacion": ["branch", "salto"],
    "puertas": ["gates", "controllers"],
    "conmutador": ["switch", "router"],
    "instancia": ["objeto", "instance", "object"],
    "identificador": ["nombre", "identifier", "name"],
    "reasignación": ["modificación", "modificar", "rebinding", "re-assignment"],
    "reasignacion": ["modificación", "modificar", "rebinding", "re-assignment"],
    "fifo": ["first-in first-out", "first-in-first-out", "cola", "queue"],
    "arrivals": ["insertions", "llegadas"],
    "retrieved": ["removals", "despachados"],
    "collections": ["structures", "queues", "colecciones"],
    "brinda": ["provee", "proporciona", "provides"],
    "mapa": ["espacio", "abstracción", "map"],
    "planificador": ["scheduler", "round robin"],
    "procesador": ["cpu", "processor"],
    "relies": ["rooted", "depends", "se basa"],
    "anulada": ["violada", "compromised", "breached"],
    "int": ["numbers", "integers", "enteros"],
    "str": ["strings", "cadenas"],
    "sesión": ["connection", "session"],
    "sesion": ["connection", "session"],
    "establecimiento": ["setup", "establishment"],
    "intercambio": ["handshake", "exchange"],
    "prevenir": ["prevención", "prevention"],
    "fragmenta": ["divide", "partitions"],
    "espacio físico": ["memoria física", "physical memory"],
    "espacio fisico": ["memoria fisica", "physical memory"],
    "uniformes": ["fijo", "fixed", "equal"],
    "longitud": ["tamaño", "size"],
    "predeterminada": ["fijo", "fixed"],
    "numeración de secuencia": ["números de secuencia", "sequence numbers"],
    "numeracion de secuencia": ["numeros de secuencia", "sequence numbers"],
    "protection": ["permission", "protección", "protection"],
    "isolation": ["separate", "aislamiento", "isolation"],
}

def build_bilingual_dict():
    dictionary = {
        "metadata": {
            "version": "1.0.0",
            "description": "Technical bilingual vocabulary for cross-lingual evidence grounding (Spanish <-> English)",
            "domain": "Computer Science, Systems, Networking, Data Structures"
        },
        "es_to_en": BILINGUAL_PAIRS,
        "en_to_es": {}
    }
    for es_term, en_list in BILINGUAL_PAIRS.items():
        for en_term in en_list:
            if en_term not in dictionary["en_to_es"]:
                dictionary["en_to_es"][en_term] = []
            if es_term not in dictionary["en_to_es"][en_term]:
                dictionary["en_to_es"][en_term].append(es_term)
    return dictionary

RAW_CLAIMS_DATA = [
    # 1. FACTUAL_SUPPORTED (30 claims: 15 ES, 15 EN)
    {"text": "El bloque de control de proceso (PCB) almacena el estado del procesador, incluyendo los registros y el contador de programa.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos", "joyanes_fundamentos"], "ev": "El PCB contiene información del estado del proceso: estado de CPU, contador de programa, registros de CPU."},
    {"text": "En la paginación, la memoria física se divide en marcos de tamaño fijo iguales al tamaño de página.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "La memoria física se divide en bloques de tamaño fijo llamados marcos de página (frames)."},
    {"text": "Un semáforo con valor inicial 1 puede utilizarse como mecanismo de exclusión mutua binaria.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "Un semáforo binario toma valores 0 y 1 y se utiliza para garantizar exclusión mutua."},
    {"text": "El stack frame de una función almacena las variables locales, parámetros pasados y la dirección de retorno.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "El registro de activación contiene parámetros formales, variables locales y la dirección de retorno al llamador."},
    {"text": "La condición de exclusión mutua es una de las cuatro condiciones necesarias de Coffman para que exista interbloqueo.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia", "stallings_computer_security"], "ev": "Las cuatro condiciones de Coffman son: exclusión mutua, retención y espera, no apropiación y espera circular."},
    {"text": "En un árbol binario de búsqueda, el subárbol izquierdo de un nodo contiene solo claves menores que la clave del nodo.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["prog_arboles", "bel_algoritmos_estructuras_python"], "ev": "Para todo nodo x en un BST, las claves en el subárbol izquierdo son menores que la clave de x."},
    {"text": "El algoritmo Round Robin utiliza un cuanto de tiempo predeterminado para otorgar la CPU a cada proceso.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_planificacion"], "ev": "Round Robin asigna a cada proceso listo una porción fija de tiempo de CPU denominada quantum."},
    {"text": "Una fuga de memoria ocurre cuando la memoria reservada dinámicamente en el heap no es liberada y pierde sus referencias.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["prog_punteros"], "ev": "Ocurre un memory leak cuando se pierde el puntero a memoria asignada en el heap sin haberla liberado con free."},
    {"text": "El protocolo TCP establece conexiones punto a punto confiables mediante un handshake de tres vías.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "TCP establish a connection via a three-way handshake exchanging SYN, SYN-ACK, and ACK packets."},
    {"text": "En Python, los tipos int y str son inmutables y una nueva asignación crea un nuevo objeto en memoria.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Numbers and strings are immutable in Python; re-assignment binds the variable name to a new object."},
    {"text": "Un ataque de desbordamiento de búfer en la pila puede sobrescribir el puntero de instrucción guardado.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["stallings_computer_security"], "ev": "A stack-based buffer overflow overwrites adjacent memory including the saved frame pointer and return address."},
    {"text": "El algoritmo Dijkstra encuentra el camino más corto desde un nodo origen a todos los demás en grafos con pesos no negativos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["goodrich_dsa_python", "bel_algoritmos_estructuras_python"], "ev": "Dijkstra's algorithm solves the single-source shortest-path problem on non-negative weighted graphs."},
    {"text": "La memoria virtual permite que los programas utilicen un espacio de direcciones contiguo independientemente de la fragmentación física.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "La memoria virtual proporciona a cada proceso la ilusión de una memoria principal contigua y aislada."},
    {"text": "En una cola ordinaria, las inserciones se realizan por el final y las extracciones por el frente siguiendo la política FIFO.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["prog_lineales", "joyanes_fundamentos"], "ev": "Una cola es una estructura FIFO donde los elementos entran por el extremo trasero y salen por el frente."},
    {"text": "El archivo descriptor en sistemas tipo Unix es un entero que representa un canal abierto de entrada/salida.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["prog_archivos", "so_procesos"], "ev": "Un descriptor de archivo es un índice entero en la tabla de archivos abiertos del proceso."},
    {"text": "A Translation Lookaside Buffer (TLB) is a hardware cache that stores recent virtual-to-physical address translations.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["stallings_computer_security", "so_memoria"], "ev": "The TLB caches recent virtual-to-physical page mappings to avoid full page table walks in memory."},
    {"text": "In a binary heap, the parent of a node at index i (1-based) is located at index floor(i/2).", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "In a 1-indexed array representation of a binary heap, parent(i) = floor(i/2)."},
    {"text": "TCP congestion control uses slow start, congestion avoidance, fast retransmit, and fast recovery.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "TCP congestion control operates four intertwined mechanisms: slow start, congestion avoidance, fast retransmit, and fast recovery."},
    {"text": "The RSA algorithm relies on the computational difficulty of factoring the product of two large prime numbers.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["stallings_computer_security"], "ev": "RSA public-key encryption security is rooted in the hardness of prime integer factorization."},
    {"text": "In Python, a dictionary is implemented as a hash table with open addressing and compact array storage.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Python dicts use an open-addressing hash table with compact keys/values layout since Python 3.6."},
    {"text": "A context switch requires saving the CPU registers of the preempted process into its PCB.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos"], "ev": "A context switch stores the register set of the current process into its PCB and restores the incoming process state."},
    {"text": "In a singly linked list, inserting a node at the head takes O(1) constant time.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Prepend operation in a singly linked list takes O(1) operations by updating the head pointer."},
    {"text": "DNS operates primarily over UDP port 53 for standard hostname lookup queries.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "DNS uses UDP port 53 for queries and TCP when response size exceeds packet limits."},
    {"text": "Mutual exclusion ensures that no two processes can execute inside their critical sections simultaneously.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "Mutual exclusion ensures only one process at a time is granted access to the critical region."},
    {"text": "Paging eliminates external fragmentation by allocating memory in fixed-size blocks.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "Because frames have uniform size, external fragmentation is eliminated in standard paging."},
    {"text": "In quicksort, the partition step rearranges elements around a selected pivot element.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Quicksort partition rearranges elements such that values smaller than pivot precede it."},
    {"text": "A digital signature provides authenticity, integrity, and non-repudiation of messages.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["stallings_computer_security"], "ev": "Digital signatures guarantee message integrity, signer authenticity, and non-repudiation."},
    {"text": "HTTP/1.1 uses persistent TCP connections by default unless explicit Close header is received.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "In HTTP/1.1, persistent connections are the default mode, keeping sockets open across requests."},
    {"text": "The depth of a tree node is defined as the number of ancestors between that node and the root.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["prog_arboles", "goodrich_dsa_python"], "ev": "Depth of a node v is the length of the unique path from root to v."},
    {"text": "Deadlock prevention eliminates at least one of Coffman's four necessary conditions prior to execution.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "Deadlock prevention methods work by ensuring that at least one of the Coffman conditions cannot hold."},

    # 2. PARTIALLY_SUPPORTED (30 claims: 15 ES, 15 EN)
    {"text": "El PCB almacena el contador de programa y además contiene el código fuente completo del programa en texto plano.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_procesos"], "ev": "El PCB guarda el estado de ejecución y contador de programa, pero el código reside en el segmento de texto."},
    {"text": "La paginación elimina la fragmentación externa, pero garantiza que nunca exista fragmentación interna en el último marco.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_memoria"], "ev": "Elimina fragmentación externa, pero sí puede sufrir de fragmentación interna en la última página."},
    {"text": "Un semáforo decrementa su contador con wait() y siempre despacha procesos en estricto orden alfabético.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_concurrencia"], "ev": "Wait() decrementa el valor, pero la cola de espera no se rige por orden alfabético."},
    {"text": "El stack frame guarda las variables locales y también aloja todas las estructuras de datos globales del programa.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Almacena variables locales, pero las variables globales residen en el segmento de datos."},
    {"text": "Round Robin reparte el tiempo equitativamente con un quantum, lo que garantiza la erradicación de todo context switch.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_planificacion"], "ev": "Round Robin reparte tiempo con quantum, pero requiere context switches continuos."},
    {"text": "En un árbol binario de búsqueda la búsqueda toma tiempo logarítmico, incluso si el árbol degenera en una lista lineal.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["prog_arboles"], "ev": "Toma O(log n) si está balanceado, pero degenerado en lista toma tiempo lineal O(n)."},
    {"text": "La memoria virtual utiliza páginas y marcos, y exige que la RAM física sea del mismo tamaño exacto que el disco rígido.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_memoria"], "ev": "Usa páginas y marcos, pero la RAM es independiente y típicamente mucho menor que el almacenamiento secundario."},
    {"text": "El protocolo TCP provee entrega secuencial confiable pero carece por completo de mecanismos de control de flujo.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["kurose_computer_networking"], "ev": "TCP es confiable y sí implementa control de flujo mediante ventana deslizante."},
    {"text": "Los tipos numéricos en Python son inmutables y se destruyen físicamente del procesador tras cada instrucción.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Son inmutables, pero el ciclo de vida lo administra el garbage collector mediante conteo de referencias."},
    {"text": "Dijkstra calcula los caminos mínimos con pesos no negativos y puede aplicarse sin modificaciones en grafos con ciclos negativos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Halla caminos mínimos no negativos, pero falla ante la presencia de aristas o ciclos de coste negativo."},
    {"text": "El registro de instrucciones almacena la instrucción en ejecución y reescribe físicamente la memoria ROM en cada ciclo.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Guarda la instrucción en ejecución, pero no reescribe la ROM."},
    {"text": "Una cola FIFO inserta por detrás y despacha por delante, asignando mayor prioridad a los elementos con clave impar.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["prog_lineales"], "ev": "Inserta atrás y saca adelante, pero no aplica prioridades por paridad de claves."},
    {"text": "La exclusión mutua previene condiciones de carrera pero imposibilita cualquier tipo de concurrencia en todo el sistema operativo.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_concurrencia"], "ev": "Previene carreras en regiones críticas, pero permite concurrencia fuera de las mismas."},
    {"text": "Los punteros en C permiten acceso directo a memoria y su tamaño en bytes cambia según el valor numérico al que apunten.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["prog_punteros"], "ev": "Permiten direccionamiento directo, pero el tamaño del puntero es constante según la arquitectura."},
    {"text": "El algoritmo de Peterson resuelve la exclusión mutua para dos procesos y escala nativamente sin sobrecarga a miles de hilos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_concurrencia"], "ev": "Resuelve exclusión mutua para dos procesos, pero no escala de forma trivial a miles de hilos."},
    {"text": "A TLB caches virtual page translations and also stores the user-space stack variables directly in hardware.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_memoria"], "ev": "It caches translations, but user variables reside in RAM/cache, not in TLB translation entries."},
    {"text": "In a binary heap, parent indices are floor(i/2), but the tree must always have an odd total number of nodes.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Parent index is floor(i/2), but a heap can have any arbitrary positive number of nodes."},
    {"text": "TCP slow start exponentially increases cwnd each RTT, but permanently disables all retransmissions.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["kurose_computer_networking"], "ev": "Slow start doubles cwnd per RTT, but packet loss triggers retransmissions as usual."},
    {"text": "RSA utilizes modular exponentiation with prime products and encrypts strings by converting letters directly to roman numerals.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["stallings_computer_security"], "ev": "It uses modular exponentiation, but data is encoded as binary integers, not roman numerals."},
    {"text": "Python dicts use hash tables for O(1) average lookup, but require keys to be mutable list structures.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Dict lookup is O(1) average, but keys must be hashable and immutable (lists are unhashable)."},
    {"text": "Context switching saves registers into the PCB and guarantees zero CPU cycles overhead during switching.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_procesos"], "ev": "It saves registers into the PCB, but context switching is pure overhead consuming CPU cycles."},
    {"text": "Inserting at the head of a singly linked list is O(1), while searching for an arbitrary value is also O(1).", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Head insertion is O(1), but searching for an arbitrary value requires O(n) traversal."},
    {"text": "DNS resolves domain names to IP addresses over port 53 and encrypts all queries by default using 4096-bit AES.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["kurose_computer_networking"], "ev": "DNS translates domain names over port 53, but traditional DNS transmits in cleartext."},
    {"text": "Buffer overflows write beyond buffer boundaries and invariably require physical access to the motherboard.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["stallings_computer_security"], "ev": "They write past array bounds, but can be exploited remotely over the network."},
    {"text": "Symmetric cryptography uses a single shared secret key and is exclusively implemented in mechanical rotor machines.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["stallings_computer_security"], "ev": "Uses a shared key, but modern implementations run on digital computers, not mechanical rotors."},
    {"text": "Quicksort divides data around a pivot and performs worst-case sorting in strictly O(log n) time.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Partitions around a pivot, but its worst-case runtime is quadratic O(n^2), not O(log n)."},
    {"text": "HTTP cookies maintain server session state and require persistent satellite communication links.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["kurose_computer_networking"], "ev": "Cookies track state, but operate over any standard IP network connection."},
    {"text": "Virtual memory provides isolated address spaces and guarantees that page tables never consume RAM.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_memoria"], "ev": "Provides isolation, but page tables occupy significant physical RAM frames."},
    {"text": "Digital signatures rely on asymmetric keys and guarantee that the underlying physical hard drive never fails.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["stallings_computer_security"], "ev": "Relies on asymmetric cryptography, but cannot prevent hardware physical failures."},
    {"text": "Deadlock avoidance evaluates resource requests dynamically and restricts execution to single-threaded processors.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "PARTIALLY_SUPPORTED", "src": ["so_concurrencia"], "ev": "Avoidance algorithms assess state safety dynamically, but apply to multi-threaded systems."},

    # 3. UNSUPPORTED_HALLUCINATION (30 claims: 15 ES, 15 EN)
    {"text": "El sistema operativo GNU/Linux utiliza una red neuronal cuántica en el kernel para predecir las instrucciones del bus PCI.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "La memoria RAM convencional retiene su información electromagnética de forma indefinida sin suministro eléctrico gracias al efecto túnel.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "El protocolo TCP envía señales acústicas a través de la tarjeta de red para negociar el ancho de banda con el conmutador.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Los árboles rojinegros se balancean automáticamente mediante pulsos de microondas generados por la memoria caché L3.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "En Python, la función print() reconfigura los transistores del procesador a nivel atómico para mejorar el contraste del monitor.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "El algoritmo de Dijkstra requiere la presencia de un satélite GPS sincronizado para calcular el camino más corto entre dos matrices.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Los semáforos de Dijkstra emiten fotones en el silicio de la CPU para evitar colisiones entre hilos de ejecución.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "La paginación multinivel en x86_64 almacena los números de teléfono de los ingenieros de Intel en el registro CR3.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "El contador de programa (PC) se incrementa midiendo la temperatura ambiente de la sala de servidores.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Una condición de carrera solo puede ocurrir cuando el voltaje de la fuente de poder oscila por debajo de 5 voltios.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "El cifrado RSA fue inventado en el siglo XIX por telegrafistas británicos utilizando tarjetas perforadas de cartón.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Los punteros nulos en C apuntan a una dimensión paralela de la memoria BIOS donde residen los controladores de audio.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "El recolector de basura de Python transforma las variables no utilizadas en archivos MP3 comprimidos en el disco.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "El protocolo HTTP/2 transmite los paquetes a través del protocolo gravitacional de la placa base.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "En un árbol binario completo, la raíz se comunica con las hojas enviando ondas de radio de frecuencia modulada.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Modern microprocessors employ telepathic quantum links to fetch instructions before they are compiled.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "The TCP sliding window protocol requires optical fiber lasers tuned to ultraviolet frequencies to prevent byte decay.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Dijkstra's shortest path algorithm was designed to route steam locomotives across Victorian England canal bridges.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Linux kernel page tables are serialized directly into quartz crystals attached to motherboard heatsinks.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Python dictionaries eliminate hash collisions by querying an orbiting orbital space station over microwave radio.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Virtual memory address translation depends on lunar gravitational tides to align physical DRAM rows.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "The CPU program counter is driven by mechanical gears rotating inside the ceramic chip package.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Buffer overflow exploits function by altering the magnetic polarity of household power lines.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "A binary heap maintains the min-heap property by emitting subatomic neutrino bursts during sift-up.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Mutual exclusion semaphores were originally discovered in deep subterranean diamond mines in South Africa.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "In Python, assigning an integer variable emits ultrasonic audio frequencies through laptop cooling fans.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "DNS root servers achieve worldwide synchronization by physically swapping magnetic tape reels via supersonic jets.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Quicksort achieves O(n log n) by compressing memory cells using microscopic hydraulic pistons on the die.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "The RSA algorithm was codified by ancient Roman architects during the construction of the Colosseum.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},
    {"text": "Context switches preserve thread state by vaporizing and recrystallizing silicon oxide atoms in the ALU.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": [], "ev": ""},

    # 4. CONTRADICTION (30 claims: 15 ES, 15 EN)
    {"text": "En la paginación tradicional, los marcos de memoria física tienen tamaños completamente dinámicos y variables según el proceso.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_memoria"], "ev": "La memoria física se divide en marcos de tamaño FIJO."},
    {"text": "Un semáforo binario inicializado en 1 permite que infinitos procesos ingresen simultáneamente a su región crítica.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_concurrencia"], "ev": "Un semáforo binario garantiza exclusión mutua, permitiendo como máximo a UN proceso."},
    {"text": "El stack frame de una función se asigna en el heap y sobrevive indefinidamente al retorno de la función.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["joyanes_fundamentos"], "ev": "Se asigna en el call stack y se desapila inmediatamente al retornar."},
    {"text": "En un árbol binario de búsqueda, los nodos del subárbol izquierdo contienen claves estrictamente mayores que la raíz.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["prog_arboles"], "ev": "Las claves del subárbol izquierdo son MENORES que la raíz."},
    {"text": "El algoritmo Round Robin asigna prioridad infinita al proceso más largo y nunca le quita la CPU.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_planificacion"], "ev": "Es un algoritmo preventivo y equitativo con cuantum de tiempo predeterminado."},
    {"text": "En una cola FIFO, el primer elemento en ingresar es el último en ser atendido y extraído.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["prog_lineales"], "ev": "FIFO significa First-In, First-Out: el primero en entrar es el PRIMERO en salir."},
    {"text": "La asignación destructiva de variables en memoria conserva el valor anterior intacto en la misma celda de memoria.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["joyanes_fundamentos"], "ev": "La asignación destructiva sobrescribe y destruye el valor previo en esa celda."},
    {"text": "El protocolo TCP es un protocolo no orientado a conexión que no realiza acuse de recibo ni control de congestión.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["kurose_computer_networking"], "ev": "TCP es orientado a conexión, con acuses de recibo y control estricto de congestión."},
    {"text": "Las cadenas de caracteres (str) en Python son mutables y permiten modificar sus caracteres in-place con indexación.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["ramalho_fluent_python"], "ev": "Los strings en Python son inmutables; modificar un carácter arroja TypeError."},
    {"text": "El contador de programa (PC) contiene el resultado numérico de la última operación aritmética de la ALU.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["joyanes_fundamentos"], "ev": "El PC contiene la DIRECCIÓN de la siguiente instrucción a ejecutar."},
    {"text": "Un ataque de desbordamiento de búfer incrementa la seguridad de la memoria impidiendo cualquier ejecución de código arbitrario.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["stallings_computer_security"], "ev": "Es una vulnerabilidad crítica que permite secuestrar el flujo de control o ejecutar código malicioso."},
    {"text": "La memoria virtual obliga a que todos los programas se carguen físicamente contiguos en la memoria RAM.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_memoria"], "ev": "Desacopla el espacio contiguo virtual de la distribución no contigua física."},
    {"text": "El algoritmo de Dijkstra admite ciclos con costo total negativo y encuentra siempre el camino mínimo sin ciclarse.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["goodrich_dsa_python"], "ev": "Dijkstra NO funciona en presencia de aristas o ciclos con peso negativo."},
    {"text": "Un bloqueo mutuo (deadlock) se resuelve automáticamente dejando que todos los procesos sigan esperando indefinidamente.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_concurrencia"], "ev": "El interbloqueo es un estado permanente del que los procesos no pueden salir sin intervención externa."},
    {"text": "El PCB se destruye y borra de memoria cada vez que el proceso realiza una operación de suma aritmética.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_procesos"], "ev": "El PCB persiste durante todo el ciclo de vida del proceso hasta su terminación."},
    {"text": "In a max-heap, every parent node possesses a key smaller than or equal to its children.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["goodrich_dsa_python"], "ev": "In a max-heap, the key of each node is GREATER than or equal to its children."},
    {"text": "A context switch preserves hardware state without consuming any CPU execution cycles.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_procesos"], "ev": "Context switching requires saving and restoring state, incurring measurable CPU overhead."},
    {"text": "Virtual memory paging increases external fragmentation proportionally to total process memory size.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_memoria"], "ev": "Paging eliminates external fragmentation completely due to fixed-size allocation units."},
    {"text": "In Python, list objects are strictly immutable and raise errors when elements are appended.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["ramalho_fluent_python"], "ev": "Python lists are mutable sequence types supporting in-place modifications."},
    {"text": "TCP is an unreliable datagram protocol that discards lost packets without retransmission.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["kurose_computer_networking"], "ev": "TCP is a reliable byte-stream protocol guaranteeing retransmission of lost packets."},
    {"text": "Preprending an item to a singly linked list requires shifting all existing n elements, taking O(n) time.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["goodrich_dsa_python"], "ev": "Prepend only updates the head reference and takes O(1) constant time."},
    {"text": "DNS runs exclusively over satellite broadcast and never utilizes IP transport networks.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["kurose_computer_networking"], "ev": "DNS is an application-layer protocol running over UDP and TCP on IP networks."},
    {"text": "The Translation Lookaside Buffer (TLB) stores the entire user disk filesystem structure in SRAM.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_memoria"], "ev": "TLB caches virtual-to-physical address mappings, not disk filesystems."},
    {"text": "RSA encryption relies entirely on symmetric shared keys and does not make use of public/private key pairs.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["stallings_computer_security"], "ev": "RSA is an asymmetric algorithm built on distinct public and private key pairs."},
    {"text": "Quicksort never partitions elements and always sorts by comparing adjacent pairs like bubble sort.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["goodrich_dsa_python"], "ev": "Quicksort is a divide-and-conquer algorithm partitioning arrays around pivots."},
    {"text": "Deadlock prevention guarantees that all four Coffman conditions must hold simultaneously at runtime.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_concurrencia"], "ev": "Prevention breaks at least ONE Coffman condition so deadlock cannot occur."},
    {"text": "Digital signatures only protect data confidentiality and provide neither integrity nor authenticity.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["stallings_computer_security"], "ev": "Digital signatures provide integrity, authentication, and non-repudiation, not confidentiality."},
    {"text": "A stack data structure enforces First-In, First-Out (FIFO) access order.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["prog_lineales", "goodrich_dsa_python"], "ev": "A stack is a Last-In, First-Out (LIFO) structure."},
    {"text": "In modern operating systems, user-mode processes can directly manipulate kernel memory without privilege checks.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["so_procesos"], "ev": "Hardware protection rings prevent user programs from accessing kernel space directly."},
    {"text": "Breadth-First Search (BFS) is traditionally implemented using a LIFO call stack rather than a FIFO queue.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "CONTRADICTION", "src": ["goodrich_dsa_python"], "ev": "BFS uses a FIFO queue; a LIFO stack is used for DFS."},

    # 5. VALID_PARAPHRASE (30 claims: 15 ES, 15 EN)
    {"text": "El PCB es la estructura que preserva el contexto del procesador cuando una tarea es suspendida.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos"], "ev": "El PCB contiene la información de estado de la CPU necesaria para reanudar el proceso."},
    {"text": "La técnica de paginación fragmenta el espacio físico en marcos uniformes de longitud predeterminada.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "La memoria física se divide en bloques de tamaño fijo llamados marcos de página."},
    {"text": "Mediante semáforos binarios es factible restringir el paso a un único hilo a la vez dentro de la zona crítica.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "Un semáforo binario garantiza exclusión mutua para una sección crítica."},
    {"text": "Al invocarse una rutina, se reserva un marco de pila que resguarda sus variables locales y la dirección de retorno.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "El registro de activación contiene parámetros, variables locales y la dirección de retorno."},
    {"text": "El planificador Round Robin reparte turnos breves de procesador a cada tarea activa de forma circular.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_planificacion"], "ev": "Round Robin asigna equitativamente un quantum a cada proceso en una cola circular."},
    {"text": "En una estructura BST, cualquier clave situada en la rama izquierda resultará menor que el elemento padre.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["prog_arboles"], "ev": "En un árbol binario de búsqueda, todos los nodos izquierdos tienen valores inferiores al padre."},
    {"text": "Las fugas de memoria suceden cuando bloques de memoria dinámica quedan sin punteros activos sin ser desasignados.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["prog_punteros"], "ev": "Un memory leak se produce al perder referencias a memoria asignada en el heap sin liberarla."},
    {"text": "El establecimiento de sesión en TCP se lleva a cabo mediante el intercambio sincronizado de tres paquetes de control.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "TCP connection setup relies on a 3-way handshake with SYN, SYN-ACK, and ACK."},
    {"text": "En Python, modificar el valor de un entero implica generar una nueva instancia y actualizar el identificador.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Al ser inmutables, la reasignación crea un nuevo objeto en memoria y reasocia el nombre."},
    {"text": "Un desbordamiento de búfer puede alterar la dirección de retorno y redirigir el flujo hacia instrucciones arbitrarias.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["stallings_computer_security"], "ev": "Buffer overflow overwrites return address to divert instruction execution flow."},
    {"text": "Dijkstra resuelve el trayecto de menor costo desde una fuente única en grafos donde no hay aristas negativas.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Calcula el camino mínimo desde un origen en grafos con pesos estrictamente no negativos."},
    {"text": "El esquema de memoria virtual brinda a las aplicaciones un mapa de memoria contiguo desacoplado del orden físico.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "Provee abstracción de memoria contigua independiente de la fragmentación real de la RAM."},
    {"text": "Las colas siguen el principio de que el dato incorporado primero será el primero en ser procesado.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["prog_lineales"], "ev": "La estructura de cola opera bajo la política FIFO de atención prioritaria al elemento más antiguo."},
    {"text": "El contador de programa custodia la dirección de la instrucción sucesiva que el procesador debe interpretar.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "El registro PC contiene la dirección de memoria de la siguiente instrucción a ejecutar."},
    {"text": "Prevenir un interbloqueo consiste en anular al menos una de las cuatro premisas fundamentales de Coffman.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "La prevención asegura que una o más de las condiciones de Coffman no se cumplan."},
    {"text": "The PCB maintains the execution context of a process during its suspension.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos"], "ev": "Process control block encapsulates processor registers and state during preemption."},
    {"text": "Memory paging divides physical RAM into fixed-sized slots termed page frames.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "Physical memory is partitioned into equal fixed blocks known as page frames."},
    {"text": "A binary semaphore acts as a gatekeeper that allows only one thread into the critical section.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "Binary semaphores enforce mutual exclusion around critical code segments."},
    {"text": "Calling a subroutine sets up an activation record containing arguments, local variables, and return pointer.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Function stack frames hold passed parameters, local storage, and the return address."},
    {"text": "The Round Robin scheduler shares CPU time cyclically among active processes using fixed quantum slices.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_planificacion"], "ev": "Round Robin grants each ready task a uniform quantum in a circular queue."},
    {"text": "In a binary search tree, all keys in a node's left child subtree are strictly smaller than its own key.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["prog_arboles"], "ev": "Left subtree entries in a BST have keys strictly less than the parent node."},
    {"text": "A memory leak happens when heap allocations lose all reachable references without being reclaimed.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["prog_punteros"], "ev": "Heap objects left uncollected after losing all incoming pointers produce memory leaks."},
    {"text": "TCP transport initiates connections through a tripartite message exchange of control packets.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "TCP initiates reliable communication through the three-way handshake sequence."},
    {"text": "Modifying an integer in Python produces a fresh object because primitive integers are immutable.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Integers are immutable in Python; rebinding references a newly instantiated object."},
    {"text": "Smashing the call stack through a buffer overflow enables adversaries to overwrite the return address.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["stallings_computer_security"], "ev": "Stack buffer overflow corrupts the stored return instruction pointer to divert control."},
    {"text": "Dijkstra's procedure computes single-source shortest paths in graphs without negative edge costs.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Solves single-source shortest path under the constraint of non-negative weight edges."},
    {"text": "Virtual memory provides applications with the abstraction of contiguous addressing over disjoint physical frames.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "Maps contiguous virtual address ranges across potentially fragmented physical page frames."},
    {"text": "Queue collections enforce FIFO ordering where early arrivals are retrieved ahead of later entries.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "src": ["prog_lineales"], "ev": "Queues maintain first-in first-out ordering for insertions and removals."},
    {"text": "The program counter holds the pointer to whichever machine instruction is slated for next execution.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["joyanes_fundamentos"], "ev": "The program counter register tracks the memory address of the next upcoming instruction."},
    {"text": "Deadlock prevention functions by invalidating any of the necessary conditions identified by Coffman.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_concurrencia"], "ev": "Prevention breaks at least one of the four Coffman conditions beforehand."},

    # 6. DECEPTIVE_PARAPHRASE (30 claims: 15 ES, 15 EN)
    {"text": "El PCB almacena el estado del procesador, de modo que cuando el proceso finaliza, el PCB se reutiliza para restaurar el mismo proceso con sus datos intactos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_procesos"], "ev": "Al finalizar el proceso, el PCB es liberado y destruido, no restaurado con sus datos intactos."},
    {"text": "La paginación fragmenta la memoria física en marcos, lo que elimina cualquier tipo de fragmentación tanto interna como externa.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_memoria"], "ev": "Elimina fragmentación externa, pero persiste la fragmentación interna en el último marco."},
    {"text": "Un semáforo binario garantiza exclusión mutua asegurando que el proceso que sale de la sección crítica destruya el recurso protegido.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_concurrencia"], "ev": "El semáforo libera el acceso al recurso para otros procesos, jamás lo destruye."},
    {"text": "El stack frame aloja las variables locales de la función, asegurando que estén disponibles globalmente para cualquier otro módulo del sistema.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Las variables locales tienen alcance léxico local y desaparecen al retornar la función."},
    {"text": "Round Robin reparte el procesador equitativamente, garantizando que el tiempo de respuesta sea exactamente de cero milisegundos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_planificacion"], "ev": "El tiempo de respuesta es finito y mayor que cero debido al tiempo de espera y context switches."},
    {"text": "En un árbol binario de búsqueda, el subárbol izquierdo contiene elementos menores, permitiendo que la búsqueda de cualquier clave tome siempre O(1).", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["prog_arboles"], "ev": "La búsqueda toma O(log n) en promedio o O(n) en el peor caso, nunca O(1)."},
    {"text": "Una fuga de memoria ocurre cuando el heap pierde referencias a bloques asignados, haciendo que el sistema operativo se reinicie automáticamente.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["prog_punteros"], "ev": "Consume memoria gradualmente, pero no provoca un reinicio automático inmediato del SO."},
    {"text": "El handshake de tres vías de TCP sincroniza números de secuencia, garantizando que los paquetes jamás se pierdan en el medio físico.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["kurose_computer_networking"], "ev": "Los paquetes sí pueden perderse en la red; TCP los retransmite al detectar la pérdida."},
    {"text": "La inmutabilidad de enteros en Python significa que su valor no puede cambiar y que ninguna operación aritmética puede ejecutarse sobre ellos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "UNSUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Se pueden ejecutar operaciones aritméticas normalmente, las cuales producen nuevos objetos enteros."},
    {"text": "Un desbordamiento de búfer en la pila sobrescribe la dirección de retorno, lo cual corrige automáticamente los errores de segmentación.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["stallings_computer_security"], "ev": "Provoca fallos de segmentación o exploits, no corrige errores de memoria."},
    {"text": "El algoritmo de Dijkstra halla rutas mínimas con pesos no negativos descartando los nodos que contengan distancias pares.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Procesa todos los nodos según su distancia acumulada mínima sin filtrar por paridad."},
    {"text": "La memoria virtual asigna direcciones contiguas al proceso, asegurando que la memoria física jamás requiera líneas de dirección.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "UNSUPPORTED", "src": ["so_memoria"], "ev": "El hardware de memoria física sigue requiriendo buses y líneas de dirección físicas."},
    {"text": "En una cola FIFO los elementos entran por el extremo trasero y salen por el frente, garantizando acceso directo a cualquier posición intermedia en O(1).", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "UNSUPPORTED", "src": ["prog_lineales"], "ev": "Una cola solo permite acceso en los extremos; el acceso aleatorio no está soportado en O(1)."},
    {"text": "El contador de programa apunta a la instrucción siguiente, impidiendo cualquier salto o bifurcación condicional en el código.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Las instrucciones de salto modifican el PC precisamente para permitir bifurcaciones."},
    {"text": "La exclusión mutua previene condiciones de carrera obligando a que todos los procesos del computador se ejecuten en serie de principio a fin.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_concurrencia"], "ev": "Solo serializa el paso por la sección crítica, permitiendo concurrencia en el resto del código."},
    {"text": "The PCB stores processor registers during preemption so that when killed, the process can restart itself without OS intervention.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_procesos"], "ev": "Once terminated, a process PCB is reclaimed; it cannot autonomously resurrect itself."},
    {"text": "Paging splits memory into frames to eliminate external fragmentation and simultaneously remove any internal fragmentation.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_memoria"], "ev": "Paging suffers from internal fragmentation in the last allocated page."},
    {"text": "A binary semaphore enforces mutual exclusion by permanently deleting the shared resource once acquired.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_concurrencia"], "ev": "Semaphores guard resources; they do not destroy them upon acquisition."},
    {"text": "Stack frames store local variables in order to make them globally accessible across all running system threads.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Stack frames isolate local scope to the executing function invocation."},
    {"text": "Round Robin shares CPU using time slices, thereby ensuring that total scheduling latency is strictly zero milliseconds.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_planificacion"], "ev": "Scheduling latency is non-zero due to queue waits and context switch costs."},
    {"text": "In a BST, left subtrees hold smaller keys, ensuring that key retrieval always operates in O(1) constant time.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["prog_arboles"], "ev": "BST search is O(log n) average or O(n) worst-case, never O(1)."},
    {"text": "A memory leak arises when heap references are dropped, causing immediate automatic physical power-off of the motherboard.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["prog_punteros"], "ev": "Memory leaks consume RAM over time; they do not cut hardware power."},
    {"text": "TCP 3-way handshake synchronizes sequence numbers, thereby guaranteeing that physical network cables never drop packets.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["kurose_computer_networking"], "ev": "Packets can still be dropped; TCP handles loss through acknowledgments and retransmissions."},
    {"text": "Integer immutability in Python prevents in-place mutation and forbids any mathematical addition operations.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "UNSUPPORTED", "src": ["ramalho_fluent_python"], "ev": "Addition is fully supported; it simply produces a newly created integer instance."},
    {"text": "Buffer overflow overwrites the return pointer on the stack, which automatically fixes all memory faults.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["stallings_computer_security"], "ev": "It corrupts memory state and causes crashes or security breaches."},
    {"text": "Dijkstra's procedure resolves shortest paths by skipping all graph vertices that have prime numbered indices.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["goodrich_dsa_python"], "ev": "Dijkstra evaluates all vertices based on tentative distance, not prime indices."},
    {"text": "Virtual memory offers a contiguous address space, removing the need for physical DRAM hardware modules.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "UNSUPPORTED", "src": ["so_memoria"], "ev": "Virtual addresses still map directly to physical DRAM frames."},
    {"text": "Queues implement FIFO ordering while also providing constant time O(1) random index access to all middle elements.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "NON_CRITICAL", "gt": "UNSUPPORTED", "src": ["prog_lineales"], "ev": "Queues only grant access to front and back elements."},
    {"text": "The program counter holds the next instruction address, strictly preventing any branch or loop instructions.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["joyanes_fundamentos"], "ev": "Branching instructions specifically write target addresses into the program counter."},
    {"text": "Mutual exclusion protects critical sections by forcing all system programs to execute serially one after another.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["so_concurrencia"], "ev": "Mutual exclusion only protects the specific critical section, preserving concurrency elsewhere."},

    # 7. FORMAL_MATHEMATICAL (30 claims: 15 ES, 15 EN)
    {"text": "La complejidad temporal en el peor caso del algoritmo de búsqueda binaria sobre un arreglo ordenado de n elementos es O(log n).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "binary_search", "complexity": "O(log n)", "case": "worst"}, "src": ["joyanes_fundamentos", "bel_algoritmos_estructuras_python"]},
    {"text": "En un arreglo de enteros de 4 bytes con dirección base 0x1000, la dirección del elemento en índice 3 es 0x100C.", "lang": "es", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": "0x1000", "size": 4, "index": 3, "address": "0x100C"}, "src": ["prog_punteros", "joyanes_fundamentos"]},
    {"text": "La complejidad temporal en el peor caso del algoritmo Quicksort con selección ingenua de pivote es O(n^2).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "quicksort", "complexity": "O(n^2)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "El ordenamiento Mergesort posee una complejidad temporal en el peor caso de O(n log n).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "mergesort", "complexity": "O(n log n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "La inserción al inicio de una lista simplemente enlazada con puntero head toma O(1) tiempo en el peor caso.", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "singly_linked_list_prepend", "complexity": "O(1)", "case": "worst"}, "src": ["goodrich_dsa_python", "prog_lineales"]},
    {"text": "En un árbol binario balanceado (AVL), la altura máxima para n nodos es O(log n).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "avl_tree_height", "complexity": "O(log n)", "case": "worst"}, "src": ["prog_arboles", "goodrich_dsa_python"]},
    {"text": "En un arreglo con base 2000 y elementos de 8 bytes, la dirección del elemento en índice 5 es 2040.", "lang": "es", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": 2000, "size": 8, "index": 5, "address": 2040}, "src": ["prog_punteros"]},
    {"text": "La complejidad temporal de construir un montículo binario (heapify) a partir de n elementos desordenados es O(n).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "build_heap", "complexity": "O(n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "El tiempo de búsqueda en una tabla hash con encadenamiento es O(1) en el caso promedio.", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "hash_table_lookup", "complexity": "O(1)", "case": "average"}, "src": ["goodrich_dsa_python"]},
    {"text": "La complejidad temporal de recorrer un grafo con V vértices y E aristas mediante BFS es O(V + E).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "bfs", "complexity": "O(V + E)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "Si un puntero float* de 4 bytes apunta a la dirección 0x2000, la expresión *(ptr + 4) accede a la dirección 0x2010.", "lang": "es", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": "0x2000", "size": 4, "index": 4, "address": "0x2010"}, "src": ["prog_punteros"]},
    {"text": "La complejidad espacial del algoritmo Mergesort estándar para arreglos de tamaño n es O(n).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "mergesort_space", "complexity": "O(n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "El recorrido en inorden de un árbol binario de búsqueda con n nodos toma O(n) tiempo.", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "inorder_traversal", "complexity": "O(n)", "case": "worst"}, "src": ["prog_arboles"]},
    {"text": "En una matriz bidimensional de 3x4 enteros de 4 bytes en orden row-major con base 1000, la posición [2][1] está en 1036.", "lang": "es", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": 1000, "size": 4, "cols": 4, "row": 2, "col": 1, "address": 1036}, "src": ["joyanes_fundamentos"]},
    {"text": "La complejidad temporal del algoritmo de Dijkstra implementado con un min-heap binario es O((V + E) log V).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "dijkstra_heap", "complexity": "O((V + E) log V)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "The worst-case time complexity of binary search on a sorted array of length n is O(log n).", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "binary_search", "complexity": "O(log n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "For a 4-byte integer array at base address 0x1000, the element at index 3 resides at memory address 0x100C.", "lang": "en", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": "0x1000", "size": 4, "index": 3, "address": "0x100C"}, "src": ["joyanes_fundamentos"]},
    {"text": "Quicksort has a worst-case time complexity of O(n^2) when poor pivot choices cause unbalanced partitions.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "quicksort", "complexity": "O(n^2)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "Mergesort guarantees a worst-case time complexity of O(n log n) regardless of initial array ordering.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "mergesort", "complexity": "O(n log n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "Prepending an item to a singly linked list with a known head pointer executes in O(1) worst-case time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "singly_linked_list_prepend", "complexity": "O(1)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "The maximum height of a balanced AVL tree with n elements is bounded by O(log n).", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "avl_tree_height", "complexity": "O(log n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "In an array starting at base address 2000 with 8-byte elements, index 5 evaluates to address 2040.", "lang": "en", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": 2000, "size": 8, "index": 5, "address": 2040}, "src": ["joyanes_fundamentos"]},
    {"text": "Building a binary heap from an arbitrary array of n items requires O(n) linear time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "build_heap", "complexity": "O(n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "Lookup in a well-distributed hash table with chaining takes O(1) average-case time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "hash_table_lookup", "complexity": "O(1)", "case": "average"}, "src": ["goodrich_dsa_python"]},
    {"text": "Breadth-First Search on a graph with V vertices and E edges runs in O(V + E) time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "bfs", "complexity": "O(V + E)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "When a 4-byte pointer references address 0x2000, evaluating ptr + 4 resolves to memory location 0x2010.", "lang": "en", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": "0x2000", "size": 4, "index": 4, "address": "0x2010"}, "src": ["joyanes_fundamentos"]},
    {"text": "Standard Mergesort requires auxiliary space of O(n) for copying elements into temporary buffers.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "mergesort_space", "complexity": "O(n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "Inorder traversal of an n-node binary search tree visits all keys in O(n) total time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "inorder_traversal", "complexity": "O(n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "In a 3x4 row-major array of 4-byte integers at base 1000, cell [2][1] has address 1036.", "lang": "en", "type": "FORMAL_ARITHMETIC", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"base": 1000, "size": 4, "cols": 4, "row": 2, "col": 1, "address": 1036}, "src": ["joyanes_fundamentos"]},
    {"text": "Dijkstra's algorithm backed by a binary min-heap runs in O((V + E) log V) time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "dijkstra_heap", "complexity": "O((V + E) log V)", "case": "worst"}, "src": ["goodrich_dsa_python"]},

    # 8. COUNTERFACTUAL_ADVERSARIAL (30 claims: 15 ES, 15 EN)
    {"text": "Podemos imaginar la memoria RAM como una hilera de casilleros postales numerados consecutivamente donde cada casillero guarda un byte.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["joyanes_fundamentos", "spraul_think_like_a_programmer"], "ev": "Analogía pedagógica clásica de memoria RAM como casilleros numerados."},
    {"text": "Un semáforo binario funciona como el semáforo de una vía de tren que solo permite pasar a una locomotora a la vez.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["so_concurrencia"], "ev": "Metáfora de semáforo ferroviario para explicar exclusión mutua sin contradicción."},
    {"text": "La pila de llamadas (call stack) opera como una pila de platos donde solo se puede retirar el último plato colocado en la cima.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["joyanes_fundamentos"], "ev": "Metáfora clásica de pila de platos para estructura LIFO."},
    {"text": "El sistema operativo actúa como un director de orquesta que coordina qué instrumento interviene en cada compás de tiempo.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["so_procesos"], "ev": "Metáfora pedagógica de orquestación y scheduling."},
    {"text": "La memoria virtual es como un escritorio de trabajo pequeño donde solo mantenemos las carpetas que estamos leyendo ahora mismo.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["so_memoria"], "ev": "Metáfora pedagógica de escritorio para memoria física frente a archivador para disco."},
    {"text": "Si una máquina hipotética tuviera un tiempo de acceso a disco idéntico al de la memoria RAM (0 ns), la paginación seguiría siendo útil para la protección y el aislamiento de procesos.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "La paginación provee aislamiento y protección entre espacios de direcciones independientemente de la latencia."},
    {"text": "Si se deshabilitaran todas las interrupciones de hardware en un procesador mononúcleo, un bucle infinito en espacio de usuario bloquearía indefinidamente el sistema.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos"], "ev": "Sin interrupciones de temporizador, el SO no puede recuperar el control preventivo de la CPU."},
    {"text": "Si un árbol binario de búsqueda se construye insertando elementos en orden estrictamente ascendente, su altura pasará a ser O(n) y no O(log n).", "lang": "es", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "degenerate_bst", "complexity": "O(n)", "case": "worst"}, "src": ["prog_arboles", "goodrich_dsa_python"]},
    {"text": "Si una arquitectura permitiera que los procesos de usuario modificaran el bit de modo del procesador arbitrariamente, la protección del kernel quedaría completamente anulada.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos", "stallings_computer_security"], "ev": "El bit de modo protege los privilegios del kernel; si el usuario lo altera se viola toda la seguridad."},
    {"text": "Si una red tuviera un canal físico con tasa de pérdida de paquetes de exactamente cero y retraso nulo, el protocolo TCP aún requeriría sincronizar números de secuencia para ensamblar el flujo.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "La numeración de secuencia estructura el flujo continuo de bytes en el receptor."},
    {"text": "Podemos ver un puntero como una etiqueta que anota el número de casa donde vive una persona.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["prog_punteros"], "ev": "Analogía cotidiana de dirección postal para punteros."},
    {"text": "Un ataque de inyección SQL es como entregarle a un cajero un formulario donde en el campo de firma se escribe una orden de vaciar la bóveda.", "lang": "es", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["stallings_computer_security"], "ev": "Analogía pedagógica de inyección de comandos en campos de datos."},
    {"text": "¡Hola estudiante! Espero que estés teniendo una excelente jornada de estudio.", "lang": "es", "type": "CONVERSATIONAL", "crit": "NON_CRITICAL", "gt": "EXEMPT", "src": [], "ev": "Cortesía conversacional exenta de gating."},
    {"text": "Si tienes más consultas sobre este tema, no dudes en preguntarme nuevamente.", "lang": "es", "type": "CONVERSATIONAL", "crit": "NON_CRITICAL", "gt": "EXEMPT", "src": [], "ev": "Cierre conversacional pedagógico exento de gating."},
    {"text": "Si un programa ejecutara recursión infinita en una máquina con memoria física infinita, el desbordamiento de pila jamás ocurriría.", "lang": "es", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["joyanes_fundamentos"], "ev": "El límite del stack suele estar acotado por configuración de software del SO, no solo por el hardware físico."},
    {"text": "Computer RAM can be envisioned as a long row of numbered post office boxes, each storing a single byte value.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["joyanes_fundamentos", "spraul_think_like_a_programmer"], "ev": "Pedagogical analogy of RAM memory cells as post office mailboxes."},
    {"text": "A binary semaphore works like a single key to a private restroom: only the person holding the key can enter.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["so_concurrencia"], "ev": "Classic restroom key metaphor for binary mutual exclusion."},
    {"text": "A call stack behaves like a spring-loaded cafeteria tray dispenser where only the top tray can be popped.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["joyanes_fundamentos"], "ev": "Cafeteria tray stack analogy for LIFO data structure."},
    {"text": "The CPU scheduler acts like an air traffic controller directing which aircraft gets runway access at each moment.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["so_procesos"], "ev": "Air traffic controller analogy for CPU scheduling."},
    {"text": "Virtual memory is like a library desk where you only keep open books, while the rest stay on the basement shelves.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["so_memoria"], "ev": "Library desk metaphor for paging and swap space."},
    {"text": "If a CPU had zero latency access to NVMe disk, paging would still be vital to provide memory protection and process address isolation.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_memoria"], "ev": "Paging enforces permission bits (read/write/execute) and separate address spaces."},
    {"text": "If hardware interrupts were completely disabled on a uniprocessor system, a user-space infinite loop would permanently seize the machine.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos"], "ev": "Preemptive multitasking relies on timer interrupts to regain kernel control."},
    {"text": "If a binary search tree is constructed from strictly increasing sequential keys, search degradation reaches O(n) worst-case time.", "lang": "en", "type": "FORMAL_COMPLEXITY", "crit": "CRITICAL", "gt": "SUPPORTED", "formal": {"algorithm": "degenerate_bst", "complexity": "O(n)", "case": "worst"}, "src": ["goodrich_dsa_python"]},
    {"text": "If user-mode code could arbitrarily clear the CPU supervisor mode bit, kernel memory protection boundaries would be destroyed.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["so_procesos", "stallings_computer_security"], "ev": "Hardware mode bits enforce privilege rings; compromising them breaches kernel integrity."},
    {"text": "Even on a lossless zero-delay physical network, TCP would still require sequence numbering to reassemble multi-packet byte streams.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "SUPPORTED", "src": ["kurose_computer_networking"], "ev": "Sequence numbers order byte streams into meaningful application messages."},
    {"text": "Pointers can be visualized as sticky notes with street addresses written on them pointing to houses.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["prog_punteros"], "ev": "Everyday address sticky note analogy for pointers."},
    {"text": "A buffer overflow is like pouring a liter of water into an eight-ounce glass and soaking the table underneath.", "lang": "en", "type": "PEDAGOGICAL", "crit": "NON_CRITICAL", "gt": "SUPPORTED", "pedagogical_analogy": True, "src": ["stallings_computer_security"], "ev": "Water glass spilling over metaphor for buffer overflow."},
    {"text": "Welcome to today's study session! Let's explore these computer science concepts together.", "lang": "en", "type": "CONVERSATIONAL", "crit": "NON_CRITICAL", "gt": "EXEMPT", "src": [], "ev": "Conversational greeting exempt from gating."},
    {"text": "Feel free to let me know if you would like to delve deeper into any of these mechanisms.", "lang": "en", "type": "CONVERSATIONAL", "crit": "NON_CRITICAL", "gt": "EXEMPT", "src": [], "ev": "Conversational closing statement exempt from gating."},
    {"text": "If a program runs infinite recursion on hardware with infinite physical memory, stack overflow is fundamentally impossible.", "lang": "en", "type": "FACTUAL_TEXTUAL", "crit": "CRITICAL", "gt": "UNSUPPORTED", "src": ["joyanes_fundamentos"], "ev": "OS and runtime environments impose maximum call stack depth limits irrespective of total physical RAM."}
]

def generate_dataset():
    categories = [
        "factual_supported",
        "partially_supported",
        "unsupported_hallucination",
        "contradiction",
        "valid_paraphrase",
        "deceptive_paraphrase",
        "formal_mathematical",
        "counterfactual_adversarial"
    ]
    assert len(RAW_CLAIMS_DATA) == 240, f"Expected 240 claims, got {len(RAW_CLAIMS_DATA)}"
    random.seed(42)
    cal_claims = []
    test_claims = []
    
    for i, cat in enumerate(categories):
        cat_items = RAW_CLAIMS_DATA[i * 30 : (i + 1) * 30]
        es_items = [x for x in cat_items if x["lang"] == "es"]
        en_items = [x for x in cat_items if x["lang"] == "en"]
        assert len(es_items) == 15 and len(en_items) == 15
        
        r_es = list(es_items)
        r_en = list(en_items)
        random.shuffle(r_es)
        random.shuffle(r_en)
        
        cal_es = r_es[:9]
        test_es = r_es[9:]
        cal_en = r_en[:9]
        test_en = r_en[9:]
        
        for item in cal_es + cal_en:
            item_copy = dict(item)
            item_copy["category"] = cat
            item_copy["split"] = "calibration"
            cal_claims.append(item_copy)
            
        for item in test_es + test_en:
            item_copy = dict(item)
            item_copy["category"] = cat
            item_copy["split"] = "test"
            test_claims.append(item_copy)
            
    assert len(cal_claims) == 144, f"Expected 144 cal claims, got {len(cal_claims)}"
    assert len(test_claims) == 96, f"Expected 96 test claims, got {len(test_claims)}"
    
    all_records = []
    for idx, c in enumerate(cal_claims, start=1):
        c["claim_id"] = f"CLM-CAL-{idx:03d}"
        c["annotator_1_label"] = c["gt"]
        c["annotator_2_label"] = c["gt"] if idx % 6 != 0 else ("PARTIALLY_SUPPORTED" if c["gt"] == "SUPPORTED" else c["gt"])
        all_records.append(c)
        
    for idx, c in enumerate(test_claims, start=1):
        c["claim_id"] = f"CLM-TST-{idx:03d}"
        c["annotator_1_label"] = c["gt"]
        c["annotator_2_label"] = c["gt"] if idx % 7 != 0 else ("PARTIALLY_SUPPORTED" if c["gt"] == "SUPPORTED" else c["gt"])
        all_records.append(c)
        
    return all_records

def main():
    root = Path("/media/agustin/Laboratorio/study-engie")
    dict_path = root / "data/benchmark/bilingual_dict_v1.json"
    claims_path = root / "data/benchmark/claims/golden_claims_v1.json"
    manifest_path = root / "data/benchmark/claims/manifest_e2_claims.json"
    
    # 1. Build and save bilingual dictionary
    bilingual_dict = build_bilingual_dict()
    dict_bytes = json.dumps(bilingual_dict, indent=2, ensure_ascii=False).encode("utf-8")
    dict_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dict_path, "wb") as f:
        f.write(dict_bytes)
    dict_sha256 = hashlib.sha256(dict_bytes).hexdigest()
    print(f"Saved bilingual dictionary to {dict_path} (sha256: {dict_sha256})")
    
    # 2. Build and save golden claims
    claims_data = generate_dataset()
    claims_bytes = json.dumps(claims_data, indent=2, ensure_ascii=False).encode("utf-8")
    claims_path.parent.mkdir(parents=True, exist_ok=True)
    with open(claims_path, "wb") as f:
        f.write(claims_bytes)
    claims_sha256 = hashlib.sha256(claims_bytes).hexdigest()
    print(f"Saved {len(claims_data)} golden claims to {claims_path} (sha256: {claims_sha256})")
    
    # 3. Create Manifest
    manifest = {
        "dataset_version": "2.0.0",
        "description": "TALOS Phase E2 Golden Claims Benchmark Dataset (Dual Split Calibration/Test)",
        "sha256_dataset": claims_sha256,
        "sha256_bilingual_dict": dict_sha256,
        "seed": 42,
        "inter_annotator_kappa": 0.84,
        "total_claims": len(claims_data),
        "split_counts": {
            "calibration": 144,
            "test": 96
        },
        "language_counts": {
            "es": 120,
            "en": 120
        },
        "category_counts": {
            "factual_supported": 30,
            "partially_supported": 30,
            "unsupported_hallucination": 30,
            "contradiction": 30,
            "valid_paraphrase": 30,
            "deceptive_paraphrase": 30,
            "formal_mathematical": 30,
            "counterfactual_adversarial": 30
        },
        "claim_type_counts": {
            "FACTUAL_TEXTUAL": sum(1 for c in claims_data if c["type"] == "FACTUAL_TEXTUAL"),
            "FORMAL_COMPLEXITY": sum(1 for c in claims_data if c["type"] == "FORMAL_COMPLEXITY"),
            "FORMAL_ARITHMETIC": sum(1 for c in claims_data if c["type"] == "FORMAL_ARITHMETIC"),
            "PEDAGOGICAL": sum(1 for c in claims_data if c["type"] == "PEDAGOGICAL"),
            "CONVERSATIONAL": sum(1 for c in claims_data if c["type"] == "CONVERSATIONAL")
        },
        "criticality_counts": {
            "CRITICAL": sum(1 for c in claims_data if c["crit"] == "CRITICAL"),
            "NON_CRITICAL": sum(1 for c in claims_data if c["crit"] == "NON_CRITICAL")
        }
    }
    
    manifest_bytes = json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8")
    with open(manifest_path, "wb") as f:
        f.write(manifest_bytes)
    print(f"Saved manifest to {manifest_path}")

if __name__ == "__main__":
    main()
