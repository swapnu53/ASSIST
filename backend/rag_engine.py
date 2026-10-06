"""
rag_engine.py
Retrieval-Augmented Generation (RAG) and Evidence Grounding Engine for Support Helper.
Strictly adheres to:
- FR-SUP-002: Approved local knowledge search
- FR-SUP-003: Structured support procedure presentation
- FR-SUP-004: Strict anti-hallucination / zero-invention policy
- FR-SUP-005: Explicit no-approved-source fallback & escalation path
- FR-SUP-006: Comprehensive metadata tracking
- FR-SUP-007: Preserving PDF page and section citations
- FR-SUP-008: Semantic & lexical hybrid retrieval
- FR-SUP-009: Dependency-aware service recovery sequences
- FR-SUP-010: Grounded command generation with manual execution disclaimer
"""

import os
import sys
import re
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter

# Ensure package directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from backend.pdf_parser import PDFRunbookParser
    from backend.ai_articulator import AIArticulator
except ImportError:
    from pdf_parser import PDFRunbookParser
    from ai_articulator import AIArticulator

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "isn't", "it",
    "its", "itself", "me", "more", "most", "mustn't", "my", "myself", "no", "nor",
    "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "shan't", "she", "should", "shouldn't",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those", "through",
    "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "were",
    "weren't", "what", "when", "where", "which", "while", "who", "whom", "why",
    "with", "won't", "would", "wouldn't", "you", "your", "yours", "yourself", "yourselves",
    "please", "help", "issue", "error", "problem", "failing", "failed", "support"
}

def tokenize(text: str) -> List[str]:
    # Retain technical identifiers like ORA-00020, Tag-34, FIX.4.4, HTTP/504
    tokens = re.findall(r'[a-zA-Z0-9_\-\.\$]{2,}', text.lower())
    return [t for t in tokens if t not in STOP_WORDS]


def extract_technical_patterns(query: str) -> List[str]:
    """Return exact signatures plus conservative aliases for common support shorthand."""
    patterns = re.findall(
        r'(ORA-\d+|50\d|quickfix|fix|session|gateway|hikaricp|commitfailed|disconnect|'
        r'rebalance|imbalance|logon|msgseqnum|uetr|mt103|swift|batch|recon|ledger|pool)',
        query,
        re.IGNORECASE,
    )
    lowered = query.lower()

    # Operators commonly shorten "database connection-pool exhaustion" to
    # "db exhaustion". Expand only when both the database and capacity concepts
    # are present, avoiding a broad match for an isolated word such as "db".
    mentions_database = bool(re.search(r'\b(db|database|oracle)\b', lowered))
    mentions_capacity = bool(re.search(r'\b(exhaust(?:ed|ion)?|pool|connections?\s+limit)\b', lowered))
    if mentions_database and mentions_capacity:
        patterns.extend(["database", "connection", "pool", "exhaustion", "oracle"])

    return list(dict.fromkeys(pattern.lower() for pattern in patterns))

