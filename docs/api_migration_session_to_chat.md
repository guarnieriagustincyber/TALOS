# 🔄 Guía de Migración: De `/api/session` a `/api/chat` y `/api/pedagogy`

**Destinatarios:** Clientes API, Frontend (KASIU UI), Integradores externos.  
**Estado:** Canónico (Ola 4).  
**Vigencia:** Permanente. Los endpoints bajo `/api/session` responden **HTTP 410 Gone**.

---

## 1. Contexto y Justificación Arquitectónica

Históricamente, TALOS contaba con dos vías para la interacción pedagógica:
1. `/api/session/*`: Un endpoint legacy monolítico acoplado a la máquina de estados local sin streaming SSE ni control de episodios socráticos.
2. `/api/chat/*` y `/api/pedagogy/*`: Rutas canónicas con streaming Server-Sent Events (SSE), anclaje epistémico en chunks SQLite FTS5/vectorial, y tracking cognitivo formal (BKT + SM-2).

En la **Ola 4**, `/api/session` ha sido formalmente retirado (`HTTP 410 Gone`). Toda interacción debe realizarse mediante los endpoints canónicos.

---

## 2. Matriz de Equivalencia de Endpoints

| Endpoint Deprecado (Retirado) | Método | Endpoint Canónico Reemplazo | Método | Modelo de Entrega |
|---|---|---|---|---|
| `/api/session/start` | `POST` | `/api/pedagogy/episode/start` | `POST` | JSON sincrónico |
| `/api/session/turn/conceptual` | `POST` | `/api/chat/query` | `POST` | Server-Sent Events (`text/event-stream`) |
| `/api/session/turn/exercise` | `POST` | `/api/chat/query` con `/practicar [tema]` | `POST` | Server-Sent Events (`text/event-stream`) |
| `/api/session/evaluate` | `POST` | `/api/practice/evaluate` | `POST` | JSON sincrónico en Sandbox |

---

## 3. Guía de Migración por Flujo

### 3.1 Inicio de Sesión / Episodio

#### Antes (Deprecado):
```http
POST /api/session/start
Content-Type: application/json

{
  "student_id": "std-01",
  "topic": "punteros"
}
```

#### Ahora (Canónico):
```http
POST /api/pedagogy/episode/start
Content-Type: application/json

{
  "student_id": "std-01",
  "kc_id": "punteros",
  "notebook_id": "fadena-lenguajes"
}
```
**Respuesta:**
```json
{
  "episode_id": "ep-fadena-lenguajes-punteros-...",
  "student_id": "std-01",
  "kc_id": "punteros",
  "initial_phase": "conceptual",
  "p_know": 0.1
}
```

---

### 3.2 Turnos Conversacionales y Conceptuales

#### Antes (Deprecado):
```http
POST /api/session/turn/conceptual
Content-Type: application/json

{
  "session_id": "sess-123",
  "student_response": "¿Qué es un puntero en C?"
}
```

#### Ahora (Canónico):
```http
POST /api/chat/query
Content-Type: application/json

{
  "prompt": "¿Qué es un puntero en C?",
  "scope_type": "notebook",
  "scope_id": "fadena-lenguajes",
  "requested_phase": "conceptual",
  "session_id": "sess-123"
}
```
**Respuesta:** `Content-Type: text/event-stream`
```
data: {"event_type": "phase_start", "payload": {"phase": "conceptual"}}

data: {"event_type": "phase_token", "payload": {"phase": "conceptual", "token": "Un puntero..."}}

data: {"event_type": "phase_complete", "payload": {"completed_phase": "conceptual", "next_phases": ["pseudocode", "socratic"]}}
```

---

### 3.3 Despacho de Ejercicios Prácticos Socráticos

#### Ahora (Canónico):
Despacho determinista por comando de práctica:
```http
POST /api/chat/query
Content-Type: application/json

{
  "prompt": "/practicar punteros",
  "scope_type": "notebook",
  "scope_id": "fadena-lenguajes",
  "session_id": "sess-123"
}
```
El motor valida que exista un ejercicio certificado `QUALIFIABLE` para `punteros` y lo despacha de forma determinista sin alucinaciones de LLM.

---

### 3.4 Evaluación de Código / Respuestas Prácticas

#### Ahora (Canónico):
```http
POST /api/practice/evaluate
Content-Type: application/json

{
  "task_id": "task-punteros-swap-01",
  "file_path": "src/exercises/swap.py",
  "command": ":eval"
}
```
**Respuesta:**
```json
{
  "task_id": "task-punteros-swap-01",
  "status": "PASSED",
  "assertions": { "passed": 3, "total": 3 },
  "stdout": "Todos los tests pasaron exitosamente.",
  "execution_time_ms": 12.4
}
```

---

## 4. Respuestas HTTP al invocar `/api/session/*`

Cualquier invocación a `/api/session/*` devolverá:
- **HTTP Status:** `410 Gone`
- **Body:**
```json
{
  "error": "ENDPOINT_RETIRED",
  "message": "/api/session fue decomisionado. Usá /api/chat/query o /api/pedagogy/episode/*.",
  "migration_guide": "docs/api_migration_session_to_chat.md"
}
```
