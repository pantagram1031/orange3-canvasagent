from __future__ import annotations

import os
import unittest
import warnings


class WidgetImportTests(unittest.TestCase):
    def test_widget_module_imports_without_orange_installed(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from orangecontrib.canvasagent.widgets import OWCanvasAgent

        self.assertEqual(OWCanvasAgent.name, "Canvas Agent")

    def test_widget_instantiates_without_orange_installed_for_smoke_tests(self):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from orangecontrib.canvasagent.widgets.OWCanvasAgent import ORANGE_AVAILABLE, OWCanvasAgent

        app = None
        if ORANGE_AVAILABLE:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from AnyQt.QtWidgets import QApplication

            app = QApplication.instance() or QApplication([])

        widget = OWCanvasAgent()

        self.assertIsNone(widget.pending_commit)
        if ORANGE_AVAILABLE:
            widget.onDeleteWidget()
        if app is not None:
            app.quit()


if __name__ == "__main__":
    unittest.main()
