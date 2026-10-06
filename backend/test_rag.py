"""
test_rag.py
Validates RAG engine retrieval, metadata, citations, and fallback logic.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag_engine import SupportRAGEngine

def run_tests():
    pdf_dir = os.path.join(os.path.dirname(__file__), "knowledge_base", "pdf_documents")
    engine = SupportRAGEngine(pdf_dir)
    
    print("\n--- TEST 1: Summary of Indexed Documents ---")
    summaries = engine.get_all_runbooks_summary()
    print(f"Total Runbooks Indexed: {len(summaries)}")
    for s in summaries:
        print(f" -> [{s['doc_id']}] {s['title']} | Pages: {s['num_pages']} | Commands: {s['commands_count']}")

    print("\n--- TEST 2: FIX Engine Disconnection Query (FR-SUP-001, FR-SUP-002, FR-SUP-003) ---")
    res1 = engine.search_and_ground("FIX_SESSION_DOWN on port 9801 MsgSeqNum too low Goldman Sachs")
    print(f"Status: {res1['status']} | Confidence: {res1['confidence_score']}% | Grounded: {res1['grounded']}")
    print(f"Matched Doc: {res1['matched_document']['doc_id']} - {res1['matched_document']['title']}")
    print(f"Warnings Count: {len(res1['warnings_do_not_do'])}")
    print(f"Steps Count: {len(res1['resolution_steps'])}")
    print(f"Citations: {[c['document'] + ' p.' + str(c['page']) for c in res1['citations']]}")
    assert res1['grounded'] == True, "FIX Query should be grounded!"
    assert len(res1['warnings_do_not_do']) > 0, "Warnings should be extracted!"

    print("\n--- TEST 3: DB Pool Exhaustion (FR-SUP-009 Recovery Sequence, FR-SUP-010 Commands) ---")
    res2 = engine.search_and_ground("ORA-00020 maximum number of processes exceeded in settlement pool")
    print(f"Status: {res2['status']} | Confidence: {res2['confidence_score']}% | Grounded: {res2['grounded']}")
    print(f"Recovery Chain: {res2['recovery_sequence']['chain']}")
    print(f"Grounded Commands: {len(res2['grounded_commands'])}")
    assert res2['grounded'] == True, "DB Query should be grounded!"
    assert res2['recovery_sequence'] is not None, "Recovery sequence must exist!"

    print("\n--- TEST 3B: Common DB Exhaustion Shorthand ---")
    res2b = engine.search_and_ground("what is db exhaustion", enable_ai=False)
    print(f"Status: {res2b['status']} | Confidence: {res2b['confidence_score']}% | Grounded: {res2b['grounded']}")
    assert res2b['grounded'] == True, "DB exhaustion shorthand should match the approved Oracle pool runbook!"
    assert res2b['matched_document']['doc_id'] == "FXT-RUN-002", "DB exhaustion should select FXT-RUN-002!"

    print("\n--- TEST 4: Unknown Alert / Unapproved Symptom (FR-SUP-004 & FR-SUP-005 Fallback) ---")
    res3 = engine.search_and_ground("Kubernetes ingress nginx memory leak on crypto miner unknown cluster 99")
    print(f"Status: {res3['status']} | Confidence: {res3['confidence_score']}% | Grounded: {res3['grounded']}")
    print(f"Fallback statement: {res3['statement']}")
    assert res3['grounded'] == False, "Unknown query should NOT be grounded!"
    assert "normal_escalation_path" in res3, "Normal escalation path must be present!"
    print("All unit tests passed successfully!")

if __name__ == "__main__":
    run_tests()
