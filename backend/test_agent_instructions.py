"""Unit tests for persisted admin instructions and system-prompt injection."""

import os
import tempfile
import unittest

from backend.ai_articulator import AIArticulator


class AgentInstructionsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.articulator = AIArticulator()
        self.articulator.instructions_file = os.path.join(self.temp_dir.name, "agent_instructions.txt")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_saved_instructions_are_injected_into_system_prompt(self):
        instruction = "Begin every response with 'Hello Mate'."
        self.articulator.set_agent_instructions(instruction)
        prompt = self.articulator._build_system_prompt(
            {"title": "Test", "doc_id": "TEST-1"},
            {"warnings": [], "resolution_steps": []},
            [],
        )
        self.assertIn(instruction, prompt)
        self.assertIn("ADMIN AGENT INSTRUCTIONS", prompt)
        self.assertEqual(self.articulator.get_agent_instructions(), instruction + "\n")

    def test_empty_instructions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "cannot be empty"):
            self.articulator.set_agent_instructions("   ")

    def test_oversized_instructions_are_rejected(self):
        oversized = "x" * (self.articulator.MAX_AGENT_INSTRUCTIONS_LENGTH + 1)
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            self.articulator.set_agent_instructions(oversized)


if __name__ == "__main__":
    unittest.main()
