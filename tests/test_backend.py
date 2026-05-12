from __future__ import annotations

import json
import unittest

from tests.fakes import CompletedProcess

from orangecontrib.canvasagent.backend import AuthStatus
from orangecontrib.canvasagent.codex_backend import CodexCliBackend
from orangecontrib.canvasagent.schema import PlanValidationError


class CodexCliBackendTests(unittest.TestCase):
    def test_reports_missing_cli_as_not_authenticated(self):
        backend = CodexCliBackend(which=lambda _: None)

        status = backend.is_authenticated()

        self.assertFalse(status.authenticated)
        self.assertIn("not found", status.message.lower())

    def test_parses_schema_conforming_codex_output(self):
        payload = {
            "summary": "Add a File widget",
            "actions": [
                {
                    "type": "add_widget",
                    "node_id": "file",
                    "qualified_name": "Orange.widgets.data.owfile.OWFile",
                    "position": [0, 0],
                }
            ],
            "warnings": [],
        }
        backend = CodexCliBackend(
            which=lambda _: "codex",
            run_process=lambda *args, **kwargs: CompletedProcess(
                stdout=json.dumps(payload), returncode=0
            ),
        )

        plan = backend.run("add file", {"nodes": []}, {"type": "object"})

        self.assertEqual(plan.summary, "Add a File widget")
        self.assertEqual(plan.actions[0].qualified_name, "Orange.widgets.data.owfile.OWFile")

    def test_rejects_non_json_codex_output(self):
        backend = CodexCliBackend(
            which=lambda _: "codex",
            run_process=lambda *args, **kwargs: CompletedProcess(
                stdout="I would add a widget.", returncode=0
            ),
        )

        with self.assertRaises(PlanValidationError):
            backend.run("add file", {"nodes": []}, {"type": "object"})


if __name__ == "__main__":
    unittest.main()

