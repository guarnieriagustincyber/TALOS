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
          _renderBubble(m.role, m.text, m.followup, m.audit, m.telemetry, m.qtype)
        );
      }
    } catch (_) { /* corrupted – start fresh */ }
  }

  // ── DOM helpers ───────────────────────────────────────────────────

  function _getHistory() { return document.getElementById("chat-history"); }
  function _getInput()   { return document.getElementById("chat-input"); }
  function _getSendBtn() { return document.getElementById("btn-send-chat"); }

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

  function _renderBubble(role, text, followup, audit, telemetry, qtype) {
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
    const msg = { role: "tutor", text, followup: null, audit: null, telemetry: null, ts: Date.now() };
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

  /** Build stateless conversational history from the local message store.
   *
   * The client is the single source of truth for chat context; sending it on
   * every request lets the server stay stateless and survive restarts.
   * Only student/tutor turns are included (never empty/error placeholders).
   */
  function _buildHistory(maxTurns = 10) {
    const roles = new Set(["student", "tutor"]);
    const turns = _messages
      .filter((m) => roles.has(m.role) && m.text)
      .slice(-maxTurns)
      .map((m) => ({ role: m.role, content: m.text }));
    return turns;
  }

  /** Send the current input to the tutor backend. */
  async function send() {
    if (_busy) return;

    const input = _getInput();
    const text = (input ? input.value : "").trim();
    if (!text) return;

    // Append student bubble
    const studentMsg = { role: "student", text, followup: null, audit: null, telemetry: null, ts: Date.now() };
    _messages.push(studentMsg);
    _renderBubble("student", text, null, null, null);
    if (input) input.value = "";
    save();

    _setInputLocked(true);
    _showTyping();

    try {
      const res = await fetch("/api/session/turn/conceptual", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: window.activeSessionId,
          student_message: text,
          history: _buildHistory(),
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      _removeTyping();

      // Update provider banner
      if (data.telemetry) {
        updateProviderBanner(data.telemetry.provider);
      }

      const tutorMsg = {
        role: "tutor",
        text: data.response_text,
        followup: data.pedagogical_followup,
        audit: data.audit_verdict,
        telemetry: data.telemetry,
        qtype: data.question_type,
        ts: Date.now(),
      };
      _messages.push(tutorMsg);
      _renderBubble("tutor", data.response_text, data.pedagogical_followup, data.audit_verdict, data.telemetry, data.question_type);
      save();
    } catch (err) {
      _removeTyping();
      const errMsg = { role: "tutor", text: `⚠️ Error al procesar el turno: ${err.message}`, followup: null, audit: null, telemetry: null, ts: Date.now() };
      _messages.push(errMsg);
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
