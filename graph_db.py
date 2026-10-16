"""
FraudLens - Graph Database Module (graph_db.py)
Encapsulates all connections and query execution against FalkorDB.
"""

import os
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from falkordb import FalkorDB

# Load environment variables
load_dotenv()

def get_db_client() -> FalkorDB:
    """
    Connects to FalkorDB using settings from .env.
    Auto-detects host, port, username, and password.
    """
    host = os.getenv("FALKORDB_HOST", "localhost").strip()
    port = int(os.getenv("FALKORDB_PORT", "6379").strip())
    password = os.getenv("FALKORDB_PASSWORD", "").strip() or None
    username = os.getenv("FALKORDB_USERNAME", "").strip() or None

    # Strip prefixes if entered with redis://
    if host.startswith("redis://"):
        host = host.replace("redis://", "")
    elif host.startswith("rediss://"):
        host = host.replace("rediss://", "")

    return FalkorDB(
        host=host,
        port=port,
        password=password,
        username=username
    )

def get_graph(graph_name: Optional[str] = None):
    """
    Returns a FalkorDB Graph object for querying.
    Defaults to the FALKORDB_GRAPH_NAME specified in .env or 'fraudlens'.
    """
    client = get_db_client()
    name = graph_name or os.getenv("FALKORDB_GRAPH_NAME", "fraudlens")
    return client.select_graph(name)

def execute_query(query: str, params: Optional[Dict[str, Any]] = None, graph_name: Optional[str] = None):
    """
    Executes a Cypher query on the graph and returns the result set.
    """
    graph = get_graph(graph_name)
    if params:
        return graph.query(query, params)
    return graph.query(query)

def clear_graph(graph_name: Optional[str] = None):
    """
    Deletes all nodes and relationships in the dedicated graph.
    Useful for resetting the graph before re-seeding synthetic data.
    """
    query = "MATCH (n) DETACH DELETE n"
    return execute_query(query, graph_name=graph_name)

