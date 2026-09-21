# ADR-008: ARQUITECTURA FRONTEND Y POLÍTICA DE CADENA DE SUMINISTRO DETERMINISTA

**Estado:** Aprobado para Implementación
**Destinatario:** Antigravity / Tech Lead
**Fecha:** Marzo 2026
**Contexto:** KASIU v0.3.0 Core — Interfaz de Adquisición Doctrinal y Telemetría Forense

---

## 1. CONTEXTO Y PROBLEMA

KASIU requiere una interfaz de usuario de alta densidad (Bento Grid, telemetría temporal con curvas Bezier, inspección forense en split-view y consola S6), con bajo consumo de recursos de sistema en entornos Linux y sin comprometer los invariantes deterministas del backend.

Asimismo, la interfaz no puede depender de árboles de dependencias dinámicos o no verificables que introduzcan riesgos de envenenamiento de la cadena de suministro (*supply-chain attack*) o impidan la reproducibilidad de compilación en entornos aislados.

---

## 2. LAS TRES FRONTERAS INVARIANTES

Quedan congeladas como reglas no negociables de diseño:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. FRONTEND:     Puede representar y solicitar. Jamás decidir.             │
│ 2. BACKEND:      Puede validar, decidir y persistir. Autoridad única.      │
│ 3. BUILD SYSTEM: Incorpora software únicamente mediante fuentes             │
│                  versionadas, verificables criptográficamente y auditables. │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **El Frontend carece de autoridad epistémica:** No calcula estados (`MASTERED`, `LOCKED`), no valida pertenencia de scopes por cuenta propia y no produce transiciones a `PASSED` en ejercicios prácticos. Consume proyecciones del backend y captura intenciones del operador.
* **El Backend es la autoridad determinista:** Todo avance curricular exige un bloque firmado en el Ledger. Toda cita exige resolución en el `CitationManifest` de S4.4. Toda ejecución de código ocurre en el contenedor aislado de Sandbox S6.
* **El Build System es determinista:** La compilación debe poder ejecutarse de forma hermética (sin conexión a Internet), a partir de fuentes congeladas con hash de integridad verificado.

---

## 3. DECISIÓN DE STACK Y COMPONENTES

Se ratifica el stack base sin introducir cambios de paradigma prematuros que dilaten el desarrollo:

```
[ FRONTEND APPLICATION ]
React 19 + TypeScript + Vite
       │
       ├── Código propio (clean architecture: Domain, Adapters, Presentation)
       ├── Dependencias de runtime strictly mínimas
       └── Gestión de estado:
           ├── UI Ephemeral State: Zustand (solo layout, tabs, paneles)
           └── Server State Cache: TanStack Query (proyección read-only)

[ ESTILOS Y MAQUETACIÓN ]
Tailwind CSS Standalone CLI
       │
       └── Binario local con hash SHA-256 verificado en repositorio
           Compilación directa sin capas intermedias de scripts no auditados

[ SHELL DE ESCRITORIO (PRODUCCIÓN) ]
Tauri v2 (Rust + WebKitGTK en Linux)
       │
       └── Binario nativo ligero (~10 MB), integración local (xdg-open / IPC)
           Sin runtime de Node.js ni empaquetado Chromium en producción
```

---

## 4. POLÍTICA DE SEGURIDAD Y CADENA DE SUMINISTRO (SUPPLY-CHAIN POLICY)

En lugar de asumir que una herramienta es "100% segura" por omisión, se establece un pipeline de control de artefactos:

```
UPSTREAM SOURCE
       │
       ▼
PINNED VERSION (Versión exacta fijada en lockfile, sin rangos ^ o ~)
       │
       ▼
INTEGRITY HASH (Validación de sub-resource integrity / sha512 en lockfile)
       │
       ▼
LOCAL CACHE / VENDOR (Almacén local inmutable para compilación)
       │
       ▼
OFFLINE BUILD (Compilación verificada con flag --offline / red deshabilitada)
       │
       ▼
REPRODUCIBLE ARTIFACT (Binario final de distribución con digest SHA-256)
```

### Reglas de Incorporación de Dependencias

1. **Auditoría de Inclusión:** Toda nueva librería externa requiere justificación técnica de costo/beneficio. Se prohíbe la inclusión de micro-paquetes para tareas resolubles en código nativo.
2. **Lockfiles Estrictos:** `package-lock.json` o `pnpm-lock.yaml` versionado obligatoriamente en Git. Las instalaciones de CI/build utilizan únicamente banderas de congelamiento (`npm ci --ignore-scripts` o equivalente).
3. **Desactivación de Scripts de Ciclo de Vida:** Queda prohibida la ejecución de scripts arbitrarios en la fase de instalación (`postinstall`).
4. **Tailwind CLI Standalone:** Se descarga una versión específica del binario de Tailwind para Linux x64, se asienta su hash SHA-256 en el repositorio y se ejecuta de forma local.

