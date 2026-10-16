"""
FraudLens - Deterministic Explainable Risk Scoring Engine (risk_engine.py)

Calculates a demo investigation-priority score (0-100) based on actual
graph relationships and transaction topologies in FalkorDB.

IMPORTANT NOTE:
This score is an investigation-priority score for demo workflows, NOT a
calibrated statistical probability of fraud. Shared devices and high-value
transfers are investigation signals, not proof of wrongdoing.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from graph_db import execute_query

@dataclass
class RiskConfig:
    """
    Configurable thresholds and point allocations for investigation signals.
    All parameters can be tuned for demo scenarios.
    """
    # Signal 1: Shared physical device with another account
    shared_device_points: int = 25

    # Signal 2: Destination connected to multiple sender accounts
    suspicious_destination_points: int = 20

    # Signal 3: Outbound transaction exceeding threshold
    # Configurable demo threshold (default: ₹5,000.0 for our synthetic dataset scale, or ₹50,000)
    high_amount_threshold: float = float(os.getenv("RISK_HIGH_AMOUNT_THRESHOLD", "5000.0"))
    high_amount_points: int = 15

    # Signal 4: Rapid transaction burst within a short time window
    burst_window_minutes: int = 120  # 2 hours
    burst_min_tx_count: int = 2     # At least 2 transactions in the window
    burst_points: int = 20

    # Classification thresholds
    low_max_score: int = 29         # 0 - 29: Low
    medium_max_score: int = 69      # 30 - 69: Medium
    # 70 - 100: High

def parse_iso_datetime(dt_str: str) -> Optional[datetime]:
    """Safely parses timestamp strings from graph database."""
    if not dt_str:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(dt_str).strip(), fmt)
        except ValueError:
            continue
    return None

def calculate_account_risk(
    account_id: str,
    config: Optional[RiskConfig] = None
) -> Dict[str, Any]:
    """
    Calculates the deterministic investigation-priority score for a specific account.

    Evaluates 4 graph signals:
    1. Shared Device: Account shares physical device with other account(s) (+25)
    2. Multi-Sender Destination: Transferred to a destination connected to other senders (+20)
    3. High-Value Transfer: At least one transfer >= high_amount_threshold (+15)
    4. Transaction Velocity Burst: >= burst_min_tx_count within burst_window_minutes (+20)

    Score is capped at 100.
    """
    if config is None:
        config = RiskConfig()

    account_id = str(account_id or "").strip()
    
    # 0. Handle Missing Data / Empty input gracefully
    if not account_id:
        return {
            "account_id": "",
            "account_exists": False,
            "risk_score": 0,
            "risk_level": "Low",
            "factors": [],
            "evidence_ids": [],
            "explanations": ["No account ID provided for evaluation."],
            "investigation_disclaimer": "Demo investigation-priority score only. Not proof of wrongdoing."
        }

    # Verify account exists in graph
    exists_query = "MATCH (a:Account {id: $account_id}) RETURN a.id, a.name, a.balance"
    exists_res = execute_query(exists_query, {"account_id": account_id})
    if not exists_res.result_set:
        return {
            "account_id": account_id,
            "account_exists": False,
            "risk_score": 0,
            "risk_level": "Low",
            "factors": [],
            "evidence_ids": [],
            "explanations": [f"Account '{account_id}' was not found in the graph database."],
            "investigation_disclaimer": "Demo investigation-priority score only. Not proof of wrongdoing."
        }

    account_data = exists_res.result_set[0]
    total_score = 0
    factors: List[Dict[str, Any]] = []
    all_evidence_ids: Set[str] = set()

    # -------------------------------------------------------------------------
    # Signal 1: Shared Device with other accounts (+25 points)
    # -------------------------------------------------------------------------
    device_query = """
    MATCH (a:Account {id: $account_id})-[:USED_DEVICE]->(d:Device)<-[:USED_DEVICE]-(other:Account)
    WHERE other.id <> a.id
    RETURN d.id AS device_id, d.device_type AS dev_type, collect(DISTINCT other.id) AS co_accounts
    """
    dev_res = execute_query(device_query, {"account_id": account_id})
    if dev_res.result_set:
        shared_devices = []
        co_accounts_all = []
        for row in dev_res.result_set:
            d_id = row[0]
            co_accs = row[2]
            shared_devices.append(d_id)
            co_accounts_all.extend(co_accs)
            all_evidence_ids.add(d_id)
            for ca in co_accs:
                all_evidence_ids.add(ca)

        total_score += config.shared_device_points
        factors.append({
            "signal_name": "SHARED_DEVICE",
            "points": config.shared_device_points,
            "evidence_ids": sorted(list(set(shared_devices + co_accounts_all))),
            "explanation": (
                f"Shared device signal: Account shares hardware device(s) {shared_devices} "
                f"with {len(set(co_accounts_all))} other account(s) ({sorted(list(set(co_accounts_all)))})."
            )
        })

    # -------------------------------------------------------------------------
    # Signal 2: Destination connected to multiple accounts (+20 points)
    # -------------------------------------------------------------------------
    dest_query = """
    MATCH (a:Account {id: $account_id})-[r:TRANSFERRED_TO]->(dst:Account)<-[:TRANSFERRED_TO]-(other:Account)
    WHERE other.id <> a.id
    RETURN dst.id AS destination_id, collect(DISTINCT other.id) AS other_senders
    """
    dest_res = execute_query(dest_query, {"account_id": account_id})
    if dest_res.result_set:
        dest_ids = []
        other_senders_all = []
        for row in dest_res.result_set:
            dst_id = row[0]
            others = row[1]
            dest_ids.append(dst_id)
            other_senders_all.extend(others)
            all_evidence_ids.add(dst_id)
            for o in others:
                all_evidence_ids.add(o)

        total_score += config.suspicious_destination_points
        factors.append({
            "signal_name": "MULTI_SENDER_DESTINATION",
            "points": config.suspicious_destination_points,
            "evidence_ids": sorted(list(set(dest_ids + other_senders_all))),
            "explanation": (
                f"Multi-sender destination signal: Transferred funds to destination(s) {dest_ids}, "
                f"which also receive transfers from other accounts ({sorted(list(set(other_senders_all)))})."
            )
        })

    # -------------------------------------------------------------------------
    # Signal 3: Transaction over configurable demo threshold (+15 points)
    # -------------------------------------------------------------------------
    high_val_query = """
    MATCH (a:Account {id: $account_id})-[r:TRANSFERRED_TO]->(dst:Account)
    WHERE r.amount >= $threshold
    RETURN r.tx_id AS tx_id, r.amount AS amount, dst.id AS destination, r.timestamp AS timestamp
    """
    high_val_res = execute_query(high_val_query, {
        "account_id": account_id,
        "threshold": config.high_amount_threshold
    })
    if high_val_res.result_set:
        high_tx_ids = []
        max_amt = 0.0
        for row in high_val_res.result_set:
            tx_id = row[0]
            amt = float(row[1])
            high_tx_ids.append(tx_id)
            all_evidence_ids.add(tx_id)
            if amt > max_amt:
                max_amt = amt

        total_score += config.high_amount_points
        factors.append({
            "signal_name": "HIGH_VALUE_TRANSACTION",
            "points": config.high_amount_points,
            "evidence_ids": high_tx_ids,
            "explanation": (
                f"High-value transfer signal: Outbound transaction(s) {high_tx_ids} "
                f"exceeded investigation threshold (>= {config.high_amount_threshold}), peak: ₹{max_amt:,.2f}."
            )
        })

    # -------------------------------------------------------------------------
    # Signal 4: Several transactions in short time window (+20 points)
    # -------------------------------------------------------------------------
    all_tx_query = """
    MATCH (a:Account {id: $account_id})-[r:TRANSFERRED_TO]->(dst:Account)
    RETURN r.tx_id AS tx_id, r.amount AS amount, r.timestamp AS timestamp
    ORDER BY r.timestamp ASC
    """
    all_tx_res = execute_query(all_tx_query, {"account_id": account_id})
    if all_tx_res.result_set and len(all_tx_res.result_set) >= config.burst_min_tx_count:
        parsed_txs = []
        for row in all_tx_res.result_set:
            dt = parse_iso_datetime(row[2])
            if dt:
                parsed_txs.append({"tx_id": row[0], "amount": row[1], "dt": dt})

        # Check for clustering within burst_window_minutes
        burst_detected = False
        burst_evidence: List[str] = []
        window_seconds = config.burst_window_minutes * 60

        for i in range(len(parsed_txs)):
            cluster = [parsed_txs[i]]
            for j in range(i + 1, len(parsed_txs)):
                delta = (parsed_txs[j]["dt"] - parsed_txs[i]["dt"]).total_seconds()
                if delta <= window_seconds:
                    cluster.append(parsed_txs[j])
            
            if len(cluster) >= config.burst_min_tx_count:
                burst_detected = True
                burst_evidence = [item["tx_id"] for item in cluster]
                break

        if burst_detected:
            total_score += config.burst_points
            for tid in burst_evidence:
                all_evidence_ids.add(tid)
            factors.append({
                "signal_name": "HIGH_VELOCITY_BURST",
                "points": config.burst_points,
                "evidence_ids": burst_evidence,
                "explanation": (
                    f"Velocity burst signal: {len(burst_evidence)} transactions ({burst_evidence}) "
                    f"executed within a {config.burst_window_minutes}-minute window."
                )
            })

    # -------------------------------------------------------------------------
    # Cap score at 100 & Assign Categorical Level
    # -------------------------------------------------------------------------
    final_score = min(100, max(0, total_score))

    if final_score <= config.low_max_score:
        risk_level = "Low"
    elif final_score <= config.medium_max_score:
        risk_level = "Medium"
    else:
        risk_level = "High"

    human_explanations = [f["explanation"] for f in factors]
    if not human_explanations:
        human_explanations.append("No suspicious graph signals, shared devices, or burst transfers detected.")

    return {
        "account_id": account_id,
        "account_name": account_data[1] if account_data else account_id,
        "account_exists": True,
        "risk_score": final_score,
        "risk_level": risk_level,
        "factors": factors,
        "evidence_ids": sorted(list(all_evidence_ids)),
        "explanations": human_explanations,
        "investigation_disclaimer": (
            "This is a demo investigation-priority score intended to guide review queues, "
            "not a calibrated probability of fraud or proof of wrongdoing."
        )
    }

def get_all_account_risk_summaries(config: Optional[RiskConfig] = None) -> List[Dict[str, Any]]:
    """
    Scans all accounts in the graph and returns sorted risk summaries.
    """
    accounts_res = execute_query("MATCH (a:Account) RETURN a.id ORDER BY a.id")
    results = []
    if accounts_res.result_set:
        for row in accounts_res.result_set:
            acc_id = row[0]
            summary = calculate_account_risk(acc_id, config=config)
            results.append(summary)

    return sorted(results, key=lambda x: x["risk_score"], reverse=True)

if __name__ == "__main__":
    print("Testing Risk Engine against active FalkorDB graph...")
    summaries = get_all_account_risk_summaries()
    print(f"Total Accounts Evaluated: {len(summaries)}")
    for s in summaries[:5]:
        print(f"[{s['risk_level']}] Account {s['account_id']} - Score: {s['risk_score']}/100")
        for exp in s["explanations"]:
            print(f"   • {exp}")
