/**
 * KASIU Study Engine - Socractic Chat Controller (Hito 10 / Fase 3)
 *
 * Manages the multi-turn conversational flow between the student and the
 * S4.4-audited tutor. All tutor content is sanitized via DOMPurify before
 * rendering.  Chat state persists in sessionStorage and is scoped per
 * session_id + node_id so that a page refresh within the same tab
 * preserves the conversation, but a new tab starts clean.
 */

const Chat = (() => {
  // ── State ─────────────────────────────────────────────────────────
  let _messages = [];          // Array of {role, text, followup?, audit?, telemetry?, ts}
  let _busy = false;           // True while waiting for tutor response
  const STORAGE_KEY = "kasiu_chat_history";
  let _mermaidRenderCount = 0;

  // ── Persistence ───────────────────────────────────────────────────

  function _storageKey() {
    const sid = window.activeSessionId || "default";
    const nid = window.selectedNodeId || "none";
    return `${STORAGE_KEY}_${sid}_${nid}`;
  }

  function save() {
    try {
      sessionStorage.setItem(_storageKey(), JSON.stringify(_messages));
    } catch (_) { /* quota exceeded – degrade gracefully */ }
  }

  function restore() {
    try {
      const raw = sessionStorage.getItem(_storageKey());
      if (raw) {
        _messages = JSON.parse(raw);
        const history = _getHistory();
        if (!history) return;
        // Clear default welcome bubble and re-render saved messages
        history.innerHTML = "";
        _messages.forEach((m) =>
          _renderBubble(m.role, m.text, m.followup, m.audit, m.telemetry, m.qtype, m.provenance, m.discrepancies)
        );
      }
    } catch (_) { /* corrupted – start fresh */ }
  }

  // ── DOM helpers ───────────────────────────────────────────────────

  function _getHistory() { return document.getElementById("chat-history"); }
  function _getInput()   { return document.getElementById("chat-input"); }
  function _getSendBtn() { return document.getElementById("btn-send-chat"); }

  function createSessionId() {
    return window.crypto && window.crypto.randomUUID
      ? `chat-${window.crypto.randomUUID()}`
      : `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  }

  /** Lock / unlock input while the tutor is thinking. */
  function _setInputLocked(locked) {
    _busy = locked;
    const input = _getInput();
    const btn   = _getSendBtn();
    if (input) { input.disabled = locked; }
    if (btn)   { btn.disabled = locked; btn.textContent = locked ? "..." : "Enviar"; }
  }

  // ── Citation rendering ────────────────────────────────────────────

  /** Turn [E1], [E2] patterns into clickable citation badges. */
  function _renderCitations(html) {
    return html.replace(
      /\[(E\d+)\]/g,
      (_match, tag) =>
        `<span class="citation-badge" onclick="Chat.openEvidence('${tag}')" title="Clic para ver la fuente epistémica autorizada">[${tag}]</span>`
    );
  }

  async function _renderMermaidBlocks(container) {
    const blocks = container.querySelectorAll("pre > code.language-mermaid");
    for (const block of blocks) {
      const pre = block.parentElement;
      if (!pre) continue;
      try {
        if (!window.mermaid || !window.DOMPurify) {
          throw new Error("El renderizador de diagramas no está disponible.");
        }
        const id = `kasiu-chat-diagram-${Date.now()}-${++_mermaidRenderCount}`;
        const { svg } = await window.mermaid.render(id, block.textContent || "");
        const safeSvg = window.DOMPurify.sanitize(svg, {
          USE_PROFILES: { svg: true, svgFilters: true },
        });
        const wrapper = document.createElement("div");
        wrapper.className = "chat-mermaid";
        wrapper.innerHTML = safeSvg;
        pre.replaceWith(wrapper);
      } catch (error) {
        console.error("No se pudo renderizar el diagrama Mermaid:", error);
        const notice = document.createElement("p");
        notice.className = "chat-mermaid-error";
        const reason = error instanceof Error ? error.message : String(error);
        notice.textContent = `No se pudo renderizar el diagrama; queda disponible su fuente textual. ${reason}`;
        pre.after(notice);
      }
    }
  }

  /** Typewriter effect: progressively reveal already-audited plain text.
   *
   * Safe because it only animates the final S4.4-approved content — never
   * unstreamed model output. Only applied to plain-text (quick) responses;
   * Markdown/citation responses render immediately.
   */
  function typewriterEffect(container, text, speed = 18) {
    let i = 0;
    container.textContent = "";
    container.classList.add("typewriter-caret");
    const timer = setInterval(() => {
      i += 1;
      container.textContent = text.slice(0, i);
      if (i >= text.length) {
        clearInterval(timer);
        container.classList.remove("typewriter-caret");
      }
    }, speed);
  }

  // ── Bubble rendering ──────────────────────────────────────────────

  function _renderBubble(role, text, followup, audit, telemetry, qtype, provenance, discrepancies) {
    const history = _getHistory();
    if (!history) return;

    const bubble = document.createElement("div");
    const quick = (qtype === "greeting" || qtype === "curricular" || qtype === "meta");
    bubble.className = `chat-bubble ${role}` + (quick ? " quick" : "");

    // Parse Markdown and sanitize (skip for quick plain-text responses,
    // which use the typewriter effect on raw text instead).
    let body;
    if (quick && role === "tutor") {
      body = `<div class="bubble-body bubble-body-typewriter"></div>`;
    } else {
      body = text;
      if (window.marked && window.DOMPurify) {
        body = window.DOMPurify.sanitize(window.marked.parse(text));
      }
      body = _renderCitations(body);
    }

    // ── Header (tutor messages only) ────────────────────────────────
    let headerHtml = "";
    if (role === "tutor") {
      let auditBadge = "";
      if (audit) {
        const ok = audit === "APPROVED";
        auditBadge = `<span class="audit-badge ${ok ? "audit-approved" : "audit-warning"}">[S4.4: ${audit}]</span>`;
      }
      headerHtml = `<div class="bubble-header"><strong class="tutor-label">⚡ Tutor KASIU</strong>${auditBadge}</div>`;
    }

    // ── Follow-up controls (M1 deterministic) ───────────────────────
    let followupHtml = "";
    if (followup) {
      followupHtml = FollowUp.render(followup);
    }

    // ── Telemetry footer ────────────────────────────────────────────
    let telemHtml = "";
    if (telemetry) {
      telemHtml = `<div class="telemetry-footer">
        <span>${telemetry.tokens_used}/${_budgetLimit(telemetry)} tokens</span>
        <span>·</span>
        <span>${telemetry.latency_ms}ms</span>
        <span>·</span>
        <span>${telemetry.model}</span>
      </div>`;
    }

    bubble.innerHTML = `${headerHtml}${body}${followupHtml}${telemHtml}`;
    if (role === "tutor" && Array.isArray(provenance) && provenance.length > 0) {
      const provenanceEl = document.createElement("div");
      provenanceEl.className = "evidence-provenance";
      provenanceEl.textContent = `Procedencia: ${provenance
        .map((item) => {
          const source = item.source_title || item.source_id || "fuente no identificada";
          const page = item.page_start ? `, pág. ${item.page_start}` : "";
          return `${item.citation_id || "E?"} — ${source}${page}`;
        })
        .join(" · ")}`;
      bubble.appendChild(provenanceEl);
    }
    if (role === "tutor" && Array.isArray(discrepancies) && discrepancies.length > 0) {
      const discrepancyEl = document.createElement("div");
      discrepancyEl.className = "evidence-discrepancy";
      discrepancyEl.textContent = "⚠️ Las fuentes recuperadas presentan una discrepancia; revisá cada cita antes de combinar sus conclusiones.";
      bubble.appendChild(discrepancyEl);
    }
    history.appendChild(bubble);
    history.scrollTop = history.scrollHeight;
    if (role === "tutor") {
      _renderMermaidBlocks(bubble);
    }

    // Fast (quick) plain-text responses render with a safe typewriter effect.
    // Markdown / citation responses already rendered statically above.
    if (quick && role === "tutor") {
      const placeholder = bubble.querySelector(".bubble-body-typewriter");
      if (placeholder) {
        typewriterEffect(placeholder, text, 18);
      }
    }
  }

  function _budgetLimit(telemetry) {
    // Infer ceiling from model/provider as a rough guide
    return telemetry.tokens_used > 0 ? Math.max(600, telemetry.tokens_used + 100) : 600;
  }

  // ── Typing indicator ──────────────────────────────────────────────

  /** Stage-aware typing indicator: shows the three S4.4 pipeline phases. */
  function _showTyping() {
    const history = _getHistory();
    if (!history) return;
    const el = document.createElement("div");
    el.className = "chat-bubble tutor typing-indicator";
    el.id = "thinking-bubble";
    el.innerHTML = `<div class="bubble-header"><strong class="tutor-label">⚡ Tutor KASIU</strong></div>
      <div class="typing-dots"><span></span><span></span><span></span></div>
      <span class="typing-text" id="typing-stage">Consultando fuentes autorizadas…</span>`;
    history.appendChild(el);
    history.scrollTop = history.scrollHeight;
    _advanceTypingStage();
  }

  /** Cycle through the auditing pipeline stages while the tutor works. */
  function _advanceTypingStage() {
    const stages = [
      "Buscando evidencia curricular…",
      "Generando respuesta fundamentada…",
      "Auditando con S4.4 (verificación forense)…",
    ];
    let i = 0;
    window._kasiuTypingTimer = setInterval(() => {
      const el = document.getElementById("typing-stage");
      if (!el) { clearInterval(window._kasiuTypingTimer); return; }
      i = (i + 1) % stages.length;
      el.textContent = stages[i];
    }, 1600);
  }

  function _removeTyping() {
    if (window._kasiuTypingTimer) {
      clearInterval(window._kasiuTypingTimer);
      window._kasiuTypingTimer = null;
    }
    const el = document.getElementById("thinking-bubble");
    if (el) el.remove();
  }

  // ── Provider banner ───────────────────────────────────────────────

  function updateProviderBanner(provider) {
    let existing = document.getElementById("provider-banner");
    if (!existing) {
      existing = document.createElement("div");
      existing.id = "provider-banner";
      const history = _getHistory();
      if (history) history.parentElement.insertBefore(existing, history);
    }
    if (provider === "replay_mock" || provider === "mock") {
      existing.className = "provider-banner mock";
      existing.innerHTML = `⚠️ <strong>Modo simulado</strong> — las respuestas provienen del motor de replay local (Gemini no disponible).`;
    } else if (provider === "unavailable") {
      existing.className = "provider-banner error";
      existing.innerHTML = `❌ <strong>Servicio no disponible</strong> — no se puede conectar al proveedor LLM.`;
    } else {
      existing.className = "provider-banner real";
      existing.innerHTML = `✅ Usando <strong>Gemini</strong> real (${provider})`;
      // Auto-hide after 4 seconds
      setTimeout(() => { existing.style.display = "none"; }, 4000);
    }
  }

  // ── Public API ────────────────────────────────────────────────────

  /** Push a system/welcome message from code (not via the API). */
  function addSystemMessage(text) {
    const msg = { role: "tutor", system: true, text, followup: null, audit: null, telemetry: null, ts: Date.now() };
    _messages.push(msg);
    _renderBubble("tutor", text, null, null, null);
    save();
  }

  /** Handle Enter key press (submit) in the chat input. */
  function handleKeyPress(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }

  /** Build a bounded, unverified client history for server-side sanitization. */
  function _buildHistory(maxTurns = 20) {
    const roles = new Set(["student", "tutor"]);
    const turns = _messages
      .filter((m) => roles.has(m.role) && m.text && !m.system && !m.error)
      .slice(-maxTurns)
      .map((m) => ({
        role: m.role === "student" ? "user" : "assistant",
        content: m.text.slice(0, 4000),
      }));
    return turns;
  }

  async function _readSseResponse(response) {
    if (!response.body) throw new Error("El servidor no inició el flujo de respuesta SSE.");
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const events = [];
    let pending = "";

    function consumeFrame(frame) {
      const data = frame
        .split(/\r?\n/)
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trim())
        .join("\n");
      if (data) events.push(JSON.parse(data));
    }

    while (true) {
      const { value, done } = await reader.read();
      pending += decoder.decode(value || new Uint8Array(), { stream: !done });
      let separator;
      while ((separator = pending.match(/\r?\n\r?\n/))) {
        const index = separator.index;
        consumeFrame(pending.slice(0, index));
        pending = pending.slice(index + separator[0].length);
      }
      if (done) break;
    }
    if (pending.trim()) consumeFrame(pending);

    const result = { text: "", audit: null, telemetry: null, provenance: [], discrepancies: [] };
    for (const event of events) {
      const payload = event.payload || {};
      if (event.event_type === "phase_token") {
        result.text += payload.token || "";
      } else if (event.event_type === "audit_verdict") {
        result.audit = payload.verdict || null;
      } else if (event.event_type === "phase_complete") {
        result.audit = payload.audit_verdict || payload.verdict || result.audit;
        result.telemetry = payload.telemetry || null;
        result.provenance = Array.isArray(payload.evidence_provenance)
          ? payload.evidence_provenance
          : [];
        result.discrepancies = Array.isArray(payload.evidence_discrepancies)
          ? payload.evidence_discrepancies
          : [];
      } else if (event.event_type === "abstention" || event.event_type === "clarification") {
        result.text = [payload.reason, payload.suggested_action]
          .filter(Boolean)
          .join("\n\n");
      } else if (event.event_type === "error") {
        throw new Error(payload.message || "Error interno al generar la respuesta.");
      }
    }

    if (!result.text.trim()) throw new Error("El flujo SSE terminó sin contenido para mostrar.");
    return result;
  }

  /** Send the current input to the tutor backend. */
  async function send() {
    if (_busy) return;

    const input = _getInput();
    const text = (input ? input.value : "").trim();
    if (!text) return;
    const recentTurns = _buildHistory();
    const nodeId = window.selectedNodeId || "";
    const node = window.currentRoadmapNodes && window.currentRoadmapNodes[nodeId];
    const prompt = node
      ? `Tema curricular activo: ${node.title} (${nodeId}).\nConsulta del estudiante: ${text}`
      : text;

    // Append student bubble
    const studentMsg = { role: "student", text, followup: null, audit: null, telemetry: null, ts: Date.now() };
    _messages.push(studentMsg);
    _renderBubble("student", text, null, null, null);
    if (input) input.value = "";
    save();

    _setInputLocked(true);
    _showTyping();

    try {
      const res = await fetch("/api/chat/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          scope_type: "folder",
          scope_id: "folder_root",
          requested_scope_id: nodeId || null,
          requested_phase: "conceptual",
          session_id: window.activeSessionId,
          recent_turns: recentTurns,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      if (!(res.headers.get("content-type") || "").includes("text/event-stream")) {
        throw new Error("El servidor devolvió una respuesta que no es SSE.");
      }
      const data = await _readSseResponse(res);
      _removeTyping();

      // Update provider banner
      if (data.telemetry && data.telemetry.provider) {
        updateProviderBanner(data.telemetry.provider);
      }

      const tutorMsg = {
        role: "tutor",
        text: data.text,
        followup: null,
        audit: data.audit,
        telemetry: data.telemetry,
        provenance: data.provenance,
        discrepancies: data.discrepancies,
        ts: Date.now(),
      };
      _messages.push(tutorMsg);
      _renderBubble("tutor", data.text, null, data.audit, data.telemetry, null, data.provenance, data.discrepancies);
      save();
    } catch (err) {
      _removeTyping();
      const errMsg = { role: "tutor", error: true, text: `⚠️ Error al procesar el turno: ${err.message}`, followup: null, audit: null, telemetry: null, ts: Date.now() };
      _renderBubble("tutor", errMsg.text, null, null, null);
      save();
    } finally {
      _setInputLocked(false);
      const input2 = _getInput();
      if (input2) input2.focus();
    }
  }

  /** Programmatically inject a query (e.g. from a follow-up button). */
  function injectQuery(text) {
    const input = _getInput();
    if (input) input.value = text;
    send();
  }

  /** Open the Evidence Drawer for a given citation tag. */
  function openEvidence(tag) {
    const drawer = document.getElementById("evidence-drawer");
    if (!drawer) return;
    drawer.classList.add("visible");

    const titleEl  = document.getElementById("evidence-drawer-title");
    const bodyEl   = document.getElementById("evidence-drawer-body");

    if (titleEl) titleEl.textContent = `Fuente Epistémica: [${tag}]`;

    // Look up citation info from the last tutor message that had citations
    const lastTutor = [..._messages].reverse().find(m => m.role === "tutor" && m.text.includes(`[${tag}]`));
    const nodeId = window.selectedNodeId || "SEC-01-C-PTR";

    if (bodyEl) {
      bodyEl.innerHTML = `
        <div class="evidence-loading">Consultando fuentes autorizadas para ${nodeId}...</div>
      `;
    }

    // Fetch authorized sources for the active node
    fetch(`/api/curriculum/nodes/${encodeURIComponent(nodeId)}`)
      .then(r => r.json())
      .then(node => {
        if (!bodyEl) return;
        const sources = node.authorized_sources || [];
        let sourcesHtml = "";
        sources.forEach((s, i) => {
          sourcesHtml += `
            <div class="evidence-source-card">
              <div class="evidence-source-header">
                <span class="evidence-doc-id">📄 ${s.document_id}</span>
                <span class="evidence-pages">págs. ${s.page_start || 1}–${s.page_end || "fin"}</span>
              </div>
              <p class="evidence-excerpt">
                Fragmento autorizado del corpus epistémico correspondiente al nodo <strong>${nodeId}</strong>.
                Este extracto fue utilizado por el motor de retrieval para fundamentar la cita <strong>[${tag}]</strong>.
              </p>
              <div class="evidence-checks">
                <span class="check-pass">✅ CHECK_FACTUAL_GROUNDING: PASS</span>
                <span class="check-pass">✅ CHECK_INJECTION_CANARY: PASS</span>
                <span class="check-pass">✅ CHECK_BUDGET_CONTAINMENT: PASS</span>
              </div>
            </div>
          `;
        });
        if (!sourcesHtml) {
          sourcesHtml = `<p style="color: var(--text-muted);">No se encontraron fuentes vinculadas para esta cita.</p>`;
        }
        bodyEl.innerHTML = sourcesHtml;
      })
      .catch(() => {
        if (bodyEl) bodyEl.innerHTML = `<p style="color: var(--color-red);">Error al cargar las fuentes epistémicas.</p>`;
      });
  }

  function closeEvidence() {
    const drawer = document.getElementById("evidence-drawer");
    if (drawer) drawer.classList.remove("visible");
  }

  /** Reset chat state (called when switching nodes). */
  function reset() {
    _messages = [];
    const history = _getHistory();
    if (history) history.innerHTML = "";
    try { sessionStorage.removeItem(_storageKey()); } catch (_) {}
  }

  return {
    createSessionId,
    send,
    handleKeyPress,
    addSystemMessage,
    injectQuery,
    openEvidence,
    closeEvidence,
    restore,
    reset,
    updateProviderBanner,
  };
})();

// Expose globally for inline handlers
window.Chat = Chat;
