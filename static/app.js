/**
 * app.js
 * Support Helper Frontend Application Logic
 * Adheres to FR-SUP-001 through FR-SUP-010.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM References
  const queryInput = document.getElementById("support-query-input");
  const searchBtn = document.getElementById("search-runbook-btn");
  const clearBtn = document.getElementById("clear-input-btn");
  const appFilter = document.getElementById("filter-app");
  const envFilter = document.getElementById("filter-env");
  const loadingIndicator = document.getElementById("loading-indicator");
  const resultsContainer = document.getElementById("results-container");
  const evidenceBanner = document.getElementById("evidence-banner");
  const fallbackBanner = document.getElementById("fallback-banner");
  const groundedContentView = document.getElementById("grounded-content-view");
  const themeToggleBtn = document.getElementById("theme-toggle-btn");
  const themeIcon = document.getElementById("theme-icon");
  const themeText = document.getElementById("theme-text");
  const toast = document.getElementById("app-toast");
  const kbCountBadge = document.getElementById("kb-count-badge");
  const headerKbStatus = document.getElementById("header-kb-status");
  const kbTableBody = document.getElementById("kb-table-body");
  const refreshKbBtn = document.getElementById("refresh-kb-btn");
  const uploadDropzone = document.getElementById("upload-dropzone");
  const pdfFileInput = document.getElementById("pdf-file-input");
  const docModal = document.getElementById("doc-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalDocTitle = document.getElementById("modal-doc-title");
  const modalMetaBar = document.getElementById("modal-meta-bar");
  const modalPageTabs = document.getElementById("modal-page-tabs");
  const modalPageContent = document.getElementById("modal-page-content");
  const viewDocBtn = document.getElementById("view-doc-btn");
  const downloadPdfLink = document.getElementById("download-pdf-link");

  // AI Modal References
  const aiSettingsBtn = document.getElementById("ai-settings-btn");
  const aiProviderLabel = document.getElementById("ai-provider-label");
  const aiModal = document.getElementById("ai-modal");
  const modalAiCloseBtn = document.getElementById("modal-ai-close-btn");
  const modalAiCancelBtn = document.getElementById("modal-ai-cancel-btn");
  const settingAiProvider = document.getElementById("setting-ai-provider");
  const settingOpenaiKey = document.getElementById("setting-openai-key");
  const settingOpenaiModel = document.getElementById("setting-openai-model");
  const settingOpenaiBaseurl = document.getElementById("setting-openai-baseurl");
  const saveOpenaiBtn = document.getElementById("save-openai-btn");
  const toggleKeyVisibilityBtn = document.getElementById("toggle-key-visibility-btn");
  const aiTestFeedback = document.getElementById("ai-test-feedback");
  const currentAiEngineText = document.getElementById("current-ai-engine-text");
  const openaiConfigFields = document.getElementById("openai-config-fields");

  let currentMatchedDocName = null;
  let cachedDocuments = [];

  // Load saved AI config from localStorage
  let aiConfig = {
    provider: localStorage.getItem("sh_ai_provider") || "openai",
    openai_key: localStorage.getItem("sh_openai_key") || "",
    openai_model: localStorage.getItem("sh_openai_model") || "gpt-4o-mini",
    openai_baseurl: localStorage.getItem("sh_openai_baseurl") || "https://api.openai.com/v1"
  };

  function updateAiHeaderBadge() {
    if (aiConfig.provider === "openai") {
      const hasKey = Boolean(aiConfig.openai_key);
      aiProviderLabel.textContent = hasKey ? `AI: OpenAI (${aiConfig.openai_model})` : `AI: OpenAI (Add Key)`;
      currentAiEngineText.textContent = hasKey ? `OpenAI API (${aiConfig.openai_model}) • Configured` : `OpenAI API (Please enter your API Key below)`;
    } else if (aiConfig.provider === "ollama") {
      aiProviderLabel.textContent = `AI: Ollama (Local)`;
      currentAiEngineText.textContent = `Ollama Local LLM (http://127.0.0.1:11434)`;
    } else {
      aiProviderLabel.textContent = `AI: Built-in`;
      currentAiEngineText.textContent = `Support Helper Built-in Neural Articulator (100% PDF Grounded)`;
    }
  }

  // Check server configuration for OpenAI key
  fetch("/api/settings/openai")
    .then(r => r.json())
    .then(data => {
      if (data.is_configured && !aiConfig.openai_key) {
        aiConfig.provider = "openai";
        aiConfig.openai_model = data.model;
        updateAiHeaderBadge();
      }
    })
    .catch(() => {});

  updateAiHeaderBadge();

  // AI Modal Interactions
  aiSettingsBtn.addEventListener("click", () => {
    settingAiProvider.value = aiConfig.provider;
    settingOpenaiKey.value = aiConfig.openai_key;
    settingOpenaiModel.value = aiConfig.openai_model;
    settingOpenaiBaseurl.value = aiConfig.openai_baseurl;
    openaiConfigFields.style.display = settingAiProvider.value === "openai" ? "block" : "none";
    aiTestFeedback.textContent = "";
    aiModal.style.display = "flex";
  });

  settingAiProvider.addEventListener("change", () => {
    openaiConfigFields.style.display = settingAiProvider.value === "openai" ? "block" : "none";
  });

  toggleKeyVisibilityBtn.addEventListener("click", () => {
    if (settingOpenaiKey.type === "password") {
      settingOpenaiKey.type = "text";
      toggleKeyVisibilityBtn.textContent = "Hide Key";
    } else {
      settingOpenaiKey.type = "password";
      toggleKeyVisibilityBtn.textContent = "Show Key";
    }
  });

  modalAiCloseBtn.addEventListener("click", () => { aiModal.style.display = "none"; });
  modalAiCancelBtn.addEventListener("click", () => { aiModal.style.display = "none"; });
  aiModal.addEventListener("click", (e) => {
    if (e.target === aiModal) aiModal.style.display = "none";
  });

  saveOpenaiBtn.addEventListener("click", async () => {
    const provider = settingAiProvider.value;
    const key = settingOpenaiKey.value.trim();
    const model = settingOpenaiModel.value;
    const baseurl = settingOpenaiBaseurl.value.trim();

    aiConfig.provider = provider;
    aiConfig.openai_model = model;
    aiConfig.openai_baseurl = baseurl;
    if (key) aiConfig.openai_key = key;

    localStorage.setItem("sh_ai_provider", provider);
    localStorage.setItem("sh_openai_model", model);
    localStorage.setItem("sh_openai_baseurl", baseurl);
    if (key) localStorage.setItem("sh_openai_key", key);

    if (provider === "openai" && key) {
      aiTestFeedback.textContent = "Testing connection with OpenAI...";
      aiTestFeedback.style.color = "var(--text-muted)";
      try {
        const res = await fetch("/api/settings/openai", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ api_key: key, model: model, base_url: baseurl })
        });
        const data = await res.json();
        if (res.ok) {
          aiTestFeedback.textContent = "✅ " + data.message;
          aiTestFeedback.style.color = "var(--lg-600)";
          showToast(`OpenAI connected! Active model: ${model}`);
          updateAiHeaderBadge();
          setTimeout(() => { aiModal.style.display = "none"; }, 1200);
        } else {
          aiTestFeedback.textContent = "❌ " + (data.detail || "Connection failed");
          aiTestFeedback.style.color = "#dc2626";
        }
      } catch (err) {
        aiTestFeedback.textContent = "❌ " + err.message;
        aiTestFeedback.style.color = "#dc2626";
      }
    } else {
      updateAiHeaderBadge();
      showToast(`AI Articulation Engine set to: ${provider}`);
      aiModal.style.display = "none";
    }
  });

  // ==========================================
  // 1. THEME SWITCHER (Dark Green / Light Green)
  // ==========================================
  themeToggleBtn.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("theme-dark-green");
    if (isDark) {
      document.body.classList.remove("theme-light-green");
      themeIcon.textContent = "☀️";
      themeText.textContent = "Light Green Canvas";
    } else {
      document.body.classList.add("theme-light-green");
      themeIcon.textContent = "🌙";
      themeText.textContent = "Dark Green Canvas";
    }
  });

  // ==========================================
  // 2. TAB NAVIGATION
  // ==========================================
  const navTabs = document.querySelectorAll(".nav-tab");
  navTabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      navTabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      const targetPaneId = tab.getAttribute("data-tab");
      document.querySelectorAll(".tab-pane").forEach((pane) => {
        pane.classList.remove("active");
      });
      const activePane = document.getElementById(targetPaneId);
      if (activePane) activePane.classList.add("active");

      if (targetPaneId === "tab-knowledge") {
        loadKnowledgeBase();
      } else if (targetPaneId === "tab-sequences") {
        loadRecoverySequences();
      } else if (targetPaneId === "tab-instructions") {
        loadAgentInstructions();
      }
    });
  });

  // ==========================================
  // 3. FAST INCIDENT PRESETS
  // ==========================================
  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const q = chip.getAttribute("data-query");
      queryInput.value = q;
      executeSearch();
    });
  });

  clearBtn.addEventListener("click", () => {
    queryInput.value = "";
    resultsContainer.style.display = "none";
    queryInput.focus();
  });

  searchBtn.addEventListener("click", executeSearch);
  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      executeSearch();
    }
  });

  // ==========================================
  // 4. SEARCH & GROUNDING (FR-SUP-001 - 005)
  // ==========================================
  async function executeSearch() {
    const query = queryInput.value.trim();
    if (!query) {
      showToast("Please enter an incident description or error message.");
      queryInput.focus();
      return;
    }

    loadingIndicator.style.display = "block";
    resultsContainer.style.display = "none";

    try {
      const response = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          application: appFilter.value,
          environment: envFilter.value,
          ai_provider: aiConfig.provider,
          custom_key: aiConfig.openai_key || undefined,
          custom_endpoint: aiConfig.openai_baseurl || undefined,
          custom_model: aiConfig.openai_model || undefined,
          enable_ai: true
        })
      });

      if (!response.ok) {
        throw new Error(`Search failed: HTTP ${response.status}`);
      }

      const data = await response.json();
      renderSearchResults(data);
    } catch (err) {
      console.error(err);
      showToast(`Error communicating with RAG Engine: ${err.message}`);
    } finally {
      loadingIndicator.style.display = "none";
      resultsContainer.style.display = "block";
      resultsContainer.scrollIntoView({ behavior: "smooth" });
    }
  }

  function renderSearchResults(data) {
    if (data.grounded && data.status === "APPROVED_RUNBOOK_FOUND") {
      // CASE A: APPROVED RUNBOOK GROUNDED MATCH
      evidenceBanner.style.display = "flex";
      fallbackBanner.style.display = "none";
      groundedContentView.style.display = "block";

      const doc = data.matched_document;
      currentMatchedDocName = doc.filename;

      // Evidence Banner
      document.getElementById("evidence-score-value").textContent = `${data.confidence_score}%`;
      document.getElementById("evidence-doc-title").textContent = `[${doc.doc_id}] ${doc.title}`;
      document.getElementById("evidence-citation-line").textContent = 
        `Grounded in ${doc.filename} • Pages 1-${doc.total_pages} (${data.confidence_rating})`;
      downloadPdfLink.href = `/api/documents/${encodeURIComponent(doc.filename)}/download`;

      // Render AI Articulated Guidance (Grounded in PDF facts)
      const aiCard = document.getElementById("ai-articulated-card");
      const aiMarkdown = document.getElementById("ai-markdown-content");
      const aiModelPill = document.getElementById("ai-model-pill");
      const aiProviderAlert = document.getElementById("ai-provider-alert");

      if (data.ai_articulation) {
        aiCard.style.display = "block";
        aiModelPill.textContent = data.ai_articulation.articulated_by || "AI Articulated";
        
        if (data.ai_articulation.provider_notice) {
          aiProviderAlert.style.display = "block";
          aiProviderAlert.textContent = "ℹ️ " + data.ai_articulation.provider_notice;
        } else {
          aiProviderAlert.style.display = "none";
        }

        aiMarkdown.innerHTML = formatMarkdown(data.ai_articulation.markdown_articulation || "");
      } else {
        aiCard.style.display = "none";
      }

      // Metadata Grid (FR-SUP-006)
      const metaGrid = document.getElementById("metadata-grid");
      metaGrid.innerHTML = `
        <div class="meta-item"><span class="meta-label">Application</span><span class="meta-value">${escapeHtml(doc.application)}</span></div>
        <div class="meta-item"><span class="meta-label">Service</span><span class="meta-value">${escapeHtml(doc.service)}</span></div>
        <div class="meta-item"><span class="meta-label">Region</span><span class="meta-value">${escapeHtml(doc.region)}</span></div>
        <div class="meta-item"><span class="meta-label">Environment</span><span class="meta-value">${escapeHtml(doc.environment)}</span></div>
        <div class="meta-item"><span class="meta-label">Category</span><span class="meta-value">${escapeHtml(doc.category)}</span></div>
        <div class="meta-item"><span class="meta-label">Owner / Team</span><span class="meta-value">${escapeHtml(doc.owner)}</span></div>
        <div class="meta-item"><span class="meta-label">Version</span><span class="meta-value">${escapeHtml(doc.version)}</span></div>
        <div class="meta-item"><span class="meta-label">Last Updated</span><span class="meta-value">${escapeHtml(doc.last_updated)}</span></div>
      `;

      // Summary & Causes
      document.getElementById("res-summary-text").textContent = data.issue_summary;
      
      const symptomsList = document.getElementById("res-symptoms-list");
      symptomsList.innerHTML = (data.symptoms_matched || []).map(s => `<li>${escapeHtml(s)}</li>`).join("");

      const causesList = document.getElementById("res-causes-list");
      causesList.innerHTML = (data.possible_causes || []).map(c => `<li>${escapeHtml(c)}</li>`).join("");

      // Critical Warnings (DO NOT DO) (FR-SUP-003)
      const warningsList = document.getElementById("warnings-list");
      if (data.warnings_do_not_do && data.warnings_do_not_do.length > 0) {
        warningsList.innerHTML = data.warnings_do_not_do.map(w => `
          <div class="warning-item">
            <span style="font-size: 16px;">🛑</span>
            <span>${escapeHtml(w)}</span>
          </div>
        `).join("");
      } else {
        warningsList.innerHTML = `<p style="font-size: 13px; color: var(--text-muted);">No critical safety warnings cataloged for this runbook.</p>`;
      }

      // Numbered Steps (FR-SUP-003)
      const stepsList = document.getElementById("resolution-steps-list");
      if (data.resolution_steps && data.resolution_steps.length > 0) {
        stepsList.innerHTML = data.resolution_steps.map((st, i) => `
          <div class="step-card">
            <input type="checkbox" id="chk-step-${st.step_number}" class="step-checkbox" title="Mark step completed">
            <div class="step-content">
              <div class="step-title-row">
                <span class="step-badge">Step ${st.step_number}</span>
                <span class="step-title">${escapeHtml(st.title)}</span>
              </div>
              <div class="step-detail">${escapeHtml(st.detail)}</div>
              ${st.command ? `
                <div class="command-block">
                  <div class="command-header">
                    <span class="command-type-tag">${escapeHtml(st.cmd_type || 'Script')}</span>
                    <button class="copy-btn" onclick="copyCode(this, \`${escapeJsString(st.command)}\`)">📋 Copy Command</button>
                  </div>
                  <div class="command-text">${escapeHtml(st.command)}</div>
                </div>
              ` : ''}
            </div>
          </div>
        `).join("");
      } else {
        stepsList.innerHTML = `<p style="font-size: 13px; color: var(--text-muted);">Refer to detailed instructions in approved PDF.</p>`;
      }

      // Verification Steps (FR-SUP-003)
      const verList = document.getElementById("verification-steps-list");
      if (data.verification_steps && data.verification_steps.length > 0) {
        verList.innerHTML = data.verification_steps.map((v, i) => `
          <div style="margin-bottom: 6px; display: flex; align-items: flex-start; gap: 8px;">
            <span style="color: var(--lg-600); font-weight: 800;">✓</span>
            <span><strong>V-${i+1}:</strong> ${escapeHtml(v)}</span>
          </div>
        `).join("");
      } else {
        verList.innerHTML = `<p style="font-size: 13px; color: var(--text-muted);">Standard health checks apply.</p>`;
      }

      // Recovery Sequence (FR-SUP-009)
      const seqSection = document.getElementById("recovery-sequence-section");
      const chainList = document.getElementById("recovery-chain-list");
      const stopGateBox = document.getElementById("stop-gate-box");

      if (data.recovery_sequence && data.recovery_sequence.chain && data.recovery_sequence.chain.length > 0) {
        seqSection.style.display = "block";
        chainList.innerHTML = data.recovery_sequence.chain.map((node, i) => `
          <div class="chain-node">
            <div class="node-idx">${i + 1}</div>
            <div>${escapeHtml(node)}</div>
          </div>
          ${i < data.recovery_sequence.chain.length - 1 ? `<div class="chain-arrow">▼</div>` : ''}
        `).join("");

        stopGateBox.innerHTML = `
          <span style="font-size: 18px;">⛔</span>
          <div>
            <strong>EXPLICIT STOP / ESCALATE GATE:</strong><br/>
            ${escapeHtml(data.recovery_sequence.stop_condition || 'Abort recovery immediately if verification fails.')}
          </div>
        `;
      } else {
        seqSection.style.display = "none";
      }

      // Grounded Commands (FR-SUP-010)
      const commandsSection = document.getElementById("commands-section");
      const commandsList = document.getElementById("commands-list-container");

      if (data.grounded_commands && data.grounded_commands.length > 0) {
        commandsSection.style.display = "block";
        commandsList.innerHTML = data.grounded_commands.map((cmd) => `
          <div class="command-block">
            <div class="command-header">
              <span class="command-type-tag">${escapeHtml(cmd.type)} (Step ${cmd.step}: ${escapeHtml(cmd.title)})</span>
              <button class="copy-btn" onclick="copyCode(this, \`${escapeJsString(cmd.command)}\`)">📋 Copy Script</button>
            </div>
            <div class="command-text">${escapeHtml(cmd.command)}</div>
          </div>
        `).join("");
      } else {
        commandsSection.style.display = "none";
      }

      // Edge Cases & Escalation
      const edgeList = document.getElementById("edge-cases-list");
      edgeList.innerHTML = (data.edge_cases || []).map(e => `<li>${escapeHtml(e)}</li>`).join("");

      const esc = data.escalation || {};
      const escGrid = document.getElementById("approved-escalation-grid");
      escGrid.innerHTML = `
        <div class="escalation-card">
          <h4>Primary On-Call Support</h4>
          <p style="font-size: 13px; color: var(--text-main); font-weight: 600;">${escapeHtml(esc.primary || 'APS On-Call Lead')}</p>
          <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">SLA: ${escapeHtml(esc.sla || 'P1: 15 mins')}</p>
        </div>
        <div class="escalation-card">
          <h4>Secondary / Technical Escalation</h4>
          <p style="font-size: 13px; color: var(--text-main); font-weight: 600;">${escapeHtml(esc.secondary || 'Engineering Duty Desk')}</p>
          <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Condition: ${escapeHtml(esc.condition || 'Persistent outage')}</p>
        </div>
      `;

      // Citations (FR-SUP-007)
      const citList = document.getElementById("citations-list");
      if (data.citations && data.citations.length > 0) {
        citList.innerHTML = data.citations.map((c) => `
          <div class="citation-card">
            <div class="citation-meta">
              <span>📄 Document: <strong>${escapeHtml(c.document)}</strong></span>
              <span>Page: <strong>${c.page}</strong> | Section: <strong>${escapeHtml(c.section)}</strong></span>
            </div>
            <div class="citation-excerpt">"${escapeHtml(c.excerpt)}"</div>
          </div>
        `).join("");
      } else {
        citList.innerHTML = `<p style="font-size: 13px; color: var(--text-muted);">Source Reference: ${escapeHtml(data.source_reference)}</p>`;
      }

    } else {
      // CASE B: FALLBACK WHEN NO APPROVED RUNBOOK EXISTS (FR-SUP-004, FR-SUP-005)
      evidenceBanner.style.display = "none";
      groundedContentView.style.display = "none";
      fallbackBanner.style.display = "block";

      const fallbackGrid = document.getElementById("fallback-escalation-grid");
      const escPath = data.normal_escalation_path || {};
      const contacts = escPath.standard_contacts || [];

      fallbackGrid.innerHTML = contacts.map(c => `
        <div class="escalation-card">
          <h4>${escapeHtml(c.role)}</h4>
          <p style="font-size: 13px; color: var(--text-main); font-weight: 600;">${escapeHtml(c.channel)}</p>
          ${c.phone ? `<p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">Phone: ${escapeHtml(c.phone)}</p>` : ''}
          ${c.sla ? `<p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">SLA: ${escapeHtml(c.sla)}</p>` : ''}
        </div>
      `).join("");

      const checklistBox = document.getElementById("fallback-checklist-box");
      const checklist = escPath.incident_triage_checklist || [];
      checklistBox.innerHTML = `
        <h4 style="font-size: 13.5px; font-weight: 700; color: var(--text-main); margin-bottom: 6px;">
          Level-1 Incident Triage Checklist before Escalation:
        </h4>
        <ul style="margin-left: 20px; font-size: 13px; color: var(--text-muted); line-height: 1.6;">
          ${checklist.map(item => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
      `;
    }
  }

  // ==========================================
  // 5. KNOWLEDGE BASE REPOSITORY (FR-SUP-006, 007)
  // ==========================================
  async function loadKnowledgeBase() {
    try {
      const res = await fetch("/api/documents");
      const data = await res.json();
      cachedDocuments = data.documents || [];
      kbCountBadge.textContent = data.count;
      headerKbStatus.textContent = `Local PDF Grounding Active (${data.count} Runbooks)`;

      kbTableBody.innerHTML = cachedDocuments.map(doc => `
        <tr>
          <td><span class="table-badge">${escapeHtml(doc.doc_id)}</span></td>
          <td><strong>${escapeHtml(doc.title)}</strong></td>
          <td>${escapeHtml(doc.application)}</td>
          <td>${escapeHtml(doc.service)}</td>
          <td>${escapeHtml(doc.region)}</td>
          <td>${escapeHtml(doc.version)}</td>
          <td>${doc.num_pages}</td>
          <td><span class="table-badge">${doc.commands_count} cmds</span></td>
          <td>
            <button class="table-action-btn" onclick="openDocModal('${escapeHtml(doc.filename)}')">Inspect</button>
            <a href="/api/documents/${encodeURIComponent(doc.filename)}/download" target="_blank" style="margin-left: 4px; font-size: 12px; color: var(--text-main); text-decoration: underline;">PDF</a>
          </td>
        </tr>
      `).join("");
    } catch (err) {
      console.error(err);
      showToast("Failed to load approved runbook catalog.");
    }
  }

  refreshKbBtn.addEventListener("click", () => {
    loadKnowledgeBase();
    showToast("Approved Knowledge Base refreshed.");
  });

  // PDF Uploader (FR-SUP-007, FR-SUP-008)
  uploadDropzone.addEventListener("click", () => pdfFileInput.click());
  uploadDropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadDropzone.style.borderColor = "var(--lg-500)";
  });
  uploadDropzone.addEventListener("dragleave", () => {
    uploadDropzone.style.borderColor = "var(--border-strong)";
  });
  uploadDropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadDropzone.style.borderColor = "var(--border-strong)";
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  pdfFileInput.addEventListener("change", () => {
    if (pdfFileInput.files && pdfFileInput.files.length > 0) {
      handleFileUpload(pdfFileInput.files[0]);
    }
  });

  async function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showToast("Only PDF documents (.pdf) exported from Wiki are supported.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    showToast(`Uploading and indexing "${file.name}"...`);

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Upload failed");
      }

      const resData = await res.json();
      showToast(`Success: ${resData.message}`);
      loadKnowledgeBase();
    } catch (err) {
      console.error(err);
      showToast(`Upload failed: ${err.message}`);
    }
  }

  // ==========================================
  // 6. OPERATIONAL RECOVERY SEQUENCES (FR-SUP-009)
  // ==========================================
  async function loadRecoverySequences() {
    const container = document.getElementById("sequences-catalog-container");
    container.innerHTML = `<p style="font-size: 13px; color: var(--text-muted);">Loading dependency-aware recovery sequences...</p>`;

    try {
      const res = await fetch("/api/recovery-sequences");
      const data = await res.json();
      const sequences = data.sequences || [];

      if (sequences.length === 0) {
        container.innerHTML = `<p>No recovery sequences found.</p>`;
        return;
      }

      container.innerHTML = sequences.map((seq, idx) => `
        <div class="result-section">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div>
              <span class="table-badge">${escapeHtml(seq.doc_id)}</span>
              <strong style="margin-left: 8px; font-size: 15px; color: var(--text-main);">${escapeHtml(seq.title)}</strong>
            </div>
            <span style="font-size: 12px; color: var(--text-muted);">${escapeHtml(seq.application)} • ${escapeHtml(seq.service)}</span>
          </div>

          <div class="recovery-chain" style="margin-top: 10px;">
            ${seq.chain.map((c, i) => `
              <div class="chain-node">
                <div class="node-idx">${i + 1}</div>
                <div>${escapeHtml(c)}</div>
              </div>
              ${i < seq.chain.length - 1 ? `<div class="chain-arrow">▼</div>` : ''}
            `).join("")}
          </div>

          <div class="stop-gate-box" style="margin-top: 10px;">
            <span style="font-size: 18px;">⛔</span>
            <div>
              <strong>EXPLICIT STOP / ESCALATE GATE:</strong><br/>
              ${escapeHtml(seq.stop_condition)}
            </div>
          </div>
        </div>
      `).join("");

    } catch (err) {
      console.error(err);
      container.innerHTML = `<p style="color: red;">Failed to load recovery sequences.</p>`;
    }
  }

  // ==========================================
  // 7. DOCUMENT INSPECTOR MODAL
  // ==========================================
  window.openDocModal = async function(filename) {
    modalDocTitle.textContent = `Approved Runbook: ${filename}`;
    modalMetaBar.textContent = "Loading extracted text and pages...";
    modalPageTabs.innerHTML = "";
    modalPageContent.textContent = "";
    docModal.style.display = "flex";

    try {
      const res = await fetch(`/api/documents/${encodeURIComponent(filename)}`);
      if (!res.ok) throw new Error("Could not retrieve document details");
      const doc = await res.json();

      modalMetaBar.innerHTML = `
        <strong>App:</strong> ${escapeHtml(doc.metadata.application || 'N/A')} | 
        <strong>Service:</strong> ${escapeHtml(doc.metadata.service || 'N/A')} | 
        <strong>Version:</strong> ${escapeHtml(doc.metadata.version || '1.0')} | 
        <strong>Pages:</strong> ${doc.num_pages} | 
        <a href="/api/documents/${encodeURIComponent(filename)}/download" target="_blank" style="color: var(--text-main); text-decoration: underline; font-weight: 700;">Open Original PDF</a>
      `;

      modalPageTabs.innerHTML = doc.pages.map((p, i) => `
        <button class="page-tab-btn ${i === 0 ? 'active' : ''}" onclick="switchModalPage(${i})">
          Page ${p.page_number}
        </button>
      `).join("");

      window._activeDocPages = doc.pages;
      if (doc.pages.length > 0) {
        modalPageContent.textContent = doc.pages[0].text;
      }
    } catch (err) {
      console.error(err);
      modalMetaBar.textContent = "Error loading document.";
    }
  };

  window.switchModalPage = function(pageIndex) {
    document.querySelectorAll(".page-tab-btn").forEach((btn, idx) => {
      btn.classList.toggle("active", idx === pageIndex);
    });
    if (window._activeDocPages && window._activeDocPages[pageIndex]) {
      modalPageContent.textContent = window._activeDocPages[pageIndex].text;
    }
  };

  viewDocBtn.addEventListener("click", () => {
    if (currentMatchedDocName) {
      openDocModal(currentMatchedDocName);
    }
  });

  modalCloseBtn.addEventListener("click", () => {
    docModal.style.display = "none";
  });

  docModal.addEventListener("click", (e) => {
    if (e.target === docModal) {
      docModal.style.display = "none";
    }
  });

  // ==========================================
  // 8. CLIPBOARD & TOAST UTILITIES (FR-SUP-010)
  // ==========================================
  window.copyCode = function(button, codeText) {
    navigator.clipboard.writeText(codeText).then(() => {
      const origText = button.innerHTML;
      button.innerHTML = "✅ Copied!";
      showToast("Command copied to clipboard. Manual review required prior to execution (FR-SUP-010).");
      setTimeout(() => {
        button.innerHTML = origText;
      }, 2000);
    }).catch(err => {
      console.error(err);
      showToast("Unable to copy to clipboard.");
    });
  };

  function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => {
      toast.classList.remove("show");
    }, 3800);
  }

  function escapeHtml(text) {
    if (!text) return "";
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function escapeJsString(text) {
    if (!text) return "";
    return String(text)
      .replace(/\\/g, "\\\\")
      .replace(/`/g, "\\`")
      .replace(/\$/g, "\\$");
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);
    // Headings
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2 style="font-size: 16px; margin-top: 14px; margin-bottom: 6px;">$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1 style="font-size: 18px; margin-top: 14px; margin-bottom: 6px;">$1</h1>');
    // Horizontal Rule
    html = html.replace(/^---$/gim, '<hr>');
    // Blockquote
    html = html.replace(/^&gt; (.*$)/gim, '<blockquote>$1</blockquote>');
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Code inline
    html = html.replace(/`(.*?)`/g, '<code style="background: rgba(34, 197, 94, 0.15); padding: 2px 5px; border-radius: 4px; font-family: monospace;">$1</code>');
    // Bullet lists
    html = html.replace(/^\- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gms, '<ul style="margin-left: 20px; margin-bottom: 10px;">$1</ul>');
    // Paragraph newlines
    html = html.replace(/\n\n/g, '<br><br>');
    return html;
  }

  // ==========================================
  // 9. AGENT INSTRUCTIONS (ADMIN PANEL)
  // ==========================================
  window.switchToTab = function(tabId) {
    document.querySelectorAll(".nav-tab").forEach(t => {
      t.classList.toggle("active", t.getAttribute("data-tab") === tabId);
    });
    document.querySelectorAll(".tab-pane").forEach(p => {
      p.classList.toggle("active", p.id === tabId);
    });
  };

  const agentInstructionsEditor = document.getElementById("agent-instructions-editor");
  const saveInstructionsBtn = document.getElementById("save-instructions-btn");
  const resetInstructionsBtn = document.getElementById("reset-instructions-btn");
  const instructionsStatusMsg = document.getElementById("instructions-status-msg");
  const instructionsCharCount = document.getElementById("instructions-char-count");
  const adminUploadDocBtn = document.getElementById("admin-upload-doc-btn");
  const adminSyncDocBtn = document.getElementById("admin-sync-doc-btn");
  const adminDocList = document.getElementById("admin-doc-list");
  const adminSwitchChatBtn = document.getElementById("admin-switch-chat-btn");
  let savedAgentInstructions = "";
  let maxAgentInstructionsLength = 20000;

  function updateInstructionsEditorState() {
    if (!agentInstructionsEditor) return;
    const length = agentInstructionsEditor.value.length;
    const isDirty = agentInstructionsEditor.value !== savedAgentInstructions;
    instructionsCharCount.textContent = `${length.toLocaleString()} / ${maxAgentInstructionsLength.toLocaleString()}`;
    saveInstructionsBtn.disabled = !isDirty || length === 0 || length > maxAgentInstructionsLength;
    if (isDirty && length > 0 && length <= maxAgentInstructionsLength) {
      instructionsStatusMsg.textContent = "Unsaved changes";
    }
  }

  if (agentInstructionsEditor) {
    agentInstructionsEditor.addEventListener("input", updateInstructionsEditorState);
  }

  if (adminSwitchChatBtn) {
    adminSwitchChatBtn.addEventListener("click", () => switchToTab("tab-assistant"));
  }
  if (adminUploadDocBtn) {
    adminUploadDocBtn.addEventListener("click", () => pdfFileInput.click());
  }
  if (adminSyncDocBtn) {
    adminSyncDocBtn.addEventListener("click", () => {
      loadKnowledgeBase();
      loadAgentInstructions();
      showToast("Documents synchronized.");
    });
  }

  async function loadAgentInstructions() {
    try {
      const res = await fetch("/api/agent-instructions");
      const data = await res.json();
      if (agentInstructionsEditor) {
        agentInstructionsEditor.value = data.instructions || "";
        savedAgentInstructions = agentInstructionsEditor.value;
        maxAgentInstructionsLength = data.max_length || 20000;
        agentInstructionsEditor.maxLength = maxAgentInstructionsLength;
        updateInstructionsEditorState();
      }
      updateAdminDocList();
    } catch (err) {
      console.error(err);
    }
  }

  function updateAdminDocList() {
    if (!adminDocList) return;
    if (cachedDocuments.length === 0) {
      adminDocList.innerHTML = `<span style="color: var(--text-muted);">No documents yet</span>`;
      return;
    }
    adminDocList.innerHTML = cachedDocuments.map(d => `
      <div style="display: flex; align-items: center; gap: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${escapeHtml(d.filename)}">
        <span style="color: var(--lg-500);">📄</span>
        <span style="overflow: hidden; text-overflow: ellipsis;">${escapeHtml(d.filename)}</span>
      </div>
    `).join("");
  }

  if (saveInstructionsBtn) {
    saveInstructionsBtn.addEventListener("click", async () => {
      const text = agentInstructionsEditor.value;
      if (!text.trim()) {
        instructionsStatusMsg.textContent = "Instructions cannot be empty.";
        return;
      }
      instructionsStatusMsg.textContent = "Saving...";
      try {
        const res = await fetch("/api/agent-instructions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ instructions: text })
        });
        const data = await res.json();
        if (res.ok) {
          savedAgentInstructions = text.trim() + "\n";
          agentInstructionsEditor.value = savedAgentInstructions;
          instructionsStatusMsg.textContent = "Saved successfully.";
          updateInstructionsEditorState();
          showToast("Agent instructions saved and injected into prompt!");
        } else {
          instructionsStatusMsg.textContent = data.detail || "Failed to save.";
        }
      } catch (err) {
        instructionsStatusMsg.textContent = "Error: " + err.message;
      }
    });
  }

  if (resetInstructionsBtn) {
    resetInstructionsBtn.addEventListener("click", () => {
      agentInstructionsEditor.value = 
`<!-- Edit this file (or use the Admin panel) to guide the agent's scope and behavior. -->
<!-- It's injected into the system prompt on every chat request. -->

- Stay focused on topics covered by the uploaded documents when they're relevant.
- If a question is out of scope, say so instead of guessing.
- Ground all recommendations strictly in approved runbook procedures and evidence.
- Prominently highlight critical "DO NOT DO" warnings and safety directives.
- Generate commands (PowerShell, Bash, SQL) only when grounded in an approved runbook.
- Never execute commands automatically; require manual operator review.`;
      showToast("Reset to default instructions template. Click Save to persist.");
      updateInstructionsEditorState();
    });
  }

  // Initial load
  loadKnowledgeBase();
  loadAgentInstructions();
});
