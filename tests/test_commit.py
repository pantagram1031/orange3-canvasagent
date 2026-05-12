from __future__ import annotations

import unittest

from tests.fakes import FakeScheme

from orangecontrib.canvasagent.commit import AiCommit
from orangecontrib.canvasagent.schema import CanvasPlan


class AiCommitTests(unittest.TestCase):
    def test_revert_loads_before_snapshot(self):
        scheme = FakeScheme()
        before_snapshot = b"File,Data Table"
        plan = CanvasPlan.from_dict(
            {"summary": "No-op", "actions": [], "warnings": []}
        )
        commit = AiCommit.create(
            prompt="add file",
            backend="Codex CLI",
            model="codex/default",
            before_snapshot=before_snapshot,
            plan=plan,
            messages=["No changes"],
        )

        commit.revert(scheme)

        self.assertEqual(scheme.loaded_snapshot, before_snapshot)


if __name__ == "__main__":
    unittest.main()

