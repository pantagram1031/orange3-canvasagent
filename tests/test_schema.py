from __future__ import annotations

import unittest

from orangecontrib.canvasagent.schema import CanvasPlan, PlanValidationError


class CanvasPlanSchemaTests(unittest.TestCase):
    def test_accepts_valid_canvas_plan(self):
        plan = CanvasPlan.from_dict(
            {
                "summary": "Create a simple file workflow",
                "actions": [
                    {
                        "type": "add_widget",
                        "node_id": "file",
                        "qualified_name": "Orange.widgets.data.owfile.OWFile",
                        "title": "File",
                        "position": [10, 20],
                    },
                    {
                        "type": "connect",
                        "source_node_id": "file",
                        "sink_node_id": "table",
                    },
                ],
                "warnings": ["Requires user to choose a file"],
            }
        )

        self.assertEqual(plan.summary, "Create a simple file workflow")
        self.assertEqual(plan.actions[0].type, "add_widget")
        self.assertEqual(plan.actions[0].position, (10.0, 20.0))
        self.assertEqual(plan.warnings, ["Requires user to choose a file"])

    def test_rejects_unknown_action_type(self):
        with self.assertRaisesRegex(PlanValidationError, "Unsupported action type"):
            CanvasPlan.from_dict(
                {
                    "summary": "Bad plan",
                    "actions": [{"type": "run_python", "code": "print('nope')"}],
                    "warnings": [],
                }
            )

    def test_rejects_missing_required_action_field(self):
        with self.assertRaisesRegex(PlanValidationError, "qualified_name"):
            CanvasPlan.from_dict(
                {
                    "summary": "Incomplete plan",
                    "actions": [{"type": "add_widget", "node_id": "file"}],
                    "warnings": [],
                }
            )


if __name__ == "__main__":
    unittest.main()

