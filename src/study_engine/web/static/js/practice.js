/**
 * KASIU Study Engine - Practice & Hermetic Sandbox Controller (Hito 10 / Fase 4)
 *
 * Manages the interactive code editor, localStorage draft persistence,
 * Tab key handling, sandbox submission to POST /api/session/practice/submit,
 * and rendering of the 3-tab feedback console (stdout/stderr, rubric, ledger).
 */

const Practice = (() => {
  let _taskId = null;
  let _nodeId = null;
  let _autoSaveTimer = null;
  let _activeConsoleTab = "stdout";

  // ── DOM Helpers ───────────────────────────────────────────────────

  function _getEditor()       { return document.getElementById("code-editor"); }
  function _getSubmitBtn()    { return document.getElementById("btn-submit-practice"); }
  function _getStatusLabel()  { return document.getElementById("practice-status-bar"); }
  function _getTaskDesc()     { return document.getElementById("practice-task-desc"); }

  // ── Initialization & Task Dispatch ────────────────────────────────

  async function init(nodeId) {
    _nodeId = nodeId || window.selectedNodeId || "SEC-01-C-PTR";
    const descEl = _getTaskDesc();
    if (descEl) descEl.innerHTML = `<p style="color: var(--text-secondary);">Cargando desafío práctico para ${_nodeId}...</p>`;

    try {
      const res = await fetch(`/api/session/practice/task?session_id=${encodeURIComponent(window.activeSessionId)}&node_id=${encodeURIComponent(_nodeId)}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      _taskId = data.task_id;

      // Render Markdown task description
      if (descEl) {
        let mdHtml = data.description;
        if (window.marked && window.DOMPurify) {
          mdHtml = window.DOMPurify.sanitize(window.marked.parse(data.description));
        }
        descEl.innerHTML = mdHtml;
      }

      // Restore code draft from localStorage or use template
      const editor = _getEditor();
      if (editor) {
        const savedDraft = localStorage.getItem(`kasiu_draft_${_taskId}`);
        if (savedDraft) {
          editor.value = savedDraft;
          _setStatus("💾 Borrador guardado localmente restaurado", "#60a5fa");
        } else {
          editor.value = data.template_code;
          _setStatus("✅ Plantilla inicial cargada", "#34d399");
        }
      }

      // Update task header labels
      const taskTitleEl = document.getElementById("practice-task-title");
      if (taskTitleEl) taskTitleEl.textContent = `${data.title} (${_nodeId})`;

    } catch (err) {
      console.error("Error al cargar la tarea de práctica:", err);
      if (descEl) {
        descEl.innerHTML = `<p style="color: var(--color-red);">⚠️ Error al cargar el desafío práctico: ${err.message}</p>`;
      }
    }
  }

  // ── Code Editor Event Handlers ────────────────────────────────────

  /** Handle Tab key inside textarea (insert 4 spaces). */
  function handleEditorKeyDown(event) {
    if (event.key === "Tab") {
      event.preventDefault();
      const editor = _getEditor();
      if (!editor) return;

      const start = editor.selectionStart;
      const end = editor.selectionEnd;

      // Insert 4 spaces
      editor.value = editor.value.substring(0, start) + "    " + editor.value.substring(end);
      editor.selectionStart = editor.selectionEnd = start + 4;

      triggerAutoSave();
    }
  }

  /** Trigger debounced auto-save to localStorage. */
  function triggerAutoSave() {
    clearTimeout(_autoSaveTimer);
    _autoSaveTimer = setTimeout(() => {
      if (!_taskId) return;
      const editor = _getEditor();
      if (editor) {
        localStorage.setItem(`kasiu_draft_${_taskId}`, editor.value);
        _setStatus("💾 Borrador guardado automáticamente (localStorage)", "#9ca3af");
      }
    }, 500);
  }

  /** Reset current draft to original template. */
  function resetDraft() {
    if (!_taskId) return;
    if (confirm("¿Estás seguro de resetear el código a la plantilla inicial? Se borrará tu borrador local.")) {
      localStorage.removeItem(`kasiu_draft_${_taskId}`);
      init(_nodeId);
    }
  }

  function _setStatus(msg, color = "#9ca3af") {
    const sb = _getStatusLabel();
    if (sb) {
      sb.textContent = msg;
      sb.style.color = color;
    }
  }

  // ── Console Tab Navigation ────────────────────────────────────────

  function switchConsoleTab(tabName) {
    _activeConsoleTab = tabName;
    const tabs = ["stdout", "rubric", "ledger"];
    tabs.forEach((t) => {
      const btn = document.getElementById(`console-tab-btn-${t}`);
      const view = document.getElementById(`console-tab-view-${t}`);
      if (btn) btn.classList.toggle("active", t === tabName);
      if (view) view.classList.toggle("active", t === tabName);
    });
  }

  // ── Code Submission & Execution ───────────────────────────────────

  async function submitSolution() {
    const editor = _getEditor();
    if (!editor) return;
    const code = editor.value.trim();
    if (!code) {
      alert("Por favor escribí alguna solución antes de enviar.");
      return;
    }

    const btn = _getSubmitBtn();
    const origText = btn ? btn.textContent : "Ejecutar y Entregar";

    if (btn) {
      btn.disabled = true;
      btn.textContent = "⏳ Ejecutando en Sandbox Tier 0...";
    }
    _setStatus("⚙️ Ejecutando evaluación hermética y rúbrica S9.1...", "#fbbf24");

    try {
      const res = await fetch("/api/session/practice/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: window.activeSessionId,
          node_id: _nodeId || window.selectedNodeId || "SEC-01-C-PTR",
          code: code,
        }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      _renderExecutionResults(data);

      if (data.passed) {
        _setStatus("✅ ¡DESAFÍO APROBADO! Evidencia sellada en el Ledger", "#34d399");
        // Reload DAG to reflect updated ASSESSED_PROFICIENT state
        if (typeof loadRoadmap === "function") loadRoadmap();
      } else {
        _setStatus("❌ Evaluación incompleta. Revisá la consola de rúbrica", "#f87171");
      }

    } catch (err) {
      console.error("Error en la ejecución:", err);
      _setStatus(`⚠️ Error de red/servidor: ${err.message}`, "#f87171");
      alert("Error al enviar la solución: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = origText;
      }
    }
  }

  // ── Render Results across 3 Console Tabs ─────────────────────────

  function _renderExecutionResults(data) {
    // 1. Tab 1: Stdout / Stderr
    const stdoutView = document.getElementById("console-tab-view-stdout");
    if (stdoutView) {
      const exec = data.execution || {};
      const isOk = exec.exit_code === 0;
      stdoutView.innerHTML = `
        <div class="console-summary-bar">
          <span class="badge ${isOk ? "badge-pass" : "badge-fail"}">Exit Code: ${exec.exit_code}</span>
          <span>Duración: ${exec.duration_ms || 12.5}ms</span>
          <span>Status: <strong>${data.status}</strong></span>
        </div>
        <div class="console-output-box">
          <div class="output-header">STDOUT (Salida Estándar):</div>
          <pre class="stdout-text">${_escapeHtml(exec.stdout || "(Sin salida estándar)")}</pre>
        </div>
        ${exec.stderr ? `
        <div class="console-output-box error">
          <div class="output-header error">STDERR (Salida de Error):</div>
          <pre class="stderr-text">${_escapeHtml(exec.stderr)}</pre>
        </div>` : ""}
      `;
    }

    // 2. Tab 2: Rúbrica & Score Breakdown
    const rubricView = document.getElementById("console-tab-view-rubric");
    if (rubricView) {
      let dimsHtml = "";
      const dims = data.rubric_dimensions || [];
      dims.forEach((d) => {
        const pct = (d.score * 100).toFixed(0);
        dimsHtml += `
          <div class="rubric-dim-card">
            <div class="rubric-dim-header">
              <span class="rubric-dim-name">${d.name || d.id} (Peso: ${(d.weight * 100).toFixed(0)}%)</span>
              <span class="rubric-dim-score">${pct}% [${d.level || "N/A"}]</span>
            </div>
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width: ${pct}%;"></div>
            </div>
          </div>
        `;
      });

      rubricView.innerHTML = `
        <div class="rubric-summary-card ${data.passed ? "passed" : "failed"}">
          <div class="rubric-overall">
            <span>Score Global: <strong>${(data.score * 100).toFixed(1)}%</strong></span>
            <span class="badge ${data.passed ? "badge-pass" : "badge-fail"}">${data.overall_level} (${data.passed ? "PASS" : "FAIL"})</span>
          </div>
          <p class="feedback-msg">${_escapeHtml(data.feedback_message)}</p>
        </div>
        <div class="rubric-dims-list">
          ${dimsHtml || "<p style='color: var(--text-muted);'>No hay desglose por dimensiones disponible.</p>"}
        </div>
      `;
    }

    // 3. Tab 3: Sovereign Ledger Commitment
    const ledgerView = document.getElementById("console-tab-view-ledger");
    if (ledgerView) {
      if (data.ledger_committed) {
        ledgerView.innerHTML = `
          <div class="ledger-commit-card success">
            <h4>📜 Evidencia Ingerida en el Ledger Inmutable (S5.2.A/B)</h4>
            <div class="ledger-detail-item">
              <span>Evidence Record ID:</span>
              <span class="font-mono">${data.evidence_record_id}</span>
            </div>
            <div class="ledger-detail-item">
              <span>Cryptographic Hash (SHA-256):</span>
              <span class="font-mono">${data.ledger_entry_hash}...</span>
            </div>
            <div class="ledger-detail-item">
              <span>Nuevo Estado del Nodo:</span>
              <span class="badge badge-pass">${data.updated_node_status || "ASSESSED_PROFICIENT"}</span>
            </div>
            <p style="font-size: 0.78rem; color: var(--text-muted); margin-top: 0.5rem;">
              La evidencia de maestría fue admitida y sellada de forma determinística en la base inmutable.
            </p>
          </div>
        `;
      } else {
        ledgerView.innerHTML = `
          <div class="ledger-commit-card rejected">
            <h4>⚠️ Evidencia Rechazada para Ingestión</h4>
            <p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
              La solución no alcanzó el umbral determinístico requerido por la rúbrica S9.1. No se ha modificado el estado del estudiante en el Ledger.
            </p>
          </div>
        `;
      }
    }

    // Default to Rubric tab if execution finished
    switchConsoleTab("rubric");
  }

  function _escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  return {
    init,
    handleEditorKeyDown,
    triggerAutoSave,
    resetDraft,
    switchConsoleTab,
    submitSolution,
  };
})();

// Expose globally
window.Practice = Practice;