---

## 5. TAXONOMÍA DE ESTADO (UI EFÍMERO VS. DOMINIO)

Para impedir que el frontend se convierta en una segunda fuente de verdad:

```typescript
// ESTADO EFÍMERO DE UI (Zustand: useUiStore) - No autoritativo
interface UiState {
  activeView: 'chat' | 'roadmap' | 'library' | 'practice';
  inspector: {
    isOpen: boolean;
    activeTab: 'notes' | 'diagram' | 'source';
  };
  activeEvidenceId: string | null;
  activeScopeBadge: string | null;
  sidebarExpanded: boolean;
}

// ESTADO AUTORITATIVO (TanStack Query / API Adapters) - Solo lectura
interface DomainStateReadOnly {
  readonly curriculum: CurriculumGraphResponse;  // Nodos con status derivado por Backend
  readonly ledgerState: LedgerStatusResponse;     // Hashes de bloques y longitud de cadena
  readonly activeEvidence: GroundedEvidence | null; // Cita resuelta por S4.4
  readonly assessment: PracticeEvaluateResponse;  // Veredicto emitido por S6
}
```

---

## 6. MÁQUINA DE ESTADOS FINITA (FSM) PARA PRÁCTICA S6 (P4)

El panel de práctica no opera como una terminal libre; proyecta estrictamente la FSM del Sandbox:

$$\text{IDLE} \longrightarrow \text{READY} \longrightarrow \text{EVALUATION\_REQUESTED} \longrightarrow \text{SANDBOX\_RUNNING} \longrightarrow \text{ASSESSMENT\_RECEIVED} \longrightarrow \begin{cases} \text{PASSED} \\ \text{FAILED} \\ \text{ABSTAINED} \end{cases}$$

* La transición a `EVALUATION_REQUESTED` solo puede ser originada por acción explícita del usuario (comando CLI `:eval` o botón táctico).
* El estado `PASSED` solo es emitido si la respuesta del backend contiene `ledger_block_hash` válido y el total de aserciones aprobadas coincide con el total evaluado ($N/N$).

---

## 7. OBJETIVOS DE RENDIMIENTO (TARGETS, NO INVARIANTES)

Se definen como objetivos de ingeniería a monitorizar mediante instrumentación reproducible:

* **Huella de Memoria (Tauri v2 en Linux):** Target de referencia en reposo de $\approx 35 - 65 \text{ MB}$ RSS (sujeto al motor `WebKitGTK` del sistema).
* **Latencia de Renderizado de Página PyMuPDF:** Target de P95 $\le 45 \text{ ms}$ para páginas de texto técnico a 140 DPI sobre almacenamiento SSD local.
* **Tiempo de Respuesta del Inspector Forense:** Apertura y renderizado de evidencia $\le 16 \text{ ms}$ (1 frame a 60 fps).

---

## 8. PLAN DE IMPLEMENTACIÓN PARA ANTIGRAVITY

```
FASE 1: Contratos e Integración Base (Completada en Lab)
  └── Backend Contract Server activo (server.py) con schemas Pydantic tipados (FAC-0.1).

FASE 2: Skeleton Frontend & Supply-Chain Lock
  ├── Inicialización del proyecto React 19 + TypeScript + Vite en ui/.
  ├── Descarga y validación por SHA-256 del binario Tailwind Standalone CLI.
  ├── Bloqueo de lockfile (--ignore-scripts) y verificación de build offline.
  └── Montaje de la capa de Adaptadores de Dominio (Clean Architecture).

FASE 3: Vertical Slice P1 (Chat Core + Inspector Forense)
  ├── Chat Stream con renderizado de tokens [E#].
  ├── Inspector Forense flotante (Claim vs. Ground Truth S4.4 + Audit Manifest).
  └── Endpoints reales de FastAPI: /api/chat/query y /api/sources/{hash}/page-render.

FASE 4: Expansión de Módulos (P4 -> P3 -> P2)
  ├── P4: FSM de Sandbox S6 y telemetría de rúbrica.
  ├── P3: Catálogo Bento, protocolo formal de scopes e ingesta streaming.
  └── P2: Grafo curricular horizontal con curvas Bezier y métricas de avance.

FASE 5: Empaquetado Desktop con Tauri v2
  └── Configuración de IPC nativo y generación de binario Linux (.deb / AppImage).
```
