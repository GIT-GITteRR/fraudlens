"""
FraudLens - AI Investigation Assistant (ai_assistant.py)

Provides grounded, explainable forensic answers using existing FalkorDB query results.
Security & Guardrails:
- Reads API key strictly from environment variables (GEMINI_API_KEY or OPENAI_API_KEY).
- Never hardcodes API keys or transmits database credentials.
- Input is treated as untrusted text; no arbitrary Cypher execution.
- LLM is constrained strictly to the supplied evidence dossier.
- Deterministic fallback summary is provided whenever an API key is missing or unavailable.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from graph_db import get_account_transactions, get_account_devices
from risk_engine import calculate_account_risk, RiskConfig

# System instruction strictly enforcing grounding and neutrality
FORENSIC_SYSTEM_INSTRUCTION = """
You are the FraudLens Forensic AI Assistant, analyzing synthetic financial investigation graphs.
Answer the investigator's question STRICTLY and ONLY using the factual Evidence Dossier provided below.

MANDATORY RULES:
1. Grounding: Rely solely on the provided Evidence Dossier. Do NOT invent transactions, accounts, devices, or relationships.
2. Identifiers: Always cite the actual IDs (e.g. Account 'A115', Device 'D08', Transaction 'T1001') that support your answer.
3. Insufficient Evidence: If the provided evidence does not contain the answer, explicitly state: "Insufficient evidence in the graph records to determine [X]."
4. Neutrality & Compliance: Never claim that an individual or account is definitively "guilty" of fraud or criminal conduct. Treat all signals as demo investigation-priority indicators warranting analyst review.
5. Safety: Never execute or generate Cypher queries or reveal database configuration. Keep responses concise, objective, and professional.
"""

def compile_evidence_dossier(account_id: str, config: Optional[RiskConfig] = None) -> Dict[str, Any]:
    """
    Retrieves and structures all factual evidence for an account using
    the existing verified FalkorDB investigation functions.
    """
    account_id = str(account_id or "").strip()
    
    # 1. Risk scoring and signal breakdown
    risk_info = calculate_account_risk(account_id, config=config)
    
    # 2. Transaction ledger
    transactions = get_account_transactions(account_id)
    
    # 3. Hardware device associations
    devices = get_account_devices(account_id)
    
    return {
        "account_id": account_id,
        "account_exists": risk_info.get("account_exists", False),
        "account_name": risk_info.get("account_name", account_id),
        "risk_score": risk_info.get("risk_score", 0),
        "risk_level": risk_info.get("risk_level", "Low"),
        "triggered_signals": risk_info.get("factors", []),
        "evidence_ids": risk_info.get("evidence_ids", []),
        "explanations": risk_info.get("explanations", []),
        "transactions": transactions,
        "devices": devices
    }

def format_dossier_text(dossier: Dict[str, Any]) -> str:
    """
    Converts structured evidence into a clean, read-only text dossier for LLM ingestion.
    """
    if not dossier.get("account_exists", False):
        return f"Evidence Dossier: Account '{dossier.get('account_id', '')}' was not found in graph database."

    lines = [
        f"=== EVIDENCE DOSSIER FOR ACCOUNT: {dossier['account_id']} ===",
        f"Account Name: {dossier.get('account_name', dossier['account_id'])}",
        f"Investigation Priority Score: {dossier['risk_score']} / 100 ({dossier['risk_level']} Priority)",
        f"Verified Evidence Identifiers: {', '.join(dossier['evidence_ids']) if dossier['evidence_ids'] else 'None'}",
        "\n--- TRIGGERED GRAPH SIGNALS ---"
    ]

    if dossier["triggered_signals"]:
        for factor in dossier["triggered_signals"]:
            lines.append(f"• [{factor['signal_name']} (+{factor['points']} pts)]: {factor['explanation']} (IDs: {', '.join(factor['evidence_ids'])})")
    else:
        lines.append("• Clean Baseline: No abnormal graph rings, shared devices, or velocity spikes.")

    lines.append("\n--- CONNECTED HARDWARE DEVICES ---")
    if dossier["devices"]:
        for dev in dossier["devices"]:
            sharing_info = f"SHARED with co-accounts: {', '.join(dev['Shared Co-Accounts'])}" if dev["Is Shared"] else "Dedicated to this account"
            lines.append(f"• Device {dev['Device ID']} ({dev['Device Type']}, {dev['Operating System']}): {sharing_info}")
    else:
        lines.append("• No device associations recorded.")

    lines.append("\n--- TRANSACTION ACTIVITY LEDGER ---")
    if dossier["transactions"]:
        for tx in dossier["transactions"]:
            lines.append(f"• Tx {tx['Transaction ID']} [{tx['Direction']}]: {tx['Amount (₹)']} at {tx['Timestamp']} (Counterparty: {tx['Counterparty Account']})")
    else:
        lines.append("• No transaction activity recorded.")

    return "\n".join(lines)

def generate_deterministic_summary(dossier: Dict[str, Any], question: str) -> str:
    """
    Deterministic fallback when an LLM API key is not configured or unavailable.
    Synthesizes real FalkorDB evidence directly with zero hallucination.
    """
    acc_id = dossier.get("account_id", "Unknown")
    score = dossier.get("risk_score", 0)
    level = dossier.get("risk_level", "Low")
    evidence_ids = dossier.get("evidence_ids", [])
    signals = dossier.get("triggered_signals", [])
    devices = dossier.get("devices", [])
    txs = dossier.get("transactions", [])

    output = [
        f"### 🛡️ Forensic Evidence Summary for `{acc_id}`",
        f"**Investigation Priority:** `{level.upper()}` ({score} / 100)",
        f"**Linked Evidence Identifiers:** `{', '.join(evidence_ids) if evidence_ids else 'None'}`",
        ""
    ]

    # Shared device highlights
    shared_devs = [d for d in devices if d.get("Is Shared")]
    if shared_devs:
        output.append("#### ⚠️ Hardware Infrastructure Signal:")
        for d in shared_devs:
            output.append(f"- Account `{acc_id}` shares physical device `{d['Device ID']}` with co-accounts: {', '.join([f'`{a}`' for a in d['Shared Co-Accounts']])}.")

    # Signals
    if signals:
        output.append("#### 🚨 Graph Risk Factors:")
        for s in signals:
            output.append(f"- **{s['signal_name']}** (+{s['points']} pts): {s['explanation']}")
    else:
        output.append("#### ✅ Clean Baseline:")
        output.append(f"- No high-value transfers, burst velocity, or shared hardware rings detected for `{acc_id}`.")

    # Transactions
    if txs:
        output.append(f"#### 💳 Activity Ledger ({len(txs)} records):")
        for t in txs[:5]:
            output.append(f"- `{t['Transaction ID']}`: {t['Direction']} {t['Amount (₹)']} with Account `{t['Counterparty Account']}` on {t['Timestamp']}")

    output.append("")
    output.append("> ℹ️ *Deterministic Evidence Mode: Generated directly from FalkorDB query records. Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env` to enable generative AI natural language Q&A.*")

    return "\n".join(output)

def query_llm_assistant(
    account_id: str,
    question: str,
    config: Optional[RiskConfig] = None,
    api_key_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Orchestrates the investigation assistant flow:
    1. Collects factual evidence from FalkorDB.
    2. Checks for configured API key (Gemini or OpenAI).
    3. If available, sends grounded prompt to LLM.
    4. If unavailable, rate-limited, or error, seamlessly falls back to deterministic summary.
    """
    dossier = compile_evidence_dossier(account_id, config=config)
    dossier_text = format_dossier_text(dossier)
    clean_question = str(question or "").strip()

    if not clean_question:
        clean_question = f"Summarize the forensic evidence and risk factors for Account {account_id}."

    # Look for API keys strictly in environment, st.secrets, or override
    from graph_db import get_config_val
    gemini_key = api_key_override or get_config_val("GEMINI_API_KEY", "")
    openai_key = get_config_val("OPENAI_API_KEY", "")

    # -------------------------------------------------------------------------
    # Route 1: Google Gemini API (if GEMINI_API_KEY is configured)
    # -------------------------------------------------------------------------
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {"parts": [{"text": FORENSIC_SYSTEM_INSTRUCTION}]},
                "contents": [
                    {
                        "parts": [
                            {"text": f"INVESTIGATION QUESTION: {clean_question}\n\n{dossier_text}"}
                        ]
                    }
                ],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 600}
            }
            resp = requests.post(url, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                return {
                    "provider": "Google Gemini (1.5 Flash)",
                    "status": "success",
                    "answer": text,
                    "evidence_ids": dossier["evidence_ids"],
                    "is_fallback": False
                }
        except Exception:
            pass  # Fail gracefully to deterministic fallback below

    # -------------------------------------------------------------------------
    # Route 2: OpenAI API (if OPENAI_API_KEY is configured)
    # -------------------------------------------------------------------------
    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"}
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": FORENSIC_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": f"INVESTIGATION QUESTION: {clean_question}\n\n{dossier_text}"}
                ],
                "temperature": 0.1,
                "max_tokens": 600
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                return {
                    "provider": "OpenAI (GPT-4o-mini)",
                    "status": "success",
                    "answer": text,
                    "evidence_ids": dossier["evidence_ids"],
                    "is_fallback": False
                }
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Route 3: Deterministic Evidence-Based Fallback
    # -------------------------------------------------------------------------
    fallback_text = generate_deterministic_summary(dossier, clean_question)
    return {
        "provider": "Deterministic Evidence Engine (FalkorDB)",
        "status": "fallback",
        "answer": fallback_text,
        "evidence_ids": dossier["evidence_ids"],
        "is_fallback": True
    }
