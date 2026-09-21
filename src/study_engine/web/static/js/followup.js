/**
 * KASIU Study Engine - Deterministic Pedagogical Follow-Up Renderer (Hito 10 / Fase 3)
 *
 * Renders the M1-generated PedagogicalFollowUp metadata as interactive
 * button panels below each tutor response.  These controls are produced
 * 100% deterministically by DeterministicTutorPolicy and never transit
 * through S4.4 (they are metadata attached *a posteriori*).
 */

const FollowUp = (() => {

  /**
   * Render the follow-up control panel HTML from a PedagogicalFollowUpDto.
   * Returns an HTML string to be injected inside the tutor bubble.
   */
  function render(followup) {
    if (!followup) return "";

    let html = `<div class="followup-panel">`;
    html += `<div class="followup-divider"></div>`;

    // 1. Socratic verification question
    if (followup.verification_question) {
      html += `
        <div class="followup-section">
          <span class="followup-label">🤔 ¿Entendiste? Comprobá tu comprensión:</span>
          <button class="followup-btn followup-verify"
                  onclick="FollowUp.sendVerification('${_escape(followup.verification_question)}')">
            ${_escape(followup.verification_question)}
          </button>
        </div>`;
    }

    // 2. Deepen options (adjacent DAG nodes)
    if (followup.deepen_options && followup.deepen_options.length > 0) {
      html += `<div class="followup-section">
        <span class="followup-label">🔍 Profundizar en temas relacionados:</span>
        <div class="followup-options">`;
      followup.deepen_options.forEach((opt) => {
        html += `<button class="followup-btn followup-deepen" onclick="FollowUp.deepen('${_escape(opt)}')">
          ${_escape(opt)}
        </button>`;
      });
      html += `</div></div>`;
    }

    // 3. Code example available
    if (followup.code_example_available) {
      html += `
        <div class="followup-section">
          <button class="followup-btn followup-code" onclick="FollowUp.showCodeExample()">
            💻 Ver ejemplo de código ilustrativo
          </button>
        </div>`;
    }

    // 4. Next node suggestion
    if (followup.next_node_id) {
      const nodeTitle = _getNodeTitle(followup.next_node_id);
      html += `
        <div class="followup-section">
          <span class="followup-label">➡️ Siguiente tema sugerido:</span>
          <button class="followup-btn followup-next" onclick="FollowUp.goToNode('${_escape(followup.next_node_id)}')">
            ${_escape(nodeTitle || followup.next_node_id)} →
          </button>
        </div>`;
    }

    html += `</div>`;
    return html;
  }

  // ── Button action handlers ──────────────────────────────────────

  /** Send the socratic verification question as a student message. */
  function sendVerification(question) {
    Chat.injectQuery(question);
  }

  /** Inject a deepening query about the selected adjacent topic. */
  function deepen(topic) {
    Chat.injectQuery(`Explicame más sobre ${topic} y cómo se conecta con el tema actual.`);
  }

  /** Switch to the Practice tab with a code example prompt. */
  function showCodeExample() {
    Chat.injectQuery("Mostrá un ejemplo de código en C que ilustre este concepto con comentarios explicativos.");
  }

  /** Navigate the DAG to a new node and start a fresh session. */
  function goToNode(nodeId) {
    if (typeof selectNode === "function") {
      selectNode(nodeId);
    }
    if (typeof startSessionForActiveNode === "function") {
      // Small delay to let the drawer update
      setTimeout(() => startSessionForActiveNode(), 150);
    }
  }

  // ── Helpers ───────────────────────────────────────────────────────

  function _escape(str) {
    if (!str) return "";
    return str
      .replace(/\\/g, "\\\\")
      .replace(/'/g, "\\'")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function _getNodeTitle(nodeId) {
    if (window.currentRoadmapNodes && window.currentRoadmapNodes[nodeId]) {
      return window.currentRoadmapNodes[nodeId].title;
    }
    return null;
  }

  return { render, sendVerification, deepen, showCodeExample, goToNode };
})();

// Expose globally for inline onclick handlers
window.FollowUp = FollowUp;
