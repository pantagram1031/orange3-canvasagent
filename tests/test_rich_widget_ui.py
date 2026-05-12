from __future__ import annotations

import os
import unittest
import warnings


class RichWidgetUiTests(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from AnyQt.QtWidgets import QApplication

        self.app = QApplication.instance() or QApplication([])

    def test_widget_has_codex_like_tabs_and_onboarding_steps(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from orangecontrib.canvasagent.widgets import OWCanvasAgent

        widget = OWCanvasAgent()
        try:
            tab_names = [widget.tabs.tabText(index) for index in range(widget.tabs.count())]

            self.assertEqual(tab_names, ["Setup", "Chat", "Preview", "Diagnostics"])
            self.assertEqual(
                [label.text() for label in widget.setup_step_labels],
                ["1. Check Codex", "2. Sign in", "3. Test agent", "4. Start"],
            )
            self.assertFalse(widget.send_button.isEnabled())
        finally:
            widget.onDeleteWidget()


if __name__ == "__main__":
    unittest.main()