class SupportRAGEngine:
    def __init__(self, pdf_dir: str):
        self.pdf_dir = pdf_dir
        self.parser = PDFRunbookParser(pdf_dir)
        self.articulator = AIArticulator()
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.chunks: List[Dict[str, Any]] = []
        self.doc_frequencies: Dict[str, int] = Counter()
        self.total_docs = 0
        self.confidence_threshold = 0.26 # FR-SUP-005 cutoff
        self.load_and_index()

    def load_and_index(self):
        """
        Parses all PDF documents in the repository and indexes chunks.
        """
        self.documents.clear()
        self.chunks.clear()
        self.doc_frequencies.clear()
        
        pdf_files = self.parser.list_pdf_files()
        print(f"[RAG] Indexing {len(pdf_files)} PDF runbooks from {self.pdf_dir}...")
        
        all_chunk_tokens = []
        for f in pdf_files:
            full_path = os.path.join(self.pdf_dir, f)
            try:
                doc_data = self.parser.parse_pdf(full_path)
                self.documents[f] = doc_data
                for c in doc_data["chunks"]:
                    tokens = tokenize(c["text"] + " " + c["metadata"]["application"] + " " + c["metadata"]["service"])
                    c["tokens"] = tokens
                    c["token_counts"] = Counter(tokens)
                    self.chunks.append(c)
                    all_chunk_tokens.append(set(tokens))
            except Exception as e:
                print(f"[RAG Error] Failed parsing {f}: {e}")

        self.total_docs = len(self.chunks)
        for token_set in all_chunk_tokens:
            for t in token_set:
                self.doc_frequencies[t] += 1
                
        print(f"[RAG] Successfully indexed {len(self.documents)} runbooks with {len(self.chunks)} semantic chunks.")

    def search_and_ground(
        self,
        query: str,
        app_filter: Optional[str] = None,
        env_filter: Optional[str] = None,
        ai_provider: Optional[str] = None,
        custom_key: Optional[str] = None,
        custom_endpoint: Optional[str] = None,
        custom_model: Optional[str] = None,
        enable_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Executes hybrid retrieval, grounding verification, and structured response synthesis,
        followed by an AI articulation layer grounded in the retrieved PDF context.
        """
        cleaned_query = query.strip()
        if not cleaned_query:
            return self._build_empty_response()

        query_tokens = tokenize(cleaned_query)
        if not query_tokens:
            query_tokens = [w.lower() for w in re.findall(r'\w+', cleaned_query)]

        # Find best matching chunks
        scored_chunks: List[Tuple[float, Dict[str, Any]]] = []
        
        # Key technical signature boost (error codes, specific exception names, operational terms)
        tech_patterns = extract_technical_patterns(cleaned_query)

        for chunk in self.chunks:
            # Metadata filter checks
            if app_filter and app_filter != "ALL":
                app_name = chunk["metadata"].get("application", "")
                if app_filter.lower() not in app_name.lower():
                    continue
            if env_filter and env_filter != "ALL":
                env_name = chunk["metadata"].get("environment", "")
                if env_filter.lower() not in env_name.lower():
                    continue

            score = self._compute_chunk_score(query_tokens, tech_patterns, chunk)
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        # Aggregate document level scores
        doc_scores: Dict[str, float] = Counter()
        for score, chunk in scored_chunks:
            doc_name = chunk["document"]
            doc_scores[doc_name] += score

        if not scored_chunks or not doc_scores:
            return self._build_unapproved_fallback_response(query, max_score=0.0)

        best_doc_name, top_doc_score = max(doc_scores.items(), key=lambda x: x[1])
        # Confidence must be based on a chunk from the document that actually
        # won aggregation, not an unrelated document's globally highest chunk.
        top_chunk_score = max(
            score for score, chunk in scored_chunks if chunk["document"] == best_doc_name
        )
        
        # Calibrate confidence score between 0.0 and 1.0 (0% to 100%)
        # Normalized by query length and signal density
        normalized_confidence = min(0.98, top_chunk_score / (math.sqrt(len(query_tokens) + 1) * 3.8))
        # Boost confidence if exact error signature or runbook title matched
        if any(tp in self.documents[best_doc_name]["metadata"]["title"].lower() or tp in self.documents[best_doc_name]["metadata"]["service"].lower() for tp in tech_patterns):
            normalized_confidence = min(0.99, normalized_confidence * 1.35)

        # STRICT GROUNDING ENFORCEMENT (FR-SUP-004, FR-SUP-005)
        if normalized_confidence < self.confidence_threshold:
            return self._build_unapproved_fallback_response(query, max_score=normalized_confidence)

        # Compile structured procedure from approved document (FR-SUP-003)
        doc_data = self.documents[best_doc_name]
        meta = doc_data["metadata"]
        structured = doc_data["structured_data"]
        
        # Top supporting citation chunks for this document
        top_citations = [
            {
                "document": c["document"],
                "page": c["page"],
                "section": c["section"],
                "excerpt": c["text"][:380] + ("..." if len(c["text"]) > 380 else ""),
                "score": round(sc, 3)
            }
            for sc, c in scored_chunks if c["document"] == best_doc_name
        ][:3]

        # Grounded commands disclaimer (FR-SUP-010)
        commands_with_policy = []
        for cmd in structured.get("commands", []):
            commands_with_policy.append({
                "step": cmd.get("step"),
                "title": cmd.get("title"),
                "type": cmd.get("type"),
                "command": cmd.get("command"),
                "source_doc": best_doc_name,
                "execution_policy": "MANUAL_OPERATOR_REVIEW_REQUIRED",
                "policy_notice": "Commands are strictly grounded in approved runbook documentation. Automated execution is prohibited per FR-SUP-010 policy."
            })

        # AI Articulation Layer (Fetches PDF result and articulates answers)
        ai_articulation = None
        if enable_ai:
            ai_articulation = self.articulator.articulate(
                query=query,
                doc_metadata=meta,
                structured_data=structured,
                citations=top_citations,
                provider=ai_provider,
                custom_key=custom_key,
                custom_endpoint=custom_endpoint,
                custom_model=custom_model
            )

        return {
            "grounded": True,
            "status": "APPROVED_RUNBOOK_FOUND",
            "confidence_score": round(normalized_confidence * 100, 1),
            "confidence_rating": "High Grounded Match" if normalized_confidence > 0.70 else "Moderate Grounded Match",
            "query_analyzed": query,
            "ai_articulation": ai_articulation, # AI articulated response
            "matched_document": {
                "filename": best_doc_name,
                "title": meta.get("title"),
                "doc_id": meta.get("doc_id"),
                "version": meta.get("version"),
                "last_updated": meta.get("last_updated"),
                "owner": meta.get("owner"),
                "application": meta.get("application"),
                "service": meta.get("service"),
                "region": meta.get("region"),
                "environment": meta.get("environment"),
                "category": meta.get("category"),
                "total_pages": doc_data.get("num_pages", 1)
            },
            "issue_summary": structured.get("summary", "Approved incident procedure matched in local knowledge."),
            "symptoms_matched": structured.get("symptoms", []),
            "possible_causes": structured.get("causes", []),
            "warnings_do_not_do": structured.get("warnings", []), # FR-SUP-003 Critical Warnings
            "resolution_steps": structured.get("resolution_steps", []), # FR-SUP-003 Numbered Steps
            "verification_steps": structured.get("verification_steps", []), # FR-SUP-003 Verification
            "recovery_sequence": structured.get("recovery_sequence"), # FR-SUP-009 Dependency Sequence
            "edge_cases": structured.get("edge_cases", []),
            "escalation": structured.get("escalation", {}),
            "grounded_commands": commands_with_policy, # FR-SUP-010
            "citations": top_citations, # FR-SUP-007 Page & Section citations
            "source_reference": f"{best_doc_name} (Page 1-{doc_data.get('num_pages', 2)}, Approved Knowledge Base)"
        }

    def _compute_chunk_score(self, query_tokens: List[str], tech_patterns: List[str], chunk: Dict[str, Any]) -> float:
        score = 0.0
        chunk_text_lower = chunk["text"].lower()
        chunk_tokens = chunk["token_counts"]
        doc_len = len(chunk["tokens"]) + 1

        # Lexical BM25-like scoring
        for qt in query_tokens:
            if qt in chunk_tokens:
                tf = chunk_tokens[qt] / doc_len
                df = self.doc_frequencies.get(qt, 1)
                idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
                score += tf * (idf + 1.2) * 5.0

        # Technical pattern boost
        for tp in tech_patterns:
            if tp in chunk_text_lower:
                score += 4.5
            if tp in chunk["section"].lower():
                score += 3.0

        # Title & Service keyword boost
        meta = chunk["metadata"]
        for qt in query_tokens:
            if qt in meta.get("service", "").lower():
                score += 2.0
            if qt in meta.get("application", "").lower():
                score += 1.5

        return score

    def _build_unapproved_fallback_response(self, query: str, max_score: float) -> Dict[str, Any]:
        """
        FR-SUP-004 & FR-SUP-005 Compliance:
        Zero invention of procedures, commands, servers, or owners.
        Directs user to normal escalation path and standard incident triage checklist.
        """
        return {
            "grounded": False,
            "status": "NO_APPROVED_RUNBOOK_FOUND",
            "confidence_score": round(max_score * 100, 1),
            "confidence_rating": "Below Approved Confidence Threshold (< 26%)",
            "query_analyzed": query,
            "ai_articulation": None,
            "statement": "No approved runbook or procedure was found in the local knowledge base for this issue.",
            "policy_advisory": (
                "ANTI-HALLUCINATION POLICY ENFORCED (FR-SUP-004): Support Helper will not invent or guess "
                "recovery steps, server hostnames, database commands, or contacts without a verified approved runbook source."
            ),
            "normal_escalation_path": { # FR-SUP-005
                "guidance": "Please follow the standard Level-1 Application Support escalation workflow below:",
                "standard_contacts": [
                    {
                        "role": "Global Incident Command (GIC) Major Incident Manager",
                        "channel": "Slack: #incident-command-bridge | Webex: gic.bridge.fxtrading.internal",
                        "phone": "+1-800-555-0100 (Toll Free) / Ext. 9911"
                    },
                    {
                        "role": "Core Enterprise Operations On-Call Desk",
                        "channel": "Email: enterprise-ops-duty@fxtrading.internal",
                        "sla": "15-minute response for P1/P2 unmapped production events"
                    }
                ],
                "incident_triage_checklist": [
                    "1. Record exact timestamp of initial alert and affected counterparty/trading account.",
                    "2. Capture active log snippets, thread dumps, and full stack trace without restarting.",
                    "3. Validate whether client order entry, settlement booking, or market data feeds are impacted.",
                    "4. Open an Unmapped Incident Ticket (ServiceNow / Jira Service Management).",
                    "5. Page the secondary application support duty manager to review uncataloged symptoms."
                ]
            },
            "suggestions": [
                "Verify spelling of application name, service, or error code (e.g., FIX, ORA-00020, Kafka, 504 Gateway).",
                "Ensure the relevant Wiki runbook PDF has been uploaded to the Approved Knowledge Base repository.",
                "Adjust application or environment filters if currently set to a specific subsystem."
            ]
        }

    def _build_empty_response(self) -> Dict[str, Any]:
        return {
            "grounded": False,
            "status": "EMPTY_QUERY",
            "confidence_score": 0.0,
            "statement": "Please enter an issue description, alert, or error message to search approved runbooks."
        }

    def get_all_runbooks_summary(self) -> List[Dict[str, Any]]:
        """
        Returns metadata for all approved runbook PDFs in the local knowledge base.
        """
        summary_list = []
        for filename, doc in self.documents.items():
            meta = doc["metadata"]
            summary_list.append({
                "filename": filename,
                "title": meta.get("title"),
                "doc_id": meta.get("doc_id"),
                "application": meta.get("application"),
                "service": meta.get("service"),
                "region": meta.get("region"),
                "environment": meta.get("environment"),
                "category": meta.get("category"),
                "version": meta.get("version"),
                "last_updated": meta.get("last_updated"),
                "owner": meta.get("owner"),
                "num_pages": doc.get("num_pages", 1),
                "chunks_count": len(doc.get("chunks", [])),
                "has_recovery_sequence": doc.get("structured_data", {}).get("recovery_sequence") is not None,
                "commands_count": len(doc.get("structured_data", {}).get("commands", []))
            })
        return summary_list

    def get_document_full_detail(self, filename: str) -> Optional[Dict[str, Any]]:
        if filename not in self.documents:
            return None
        return self.documents[filename]
