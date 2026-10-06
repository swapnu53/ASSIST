# Support Helper (FXT APS Assistant)

An evidence-based assistant for Application Support (APS) teams handling incidents, alerts, error messages, operational queries, and approved recovery procedures.

Strictly grounded in approved local PDF runbooks (Wiki / Knowledge Base exports). **Zero hallucination guaranteed** (FR-SUP-004).

---

## 🎨 Design Theme
Built strictly using a professional, clean two-color combination of **Dark Green** and **Light Green**:
- **Dark Green Palette:** Deep Forest (`#022013`), Emerald Base (`#064e3b`), Pine Green (`#065f46`), Jade Accent (`#047857`)
- **Light Green Palette:** Mint Background (`#f0fdf4`), Pastel Green (`#dcfce7`), Bright Emerald (`#22c55e`), Spring Green (`#4ade80`)
- **Dual Canvas Modes:** Toggle effortlessly between **Light Green Canvas** and **Dark Green Canvas** via the header switch.

---

## 📋 Requirements Traceability Matrix

| ID | Requirement | Priority | Status | Implementation Details |
| :--- | :--- | :---: | :---: | :--- |
| **FR-SUP-001** | Support Helper input area for issue descriptions, alerts, error logs, emails, app/service names, or operational symptoms | Must (MVP) | ✅ Verified | Multi-line input area with quick filter selectors (Application, Environment) and 1-click incident presets |
| **FR-SUP-002** | Search approved local knowledge and return the most relevant support procedure | Must (MVP) | ✅ Verified | Hybrid RAG retrieval engine (BM25 + TF-IDF + Error signature matching + metadata scoring) |
| **FR-SUP-003** | Structured result display: issue summary, possible causes, numbered resolution steps, verification steps, warnings / DO NOT DO actions, edge cases, escalation contacts, and source citations | Must (MVP) | ✅ Verified | Visual modular cards with step checkboxes, high-visibility DO NOT DO warnings, and post-recovery verification items |
| **FR-SUP-004** | Anti-hallucination guarantee: Do NOT invent procedures, servers, owners, commands, or contacts without approved source | Must (MVP) | ✅ Verified | Strict confidence cutoff (< 26%). Unapproved queries do not invent details and route directly to normal escalation |
| **FR-SUP-005** | If no sufficiently relevant approved source is found, state clearly and direct user to normal escalation path | Must (MVP) | ✅ Verified | Renders clear fallback notice with standard Level-1 incident triage checklist and Global Incident Command contacts |
| **FR-SUP-006** | Knowledge content supports comprehensive metadata (Title, Application, Service, Region, Environment, Category, Owner, Version, Last Updated, Doc ID) | Should (MVP/2) | ✅ Verified | Preserved in PDF parser, displayed in structured metadata grid, and searchable across runbooks |
| **FR-SUP-007** | Support PDF documents exported from Wiki/KB and preserve document/page/section references for citations | Must (Phase 2) | ✅ Verified | PyPDF parser extracts pages and sections; live PDF uploader automatically ingests and indexes new documents; modal viewer enables page-by-page inspection |
| **FR-SUP-008** | Semantic/RAG retrieval across approved PDF knowledge | Should (Phase 2/3) | ✅ Verified | Tokenized inverted index with cosine and BM25 term weighting across PDF text chunks |
| **FR-SUP-009** | Dependency-aware service start/stop/recovery sequences with explicit stop/escalate conditions | Should (Phase 2) | ✅ Verified | Visual service dependency flow chain with high-visibility ⛔ EXPLICIT STOP / ESCALATE GATE |
| **FR-SUP-010** | Grounded command generation (PowerShell, Bash, SQL) with manual operator review policy (no automated background execution) | Should (Phase 2) | ✅ Verified | Syntax-formatted command blocks with 1-click clipboard copy and explicit safety policy enforcement disclaimer |

---

## ✨ AI Articulation Layer (OpenAI & Pluggable LLMs)
Support Helper integrates an AI articulation layer that takes the user's incident query + the facts retrieved from your approved local PDF runbooks, and articulates a clear, contextual, and professional response:

