# DEVELOPMENT SAFETY POLICY
## Study Engine — Controlled AI-Assisted Development

**Documento:** 04  
**Versión:** 1.0  
**Estado:** ACTIVE  
**Aplicación:** Desarrollo de V1.0  
**Agente principal:** Antigravity  
**Principio rector:** Deterministic Control First

---

## 1. Propósito

Este documento define las restricciones de seguridad, aislamiento,
reproducibilidad y control aplicables durante el desarrollo del Study
Engine mediante agentes de inteligencia artificial.

El objetivo es permitir el uso intensivo de agentes de desarrollo sin
otorgarles autoridad irrestricta sobre el sistema operativo, los datos
personales, las credenciales o la infraestructura del usuario.

El agente puede producir código, ejecutar pruebas, investigar errores y
proponer soluciones.

El agente NO posee autoridad final sobre:

- el sistema operativo;
- los secretos;
- los datos personales;
- la arquitectura fuera del alcance de la tarea;
- la certificación de un componente;
- la modificación de tests protegidos;
- la decisión de avanzar a una etapa posterior.

---

# 2. Principios fundamentales

## 2.1 Least Privilege

El agente debe recibir únicamente los permisos necesarios para realizar
la tarea actual.

No se conceden permisos administrativos por comodidad.

---

## 2.2 Repository Boundary

El área de trabajo normal del agente es exclusivamente el repositorio:

    <PROJECT_ROOT>/

El agente no debe modificar archivos fuera de dicho directorio salvo
autorización humana explícita.

---

## 2.3 No Administrative Privileges

El agente no debe utilizar:

    sudo

ni ejecutar acciones equivalentes para modificar el sistema operativo.

Si una tarea requiere privilegios administrativos:

1. el agente debe detenerse;
2. explicar por qué los necesita;
3. identificar exactamente qué acción requiere privilegios;
4. solicitar autorización humana.

---

## 2.4 Deterministic Verification

El agente nunca puede certificarse a sí mismo.

La afirmación:

    "La implementación está terminada"

no equivale a:

    "La implementación está certificada."

La certificación depende exclusivamente de Quality Gates deterministas.

---

## 2.5 Smallest Safe Change

Cada tarea debe implementar el cambio mínimo necesario para satisfacer
la especificación.

No realizar refactors no solicitados.

No modificar componentes no relacionados con la tarea.

---

## 2.6 Reproducibility

Toda modificación relevante debe poder:

1. reproducirse;
2. probarse;
3. revertirse;
4. explicarse.

---

# 3. Clasificación de acciones

Las acciones del agente se clasifican en tres niveles.

---

## 3.1 ALLOW

Acciones permitidas normalmente dentro del repositorio:

- crear archivos;
- modificar archivos del proyecto;
- leer archivos del proyecto;
- ejecutar Python del entorno virtual;
- ejecutar pytest;
- ejecutar linters;
- ejecutar type checkers;
- ejecutar scripts del proyecto;
- ejecutar benchmarks;
- ejecutar Docker Compose del proyecto;
- leer documentación;
- generar documentación;
- crear tests;
- ejecutar tests existentes;
- utilizar Git para inspección;
- crear commits si la tarea lo autoriza explícitamente.

---

## 3.2 ASK

El agente debe detenerse y solicitar autorización antes de:

- utilizar sudo;
- modificar archivos fuera del repositorio;
- instalar paquetes del sistema;
- modificar configuraciones del sistema;
- modificar firewall;
- modificar configuración de red;
- modificar Docker del host;
- eliminar volúmenes persistentes;
- eliminar grandes cantidades de datos;
- acceder a credenciales;
- acceder a claves SSH;
- modificar archivos de configuración globales;
- acceder a otros repositorios;
- realizar cambios destructivos;
- descargar ejecutables fuera de los mecanismos definidos;
- enviar datos sensibles a servicios externos.

---

## 3.3 DENY

Las siguientes acciones están prohibidas salvo intervención humana
directa fuera del agente:

- borrar el sistema operativo;
- modificar `/boot`;
- modificar `/etc` de forma no autorizada;
- modificar `/usr`;
- modificar `/var` fuera del alcance de Docker autorizado;
- modificar `~/.ssh`;
- exfiltrar secretos;
- publicar credenciales;
- desactivar mecanismos de seguridad del sistema;
- modificar tests protegidos para eliminar fallos;
- falsificar resultados de tests;
- ocultar errores;
- eliminar evidencia de fallos;
- declarar certificación sin pasar los Quality Gates.

---

# 4. Python Environment

El proyecto debe utilizar un entorno virtual aislado.

Ubicación:

    .venv/

Las dependencias del proyecto deben declararse mediante archivos
versionados.

Ejemplo:

    requirements.txt

o el mecanismo de gestión de dependencias definido posteriormente.

No se deben instalar dependencias Python globalmente.

Preferido:

    python -m venv .venv

    source .venv/bin/activate

    python -m pip install ...

Nunca utilizar instalaciones globales como mecanismo normal del proyecto.

---

# 5. Sistema de dependencias

Toda dependencia nueva debe:

1. tener una justificación;
2. estar relacionada con una necesidad concreta;
3. quedar registrada;
4. poder reproducirse;
5. pasar los tests correspondientes.

El agente no debe introducir dependencias únicamente por conveniencia.

Antes de agregar una dependencia importante debe explicar:

- propósito;
- alternativa estándar;
- impacto;
- licencia;
- superficie adicional;
- necesidad real.

---

# 6. Docker

