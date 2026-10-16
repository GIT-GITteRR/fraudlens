"""
FraudLens - Synthetic Financial Dataset Generator (seed_data.py)

Creates a reproducible synthetic financial dataset for FalkorDB Graph Hacks.
Includes:
- 20 synthetic accounts (A101 - A120)
- 8 synthetic devices (D01 - D08)
- 40 synthetic transactions (T1001 - T1040)
- 1 deliberately constructed suspicious-looking network (Circular money routing + shared device)
- Ordinary baseline transactions
- Strictly uses invented IDs and zero real personal or financial data
- Idempotent loading using Cypher MERGE
- Clear validation reporting
"""

import sys
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from graph_db import get_graph, clear_graph, execute_query

# Fixed random seed for 100% reproducibility
SEED = 42

def generate_synthetic_data() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Generates synthetic accounts, devices, device associations, and transactions.
    """
    random.seed(SEED)

    # ---------------------------------------------------------
    # 1. Accounts (20 total: A101 to A120)
    # ---------------------------------------------------------
    accounts = []
    base_date = datetime(2026, 1, 1)
    for i in range(1, 21):
        acc_id = f"A{100 + i}"
        created_date = (base_date + timedelta(days=i * 12)).strftime("%Y-%m-%d")
        initial_balance = round(random.uniform(2500.0, 15000.0), 2)
        accounts.append({
            "id": acc_id,
            "name": f"Account {acc_id}",
            "balance": initial_balance,
            "created_date": created_date,
            "account_type": "standard_checking"
        })

    # ---------------------------------------------------------
    # 2. Devices (8 total: D01 to D08)
    # ---------------------------------------------------------
    devices = [
        {"id": "D01", "device_type": "Mobile_iOS", "os": "iOS 17.4"},
        {"id": "D02", "device_type": "Laptop_macOS", "os": "macOS 14.3"},
        {"id": "D03", "device_type": "Mobile_Android", "os": "Android 14"},
        {"id": "D04", "device_type": "Desktop_Windows", "os": "Windows 11"},
        {"id": "D05", "device_type": "Mobile_Android", "os": "Android 13"},
        {"id": "D06", "device_type": "Tablet_iPadOS", "os": "iPadOS 17"},
        {"id": "D07", "device_type": "Laptop_Windows", "os": "Windows 11"},
        {"id": "D08", "device_type": "Mobile_Android", "os": "Android 12"}  # Used for device-sharing ring
    ]

    # ---------------------------------------------------------
    # 3. Device Associations (Account -> Device)
    # ---------------------------------------------------------
    # Ordinary accounts (A101 - A114, A119 - A120) map to normal devices (D01 - D07)
    device_associations = []
    for acc in accounts[:14]:
        # Pick normal device deterministically
        dev_idx = (int(acc["id"][1:]) % 7)  # Maps to D01 - D07
        device_associations.append((acc["id"], devices[dev_idx]["id"]))

    for acc in accounts[18:]:  # A119, A120
        device_associations.append((acc["id"], "D02"))

    # Deliberately constructed Suspicious Network:
    # Accounts A115, A116, A117, A118 ALL share Device D08!
    for acc_id in ["A115", "A116", "A117", "A118"]:
        device_associations.append((acc_id, "D08"))

    # ---------------------------------------------------------
    # 4. Transactions (40 total: T1001 to T1040)
    # ---------------------------------------------------------
    transactions = []

    # A) Suspicious Network (4 transactions forming a rapid money muling cycle):
    # A115 -> A116 -> A117 -> A118 -> A115
    # High-velocity, circular fund routing within a 70-minute window
    suspicious_cycle = [
        {"id": "T1001", "sender": "A115", "destination": "A116", "amount": 9500.00, "timestamp": "2026-10-15 14:00:00", "description": "urgent transfer"},
        {"id": "T1002", "sender": "A116", "destination": "A117", "amount": 9200.00, "timestamp": "2026-10-15 14:20:00", "description": "funds allocation"},
        {"id": "T1003", "sender": "A117", "destination": "A118", "amount": 8900.00, "timestamp": "2026-10-15 14:45:00", "description": "settlement"},
        {"id": "T1004", "sender": "A118", "destination": "A115", "amount": 8600.00, "timestamp": "2026-10-15 15:10:00", "description": "return balance"}
    ]
    transactions.extend(suspicious_cycle)

    # B) Ordinary Baseline Transactions (36 transactions: T1005 to T1040):
    # Ordinary peer-to-peer / bill pay transfers across legitimate accounts (A101 - A114, A119, A120)
    legit_acc_ids = [acc["id"] for acc in accounts if acc["id"] not in ["A115", "A116", "A117", "A118"]]
    tx_start_date = datetime(2026, 10, 1, 9, 0, 0)

    for i in range(5, 41):
        tx_id = f"T{1000 + i}"
        s_idx = (i * 3) % len(legit_acc_ids)
        d_idx = (i * 7 + 1) % len(legit_acc_ids)
        if s_idx == d_idx:
            d_idx = (d_idx + 1) % len(legit_acc_ids)

        sender = legit_acc_ids[s_idx]
        destination = legit_acc_ids[d_idx]
        amount = round(random.uniform(25.0, 480.0), 2)
        # Advance timestamp gradually
        tx_time = (tx_start_date + timedelta(hours=i * 6, minutes=random.randint(5, 45))).strftime("%Y-%m-%d %H:%M:%S")

        transactions.append({
            "id": tx_id,
            "sender": sender,
            "destination": destination,
            "amount": amount,
            "timestamp": tx_time,
            "description": f"payment_{tx_id}"
        })

    return accounts, devices, transactions, device_associations


def seed_database(reset: bool = True) -> Dict[str, Any]:
    """
    Loads the synthetic dataset into FalkorDB using MERGE queries to guarantee idempotency.
    If reset=True, clears the specific demo graph first.
    Never deletes other graphs or external data.
    """
    graph = get_graph()

    # Safe demo graph reset
    if reset:
        print("Initializing / Resetting demo graph 'fraudlens'...")
        clear_graph()
    else:
        print("Upserting into demo graph 'fraudlens' without reset...")

    accounts, devices, transactions, device_associations = generate_synthetic_data()

    # 1. Create or Match Accounts (MERGE)
    for acc in accounts:
        query = (
            "MERGE (a:Account {id: $id}) "
            "ON CREATE SET a.name = $name, a.balance = $balance, a.created_date = $created_date, a.account_type = $account_type"
        )
        graph.query(query, acc)

    # 2. Create or Match Devices (MERGE)
    for dev in devices:
        query = (
            "MERGE (d:Device {id: $id}) "
            "ON CREATE SET d.device_type = $device_type, d.os = $os"
        )
        graph.query(query, dev)

    # 3. Create or Match Device Associations (Account -[:USED_DEVICE]-> Device)
    for acc_id, dev_id in device_associations:
        query = (
            "MATCH (a:Account {id: $acc_id}), (d:Device {id: $dev_id}) "
            "MERGE (a)-[r:USED_DEVICE]->(d)"
        )
        graph.query(query, {"acc_id": acc_id, "dev_id": dev_id})

    # 4. Create or Match Transactions
    # Creates both :Transaction node and direct [:TRANSFERRED_TO] relationship between accounts
    for tx in transactions:
        # Create Transaction node
        tx_node_query = (
            "MERGE (t:Transaction {id: $id}) "
            "ON CREATE SET t.amount = $amount, t.timestamp = $timestamp, t.sender = $sender, t.destination = $destination"
        )
        graph.query(tx_node_query, {
            "id": tx["id"],
            "amount": tx["amount"],
            "timestamp": tx["timestamp"],
            "sender": tx["sender"],
            "destination": tx["destination"]
        })

        # Connect accounts with direct TRANSFERRED_TO edge and link Transaction node
        edge_query = (
            "MATCH (src:Account {id: $sender}), (dst:Account {id: $destination}), (t:Transaction {id: $id}) "
            "MERGE (src)-[r:TRANSFERRED_TO {tx_id: $id}]->(dst) "
            "ON CREATE SET r.amount = $amount, r.timestamp = $timestamp "
            "MERGE (src)-[:INITIATED]->(t) "
            "MERGE (t)-[:BENEFICIARY]->(dst)"
        )
        graph.query(edge_query, {
            "sender": tx["sender"],
            "destination": tx["destination"],
            "id": tx["id"],
            "amount": tx["amount"],
            "timestamp": tx["timestamp"]
        })

    # ---------------------------------------------------------
    # Validation & Counts
    # ---------------------------------------------------------
    acc_count = graph.query("MATCH (a:Account) RETURN count(a)").result_set[0][0]
    dev_count = graph.query("MATCH (d:Device) RETURN count(d)").result_set[0][0]
    tx_count = graph.query("MATCH (t:Transaction) RETURN count(t)").result_set[0][0]
    transfers_count = graph.query("MATCH ()-[r:TRANSFERRED_TO]->() RETURN count(r)").result_set[0][0]
    shared_devices_count = graph.query(
        "MATCH (d:Device)<-[:USED_DEVICE]-(a:Account) "
        "WITH d, count(a) AS user_count WHERE user_count > 1 "
        "RETURN count(d)"
    ).result_set[0][0]

    validation_summary = {
        "accounts_created_or_matched": acc_count,
        "devices_created_or_matched": dev_count,
        "transactions_created_or_matched": tx_count,
        "transferred_to_relationships": transfers_count,
        "devices_shared_by_multiple_accounts": shared_devices_count,
        "status": "success"
    }

    return validation_summary


def print_validation_report(summary: Dict[str, Any]):
    """
    Prints a clear, beginner-friendly validation report.
    """
    print("\n" + "=" * 55)
    print("  FRAUDLENS SYNTHETIC DATASET VALIDATION REPORT")
    print("=" * 55)
    print(f" • Accounts in Graph       : {summary['accounts_created_or_matched']} (Target: ~20)")
    print(f" • Devices in Graph        : {summary['devices_created_or_matched']} (Target: ~8)")
    print(f" • Transactions in Graph   : {summary['transactions_created_or_matched']} (Target: ~40)")
    print(f" • Direct Transfer Edges   : {summary['transferred_to_relationships']}")
    print(f" • Shared Devices Detected : {summary['devices_shared_by_multiple_accounts']} (Includes Ring D08)")
    print("=" * 55)
    print(" Suspicious Network Summary:")
    print("   1. Money Muling Ring: A115 -> A116 -> A117 -> A118 -> A115 ($9,500 cycle)")
    print("   2. Shared Device: A115, A116, A117, A118 all share physical device D08")
    print("   3. Ordinary Traffic: 36 standard transactions between A101-A114 & A119-A120")
    print("=" * 55)


if __name__ == "__main__":
    # Check if user specified --no-reset
    should_reset = True
    if len(sys.argv) > 1 and sys.argv[1] == "--no-reset":
        should_reset = False

    result = seed_database(reset=should_reset)
    print_validation_report(result)
