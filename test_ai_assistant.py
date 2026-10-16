"""
Unit Tests for FraudLens AI Investigation Assistant (test_ai_assistant.py)

Tests cover:
1. API failure fallback (Deterministic summary when API key is missing or failed)
2. Grounding & Credential Safety (Ensures database passwords/host are NEVER leaked to LLM)
3. Insufficient evidence handling (Account does not exist or unrecorded forensics)
4. Normal grounded response generation with mock provider
"""

import unittest
from unittest.mock import patch, MagicMock
from ai_assistant import (
    compile_evidence_dossier,
    format_dossier_text,
    generate_deterministic_summary,
    query_llm_assistant
)

class TestAIAssistant(unittest.TestCase):

    def test_api_failure_fallback(self):
        """
        Scenario 1: API Key missing or failed -> Deterministic Evidence Fallback
        Ensures system degrades gracefully to factual FalkorDB summary.
        """
        result = query_llm_assistant(
            account_id="A115",
            question="Why was this account flagged for review?",
            api_key_override=None
        )

        self.assertTrue(result["is_fallback"])
        self.assertEqual(result["provider"], "Deterministic Evidence Engine (FalkorDB)")
        # Must cite actual evidence IDs in the fallback summary
        self.assertIn("A115", result["answer"])
        self.assertIn("D08", result["evidence_ids"])
        print("\n [TEST PASS] Fallback mode active: Returned deterministic evidence summary citing IDs:", result["evidence_ids"])

    def test_credential_leak_safety(self):
        """
        Scenario 2: Security & Privacy Guardrail
        Verifies that database credentials, passwords, and host connection strings
        are NEVER included in the evidence dossier passed to the LLM.
        """
        dossier = compile_evidence_dossier("A115")
        dossier_text = format_dossier_text(dossier)

        # Check for sensitive patterns
        self.assertNotIn("FALKORDB_PASSWORD", dossier_text)
        self.assertNotIn("Divya@123", dossier_text)  # Ensure no password leakage
        self.assertNotIn("ap-south-1.aws", dossier_text)
        self.assertNotIn("49500", dossier_text)

        # Ensure only functional investigation entities are present
        self.assertIn("A115", dossier_text)
        self.assertIn("D08", dossier_text)
        print(" [TEST PASS] Security verification: Zero database credentials or passwords exposed in dossier.")

    def test_insufficient_evidence_handling(self):
        """
        Scenario 3: Insufficient Evidence Handling
        When an unrecorded account or missing entity is queried,
        the system must explicitly state that evidence is insufficient.
        """
        dossier = compile_evidence_dossier("A999")  # Nonexistent account
        dossier_text = format_dossier_text(dossier)
        
        self.assertFalse(dossier["account_exists"])
        self.assertIn("was not found in graph database", dossier_text)

        fallback = generate_deterministic_summary(dossier, "What is the crypto balance?")
        self.assertIn("A999", fallback)
        print(" [TEST PASS] Insufficient evidence handled explicitly: Nonexistent entity flagged without errors.")

    @patch("requests.post")
    def test_normal_llm_response_flow(self, mock_post):
        """
        Scenario 4: Normal LLM Response Flow
        Mocks a valid LLM API response to verify prompt compilation,
        parsing, and citation grounding.
        """
        # Mock Gemini 200 OK response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Account A115 is prioritized for investigation due to outbound transfer T1001 (₹9,500.00) and shared device D08 with accounts A116, A117, and A118."
                            }
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        result = query_llm_assistant(
            account_id="A115",
            question="Summarize the primary investigation signals.",
            api_key_override="test_dummy_key_12345"
        )

        self.assertFalse(result["is_fallback"])
        self.assertEqual(result["status"], "success")
        self.assertIn("Google Gemini", result["provider"])
        self.assertIn("T1001", result["answer"])
        self.assertIn("D08", result["answer"])
        print(" [TEST PASS] Normal LLM response verified: Cites actual transaction T1001 and device D08.")

if __name__ == "__main__":
    unittest.main()
