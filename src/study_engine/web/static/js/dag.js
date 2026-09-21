/**
 * KASIU Study Engine - DAG Interactive Controller (Hito 10 / Fase 3)
 *
 * Handles Mermaid.js rendering, SVG node click binding, node detail
 * drawer, and session initialization integrated with the Chat module.
 */

window.currentRoadmapNodes = {};
window.selectedNodeId = null;

document.addEventListener("DOMContentLoaded", () => {
  // Initialize Mermaid with dark theme
  if (window.mermaid) {
    window.mermaid.initialize({
      startOnLoad: false,
      theme: "dark",
      themeVariables: {
        darkMode: true,
        background: "#0d121f",
        primaryColor: "#1e293b",
        primaryTextColor: "#f8fafc",
        primaryBorderColor: "#334155",
        lineColor: "#64748b",
        secondaryColor: "#1e293b",
        tertiaryColor: "#0d121f",
      },
      securityLevel: "loose",
    });
  }

  // Initial load
  loadRoadmap();
});

/**
 * Fetch authoritative roadmap and render Mermaid SVG graph.
 */
async function loadRoadmap() {
  const container = document.getElementById("dag-render-area");
  if (!container) return;

  container.innerHTML = `<p style="color: var(--text-secondary); font-size: 0.85rem;">Cargando grafo curricular soberano...</p>`;

  try {
    const res = await fetch("/api/curriculum/roadmap");
    if (!res.ok) throw new Error(`HTTP ${res.status}: Fallo al obtener el roadmap`);

    const data = await res.json();
    window.currentRoadmapNodes = {};
    for (const node of data.nodes) {
      window.currentRoadmapNodes[node.node_id] = node;
    }

    // Render with Mermaid
    const uniqueId = "mermaid-" + Date.now();
    const { svg } = await window.mermaid.render(uniqueId, data.mermaid_source);
    container.innerHTML = svg;

    // Attach click events to rendered SVG nodes
    bindSvgNodeEvents();

    // Select first available node by default if none selected
    if (!window.selectedNodeId) {
      const firstAvailable = data.nodes.find((n) => n.status === "AVAILABLE");
      if (firstAvailable) selectNode(firstAvailable.node_id);
    }
  } catch (err) {
    console.error("Error al renderizar el DAG:", err);
    container.innerHTML = `
      <div style="color: #ef4444; padding: 1rem; text-align: center;">
        <p>⚠️ No se pudo renderizar el grafo curricular.</p>
        <p style="font-size: 0.75rem; color: var(--text-muted);">${err.message}</p>
      </div>`;
  }
}

/**
 * Detect node elements in the SVG and bind click listeners.
 */
function bindSvgNodeEvents() {
  const svg = document.querySelector("#dag-render-area svg");
  if (!svg) return;

  // Scan all Mermaid node groups and match by text content
  const nodeGroups = svg.querySelectorAll("g.node");
  nodeGroups.forEach((group) => {
    group.style.cursor = "pointer";
    const text = group.textContent || "";
    for (const nodeId of Object.keys(window.currentRoadmapNodes)) {
      const node = window.currentRoadmapNodes[nodeId];
      if (text.includes(nodeId) || text.includes(node.title.slice(0, 15))) {
        group.addEventListener("click", () => selectNode(nodeId));
        break;
      }
    }
  });
}

/**
 * Fetch detailed specification for a node and display in Drawer.
 */
async function selectNode(nodeId) {
  window.selectedNodeId = nodeId;
  const drawer = document.getElementById("node-drawer");
  if (!drawer) return;
  drawer.classList.add("visible");

  try {
    const res = await fetch(`/api/curriculum/nodes/${encodeURIComponent(nodeId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const node = await res.json();

    document.getElementById("drawer-node-title").textContent = node.title;
    document.getElementById("drawer-node-id").textContent = node.node_id;
    document.getElementById("drawer-node-desc").textContent = node.description;

    // Status Badge
    const statusBadge = document.getElementById("drawer-node-status");
    statusBadge.textContent = node.status;
    statusBadge.className = `node-status-badge badge-${node.status.toLowerCase()}`;

    // Prerequisites
    const prereqsList = document.getElementById("drawer-prereqs-list");
    prereqsList.textContent = (node.prerequisites && node.prerequisites.length > 0)
      ? node.prerequisites.join(", ")
      : "Ninguno (Nodo Raíz)";

    // Authorized Sources
    const sourcesList = document.getElementById("drawer-sources-list");
    if (node.authorized_sources && node.authorized_sources.length > 0) {
      sourcesList.textContent = node.authorized_sources
        .map((s) => `${s.document_id} (págs. ${s.page_start || 1}–${s.page_end || "fin"})`)
        .join("; ");
    } else {
      sourcesList.textContent = "General";
    }

    // Start Study Button
    const startBtn = document.getElementById("btn-start-study");
    if (node.status === "LOCKED") {
      startBtn.disabled = true;
      startBtn.style.opacity = "0.5";
      startBtn.style.cursor = "not-allowed";
      startBtn.textContent = "🔒 Prerrequisitos no cumplidos";
    } else {
      startBtn.disabled = false;
      startBtn.style.opacity = "1.0";
      startBtn.style.cursor = "pointer";
      startBtn.textContent = `🚀 Iniciar Sesión (${node.node_id})`;
    }
  } catch (err) {
    console.error("Error al cargar detalle del nodo:", err);
  }
}

/**
 * Trigger session initialization for currently selected node,
 * then hand off to the Chat module.
 */
async function startSessionForActiveNode() {
  if (!window.selectedNodeId) return;

  const startBtn = document.getElementById("btn-start-study");
  const origText = startBtn.textContent;
  startBtn.textContent = "Iniciando...";
  startBtn.disabled = true;

  try {
    const res = await fetch("/api/session/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ node_id: window.selectedNodeId }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    window.activeSessionId = data.session_id;

    // Update session label
    const sessLabel = document.getElementById("active-session-label");
    if (sessLabel) {
      sessLabel.textContent = `Sesión: ${data.node_id}`;
      sessLabel.style.color = "#34d399";
    }

    // Reset and populate chat via the Chat module
    Chat.reset();
    Chat.addSystemMessage(
      `**⚡ Sesión iniciada: ${data.node_title}**\n\n` +
      `${data.message}\n\n` +
      `*Acción pedagógica: ${data.initial_action} · Presupuesto: ${data.budget}*`
    );

    // Focus chat input
    const input = document.getElementById("chat-input");
    if (input) input.focus();
  } catch (err) {
    console.error("Error al iniciar sesión:", err);
    Chat.addSystemMessage(`⚠️ Error al iniciar sesión: ${err.message}`);
  } finally {
    startBtn.textContent = origText;
    startBtn.disabled = false;
  }
}
