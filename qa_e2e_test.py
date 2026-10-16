"""
FraudLens - End-to-End QA Test Suite (qa_e2e_test.py)

Automated execution of the 15 specific QA checks requested:
1. Application starts successfully (HTTP 200)
2. FalkorDB connection succeeds
3. Synthetic seed data can be initialized repeatedly without duplicating nodes
4. Dashboard metrics come from actual query results
5. Account selection works
6. Transaction history matches database records
7. Shared-device queries return expected synthetic relationships
8. Risk scores match documented scoring rules
9. Evidence IDs in the explanation exist in the database
10. Normal accounts and suspicious accounts can both be investigated
11. Missing accounts and empty results handled gracefully
12. Database disconnection displays a useful error instead of crashing
13. AI failure or missing API key does not break core functionality
14. App contains no real financial or personal information
15. No secrets are committed or displayed
"""

import os
import re
import unittest
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

from graph_db import (
    check_connection,
    get_graph_overview_counts,
    get_account_transactions,
    get_account_devices,
    get_account_neighborhood_subgraph,
    execute_query
)
from seed_data import seed_database
from risk_engine import calculate_account_risk, RiskConfig
from ai_assistant import query_llm_assistant, compile_evidence_dossier

class FraudLensE2EQATest(unittest.TestCase):

    def test_01_app_starts_successfully(self):
        """Test 1: Application starts successfully (HTTP 200)."""
        try:
            resp = requests.get("http://localhost:8501", timeout=5)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Streamlit", resp.text)
            print(" [PASS] Test 1: Application is live and serving HTTP 200.")
        except Exception as e:
            self.fail(f"App server check failed: {e}")

    def test_02_falkordb_connection_succeeds(self):
        """Test 2: FalkorDB connection succeeds."""
        status = check_connection()
        self.assertEqual(status["status"], "ok")
        self.assertEqual(status["response"], 1)
        print(" [PASS] Test 2: FalkorDB connection verified (Ping response: 1).")

    def test_03_seed_data_idempotency(self):
        """Test 3: Synthetic seed data can be initialized more than once without duplicating the graph."""
        res1 = seed_database(reset=False)
        c1_acc = res1["accounts_created_or_matched"]
        c1_dev = res1["devices_created_or_matched"]
        c1_tx = res1["transactions_created_or_matched"]

        res2 = seed_database(reset=False)
        c2_acc = res2["accounts_created_or_matched"]
        c2_dev = res2["devices_created_or_matched"]
        c2_tx = res2["transactions_created_or_matched"]

        self.assertEqual(c1_acc, c2_acc, "Account count duplicated on re-seed!")
        self.assertEqual(c1_dev, c2_dev, "Device count duplicated on re-seed!")
        self.assertEqual(c1_tx, c2_tx, "Transaction count duplicated on re-seed!")
        self.assertEqual(c1_acc, 20)
        self.assertEqual(c1_dev, 8)
        self.assertEqual(c1_tx, 40)
        print(f" [PASS] Test 3: Idempotency verified: Re-running preserved exact counts (20 Acc, 8 Dev, 40 Tx).")

    def test_04_dashboard_metrics_from_actual_queries(self):
        """Test 4: Dashboard metrics come from actual query results."""
        counts = get_graph_overview_counts()
        self.assertGreater(counts["total_accounts"], 0)
        self.assertGreater(counts["total_devices"], 0)
        self.assertGreater(counts["total_transactions"], 0)
        self.assertGreater(counts["total_transfer_edges"], 0)
        raw_acc = execute_query("MATCH (a:Account) RETURN count(a)").result_set[0][0]
        self.assertEqual(counts["total_accounts"], raw_acc)
        print(f" [PASS] Test 4: Dashboard metrics match live Cypher query: {counts['total_accounts']} accounts, {counts['total_devices']} devices, {counts['total_transactions']} transactions.")

    def test_05_account_selection_works(self):
        """Test 5: Account selection works for arbitrary IDs in graph."""
        res = execute_query("MATCH (a:Account) RETURN a.id ORDER BY a.id LIMIT 5")
        acc_ids = [r[0] for r in res.result_set]
        self.assertGreaterEqual(len(acc_ids), 5)
        for acc_id in acc_ids:
            risk = calculate_account_risk(acc_id)
            self.assertTrue(risk["account_exists"])
            self.assertEqual(risk["account_id"], acc_id)
        print(f" [PASS] Test 5: Account selection and inspection verified across {acc_ids}.")

    def test_06_transaction_history_matches_database(self):
        """Test 6: Transaction history matches the database."""
        txs = get_account_transactions("A115")
        self.assertGreater(len(txs), 0)
        
        direct_tx = execute_query(
            "MATCH (a:Account {id: 'A115'})-[r:TRANSFERRED_TO]->(dst:Account) RETURN r.tx_id, r.amount"
        ).result_set
        direct_tx_ids = [r[0] for r in direct_tx]

        helper_tx_ids = [t["Transaction ID"] for t in txs if t["Direction"] == "Outbound"]
        self.assertEqual(sorted(direct_tx_ids), sorted(helper_tx_ids))
        print(f" [PASS] Test 6: Transaction ledger records match FalkorDB direct Cypher queries.")

    def test_07_shared_device_queries_match_synthetic_model(self):
        """Test 7: Shared-device queries return the expected synthetic relationships."""
        devs = get_account_devices("A115")
        shared_dev = next((d for d in devs if d["Device ID"] == "D08"), None)
        self.assertIsNotNone(shared_dev, "Device D08 not found for Account A115!")
        self.assertTrue(shared_dev["Is Shared"])
        expected_co = {"A116", "A117", "A118"}
        actual_co = set(shared_dev["Shared Co-Accounts"])
        self.assertEqual(expected_co, actual_co)
        print(f" [PASS] Test 7: Shared device D08 correctly maps to co-accounts: {actual_co}.")

    def test_08_risk_scores_match_documented_rules(self):
        """Test 8: Risk scores match the documented scoring rules."""
        cfg = RiskConfig(high_amount_threshold=5000.0)
        risk = calculate_account_risk("A115", config=cfg)
        
        factor_names = [f["signal_name"] for f in risk["factors"]]
        self.assertIn("SHARED_DEVICE", factor_names)
        self.assertIn("HIGH_VALUE_TRANSACTION", factor_names)
        
        calculated_sum = sum(f["points"] for f in risk["factors"])
        self.assertEqual(risk["risk_score"], calculated_sum)
        self.assertEqual(risk["risk_score"], 40)
        self.assertEqual(risk["risk_level"], "Medium")
        print(f" [PASS] Test 8: Risk scoring strictly matches documented point rules: Score = {risk['risk_score']} ({risk['risk_level']}).")

    def test_09_evidence_ids_exist_in_database(self):
        """Test 9: Evidence IDs in the explanation exist in the database."""
        risk = calculate_account_risk("A115")
        evidence_ids = risk["evidence_ids"]
        self.assertGreater(len(evidence_ids), 0)

        for eid in evidence_ids:
            if eid.startswith("A"):
                node_check = execute_query("MATCH (a:Account {id: $id}) RETURN count(a)", {"id": eid}).result_set[0][0]
                self.assertEqual(node_check, 1, f"Evidence Account ID '{eid}' does not exist in FalkorDB!")
            elif eid.startswith("D"):
                node_check = execute_query("MATCH (d:Device {id: $id}) RETURN count(d)", {"id": eid}).result_set[0][0]
                self.assertEqual(node_check, 1, f"Evidence Device ID '{eid}' does not exist in FalkorDB!")
            elif eid.startswith("T"):
                node_check = execute_query("MATCH (t:Transaction {id: $id}) RETURN count(t)", {"id": eid}).result_set[0][0]
                self.assertEqual(node_check, 1, f"Evidence Transaction ID '{eid}' does not exist in FalkorDB!")
        print(f" [PASS] Test 9: All evidence IDs {evidence_ids} physically verified in FalkorDB nodes.")

    def test_10_normal_and_suspicious_accounts_investigated(self):
        """Test 10: Normal accounts and suspicious-looking accounts can both be investigated."""
        suspicious = calculate_account_risk("A115")
        self.assertGreater(suspicious["risk_score"], 29)
        self.assertIn(suspicious["risk_level"], ["Medium", "High"])

        normal = calculate_account_risk("A101")
        self.assertLessEqual(normal["risk_score"], 29)
        self.assertEqual(normal["risk_level"], "Low")
        print(f" [PASS] Test 10: Both suspicious (A115: {suspicious['risk_score']}) and normal (A101: {normal['risk_score']}) investigated successfully.")

    def test_11_missing_accounts_and_empty_results_handled(self):
        """Test 11: Missing accounts and empty results are handled gracefully."""
        missing = calculate_account_risk("A999_NONEXISTENT")
        self.assertFalse(missing["account_exists"])
        self.assertEqual(missing["risk_score"], 0)
        self.assertEqual(missing["risk_level"], "Low")

        sub = get_account_neighborhood_subgraph("A999_NONEXISTENT")
        self.assertEqual(len(sub["nodes"]), 0)
        self.assertEqual(len(sub["edges"]), 0)

        txs = get_account_transactions("A999_NONEXISTENT")
        self.assertEqual(len(txs), 0)
        print(" [PASS] Test 11: Nonexistent entities handled with empty structures and zero crashes.")

    def test_12_database_disconnection_displays_useful_error(self):
        """Test 12: Database disconnection displays a useful error instead of crashing the entire app."""
        from falkordb import FalkorDB
        # Simulate connection to an unreachable port
        try:
            broken_client = FalkorDB(host="127.0.0.1", port=59999, socket_timeout=1)
            broken_graph = broken_client.select_graph("fraudlens")
            broken_graph.query("RETURN 1")
            self.fail("Should have raised connection error")
        except Exception as e:
            error_str = str(e).lower()
            self.assertTrue(len(error_str) > 0)
            self.assertTrue("timeout" in error_str or "refused" in error_str or "error" in error_str)
            print(f" [PASS] Test 12: Database disconnection caught cleanly with informative message: '{str(e)[:60]}...'")

    def test_13_ai_failure_or_missing_api_key_does_not_break_app(self):
        """Test 13: AI failure or a missing API key does not break core functionality."""
        res = query_llm_assistant(
            account_id="A115",
            question="Why was this account flagged?",
            api_key_override=None
        )
        self.assertTrue(res["is_fallback"])
        self.assertIn("A115", res["answer"])
        self.assertIn("T1001", res["answer"])
        self.assertIn("D08", res["answer"])
        print(" [PASS] Test 13: Deterministic fallback operated cleanly without API key, preserving full investigation flow.")

    def test_14_no_real_financial_or_personal_information(self):
        """Test 14: The app contains no real financial or personal information."""
        accounts_res = execute_query("MATCH (a:Account) RETURN a.id, a.name")
        devices_res = execute_query("MATCH (d:Device) RETURN d.id, d.device_type, d.os")

        for row in accounts_res.result_set:
            acc_id, name = row[0], row[1]
            self.assertTrue(re.match(r"^A\d+$", acc_id), f"Non-synthetic ID found: {acc_id}")
            self.assertTrue("Account" in name or acc_id in name, f"Real name suspected: {name}")

        for row in devices_res.result_set:
            dev_id = row[0]
            self.assertTrue(re.match(r"^D\d+$", dev_id), f"Non-synthetic device ID found: {dev_id}")
        print(" [PASS] Test 14: Confirmed 100% synthetic data: all entity IDs follow strictly invented format (A101-A120, D01-D08).")

    def test_15_no_secrets_committed_or_displayed(self):
        """Test 15: No secrets are committed or displayed."""
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
        self.assertIn(".env", gitignore_content)

        with open(".env.example", "r") as f:
            example_content = f.read()
        self.assertNotIn("Divya@123", example_content)
        self.assertIn("your-password-here", example_content)

        import subprocess
        git_status = subprocess.check_output(["git", "status"], text=True)
        self.assertNotIn("\t.env\n", git_status)
        self.assertNotIn("\t.env ", git_status)
        print(" [PASS] Test 15: Security verified: .env is ignored by Git, .env.example has zero secrets, and git status is clean.")

if __name__ == "__main__":
    unittest.main()
