from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch


class InstallerGuiTests(unittest.TestCase):
    def test_verify_diagnostics_start_hidden_with_matching_toggle_label(self):
        try:
            from installer.gui import CanvasAgentInstaller
        except Exception as exc:  # pragma: no cover - Tk unavailable on some hosts
            self.skipTest(f"Installer GUI could not be imported: {exc}")

        with patch.object(CanvasAgentInstaller, "_scan_installs", return_value=None):
            try:
                installer = CanvasAgentInstaller(wheel_path=Path("dist/orange3_canvasagent-0.1.3-py3-none-any.whl"))
            except Exception as exc:  # pragma: no cover - Tk display unavailable
                self.skipTest(f"Installer GUI could not be created: {exc}")

        try:
            installer.root.withdraw()

            self.assertFalse(installer.inline_diag_visible)
            self.assertEqual(installer.diag_toggle_text.get(), "Show diagnostics")
            self.assertFalse(installer.inline_diag_frame.winfo_manager())
        finally:
            installer.root.destroy()


if __name__ == "__main__":
    unittest.main()
