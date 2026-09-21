/**
 * KASIU Study Engine - Main Frontend Orchestrator (Hito 10 / Fase 3)
 *
 * Slim coordinator: delegates chat to Chat module, follow-ups to FollowUp
 * module, and DAG rendering to dag.js.  Owns tab navigation, health
 * polling, and ledger inspection.
 */

window.activeSessionId = "sess-student-study-loop-v1";

document.addEventListener("DOMContentLoaded", () => {
  // Health polling: first check immediately, then every 30 s
  fetchHealth();
  setInterval(fetchHealth, 30000);

  // Close popovers when clicking outside
  document.addEventListener("click", (e) => {
    const badge = document.getElementById("health-badge");
    const popover = document.getElementById("health-popover");
    if (badge && popover && !badge.contains(e.target)) {
      popover.classList.remove("visible");
    }
    // Close evidence drawer when clicking its backdrop
    const evDrawer = document.getElementById("evidence-drawer-backdrop");
    if (evDrawer && e.target === evDrawer) {
      Chat.closeEvidence();
    }
  });

  // Restore any existing chat from sessionStorage
  Chat.restore();
});

// ── Tab Navigation ──────────────────────────────────────────────────

function switchTab(tabName) {
  const tabs = ["study", "practice", "audit"];
  tabs.forEach((t) => {
    const btn = document.getElementById(`tab-btn-${t}`);
    const view = document.getElementById(`view-${t}`);
    if (btn) btn.classList.toggle("active", t === tabName);
    if (view) view.classList.toggle("active", t === tabName);
  });
  if (tabName === "audit") loadLedger();
  if (tabName === "practice" && typeof Practice !== "undefined") Practice.init();
}

// ── Health Polling ──────────────────────────────────────────────────

function toggleHealthPopover() {
  const popover = document.getElementById("health-popover");
  if (popover) popover.classList.toggle("visible");
}

async function fetchHealth() {
  const dot = document.getElementById("health-dot");
  const text = document.getElementById("health-text");

  try {
    const res = await fetch("/api/health");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.status === "healthy") {
      const isMock = data.components?.llm?.provider === "replay_mock";
      if (isMock) {
        dot.className = "health-dot degraded";
        text.textContent = "Modo Mock (Offline)";
      } else {
        dot.className = "health-dot";
        text.textContent = "Sistema Saludable";
      }
    } else {
      dot.className = "health-dot error";
      text.textContent = "Atención Requerida";
    }

    // Populate diagnostic popover
    const cur = data.components?.curriculum;
    if (cur) document.getElementById("diag-curriculum").textContent = `${cur.nodes_loaded} nodos cargados`;
    const led = data.components?.ledger;
    if (led) document.getElementById("diag-ledger").textContent = `${led.entries_count} entradas (${led.integrity})`;
    const llm = data.components?.llm;
    if (llm) document.getElementById("diag-llm").textContent = `${llm.provider} (${llm.model})`;
    if (data.frozen_perimeter) document.getElementById("diag-perimeter").textContent = data.frozen_perimeter;
    if (data.test_suite) document.getElementById("diag-tests").textContent = `${data.test_suite.passed}/${data.test_suite.total} pasando`;
  } catch (err) {
    console.error("Health check error:", err);
    if (dot) dot.className = "health-dot error";
    if (text) text.textContent = "Desconectado";
  }
}

// ── Ledger Inspection ───────────────────────────────────────────────

async function loadLedger() {
  const container = document.getElementById("ledger-content");
  if (!container) return;

  container.textContent = "Cargando estado cognitivo del estudiante...";

  try {
    const res = await fetch("/api/student/cognitive-state");
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const masteries = Object.entries(data.kc_mastery || {});
    if (masteries.length === 0) {
      container.innerHTML = "";
      const emptyDiv = document.createElement("div");
      emptyDiv.style.padding = "1.5rem";
      emptyDiv.style.background = "var(--bg-card)";
      emptyDiv.style.borderRadius = "6px";
      emptyDiv.style.textAlign = "center";
      emptyDiv.style.color = "var(--text-secondary)";
      const p1 = document.createElement("p");
      p1.style.fontSize = "1rem";
      p1.style.marginBottom = "0.5rem";
      p1.textContent = "📜 Estado Cognitivo Génesis (Sin maestría registrada)";
      const p2 = document.createElement("p");
      p2.style.fontSize = "0.8rem";
      p2.style.color = "var(--text-muted)";
      p2.textContent = "Las observaciones de aprendizaje se registran al completar ejercicios y desafíos.";
      emptyDiv.appendChild(p1);
      emptyDiv.appendChild(p2);
      container.appendChild(emptyDiv);
      return;
    }

    container.innerHTML = "";
    const table = document.createElement("table");
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";
    table.style.fontSize = "0.82rem";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");
    headerRow.style.borderBottom = "1px solid var(--border-color)";
    headerRow.style.textAlign = "left";
    headerRow.style.color = "var(--text-muted)";
    ["Componente (KC)", "Prob. de Dominio (p_L)", "Intentos", "Última Actualización"].forEach((h) => {
      const th = document.createElement("th");
      th.style.padding = "0.5rem";
      th.textContent = h;
      headerRow.appendChild(th);
    });
    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (const [kcId, state] of masteries) {
      const tr = document.createElement("tr");
      tr.style.borderBottom = "1px solid rgba(55, 65, 81, 0.5)";

      const tdKc = document.createElement("td");
      tdKc.style.padding = "0.5rem";
      tdKc.style.fontWeight = "600";
      tdKc.style.color = "#93c5fd";
      tdKc.textContent = kcId;

      const tdPl = document.createElement("td");
      tdPl.style.padding = "0.5rem";
      tdPl.style.fontWeight = "700";
      tdPl.style.color = state.p_L >= 0.85 ? "#34d399" : (state.p_L >= 0.5 ? "#fbbf24" : "#f87171");
      tdPl.textContent = `${(state.p_L * 100).toFixed(1)}%`;

      const tdAttempts = document.createElement("td");
      tdAttempts.style.padding = "0.5rem";
      tdAttempts.textContent = String(state.attempts);

      const tdUpdate = document.createElement("td");
      tdUpdate.style.padding = "0.5rem";
      tdUpdate.style.color = "var(--text-muted)";
      tdUpdate.textContent = new Date(state.last_update).toLocaleString();

      tr.appendChild(tdKc);
      tr.appendChild(tdPl);
      tr.appendChild(tdAttempts);
      tr.appendChild(tdUpdate);
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    container.appendChild(table);
  } catch (err) {
    container.textContent = `Error al cargar el estado cognitivo: ${err.message}`;
  }
}

// ── Legacy compat shims (called from inline onclick in index.html) ──

function handleChatKeyPress(event) { Chat.handleKeyPress(event); }
function sendChatMessage()         { Chat.send(); }
