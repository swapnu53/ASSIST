"""
generate_sample_pdfs.py
Generates 5 realistic, approved Application Support (APS) Runbook PDFs using ReportLab.
These PDFs represent official Wiki / Knowledge Base exports for FX Trading & Settlement Systems.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

DARK_GREEN = colors.HexColor("#064e3b")
MED_GREEN = colors.HexColor("#065f46")
LIGHT_GREEN = colors.HexColor("#dcfce7")
BORDER_GREEN = colors.HexColor("#16a34a")
TEXT_DARK = colors.HexColor("#0f291e")
ACCENT_GREEN = colors.HexColor("#22c55e")
BG_LIGHT = colors.HexColor("#f0fdf4")
WARNING_BG = colors.HexColor("#ecfdf5")
WARNING_BORDER = colors.HexColor("#059669")

def build_pdf(filename, doc_info):
    pdf_path = os.path.join(os.path.dirname(__file__), "knowledge_base", "pdf_documents", filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=DARK_GREEN,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=14,
        textColor=MED_GREEN,
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=DARK_GREEN,
        spaceBefore=12,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=TEXT_DARK,
        spaceAfter=5
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=TEXT_DARK,
        leftIndent=15,
        spaceAfter=4
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Code'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=DARK_GREEN,
        backColor=LIGHT_GREEN,
        spaceBefore=3,
        spaceAfter=5
    )
    
    warning_style = ParagraphStyle(
        'WarningText',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=13,
        textColor=DARK_GREEN
    )

    story = []
    
    # Title & Header
    story.append(Paragraph(f"APPROVED OPERATIONAL RUNBOOK: {doc_info['id']}", subtitle_style))
    story.append(Paragraph(doc_info['title'], title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=DARK_GREEN, spaceBefore=4, spaceAfter=10))
    
    # Metadata Table
    meta_data = [
        [
            Paragraph("<b>Application:</b> " + doc_info['application'], body_style),
            Paragraph("<b>Service:</b> " + doc_info['service'], body_style),
            Paragraph("<b>Region:</b> " + doc_info['region'], body_style)
        ],
        [
            Paragraph("<b>Environment:</b> " + doc_info['environment'], body_style),
            Paragraph("<b>Category:</b> " + doc_info['category'], body_style),
            Paragraph("<b>Version:</b> " + doc_info['version'], body_style)
        ],
        [
            Paragraph("<b>Owner / Team:</b> " + doc_info['owner'], body_style),
            Paragraph("<b>Last Updated:</b> " + doc_info['last_updated'], body_style),
            Paragraph("<b>Doc ID:</b> " + doc_info['id'], body_style)
        ]
    ]
    t = Table(meta_data, colWidths=[180, 180, 170])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_GREEN),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_GREEN),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    
    # Section 1: Issue Summary & Symptoms
    story.append(Paragraph("1. Operational Symptoms & Issue Summary", h2_style))
    story.append(Paragraph(f"<b>Issue Summary:</b> {doc_info['summary']}", body_style))
    story.append(Paragraph(f"<b>Detectable Symptoms & Alerts:</b>", body_style))
    for symptom in doc_info['symptoms']:
        story.append(Paragraph(f"• {symptom}", bullet_style))
    story.append(Spacer(1, 8))
    
    # Section 2: Possible Causes
    story.append(Paragraph("2. Root Causes & Technical Diagnosis", h2_style))
    for cause in doc_info['causes']:
        story.append(Paragraph(f"• {cause}", bullet_style))
    story.append(Spacer(1, 8))
    
    # Section 3: Critical Warnings / DO NOT DO
    story.append(Paragraph("3. Mandatory Safety Directives (DO NOT DO)", h2_style))
    warning_cells = [[Paragraph(f"<b>CRITICAL OPERATIONAL WARNING:</b><br/>{warning}", warning_style)] for warning in doc_info['warnings']]
    wt = Table(warning_cells, colWidths=[530])
    wt.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), WARNING_BG),
        ('BOX', (0,0), (-1,-1), 1.5, WARNING_BORDER),
        ('INNERGRID', (0,0), (-1,-1), 0.5, WARNING_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(wt)
    story.append(Spacer(1, 10))
    
    # Page Break for multi-page runbook structure (verifies FR-SUP-007 multi-page citations)
    story.append(PageBreak())
    
    # Section 4: Numbered Step-by-Step Resolution Procedures
    story.append(Paragraph("4. Step-by-Step Resolution Procedures", h2_style))
    for i, step in enumerate(doc_info['steps'], start=1):
        story.append(Paragraph(f"<b>Step {i}:</b> {step['title']}", body_style))
        story.append(Paragraph(f"{step['detail']}", bullet_style))
        if 'command' in step and step['command']:
            story.append(Paragraph(f"<i>Command ({step['cmd_type']}):</i>", bullet_style))
            story.append(Paragraph(f"{step['command']}", code_style))
        story.append(Spacer(1, 3))
    story.append(Spacer(1, 8))
    
    # Section 5: Verification & Health Check Steps
    story.append(Paragraph("5. Post-Recovery Verification Procedures", h2_style))
    for i, v_step in enumerate(doc_info['verifications'], start=1):
        story.append(Paragraph(f"<b>V-{i}:</b> {v_step}", bullet_style))
    story.append(Spacer(1, 8))
    
    # Section 6: Dependency-Aware Start/Stop/Recovery Sequence (FR-SUP-009)
    if 'recovery_sequence' in doc_info:
        story.append(Paragraph("6. Dependency-Aware Service Recovery Sequence", h2_style))
        seq_text = "<b>Ordered Sequence:</b><br/>" + "<br/>&nbsp;&nbsp;➔ ".join(doc_info['recovery_sequence']['chain'])
        seq_text += f"<br/><br/><b>Explicit Stop/Escalate Gate:</b> {doc_info['recovery_sequence']['stop_condition']}"
        st = Table([[Paragraph(seq_text, body_style)]], colWidths=[530])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('BOX', (0,0), (-1,-1), 1, BORDER_GREEN),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(st)
        story.append(Spacer(1, 8))

    # Section 7: Edge Cases & Escalation Contacts
    story.append(Paragraph("7. Edge Cases & Escalation Protocol", h2_style))
    for ec in doc_info['edge_cases']:
        story.append(Paragraph(f"• <b>Edge Case:</b> {ec}", bullet_style))
    story.append(Spacer(1, 5))
    
    esc = doc_info['escalation']
    esc_data = [
        [Paragraph(f"<b>Primary Contact:</b> {esc['primary']}", body_style), Paragraph(f"<b>Secondary / Bridge:</b> {esc['secondary']}", body_style)],
        [Paragraph(f"<b>Severity / SLA:</b> {esc['sla']}", body_style), Paragraph(f"<b>Escalation Condition:</b> {esc['condition']}", body_style)]
    ]
    et = Table(esc_data, colWidths=[265, 265])
    et.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('BOX', (0,0), (-1,-1), 1, BORDER_GREEN),
        ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_GREEN),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(et)
    
    doc.build(story)
    print(f"[OK] Generated approved runbook: {pdf_path}")

DOCS = [
    {
        "filename": "FXT-RUN-001_FIX_Engine_Disconnection.pdf",
        "id": "FXT-RUN-001",
        "title": "FIX Gateway Session Drop & Sequence Number Reset Runbook",
        "application": "FX Trading Core (FXT-Core)",
        "service": "FIX-Gateway-Svc",
        "region": "GLOBAL (APAC/EMEA/AMER)",
        "environment": "PROD / UAT",
        "category": "Market Connectivity & FIX Protocols",
        "version": "3.4.1",
        "owner": "FX Electronic Trading APS Team",
        "last_updated": "2026-08-15",
        "summary": "Sudden termination or heartbeat timeout of institutional client FIX 4.2 / 4.4 trading sessions, leading to session disconnect, rejected orders, or Sequence Reset Gap Fill conflicts.",
        "symptoms": [
            "Alert: 'FIX_SESSION_DOWN: Counterparty Goldman Sachs / Citi disconnected on port 9801'",
            "Log Error: 'MsgSeqNum too low, expecting 14502 but received 14200 (FIX Tag 34 mismatch)'",
            "Error: 'Heartbeat timeout after 30 seconds without TestRequest response (35=1)'",
            "Trader symptom: Order blotter shows client orders rejected with 'FIX Session Inactive'"
        ],
        "causes": [
            "Network route flapping or WAN packet loss between client colocation and FXT gateway.",
            "Client restarted their FIX client engine without persisting sequence numbers, sending lower InSeqNum.",
            "Thread deadlock in QuickFIX/J message parser caused by memory heap spikes."
        ],
        "warnings": [
            "DO NOT reset sequence numbers to 1 without explicit written email confirmation from the counterparty FIX trading desk.",
            "DO NOT terminate the primary FIX gateway process during active market trading hours (07:00-17:00 UTC) without failing over to standby port.",
            "NEVER manually edit session state files (.seqnums) while the QuickFIX daemon process is running; always stop the service first."
        ],
        "steps": [
            {
                "title": "Inspect Active Session Status",
                "detail": "Verify if the FIX session daemon is active or stuck in reconnection loop using PowerShell.",
                "cmd_type": "PowerShell",
                "command": "Get-Service -Name 'FXT-FixGateway' | Select-Object -Property Name, Status, StartType"
            },
            {
                "title": "Check Tag 34 Sequence Mismatch in Session Logs",
                "detail": "Search the live FIX engine log for the affected session compID to identify sequence gap.",
                "cmd_type": "Bash/Shell",
                "command": "grep -E '(MsgSeqNum|Tag 34|HeartBtInt)' /var/log/fxt/fix_session_GS_PROD.log | tail -n 25"
            },
            {
                "title": "Perform Clean Session Stop",
                "detail": "Gracefully disconnect the session before modifying state counters.",
                "cmd_type": "PowerShell",
                "command": "Stop-Service -Name 'FXT-FixGateway' -Force"
            },
            {
                "title": "Apply Sequence Gap Reset",
                "detail": "Set expected sequence numbers according to counterparty written specification.",
                "cmd_type": "PowerShell",
                "command": "& 'C:\\FXT\\FixEngine\\bin\\ResetSeqNum.exe' --session 'FIX.4.4:FXT->GS_NY' --inseq 14502 --outseq 18910"
            },
            {
                "title": "Restart FIX Gateway Service",
                "detail": "Restart the gateway service and watch for successful Logon (35=A) handshake.",
                "cmd_type": "PowerShell",
                "command": "Start-Service -Name 'FXT-FixGateway'"
            }
        ],
        "verifications": [
            "Inspect FIX log for received 35=A (Logon) followed by sent 35=A with matching MsgSeqNum.",
            "Verify heartbeat ping/pong messages (35=0) occur every 30 seconds continuously.",
            "Confirm test order injection succeeds via synthetic test account: 'FXT-MON-TEST'."
        ],
        "recovery_sequence": {
            "chain": [
                "1. Database Connection Validator (Port 1521)",
                "2. FXT Reference Data Cache (Redis)",
                "3. FXT FIX Gateway Core Daemon",
                "4. FIX Session Port Listener (Ports 9800-9850)"
            ],
            "stop_condition": "If Step 4 does not show 35=A handshake within 90 seconds, STOP recovery immediately. Do not attempt secondary reset. Escalate to On-Call FIX Engineering."
        },
        "edge_cases": [
            "Multiple rapid resets causing infinite logon loop: Trigger automatic port firewall block for 5 minutes.",
            "Client sending duplicate orders (PossDupFlag 43=Y): Engage Trade Surveillance desk immediately."
        ],
        "escalation": {
            "primary": "APS FIX Lead (aps-fix-lead@fxtrading.internal | On-Call Bridge: +1-800-555-0191)",
            "secondary": "FX Electronic Trading Dev Team (fxt-eng-core@fxtrading.internal)",
            "sla": "P1 Incident: 15-minute response SLA, 30-minute restoration target",
            "condition": "If session remains disconnected after 2 clean restarts or counterparty reports order losses."
        }
    },
    {
        "filename": "FXT-RUN-002_Oracle_DB_Pool_Exhaustion.pdf",
        "id": "FXT-RUN-002",
        "title": "FXT Settlement Database Connection Pool Exhaustion & Thread Hung Runbook",
        "application": "Settlement & Clearing (FXT-Settle)",
        "service": "Oracle RAC / HikariCP Pool",
        "region": "EMEA (London Core)",
        "environment": "PROD",
        "category": "Database & Transaction Processing",
        "version": "2.9.0",
        "owner": "FX Core Operations & APS Database Pod",
        "last_updated": "2026-09-02",
        "summary": "Application threads hanging on HikariCP connection checkout with ORA-00020 or connection timeout exceptions, freezing trade ticket processing.",
        "symptoms": [
            "Log Exception: 'ConnectionTimeout: Connection is not available, request timed out after 30000ms'",
            "Log Error: 'ORA-00020: maximum number of processes (1500) exceeded'",
            "Alert: 'DB_POOL_EXHAUSTED: FXT_SETTLE_PROD pool 100% utilized (300/300 active connections)'",
            "Business impact: Post-trade booking queue rising over 5,000 unconfirmed transactions"
        ],
        "causes": [
            "Uncommitted distributed transaction in batch settlement service holding exclusive row locks on T_TRADE_SETTLE.",
            "HikariCP connection leak due to missing try-with-resources in recent deployment of fx-settle-worker.",
            "Long-running ad-hoc reporting query spawned by Finance analyst blocking settlement redo logs."
        ],
        "warnings": [
            "DO NOT perform an immediate hard kill (kill -9 or ALTER SYSTEM KILL SESSION IMMEDIATE) without recording the blocking SQL_ID and SID for root-cause forensic analysis.",
            "DO NOT restart Oracle RAC node 1 while node 2 is undergoing scheduled archive log sync.",
            "NEVER flush settlement buffer cache while intraday clearing window is open (14:00-16:30 London time)."
        ],
        "steps": [
            {
                "title": "Identify Blocking Sessions and Locked Objects",
                "detail": "Run approved diagnostic query to extract blocking SID, serial, program, and wait event.",
                "cmd_type": "SQL",
                "command": "SELECT s.sid, s.serial#, s.username, s.status, s.program, s.blocking_session, s.event FROM v$session s WHERE s.blocking_session IS NOT NULL OR s.sid IN (SELECT blocking_session FROM v$session);"
            },
            {
                "title": "Analyze Active Long-Running Statements",
                "detail": "Check SQL text of the root blocker holding row exclusive locks.",
                "cmd_type": "SQL",
                "command": "SELECT sql_id, elapsed_time/1000000 elapsed_sec, cpu_time/1000000 cpu_sec, executions, sql_text FROM v$sql WHERE sql_id = '&BLOCKING_SQL_ID';"
            },
            {
                "title": "Terminate Orphaned / Hung Blocker Session",
                "detail": "Execute approved safe session kill for the blocking SID identified.",
                "cmd_type": "SQL",
                "command": "ALTER SYSTEM KILL SESSION '&SID,&SERIAL' IMMEDIATE;"
            },
            {
                "title": "Restart Worker Pods to Flush Stale Pool Leaks",
                "detail": "Restart the settlement worker deployment gracefully one replica at a time.",
                "cmd_type": "PowerShell",
                "command": "kubectl rollout restart deployment/fxt-settle-worker -n fxt-prod"
            }
        ],
        "verifications": [
            "Check HikariCP metrics: Active connections must drop below 40% (max 120/300).",
            "Verify unconfirmed transaction queue on RabbitMQ/Kafka drops to < 50 items within 5 minutes.",
            "Run SELECT COUNT(*) FROM v$session WHERE status = 'ACTIVE' AND username = 'FXT_APP';"
        ],
        "recovery_sequence": {
            "chain": [
                "1. Terminate Blocking Session in Oracle RAC",
                "2. Verify Database Lock Table Clear (v$lock count = 0 on T_TRADE_SETTLE)",
                "3. Restart HikariCP Worker Deployment (fxt-settle-worker)",
                "4. Resume Ingestion Consumer Queue"
            ],
            "stop_condition": "If ORA-00020 persists after terminating blocker, STOP immediately. Do NOT run mass session kill. Escalate to Senior Oracle DBA On-Call."
        },
        "edge_cases": [
            "2-Phase Commit In-Doubt Transaction (ORA-01591): Requires DBA command ROLLBACK FORCE 'tx_id'.",
            "RAC Inter-Node Cache Fusion Contention (gc cr request): Verify interconnect bandwidth."
        ],
        "escalation": {
            "primary": "Lead Production DBA (oracle-dba-oncall@fxtrading.internal | Phone: ext. 4402)",
            "secondary": "Settlement Operations Team (fxt-settle-ops@fxtrading.internal)",
            "sla": "P1 Critical: 10-minute acknowledgement, 20-minute mitigation",
            "condition": "Pool exhaustion unresolved after 10 minutes or queue exceeds 10,000 trades."
        }
    },
    {
        "filename": "FXT-RUN-003_Kafka_Trade_Feed_Consumer_Lag.pdf",
        "id": "FXT-RUN-003",
        "title": "Kafka Trade Event Pipeline Lag & Consumer Rebalance Failure Runbook",
        "application": "Market Data & Trade Analytics",
        "service": "Kafka-Broker-Cluster / Event-Processor",
        "region": "AMER (New York Primary)",
        "environment": "PROD",
        "category": "Messaging & Real-time Streaming",
        "version": "1.8.3",
        "owner": "Event Infrastructure & Messaging APS",
        "last_updated": "2026-07-28",
        "summary": "Consumer lag on 'fxt.orders.executed.v1' surging past 200,000 messages, resulting in delayed market data feeds and stale risk calculation for trading desks.",
        "symptoms": [
            "Alert: 'KAFKA_CONSUMER_LAG_HIGH: Group fxt-risk-calc-group lag > 250,000 on topic fxt.orders.executed.v1'",
            "Log Warning: 'CommitFailedException: Offset commit cannot be completed since the consumer is not part of group'",
            "Log Error: 'Heartbeat thread error: member has been kicked out of group due to max.poll.interval.ms timeout'",
            "Trader symptom: Pricing dashboard shows 45-second latency indicator flag"
        ],
        "causes": [
            "Heavy JSON parsing or external database lookup inside consumer loop causing processing time to exceed max.poll.interval.ms (300,000ms).",
            "Frequent rebalance storms caused by an unstable node repeatedly joining and leaving the consumer group.",
            "Uneven partition skew where Partition 4 receives 70% of peak volume."
        ],
        "warnings": [
            "DO NOT reset consumer group offsets to 'latest' without explicit approval from Risk Management; doing so will permanently drop execution records.",
            "DO NOT scale the consumer group pod count higher than the number of topic partitions (16 max partitions).",
            "DO NOT restart Kafka broker nodes during market volatility spikes (e.g. Non-Farm Payroll, FOMC release)."
        ],
        "steps": [
            {
                "title": "Inspect Consumer Group Lag and Partition Distribution",
                "detail": "Execute Kafka consumer group description command to view current lag per partition.",
                "cmd_type": "Bash/Shell",
                "command": "kafka-consumer-groups.sh --bootstrap-server kafka-prod-01:9092 --describe --group fxt-risk-calc-group"
            },
            {
                "title": "Identify Failing Consumer Pods",
                "detail": "Search Kubernetes pod logs for Rebalance and CommitFailed exceptions.",
                "cmd_type": "PowerShell",
                "command": "kubectl logs -l app=fxt-risk-calc -n fxt-prod --tail=100 | Select-String -Pattern 'CommitFailedException|rebalance'"
            },
            {
                "title": "Scale Consumers Up to Match Partition Count",
                "detail": "Scale up consumer deployment to 16 replicas (1 consumer per partition max).",
                "cmd_type": "PowerShell",
                "command": "kubectl scale deployment/fxt-risk-calc --replicas=16 -n fxt-prod"
            },
            {
                "title": "Execute Dry-Run Offset Verification If Rewind Is Needed",
                "detail": "Never execute offset reset without running --dry-run first.",
                "cmd_type": "Bash/Shell",
                "command": "kafka-consumer-groups.sh --bootstrap-server kafka-prod-01:9092 --group fxt-risk-calc-group --reset-offsets --to-offset 8940201 --dry-run --topic fxt.orders.executed.v1"
            }
        ],
        "verifications": [
            "Confirm 'TOTAL_LAG' metric is steadily decreasing at minimum 5,000 messages/sec.",
            "Verify all 16 consumer members are assigned distinct partition IDs with state 'Stable'.",
            "Check Risk Dashboard latency counter returns to < 200ms."
        ],
        "recovery_sequence": {
            "chain": [
                "1. Kafka Cluster Broker Health Check (All 5 brokers in ISR)",
                "2. Consumer Group State Verification (State != Dead)",
                "3. Replica Scale-out to match 16 partitions",
                "4. Stream Processing Verification & Latency Stabilization"
            ],
            "stop_condition": "If consumer group stays in state 'PreparingRebalance' for > 3 minutes, STOP scaling. Escalate to Messaging Platform SME."
        },
        "edge_cases": [
            "Poison Pill Message in partition: Message with malformed schema crashing consumer continuously. Quarantine message using dead-letter-queue tool.",
            "Zookeeper / KRaft Metadata Quorum desync: Do not touch offsets."
        ],
        "escalation": {
            "primary": "Kafka Platform Specialist (messaging-ops@fxtrading.internal | Slack: #kafka-prod-support)",
            "secondary": "Market Risk Technology Lead (risk-tech-oncall@fxtrading.internal)",
            "sla": "P2 High: 20-minute resolution SLA",
            "condition": "Total lag continuing to increase 15 minutes after scaling consumer instances."
        }
    },
    {
        "filename": "FXT-RUN-004_Payment_Settlement_Gateway_504.pdf",
        "id": "FXT-RUN-004",
        "title": "SWIFT / Fedwire Payment Gateway 504 Gateway Timeout Recovery Runbook",
        "application": "Global Payments & Swift Settlement (FXT-Pay)",
        "service": "Swift-Alliance-Gateway-HTTP",
        "region": "GLOBAL / AMER / EMEA",
        "environment": "PROD",
        "category": "External Banking & Payments API",
        "version": "4.1.0",
        "owner": "Payments & Clearing Support Pod",
        "last_updated": "2026-06-19",
        "summary": "Outbound cross-border wire transfers and MT103 / pacs.008 payment messages timing out with HTTP 504 Gateway Timeout or TCP handshake reset at the perimeter secure gateway.",
        "symptoms": [
            "HTTP Response Code: '504 Gateway Timeout from https://swift-gateway.fxtrading.internal/api/v2/wires'",
            "Error: 'SSLHandshakeException: PKIX path validation failed or cert expired'",
            "Alert: 'SWIFT_OUTBOUND_BUFFER_SPIKE: 420 pending wire messages queued without ACK'",
            "Business impact: Risk of missing central bank intraday cutoff (Fedwire 17:00 EST / Target2 18:00 CET)"
        ],
        "causes": [
            "Perimeter Mutual TLS (mTLS) client certificate expiration on API Gateway proxy.",
            "Upstream SWIFT Alliance Access interface maintenance without prior notice.",
            "Hardware Security Module (HSM) signature cluster latency exceeding 8,000ms."
        ],
        "warnings": [
            "DO NOT resubmit payment requests with new UUIDs if the gateway response is unknown or timed out; doing so creates DUPLICATE WIRE TRANSFERS.",
            "DO NOT bypass HSM digital signature verification under any circumstance; violates SWIFT CSP compliance.",
            "NEVER disable TLS certificate validation flags (--insecure or -k) in production payment scripts."
        ],
        "steps": [
            {
                "title": "Validate Gateway HTTP Connectivity and TLS Certificate Expiry",
                "detail": "Test TLS handshake against internal proxy endpoint and verify certificate validity dates.",
                "cmd_type": "PowerShell",
                "command": "$cert = [System.Net.ServicePointManager]::ServerCertificateValidationCallback; Test-NetConnection -ComputerName swift-gateway.fxtrading.internal -Port 8443"
            },
            {
                "title": "Query SWIFT Acknowledgment State for In-Flight Wires",
                "detail": "Check database for in-doubt payment IDs before initiating retry or failover.",
                "cmd_type": "SQL",
                "command": "SELECT payment_id, currency, amount, status, swift_uetr, created_time FROM t_payment_wire WHERE status IN ('SENT_PENDING_ACK', 'TIMEOUT') AND created_time > SYSDATE - 1/24;"
            },
            {
                "title": "Switch Payment Route to Standby Secondary Node",
                "detail": "Trigger approved automated route switch to Secondary Swift Gateway instance B.",
                "cmd_type": "PowerShell",
                "command": "Invoke-RestMethod -Uri 'https://config-svc.fxtrading.internal/api/routes/swift' -Method POST -Body '{\"active_gateway\": \"SWIFT_GATEWAY_NODE_B\"}' -ContentType 'application/json'"
            },
            {
                "title": "Reconcile In-Doubt Wires via Status Query API",
                "detail": "Poll SWIFT UETR tracking status for all unacknowledged wires.",
                "cmd_type": "Bash/Shell",
                "command": "curl -X POST https://swift-gateway-b.fxtrading.internal/api/v2/reconcile-uetr -H 'Content-Type: application/json' -d '{\"batch_window\": \"CURRENT_HOUR\"}'"
            }
        ],
        "verifications": [
            "Confirm HTTP response 200 OK received for gateway health check endpoint /actuator/health.",
            "Verify all in-flight payments change status from 'SENT_PENDING_ACK' to 'CONFIRMED_ACK_RECEIVED'.",
            "Zero new 504 errors in Grafana Payment Gateway Dashboard for 15 consecutive minutes."
        ],
        "recovery_sequence": {
            "chain": [
                "1. HSM Security Token Service Health Check",
                "2. Secondary SWIFT Gateway Node B Health Verification",
                "3. API Route Switch to Node B",
                "4. In-Doubt UETR Reconciliation Run",
                "5. Resume Payment Dispatcher Queue"
            ],
            "stop_condition": "If Node B also returns 504, STOP immediately. Do NOT dispatch queued wires. Escalate to Head of Treasury Ops and Network Security."
        },
        "edge_cases": [
            "Wire amount exceeds single transaction limit ($50,000,000): Requires manual 4-eyes approval in Payment Portal.",
            "OFAC / Sanctions screening false positive: Hold transaction in PENDING_COMPLIANCE queue."
        ],
        "escalation": {
            "primary": "Treasury & Payments Ops On-Call (payments-ops-oncall@fxtrading.internal | Phone: ext. 8831)",
            "secondary": "SWIFT Alliance Technical Lead (swift-tech@fxtrading.internal)",
            "sla": "P1 Critical: 5-minute response SLA due to cut-off penalty",
            "condition": "Failure to route within 15 minutes of central bank cutoff deadline."
        }
    },
    {
        "filename": "FXT-RUN-005_EOD_Batch_Reconciliation_Failure.pdf",
        "id": "FXT-RUN-005",
        "title": "End-of-Day (EOD) General Ledger Reconciliation Mismatch Runbook",
        "application": "Accounting & Ledger (FXT-Ledger)",
        "service": "EOD-Recon-Job / SpringBatch",
        "region": "GLOBAL / TOKYO / LONDON / NY",
        "environment": "PROD",
        "category": "Batch Processing & Accounting",
        "version": "2.2.4",
        "owner": "Financial Control & Product Control Support",
        "last_updated": "2026-05-11",
        "summary": "End-of-Day batch reconciliation job fails with exit status FAILED due to debit/credit imbalance or missing front-office trade blotter trades, blocking ledger close.",
        "symptoms": [
            "Batch Job Status: 'JOB_EXECUTION_FAILED: Step eodLedgerReconStep failed with ImbalanceException'",
            "Error: 'Reconciliation mismatch: Front Office total ($4,120,590,120) != Back Office total ($4,120,410,120), delta = $180,000'",
            "Alert: 'EOD_LEDGER_CLOSE_BLOCKED: Accounting date 2026-10-01 cannot be marked FINAL'",
            "Operations symptom: Finance team cannot generate regulatory balance sheet files"
        ],
        "causes": [
            "Late trade amendments booked after EOD trade snapshot was captured.",
            "Cross-currency FX swap leg booking failed due to exchange rate rounding discrepancy.",
            "Duplicate trade cancellation record created by Front Office manual ticket override."
        ],
        "warnings": [
            "DO NOT manually force job status to 'COMPLETED' in BATCH_JOB_EXECUTION table without balancing the ledger delta; this constitutes regulatory audit violation.",
            "DO NOT run the EOD purge script until the reconciliation mismatch is resolved and verified.",
            "NEVER update general ledger balances directly via raw UPDATE statements without audit logging."
        ],
        "steps": [
            {
                "title": "Identify Unbalanced Book and Currency Pairs",
                "detail": "Execute approved SQL query to pinpoint which book and currency pair generated the delta.",
                "cmd_type": "SQL",
                "command": "SELECT book_id, ccy_pair, fo_total, bo_total, (fo_total - bo_total) AS delta FROM t_recon_mismatch WHERE accounting_date = TRUNC(SYSDATE) ORDER BY ABS(delta) DESC;"
            },
            {
                "title": "Identify Missing or Late-Booked Trades",
                "detail": "Compare trade snapshot timestamp against actual trade booking timestamps in core table.",
                "cmd_type": "SQL",
                "command": "SELECT trade_id, book_id, ccy_pair, notional, booking_time FROM t_trade WHERE booking_time > (SELECT snapshot_time FROM t_recon_control WHERE accounting_date = TRUNC(SYSDATE));"
            },
            {
                "title": "Trigger Incremental Trade Snapshot Ingestion",
                "detail": "Run batch tool to absorb late trades into the recon staging schema.",
                "cmd_type": "PowerShell",
                "command": "& 'C:\\FXT\\Batch\\bin\\run_recon_ingest.bat' -date (Get-Date -Format 'yyyy-MM-dd') -mode INCREMENTAL"
            },
            {
                "title": "Restart Failed EOD Batch Step",
                "detail": "Restart the Spring Batch job from failed step using standard job operator command.",
                "cmd_type": "Bash/Shell",
                "command": "java -jar /opt/fxt/eod-batch/recon-runner.jar --job.name=eodLedgerReconJob --restart.execution.id=84021"
            }
        ],
        "verifications": [
            "Check t_recon_control: status must show 'RECONCILED_BALANCED' and delta = 0.00.",
            "Verify Spring Batch exit code is COMPLETED (exit_code = 'COMPLETED').",
            "Confirm notification email 'EOD Accounting Close Successful' sent to Finance Distribution List."
        ],
        "recovery_sequence": {
            "chain": [
                "1. Database Lock Check on Staging Tables",
                "2. Incremental Late Trade Ingestion",
                "3. Ledger Discrepancy Re-computation",
                "4. Spring Batch Step Restart",
                "5. EOD Ledger Close Finalization"
            ],
            "stop_condition": "If discrepancy delta remains non-zero after incremental ingestion, STOP. Do not force close. Escalate immediately to Financial Controller on duty."
        },
        "edge_cases": [
            "Month-end multi-currency revaluation discrepancy: Requires Product Control adjustment ticket.",
            "Cancelled trade resurrected by automated retry: Quarantine trade ID via recon exception portal."
        ],
        "escalation": {
            "primary": "Finance Operations / Product Control On-Call (product-control-oncall@fxtrading.internal | Phone: ext. 7100)",
            "secondary": "Core Accounting IT Team Lead (accounting-tech@fxtrading.internal)",
            "sla": "P2 High: 45-minute resolution SLA (before 22:00 regional close)",
            "condition": "Discrepancy exceeds $100,000 or persists within 1 hour of regulatory reporting deadline."
        }
    }
]

if __name__ == "__main__":
    for doc_info in DOCS:
        build_pdf(doc_info['filename'], doc_info)
    print("All 5 approved runbook PDFs successfully created!")
