from __future__ import annotations

import unittest

from orangecontrib.canvasagent.setup_status import check_codex_status
from tests.fakes import CompletedProcess


class SetupStatusTests(unittest.TestCase):
    def test_codex_missing_status(self):
        status = check_codex_status(which=lambda _: None)

        self.assertEqual(status.state, "missing")
        self.assertFalse(status.ready)

    def test_codex_logged_out_status(self):
        status = check_codex_status(
            which=lambda _: "codex",
            run_process=lambda *args, **kwargs: CompletedProcess(
                stdout="Not logged in",
                stderr="",
                returncode=1,
            ),
        )

        self.assertEqual(status.state, "signed_out")
        self.assertFalse(status.ready)

    def test_codex_ready_status(self):
        status = check_codex_status(
            which=lambda _: "codex",
            run_process=lambda *args, **kwargs: CompletedProcess(
                stdout="Logged in using ChatGPT",
                stderr="",
                returncode=0,
            ),
        )

        self.assertEqual(status.state, "ready")
        self.assertTrue(status.ready)


if __name__ == "__main__":
    unittest.main()

