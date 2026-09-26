# CHANGELOG — TALOS Frontend (`kasiu-lab/ui`)

## v0.4.0 — UI/UX Polish, Optimization & Cognitive Profile (Dark Mode Only)

### 🚀 Rendimiento
- **MermaidBlock (Lazy Rendering)**: Implementado `IntersectionObserver` con `threshold: 0.05` para diferir el renderizado de diagramas de flujo Mermaid fuera del viewport. Muestra un placeholder de carga `bg-zinc-800` y desconecta el observer tras renderizar.
- **ChatMessages (TTFT Skeleton & Streaming Memo)**:
  - Agregado Skeleton Loader (`bg-zinc-800 animate-pulse`) durante el tiempo de espera del primer token (TTFT).
  - Migrado el renderizado del mensaje durante streaming a `MemoizedMessageBody` para evitar re-renders masivos del árbol Markdown en cada token SSE.

### 🎨 Estética & Legibilidad
- **MessageBody (Jerarquía Tri-Capa)**:
  - En los títulos `h2`, se detecta automáticamente la capa pedagógica (*Intuición*, *Mecanismo*, *Máquina / Silicio*) y se aplica formato diferenciado:
    - **Intuición**: 💡 Borde azul `border-blue-500/60` con fondo `bg-blue-500/5` y texto `text-blue-100`.
    - **Mecanismo Formal**: ⚙️ Borde índigo `border-indigo-500/60` con fondo `bg-indigo-500/5` y texto `text-indigo-100`.
    - **Nivel de Máquina**: 🔬 Borde ámbar `border-amber-500/60` con fondo `bg-amber-500/5` y texto `text-amber-100`.
- **CodeBlock**:
  - Botón de copiar adaptado a visibilidad por hover (`opacity-0 group-hover:opacity-100 transition-opacity`).
  - Fuente de código refinada a `text-[13px] leading-[1.65]` para legibilidad en C/Python.

### 🧠 Panel de Perfil Cognitivo
- **CognitiveProfileDrawer**:
  - Nuevo panel lateral desplegable (Drawer) fijo a la derecha (`w-80 bg-zinc-900 border-zinc-800`).
  - Consume el endpoint `GET /api/student/profile/cognitive`.
  - Muestra **Debilidades Activas** (`occurrences >= 2`), **Fortalezas** consolidadas y mensaje motivacional.
- **ChatHeader & ChatWorkspace**:
  - Botón con icono `Brain` en el header principal para abrir/cerrar el drawer.

### ☀️ Comando `>>dia` (Card Especial)
- **ChatMessages**:
  - Detección inteligente del comando `>>dia` mediante inspección del mensaje previo del usuario o patrones del asistente.
  - Aplicación de card contenedor dorado con gradiente `from-amber-950/20 to-zinc-950`, borde ámbar `border-amber-500/30` y banner superior ☀️ *"Resumen del Día · TALOS"*.

---
*Garantía de diseño: 100% Modo Oscuro Exclusivo (`bg-zinc-950`, `bg-zinc-900`, `bg-zinc-800`). Sin referencias a paletas claras.*