Docker se utilizará para aislar servicios que razonablemente deban
ejecutarse como servicios independientes.

Los servicios deben estar definidos mediante:

    docker-compose.yml

o una estructura equivalente versionada.

Los contenedores deben:

- utilizar imágenes conocidas;
- utilizar volúmenes explícitos;
- evitar privilegios innecesarios;
- evitar montar el sistema completo;
- evitar acceso innecesario al socket Docker;
- evitar acceso a directorios personales.

Nunca montar:

    /

ni el home completo del usuario como volumen del contenedor.

---

# 7. Secretos

Los secretos nunca deben formar parte del repositorio.

Ejemplos:

- API keys;
- tokens;
- contraseñas;
- credenciales;
- claves privadas.

Los secretos se almacenarán fuera del control de versiones.

Ejemplo:

    .env

Debe existir:

    .env.example

sin valores reales.

`.gitignore` debe proteger:

    .env
    *.key
    *.pem
    credentials*
    secrets*

---

# 8. Datos de estudio

Los libros, PDFs y corpus de estudio deben considerarse datos del usuario.

El agente no debe:

- subirlos automáticamente a servicios externos;
- publicarlos;
- copiarlos al repositorio público;
- enviarlos a APIs cloud sin autorización.

El repositorio debe contener únicamente:

- configuración;
- código;
- metadatos permitidos;
- fixtures;
- datos sintéticos;
- documentación.

Los documentos originales deben almacenarse fuera del repositorio cuando
corresponda.

---

# 9. Tests protegidos

Los tests ubicados en:

    tests/protected/

son parte del contrato del sistema.

El agente NO puede modificarlos para conseguir un resultado positivo.

Un fallo debe resolverse modificando la implementación.

Si el agente considera que un test protegido es incorrecto debe:

1. detenerse;
2. explicar el conflicto;
3. proporcionar evidencia;
4. proponer una modificación;
5. esperar autorización humana.

La modificación de tests protegidos nunca debe ser utilizada como
mecanismo automático de reparación.

---

# 10. Git

Git constituye el mecanismo principal de reversibilidad.

Antes de una tarea importante debe existir un estado limpio o un commit
de referencia.

No realizar:

    git reset --hard

ni operaciones destructivas equivalentes sin autorización.

El agente debe inspeccionar:

    git status
    git diff

antes y después de cambios significativos.

---

# 11. Commits

Los commits deben representar unidades lógicas.

Ejemplos:

    feat: implement document ingestion
    test: add ingestion integration tests
    fix: handle malformed metadata
    docs: update ingestion specification

Evitar commits gigantes que mezclen:

- features;
- refactors;
- documentación;
- cambios de configuración;
- tests no relacionados.

---

# 12. Scope Lock

Cada tarea tiene un alcance definido.

El agente debe identificar:

    CURRENT TASK
    ALLOWED FILES
    FORBIDDEN FILES
    ACCEPTANCE CRITERIA

Si durante la implementación descubre una mejora fuera del alcance:

NO la implementa automáticamente.

La documenta como:

    OUT-OF-SCOPE FINDING

y continúa con la tarea actual.

---

# 13. Error Handling

Los errores nunca deben ocultarse.

Prohibido:

- capturar excepciones silenciosamente;
- ignorar errores;
- desactivar tests;
- reducir assertions;
- modificar thresholds únicamente para pasar;
- ocultar warnings relevantes;
- falsificar métricas.

Todo error debe clasificarse.

Ejemplo:

    IMPLEMENTATION_ERROR
    TEST_ERROR
    ENVIRONMENT_ERROR
    SPECIFICATION_CONFLICT
    DEPENDENCY_ERROR
    UNKNOWN

---

# 14. Quality Gate

Un componente se considera certificado únicamente cuando todos los
Hard Gates aplicables pasan.

Ejemplo:

    Unit Tests       PASS
    Integration      PASS
    Contract Tests   PASS
    Protected Tests  PASS
    Security Checks  PASS

Las métricas blandas como:

- coverage;
- performance;
- benchmark;
- latencia;

se registran como métricas y no sustituyen Hard Gates.

Un promedio nunca puede compensar un Hard Gate fallido.

---

# 15. Agente de reparación

El agente puede investigar automáticamente un fallo dentro del alcance
de la tarea.

Puede:

1. leer el error;
2. inspeccionar el código;
3. inspeccionar tests;
4. formular hipótesis;
5. implementar una corrección;
6. volver a ejecutar tests;
7. repetir.

No puede:

- modificar tests protegidos;
- ocultar el fallo;
- desactivar el test;
- declarar éxito sin evidencia.

---

# 16. External APIs

Las APIs externas solamente reciben información explícitamente
autorizada.

Antes de enviar información a una API cloud debe verificarse:

- qué datos se envían;
- si contienen secretos;
- si contienen datos personales;
- si contienen material protegido;
- qué parte del corpus es necesaria.

El Context Packer debe minimizar el contenido enviado.

---

# 17. No Self-Expansion

El agente no debe modificar esta política para facilitar su propio trabajo.

Una modificación de esta política requiere revisión humana.

---

# 18. Certification Authority

El agente desarrolla.

Los tests verifican.

Los Quality Gates certifican.

El humano autoriza cambios de política.

El agente no posee autoridad de certificación.

---

# 19. Regla final

Si existe conflicto entre:

    velocidad

y

    seguridad / reproducibilidad / evidencia

se elige:

    seguridad / reproducibilidad / evidencia.

El objetivo no es desarrollar rápido.

El objetivo es desarrollar componentes confiables.
