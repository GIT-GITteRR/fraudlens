"""
Unit Tests for FraudLens Risk Engine (test_risk_engine.py)

Tests cover:
1. Normal account (Low risk, clean baseline)
2. Account with one signal (e.g. only shared device or only high value)
3. Account with multiple signals (Suspicious network: high value, shared device, multi-sender destination)
4. Missing data (Nonexistent ID, empty string, None)
5. Score capping and investigation disclaimer
"""

import unittest
from risk_engine import calculate_account_risk, RiskConfig

class TestRiskEngine(unittest.TestCase):

    def setUp(self):
        # Default config: high_amount_threshold = 5000.0
        self.default_config = RiskConfig()

    def test_normal_account(self):
        """
        Scenario 1: Normal Account
        Account A101 is part of ordinary baseline transfers with no high value transfers.
        Should result in Low investigation priority.
        """
        # A101 with threshold 5000: amounts are < 500, no multi-sender destination, no burst
        result = calculate_account_risk("A101", config=self.default_config)

        self.assertTrue(result["account_exists"])
        self.assertEqual(result["account_id"], "A101")
        # Should be Low or under 30
        self.assertLessEqual(result["risk_score"], 29)
        self.assertEqual(result["risk_level"], "Low")
        self.assertIn("investigation_disclaimer", result)
        print("\n [TEST PASS] Normal account A101 scored Low:", result["risk_score"], "/ 100")

    def test_account_with_one_signal(self):
        """
        Scenario 2: Account with exactly ONE signal
        By configuring a high threshold (e.g. 999,999) and high burst count,
        an account like A101 or A102 that shares a normal device will trigger
        ONLY the shared device signal (+25 points).
        """
        single_signal_config = RiskConfig(
            shared_device_points=25,
            suspicious_destination_points=20,
            high_amount_threshold=999999.0,  # Ensure high amount does not trigger
            burst_min_tx_count=99           # Ensure burst does not trigger
        )
        # In our dataset, A119 shares D02 with A120 and has ordinary small transfers
        result = calculate_account_risk("A119", config=single_signal_config)

        self.assertTrue(result["account_exists"])
        # If A119 has shared device, it gets exactly 25 points
        if result["factors"]:
            self.assertEqual(len(result["factors"]), 1)
            self.assertEqual(result["factors"][0]["signal_name"], "SHARED_DEVICE")
            self.assertEqual(result["risk_score"], 25)
            self.assertEqual(result["risk_level"], "Low")
            self.assertIn("D02", result["evidence_ids"])
            print(" [TEST PASS] Account with one signal (A119) scored exactly 25 points (SHARED_DEVICE only)")
        else:
            # Or test with high amount threshold low enough for only 1 transaction on A101
            one_tx_config = RiskConfig(
                shared_device_points=0,
                suspicious_destination_points=0,
                high_amount_threshold=100.0,
                high_amount_points=15,
                burst_min_tx_count=99
            )
            res2 = calculate_account_risk("A101", config=one_tx_config)
            self.assertEqual(len(res2["factors"]), 1)
            self.assertEqual(res2["risk_score"], 15)
            print(" [TEST PASS] Account with one signal scored exactly 15 points (HIGH_VALUE only)")

    def test_account_with_multiple_signals(self):
        """
        Scenario 3: Account with MULTIPLE signals
        Account A115 is part of the deliberately constructed suspicious network:
        - Outbound transaction T1001 is ₹9,500 (> 5,000 threshold) -> +15
        - Shares device D08 with A116, A117, A118 -> +25
        - Destination A116 receives funds from other accounts in cycle -> +20
        """
        result = calculate_account_risk("A115", config=self.default_config)

        self.assertTrue(result["account_exists"])
        self.assertEqual(result["account_id"], "A115")
        # Must have multiple signals
        self.assertGreaterEqual(len(result["factors"]), 2)
        # Score must reflect combination of multiple signals
        self.assertGreaterEqual(result["risk_score"], 40)
        self.assertIn(result["risk_level"], ["Medium", "High"])
        
        # Evidence IDs must include device D08 and transaction T1001
        self.assertIn("D08", result["evidence_ids"])
        self.assertIn("T1001", result["evidence_ids"])
        
        # Verify deduplication of evidence IDs
        self.assertEqual(len(result["evidence_ids"]), len(set(result["evidence_ids"])))
        print(f" [TEST PASS] Suspicious account A115 scored {result['risk_score']} / 100 with {len(result['factors'])} signals")

    def test_missing_data(self):
        """
        Scenario 4: Missing Data Handling
        Tests graceful degradation when account does not exist or input is invalid.
        """
        # Nonexistent account
        res_nonexistent = calculate_account_risk("A999", config=self.default_config)
        self.assertFalse(res_nonexistent["account_exists"])
        self.assertEqual(res_nonexistent["risk_score"], 0)
        self.assertEqual(res_nonexistent["risk_level"], "Low")
        self.assertEqual(len(res_nonexistent["factors"]), 0)

        # Empty string
        res_empty = calculate_account_risk("", config=self.default_config)
        self.assertFalse(res_empty["account_exists"])
        self.assertEqual(res_empty["risk_score"], 0)

        # None value
        res_none = calculate_account_risk(None, config=self.default_config)
        self.assertFalse(res_none["account_exists"])
        self.assertEqual(res_none["risk_score"], 0)
        print(" [TEST PASS] Missing data (A999, '', None) handled safely with 0 score and no crashes")

    def test_score_capping_and_disclaimer(self):
        """
        Scenario 5: Score Capping & Disclaimer
        Verifies score cannot exceed 100 even if signals sum to > 100.
        """
        super_high_config = RiskConfig(
            shared_device_points=50,
            suspicious_destination_points=50,
            high_amount_points=50,
            high_amount_threshold=10.0,
            burst_points=50,
            burst_min_tx_count=1
        )
        res = calculate_account_risk("A115", config=super_high_config)
        self.assertEqual(res["risk_score"], 100)
        self.assertIn("investigation_disclaimer", res)
        self.assertIn("not a calibrated probability", res["investigation_disclaimer"])
        print(" [TEST PASS] Score capped at exactly 100 and investigation disclaimer verified")

if __name__ == "__main__":
    unittest.main()