def check_connection() -> Dict[str, Any]:
    """
    Verifies connection to FalkorDB and returns health status.
    """
    try:
        graph = get_graph()
        result = graph.query("RETURN 1 AS ping")
        return {"status": "ok", "message": "Connected to FalkorDB successfully", "response": result.result_set[0][0]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_graph_overview_counts() -> Dict[str, int]:
    """
    Returns total node and relationship counts directly from FalkorDB.
    """
    try:
        acc_res = execute_query("MATCH (a:Account) RETURN count(a)")
        dev_res = execute_query("MATCH (d:Device) RETURN count(d)")
        tx_res = execute_query("MATCH (t:Transaction) RETURN count(t)")
        edge_res = execute_query("MATCH ()-[r:TRANSFERRED_TO]->() RETURN count(r)")
        
        return {
            "total_accounts": acc_res.result_set[0][0] if acc_res.result_set else 0,
            "total_devices": dev_res.result_set[0][0] if dev_res.result_set else 0,
            "total_transactions": tx_res.result_set[0][0] if tx_res.result_set else 0,
            "total_transfer_edges": edge_res.result_set[0][0] if edge_res.result_set else 0
        }
    except Exception:
        return {
            "total_accounts": 0,
            "total_devices": 0,
            "total_transactions": 0,
            "total_transfer_edges": 0
        }

def get_account_transactions(account_id: str) -> List[Dict[str, Any]]:
    """
    Fetches actual inbound and outbound transactions for a given account.
    """
    query = """
    MATCH (a:Account {id: $account_id})-[r:TRANSFERRED_TO]->(dst:Account)
    RETURN r.tx_id AS tx_id, r.amount AS amount, r.timestamp AS timestamp, dst.id AS counterparty, 'Outbound' AS direction
    UNION
    MATCH (src:Account)-[r:TRANSFERRED_TO]->(a:Account {id: $account_id})
    RETURN r.tx_id AS tx_id, r.amount AS amount, r.timestamp AS timestamp, src.id AS counterparty, 'Inbound' AS direction
    """
    res = execute_query(query, {"account_id": account_id})
    tx_list = []
    if res.result_set:
        for row in res.result_set:
            tx_list.append({
                "Transaction ID": row[0],
                "Amount (₹)": f"₹{float(row[1]):,.2f}",
                "Raw Amount": float(row[1]),
                "Timestamp": row[2],
                "Counterparty Account": row[3],
                "Direction": row[4]
            })
    return tx_list

def get_account_devices(account_id: str) -> List[Dict[str, Any]]:
    """
    Fetches devices used by this account and other co-accounts sharing those devices.
    """
    query = """
    MATCH (a:Account {id: $account_id})-[:USED_DEVICE]->(d:Device)
    OPTIONAL MATCH (d)<-[:USED_DEVICE]-(other:Account)
    WHERE other.id <> a.id
    RETURN d.id AS device_id, d.device_type AS device_type, d.os AS os, collect(DISTINCT other.id) AS co_accounts
    """
    res = execute_query(query, {"account_id": account_id})
    devices = []
    if res.result_set:
        for row in res.result_set:
            co_accs = row[3] if row[3] else []
            devices.append({
                "Device ID": row[0],
                "Device Type": row[1],
                "Operating System": row[2],
                "Shared Co-Accounts": co_accs,
                "Is Shared": len(co_accs) > 0,
                "Co-Account Count": len(co_accs)
            })
    return devices

def get_account_neighborhood_subgraph(account_id: str) -> Dict[str, Any]:
    """
    Retrieves the actual neighborhood graph for the specified account from FalkorDB:
    - Target Account & connected co-accounts
    - Hardware Devices used & relationship 'USES'
    - Outbound Transactions & relationships 'MADE', 'TO_ACCOUNT'
    - Inbound Transactions & relationships 'MADE', 'TO_ACCOUNT'
    """
    nodes_dict: Dict[str, Dict[str, Any]] = {}
    edges_list: List[Dict[str, Any]] = []

    # 1. Fetch Target Account
    acc_res = execute_query("MATCH (a:Account {id: $account_id}) RETURN a.id, a.name, a.balance", {"account_id": account_id})
    if not acc_res.result_set:
        return {"nodes": [], "edges": []}

    target_row = acc_res.result_set[0]
    nodes_dict[account_id] = {
        "id": account_id,
        "label": f"Account {account_id}",
        "type": "Account",
        "is_target": True,
        "detail": f"Balance: Rs. {float(target_row[2]):,.2f}" if target_row[2] is not None else ""
    }

    # 2. Fetch Devices & Shared Co-Accounts
    dev_query = """
    MATCH (a:Account {id: $account_id})-[:USED_DEVICE]->(d:Device)
    OPTIONAL MATCH (d)<-[:USED_DEVICE]-(other:Account)
    WHERE other.id <> a.id
    RETURN d.id AS dev_id, d.device_type AS dev_type, d.os AS dev_os, other.id AS co_acc_id
    """
    dev_res = execute_query(dev_query, {"account_id": account_id})
    if dev_res.result_set:
        for row in dev_res.result_set:
            dev_id = row[0]
            dev_type = row[1]
            dev_os = row[2]
            co_acc_id = row[3]

            if dev_id and dev_id not in nodes_dict:
                nodes_dict[dev_id] = {
                    "id": dev_id,
                    "label": f"Device {dev_id}",
                    "type": "Device",
                    "is_target": False,
                    "detail": f"{dev_type} ({dev_os})"
                }
            
            # Target Account -> USES -> Device
            edge_key = (account_id, dev_id, "USES")
            if not any(e["from"] == edge_key[0] and e["to"] == edge_key[1] and e["label"] == edge_key[2] for e in edges_list):
                edges_list.append({"from": account_id, "to": dev_id, "label": "USES"})

            # Co-Account -> USES -> Device
            if co_acc_id:
                if co_acc_id not in nodes_dict:
                    nodes_dict[co_acc_id] = {
                        "id": co_acc_id,
                        "label": f"Account {co_acc_id}",
                        "type": "Account",
                        "is_target": False,
                        "detail": "Co-account sharing device"
                    }
                edge_key2 = (co_acc_id, dev_id, "USES")
                if not any(e["from"] == edge_key2[0] and e["to"] == edge_key2[1] and e["label"] == edge_key2[2] for e in edges_list):
                    edges_list.append({"from": co_acc_id, "to": dev_id, "label": "USES"})

    # 3. Fetch Outbound Transactions: (a)-[:INITIATED]->(t)-[:BENEFICIARY]->(dst)
    out_query = """
    MATCH (a:Account {id: $account_id})-[:INITIATED]->(t:Transaction)-[:BENEFICIARY]->(dst:Account)
    RETURN t.id AS tx_id, t.amount AS amount, t.timestamp AS timestamp, dst.id AS dst_id
    """
    out_res = execute_query(out_query, {"account_id": account_id})
    if out_res.result_set:
        for row in out_res.result_set:
            tx_id = row[0]
            amt = float(row[1])
            ts = row[2]
            dst_id = row[3]

            if tx_id not in nodes_dict:
                nodes_dict[tx_id] = {
                    "id": tx_id,
                    "label": f"Tx {tx_id}",
                    "type": "Transaction",
                    "is_target": False,
                    "detail": f"Rs. {amt:,.2f} at {ts}"
                }

            if dst_id not in nodes_dict:
                nodes_dict[dst_id] = {
                    "id": dst_id,
                    "label": f"Account {dst_id}",
                    "type": "Account",
                    "is_target": False,
                    "detail": "Destination account"
                }

            edges_list.append({"from": account_id, "to": tx_id, "label": "MADE"})
            edges_list.append({"from": tx_id, "to": dst_id, "label": "TO_ACCOUNT"})

    # 4. Fetch Inbound Transactions: (src)-[:INITIATED]->(t)-[:BENEFICIARY]->(a)
    in_query = """
    MATCH (src:Account)-[:INITIATED]->(t:Transaction)-[:BENEFICIARY]->(a:Account {id: $account_id})
    RETURN t.id AS tx_id, t.amount AS amount, t.timestamp AS timestamp, src.id AS src_id
    """
    in_res = execute_query(in_query, {"account_id": account_id})
    if in_res.result_set:
        for row in in_res.result_set:
            tx_id = row[0]
            amt = float(row[1])
            ts = row[2]
            src_id = row[3]

            if tx_id not in nodes_dict:
                nodes_dict[tx_id] = {
                    "id": tx_id,
                    "label": f"Tx {tx_id}",
                    "type": "Transaction",
                    "is_target": False,
                    "detail": f"₹{amt:,.2f} at {ts}"
                }

            if src_id not in nodes_dict:
                nodes_dict[src_id] = {
                    "id": src_id,
                    "label": f"Account {src_id}",
                    "type": "Account",
                    "is_target": False,
                    "detail": "Origin account"
                }

            edges_list.append({"from": src_id, "to": tx_id, "label": "MADE"})
            edges_list.append({"from": tx_id, "to": account_id, "label": "TO_ACCOUNT"})

    return {
        "nodes": list(nodes_dict.values()),
        "edges": edges_list
    }
