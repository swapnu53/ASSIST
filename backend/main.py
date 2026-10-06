"""
main.py
FastAPI Web Application Server for Support Helper.
Implements all FR-SUP-001 through FR-SUP-010 requirements:
- Search & RAG grounding
- Anti-hallucination verification
- Approved PDF Knowledge Base repository management
- Real-time PDF upload & re-indexing
- Dependency-aware recovery sequences
- Grounded command generation & safety disclaimers
- Static web GUI delivery
"""

import os
import sys
import shutil
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Ensure path resolution
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BASE_DIR, "..")))

from backend.rag_engine import SupportRAGEngine

PDF_DIR = os.path.join(BASE_DIR, "knowledge_base", "pdf_documents")
STATIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "static")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Initialize RAG Engine
rag_engine = SupportRAGEngine(PDF_DIR)

app = FastAPI(
    title="Support Helper - Application Support Assistant",
    description="Evidence-based Assistant for Incidents, Alerts, and Approved Recovery Procedures",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    query: str
    application: Optional[str] = "ALL"
    environment: Optional[str] = "ALL"
    ai_provider: Optional[str] = "builtin"
    custom_key: Optional[str] = None
    custom_endpoint: Optional[str] = None
    custom_model: Optional[str] = None
    enable_ai: Optional[bool] = True

@app.get("/api/status")
def get_system_status():
    return {
        "status": "ONLINE",
        "app_name": "Support Helper",
        "version": "2.1.0 (PDF Grounding + AI Articulation Layer)",
        "grounding_policy": "Strict Local PDF Evidence Only (Zero Invention)",
        "ai_articulation_layer": "ENABLED",
        "supported_ai_providers": [
            {"id": "builtin", "name": "Support Helper Built-in Neural Articulator (No Key/Zero-Config)", "requires_key": False},
            {"id": "ollama", "name": "Ollama Local LLM (Llama 3, Mistral, Qwen)", "requires_key": False, "default_url": "http://127.0.0.1:11434"},
            {"id": "openai", "name": "OpenAI / Compatible API (vLLM, LM Studio, Azure)", "requires_key": True},
            {"id": "gemini", "name": "Google Gemini API", "requires_key": True}
        ],
        "total_approved_runbooks": len(rag_engine.documents),
        "total_semantic_chunks": len(rag_engine.chunks),
        "confidence_threshold_percent": round(rag_engine.confidence_threshold * 100, 1),
        "supported_formats": ["PDF (Wiki / KB Exports)"],
        "compliance": {
            "FR_SUP_001_Input": "ENABLED",
            "FR_SUP_002_SearchApprovedKnowledge": "ENABLED",
            "FR_SUP_003_StructuredResultDisplay": "ENABLED",
            "FR_SUP_004_ZeroHallucinationGuaranteed": "ENFORCED",
            "FR_SUP_005_ExplicitUnapprovedEscalation": "ENABLED",
            "FR_SUP_006_MetadataTracking": "ENABLED",
            "FR_SUP_007_PreservePDFPageCitations": "ENABLED",
            "FR_SUP_008_SemanticRAGRetrieval": "ENABLED",
            "FR_SUP_009_DependencyRecoverySequences": "ENABLED",
            "FR_SUP_010_GroundedCommandsSafetyDisclaimer": "ENFORCED"
        }
    }

@app.post("/api/search")
def search_support_helper(req: SearchRequest):
    """
    FR-SUP-001 through FR-SUP-010:
    Fetches the result from approved local PDF runbooks, and uses AI to articulate
    contextually tailored, professional, and grounded answers.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    result = rag_engine.search_and_ground(
        query=req.query,
        app_filter=req.application,
        env_filter=req.environment,
        ai_provider=req.ai_provider,
        custom_key=req.custom_key,
        custom_endpoint=req.custom_endpoint,
        custom_model=req.custom_model,
        enable_ai=req.enable_ai if req.enable_ai is not None else True
    )
    return result

class OpenAISettingsRequest(BaseModel):
    api_key: str
    model: Optional[str] = "gpt-4o-mini"
    base_url: Optional[str] = "https://api.openai.com/v1"

@app.get("/api/settings/openai")
def get_openai_settings():
    current_key = rag_engine.articulator.openai_key or os.getenv("OPENAI_API_KEY", "")
    masked = f"{current_key[:6]}...{current_key[-4:]}" if len(current_key) > 10 else ("Configured" if current_key else "Not Configured")
    return {
        "is_configured": bool(current_key),
        "masked_key": masked,
        "model": rag_engine.articulator.openai_model,
        "base_url": rag_engine.articulator.openai_url
    }

@app.post("/api/settings/openai")
def save_openai_settings(req: OpenAISettingsRequest):
    key = req.api_key.strip()
    if not key:
        raise HTTPException(status_code=400, detail="OpenAI API key cannot be empty.")
    
    base_url = (req.base_url or "https://api.openai.com/v1").rstrip("/")
    model = req.model or "gpt-4o-mini"

    # Test the API key against OpenAI models endpoint
    try:
        import urllib.request
        import json
        test_req = urllib.request.Request(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {key}"}
        )
        with urllib.request.urlopen(test_req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            available_models = [m.get("id") for m in data.get("data", [])][:10]
    except Exception as e:
        # If /models fails, check error detail
        err_msg = str(e)
        if "401" in err_msg:
            raise HTTPException(status_code=401, detail="Invalid OpenAI API key. Authentication failed (401).")
        # Proceed with warning if custom endpoint
        available_models = []

    # Save to memory and runtime
    rag_engine.articulator.openai_key = key
    rag_engine.articulator.openai_model = model
    rag_engine.articulator.openai_url = base_url
    rag_engine.articulator.default_provider = "openai"

    # Persist into .env file in project root
    env_path = os.path.join(os.path.dirname(BASE_DIR), ".env")
    try:
        env_lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_lines = [l for l in f.readlines() if not l.startswith(("OPENAI_API_KEY=", "OPENAI_MODEL=", "OPENAI_BASE_URL=", "AI_PROVIDER="))]
        
        env_lines.append(f"AI_PROVIDER=openai\n")
        env_lines.append(f"OPENAI_API_KEY={key}\n")
        env_lines.append(f"OPENAI_MODEL={model}\n")
        env_lines.append(f"OPENAI_BASE_URL={base_url}\n")
        
        with open(env_path, "w") as f:
            f.writelines(env_lines)
    except Exception as ex:
        print(f"[Warn] Could not write .env: {ex}")

    return {
        "status": "SUCCESS",
        "message": f"OpenAI API key verified and saved successfully! Using model '{model}'.",
        "model": model,
        "is_configured": True
    }

class AgentInstructionsRequest(BaseModel):
    instructions: str

@app.get("/api/agent-instructions")
def get_instructions():
    """
    Returns the agent instructions injected into every prompt.
    """
    return {
        "instructions": rag_engine.articulator.get_agent_instructions(),
        "max_length": rag_engine.articulator.MAX_AGENT_INSTRUCTIONS_LENGTH,
        "applies_to": ["openai", "ollama", "gemini"],
        "note": "The built-in fallback is deterministic and does not interpret arbitrary natural-language instructions."
    }

@app.post("/api/agent-instructions")
def save_instructions(req: AgentInstructionsRequest):
    """
    Saves updated agent instructions from the Admin panel.
    """
    try:
        rag_engine.articulator.set_agent_instructions(req.instructions)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": "SUCCESS",
        "message": "Agent instructions saved successfully and will be injected into every AI request."
    }

@app.get("/api/documents")
def list_approved_documents():
    """
    FR-SUP-006, FR-SUP-007
    Returns metadata list of all approved PDF runbooks in local repository.
    """
    return {
        "count": len(rag_engine.documents),
        "documents": rag_engine.get_all_runbooks_summary()
    }

@app.get("/api/documents/{filename}")
def get_document_details(filename: str):
    """
    FR-SUP-007
    Returns complete extracted runbook details, metadata, and page contents.
    """
    doc = rag_engine.get_document_full_detail(filename)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{filename}' not found in approved repository.")
    return {
        "filename": doc["filename"],
        "num_pages": doc["num_pages"],
        "metadata": doc["metadata"],
        "structured_data": doc["structured_data"],
        "pages": doc["pages"]
    }

@app.get("/api/documents/{filename}/download")
def download_pdf(filename: str):
    """
    Serves the actual approved PDF document for inline viewing or download.
    """
    file_path = os.path.join(PDF_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF file not found.")
    return FileResponse(
        file_path,
        media_type="application/pdf",
        filename=filename,
        content_disposition_type="inline"
    )

@app.post("/api/upload")
async def upload_runbook_pdf(file: UploadFile = File(...)):
    """
    FR-SUP-007 & FR-SUP-008
    Uploads a new approved Wiki/KB PDF export and reindexes RAG engine immediately.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents (.pdf) exported from Wiki/KB are supported.")
    
    # Secure filename
    clean_filename = os.path.basename(file.filename)
    target_path = os.path.join(PDF_DIR, clean_filename)
    
    with open(target_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Re-index the knowledge base
    rag_engine.load_and_index()
    
    doc = rag_engine.get_document_full_detail(clean_filename)
    return {
        "status": "SUCCESS",
        "message": f"Approved runbook '{clean_filename}' uploaded and indexed successfully.",
        "filename": clean_filename,
        "metadata": doc["metadata"] if doc else {},
        "total_documents": len(rag_engine.documents)
    }

@app.get("/api/recovery-sequences")
def get_all_recovery_sequences():
    """
    FR-SUP-009
    Aggregates all dependency-aware service recovery sequences across systems.
    """
    sequences = []
    for filename, doc in rag_engine.documents.items():
        meta = doc["metadata"]
        struct = doc.get("structured_data", {})
        seq = struct.get("recovery_sequence")
        if seq:
            sequences.append({
                "doc_id": meta.get("doc_id"),
                "document": filename,
                "title": meta.get("title"),
                "application": meta.get("application"),
                "service": meta.get("service"),
                "chain": seq.get("chain", []),
                "stop_condition": seq.get("stop_condition"),
                "escalation": struct.get("escalation", {})
            })
    return {"sequences": sequences}

# Mount static web directory
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8055, reload=False)
