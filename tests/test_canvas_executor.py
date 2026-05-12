from __future__ import annotations

import unittest

from tests.fakes import FakeScheme, fake_resolver

from orangecontrib.canvasagent.canvas import CanvasActionExecutor, CanvasExecutionError
from orangecontrib.canvasagent.schema import CanvasPlan


class CanvasActionExecutorTests(unittest.TestCase):
    def test_applies_add_connect_rename_move_and_annotate_actions(self):
        scheme = FakeScheme()
        executor = CanvasActionExecutor(scheme, resolve_widget_description=fake_resolver())
        plan = CanvasPlan.from_dict(
            {
                "summary": "Create workflow",
                "actions": [
                    {
                        "type": "add_widget",
                        "node_id": "file",
                        "qualified_name": "Orange.widgets.data.owfile.OWFile",
                        "title": "File",
                        "position": [10, 20],
                    },
                    {
                        "type": "add_widget",
                        "node_id": "table",
                        "qualified_name": "Orange.widgets.data.owtable.OWDataTable",
                        "title": "Data Table",
                        "position": [200, 20],
                    },
                    {"type": "connect", "source_node_id": "file", "sink_node_id": "table"},
                    {"type": "rename_node", "node_id": "table", "title": "Preview"},
                    {"type": "move_node", "node_id": "file", "position": [25, 35]},
                    {"type": "annotate", "text": "AI created", "bounds": [0, 0, 100, 40]},
                ],
                "warnings": [],
            }
        )

        result = executor.apply(plan)

        self.assertEqual(len(scheme.nodes), 2)
        self.assertEqual(len(scheme.links), 1)
        self.assertEqual(scheme.nodes[0].position, (25.0, 35.0))
        self.assertEqual(scheme.nodes[1].title, "Preview")
        self.assertEqual(scheme.annotations[0].text, "AI created")
        self.assertIn("Connected file to table", result.messages)

    def test_invalid_connection_fails_cleanly(self):
        scheme = FakeScheme()
        resolver = fake_resolver()
        executor = CanvasActionExecutor(scheme, resolve_widget_description=resolver)
        plan = CanvasPlan.from_dict(
            {
                "summary": "Bad connection",
                "actions": [
                    {
                        "type": "add_widget",
                        "node_id": "file",
                        "qualified_name": "Orange.widgets.data.owfile.OWFile",
                    },
                    {"type": "connect", "source_node_id": "file", "sink_node_id": "missing"},
                ],
                "warnings": [],
            }
        )

        with self.assertRaisesRegex(CanvasExecutionError, "Unknown sink node"):
            executor.apply(plan)


if __name__ == "__main__":
    unittest.main()