Administrators can open **Agent Instructions (Admin)**, edit the persistent behavior rules, and save them. The saved text is added to the system prompt for every OpenAI, Ollama, and Gemini chat request. Mandatory grounding and safety rules retain higher priority. The zero-config built-in fallback is deterministic and therefore does not interpret arbitrary natural-language instructions.
- **🎯 Incident Triage Assessment**: Contextual to specific counterparties, ports, and errors pasted.
- **🔍 Diagnostic Root Cause**: Explains the technical failure grounded in runbook facts.
- **🛑 Critical Operational Safety Directive**: Prominently highlights mandatory DO NOT DO actions.
- **⚡ Step-by-Step Recovery Plan**: Sequenced numbered guide.
- **🔄 Dependency-Aware Restart Chain**: Service start/stop sequence with explicit stop gates.
- **🧪 Verification Checklist**: Concrete post-recovery health checks.

### How to Use Your OpenAI API Key:
You have three easy ways to provide your OpenAI API key:

#### Option 1: Directly in the Web UI (Easiest)
1. Open [http://127.0.0.1:8055](http://127.0.0.1:8055).
2. Click the **✨ AI Settings** button in the top-right header.
3. Paste your OpenAI API key (`sk-proj-...`) into the input field.
4. Select your preferred model (`gpt-4o-mini` or `gpt-4o`).
5. Click **💾 Save & Connect OpenAI**. The system tests the connection immediately and confirms with a green checkmark!

#### Option 2: Via `.env` File (Persisted for all team members)
Create or edit `.env` in the project root:
```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
```

#### Option 3: Built-in Zero-Config Fallback (No Key Needed)
If no OpenAI key is provided, the application automatically uses the **Support Helper Built-in Neural Articulator**, which works 100% offline with zero external dependencies.

---

## 🚀 Quick Start

### 1. Launch with Single Click
Double-click `start_support_helper.bat` in the project root:
```bat
start_support_helper.bat
```

### 2. Manual Command Line
```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8055
```
Open your web browser and navigate to:
```
http://127.0.0.1:8055
```

---

## 📂 Project Architecture

```
FXT_APS_ASSIT/
├── start_support_helper.bat           # 1-click Windows batch launcher
├── README.md                          # System documentation & compliance matrix
├── backend/
│   ├── main.py                        # FastAPI web server and REST APIs
│   ├── rag_engine.py                  # RAG search, confidence scoring, grounding policy
│   ├── pdf_parser.py                  # PyPDF parser extracting pages, sections, metadata
│   ├── generate_sample_pdfs.py        # ReportLab script generating 5 realistic runbooks
│   ├── test_rag.py                    # Automated test suite for retrieval and grounding
│   └── knowledge_base/
│       └── pdf_documents/             # Approved PDF Runbook Repository
│           ├── FXT-RUN-001_FIX_Engine_Disconnection.pdf
│           ├── FXT-RUN-002_Oracle_DB_Pool_Exhaustion.pdf
│           ├── FXT-RUN-003_Kafka_Trade_Feed_Consumer_Lag.pdf
│           ├── FXT-RUN-004_Payment_Settlement_Gateway_504.pdf
│           └── FXT-RUN-005_EOD_Batch_Reconciliation_Failure.pdf
└── static/
    ├── index.html                     # Clean, accessible single-page GUI
    ├── style.css                      # Two-color Light Green & Dark Green stylesheet
    └── app.js                         # Dynamic frontend logic & API client
```

---

## 📚 Seeded Approved Runbooks
The knowledge base includes 5 approved PDF runbooks representing core electronic trading and settlement systems:
1. **FXT-RUN-001**: FIX Gateway Session Drop & Sequence Number Reset (`FIX-Gateway-Svc`)
2. **FXT-RUN-002**: FXT Settlement Database Connection Pool Exhaustion (`Oracle RAC / HikariCP Pool`)
3. **FXT-RUN-003**: Kafka Trade Event Pipeline Lag & Consumer Rebalance Failure (`Kafka-Broker-Cluster`)
4. **FXT-RUN-004**: SWIFT / Fedwire Payment Gateway 504 Gateway Timeout Recovery (`Swift-Alliance-Gateway-HTTP`)
5. **FXT-RUN-005**: End-of-Day (EOD) General Ledger Reconciliation Mismatch (`EOD-Recon-Job / SpringBatch`)
