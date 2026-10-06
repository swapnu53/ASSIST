"""
pdf_parser.py
PDF Parser module using pypdf to extract pages, text, sections, and metadata
from approved Application Support PDF runbooks and user-uploaded documents.
Preserves page and section references for citations (FR-SUP-006, FR-SUP-007).
"""

import os
import re
from typing import List, Dict, Any, Optional
from pypdf import PdfReader

class PDFRunbookParser:
    def __init__(self, pdf_dir: str):
        self.pdf_dir = pdf_dir

    def list_pdf_files(self) -> List[str]:
        if not os.path.exists(self.pdf_dir):
            return []
        return [f for f in os.listdir(self.pdf_dir) if f.lower().endswith('.pdf')]

    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Parses a single PDF file, extracting metadata, pages, chunks, and structured runbook sections.
        """
        filename = os.path.basename(file_path)
        reader = PdfReader(file_path)
        num_pages = len(reader.pages)
        
        pages_content = []
        full_text = ""
        
        for idx, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            pages_content.append({
                "page_number": idx + 1,
                "text": page_text
            })
            full_text += f"\n--- PAGE {idx + 1} ---\n" + page_text

        # Extract or detect metadata
        metadata = self._extract_metadata(filename, full_text, reader.metadata)
        
        # Extract structured sections if it's an approved runbook format
        structured_data = self._extract_structured_sections(full_text, pages_content, filename)
        
        # Build search chunks with page and section citations
        chunks = self._build_chunks(filename, pages_content, metadata)

        return {
            "filename": filename,
            "filepath": file_path,
            "num_pages": num_pages,
            "metadata": metadata,
            "pages": pages_content,
            "structured_data": structured_data,
            "chunks": chunks
        }

    def _extract_metadata(self, filename: str, full_text: str, pdf_meta: Any) -> Dict[str, str]:
        """
        Extracts metadata conforming to FR-SUP-006:
        title, application, service, region, environment, category, owner/support team, version, last updated, doc id.
        """
        meta = {
            "title": filename.replace(".pdf", "").replace("_", " "),
            "application": "Enterprise Application",
            "service": "General Service",
            "region": "GLOBAL",
            "environment": "PROD / UAT",
            "category": "Operations Support",
            "owner": "Application Support Pod",
            "version": "1.0",
            "last_updated": "2026",
            "doc_id": filename.split("_")[0] if "_" in filename else "RUN-KB"
        }

        # Regex patterns for standard metadata tables in approved PDFs
        patterns = {
            "title": r"APPROVED OPERATIONAL RUNBOOK:[^\n]*\n+([^\n]+)",
            "application": r"Application:\s*([^\n\t]+)",
            "service": r"Service:\s*([^\n\t]+)",
            "region": r"Region:\s*([^\n\t]+)",
            "environment": r"Environment:\s*([^\n\t]+)",
            "category": r"Category:\s*([^\n\t]+)",
            "owner": r"Owner\s*/\s*Team:\s*([^\n\t]+)",
            "version": r"Version:\s*([^\n\t]+)",
            "last_updated": r"Last Updated:\s*([^\n\t]+)",
            "doc_id": r"Doc ID:\s*([^\n\t]+)"
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                val = match.group(1).strip()
                # Clean up any trailing table border or label residue
                val = re.split(r"(Service:|Region:|Category:|Version:|Last Updated:|Doc ID:)", val)[0].strip()
                meta[key] = val

        return meta

    def _extract_structured_sections(self, full_text: str, pages: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Parses sections conforming to FR-SUP-003, FR-SUP-009, FR-SUP-010.
        """
        res = {
            "summary": "",
            "symptoms": [],
            "causes": [],
            "warnings": [],
            "resolution_steps": [],
            "verification_steps": [],
            "recovery_sequence": None,
            "edge_cases": [],
            "escalation": {},
            "commands": []
        }

        # 1. Summary
        sum_match = re.search(r"Issue Summary:\s*([^\n]+(?:\n[^\n]+)?)", full_text)
        if sum_match:
            res["summary"] = sum_match.group(1).strip()

        # 2. Symptoms
        symptom_sec = re.search(r"Detectable Symptoms & Alerts:(.*?)(?=2\. Root Causes|\Z)", full_text, re.DOTALL)
        if symptom_sec:
            raw_symptoms = re.findall(r"[•\-\*]\s*([^\n\r]+)", symptom_sec.group(1))
            res["symptoms"] = [s.strip() for s in raw_symptoms if s.strip()]

        # 3. Causes
        cause_sec = re.search(r"2\. Root Causes & Technical Diagnosis(.*?)(?=3\. Mandatory Safety|\Z)", full_text, re.DOTALL)
        if cause_sec:
            raw_causes = re.findall(r"[•\-\*]\s*([^\n\r]+)", cause_sec.group(1))
            res["causes"] = [c.strip() for c in raw_causes if c.strip()]

        # 4. Warnings / DO NOT DO (FR-SUP-003)
        warn_sec = re.search(r"3\. Mandatory Safety Directives \(DO NOT DO\)(.*?)(?=4\. Step-by-Step|\Z)", full_text, re.DOTALL)
        if warn_sec:
            raw_warns = re.findall(r"(?:CRITICAL OPERATIONAL WARNING:\s*|•\s*|DO NOT\s+|NEVER\s+)([^\n\r]+(?:(?!\n(?:CRITICAL|•|4\.)).)*)", warn_sec.group(1))
            cleaned_warns = []
            for w in raw_warns:
                w_str = w.strip()
                if len(w_str) > 10 and not w_str.startswith("3."):
                    if not (w_str.upper().startswith("DO NOT") or w_str.upper().startswith("NEVER")):
                        w_str = "DO NOT " + w_str
                    cleaned_warns.append(w_str)
            res["warnings"] = cleaned_warns if cleaned_warns else [w.strip() for w in warn_sec.group(1).split("\n") if "DO NOT" in w.upper() or "NEVER" in w.upper()]

        # 5. Numbered Resolution Steps (FR-SUP-003) & Grounded Commands (FR-SUP-010)
        step_sec = re.search(r"4\. Step-by-Step Resolution Procedures(.*?)(?=5\. Post-Recovery|\Z)", full_text, re.DOTALL)
        if step_sec:
            steps_text = step_sec.group(1)
            raw_steps = re.split(r"(?=Step\s+\d+:)", steps_text)
            for raw_s in raw_steps:
                raw_s = raw_s.strip()
                if not raw_s or not raw_s.startswith("Step"):
                    continue
                m_header = re.match(r"Step\s+(\d+):\s*([^\n]+)", raw_s)
                if m_header:
                    step_num = int(m_header.group(1))
                    step_title = m_header.group(2).strip()
                    body = raw_s[m_header.end():].strip()
                    
                    cmd_type = None
                    command = None
                    m_cmd = re.search(r"Command\s*\(([^)]+)\):\s*\n\s*([^\n]+(?:\n\s+[^\n]+)?)", body)
                    if m_cmd:
                        cmd_type = m_cmd.group(1).strip()
                        command = m_cmd.group(2).strip()
                        detail = body[:m_cmd.start()].strip()
                    else:
                        detail = body
                    detail = re.sub(r"^[•\-\*]\s*", "", detail).strip()
                    
                    step_obj = {
                        "step_number": step_num,
                        "title": step_title,
                        "detail": detail,
                        "cmd_type": cmd_type,
                        "command": command
                    }
                    res["resolution_steps"].append(step_obj)
                    if command:
                        res["commands"].append({
                            "step": step_num,
                            "title": step_title,
                            "type": cmd_type or "Script",
                            "command": command,
                            "source_doc": filename,
                            "page": 2
                        })

        # 6. Verification Steps (FR-SUP-003)
        ver_sec = re.search(r"5\. Post-Recovery Verification Procedures(.*?)(?=6\. Dependency-Aware|7\. Edge Cases|\Z)", full_text, re.DOTALL)
        if ver_sec:
            raw_vers = re.findall(r"(?:V-\d+:|[•\-\*])\s*([^\n\r]+)", ver_sec.group(1))
            res["verification_steps"] = [v.strip() for v in raw_vers if v.strip()]

        # 7. Dependency-Aware Service Recovery Sequence (FR-SUP-009)
        seq_sec = re.search(r"6\. Dependency-Aware Service Recovery Sequence(.*?)(?=7\. Edge Cases|\Z)", full_text, re.DOTALL)
        if seq_sec:
            seq_text = seq_sec.group(1)
            chain = []
            chain_match = re.search(r"Ordered Sequence:\s*(.*?)(?=Explicit Stop/Escalate|\Z)", seq_text, re.DOTALL)
            if chain_match:
                for line in chain_match.group(1).split("\n"):
                    cleaned = re.sub(r"^[➔\s\d\.\-]+", "", line).strip()
                    if cleaned:
                        chain.append(cleaned)
            stop_match = re.search(r"Explicit Stop/Escalate Gate:\s*([^\n]+(?:\n[^\n]+)?)", seq_text)
            stop_condition = stop_match.group(1).strip() if stop_match else "Stop immediately and escalate if health verification fails."
            res["recovery_sequence"] = {
                "chain": chain,
                "stop_condition": stop_condition
            }

        # 8. Edge Cases (FR-SUP-003)
        edge_sec = re.search(r"7\. Edge Cases & Escalation Protocol(.*?)(?=Primary Contact|\Z)", full_text, re.DOTALL)
        if edge_sec:
            raw_edges = re.findall(r"(?:Edge Case:|[•\-\*])\s*([^\n\r]+)", edge_sec.group(1))
            res["edge_cases"] = [e.strip() for e in raw_edges if e.strip() and "Primary Contact" not in e]

        # 9. Escalation Info (FR-SUP-003)
        esc_match = re.search(r"Primary Contact:\s*([^\n\t]+)", full_text)
        sec_match = re.search(r"Secondary\s*/\s*Bridge:\s*([^\n\t]+)", full_text)
        sla_match = re.search(r"Severity\s*/\s*SLA:\s*([^\n\t]+)", full_text)
        cond_match = re.search(r"Escalation Condition:\s*([^\n\t]+)", full_text)
        
        res["escalation"] = {
            "primary": esc_match.group(1).strip() if esc_match else "APS On-Call Incident Lead",
            "secondary": sec_match.group(1).strip() if sec_match else "Engineering Core Duty Manager",
            "sla": sla_match.group(1).strip() if sla_match else "P1: 15m / P2: 30m response",
            "condition": cond_match.group(1).strip() if cond_match else "Escalate if not resolved after standard runbook execution."
        }

        return res

    def _build_chunks(self, filename: str, pages: List[Dict[str, Any]], metadata: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Builds semantic chunks tagged with exact page citations and section markers.
        """
        chunks = []
        for p in pages:
            page_num = p["page_number"]
            text = p["text"]
            
            # Split page into logical sections by headers or paragraphs
            sections = re.split(r"(?=\n\d+\.\s+[A-Za-z])", text)
            for s_idx, sec_text in enumerate(sections):
                sec_text = sec_text.strip()
                if not sec_text or len(sec_text) < 30:
                    continue
                
                # Determine section title
                first_line = sec_text.split("\n")[0].strip()
                sec_title = first_line if len(first_line) < 80 else f"Page {page_num} Section {s_idx+1}"
                
                chunks.append({
                    "chunk_id": f"{filename}_p{page_num}_s{s_idx}",
                    "document": filename,
                    "page": page_num,
                    "section": sec_title,
                    "text": sec_text,
                    "metadata": metadata
                })

        return chunks
