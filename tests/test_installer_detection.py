from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from installer.core import (
    discover_orange_installs,
    find_orange_python,
    validate_orange_folder,
)


class InstallerDetectionTests(unittest.TestCase):
    def test_finds_orange_install_from_registry_shortcut_and_common_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry_root = root / "Registry Orange"
            shortcut_root = root / "Shortcut Orange"
            common_root = root / "Common Orange"
            for folder in (registry_root, shortcut_root, common_root):
                folder.mkdir()
                (folder / "python.exe").write_text("", encoding="utf-8")

            installs = discover_orange_installs(
                registry_entries=[{"display_name": "Orange 3.40", "install_location": str(registry_root)}],
                shortcut_targets=[str(shortcut_root / "Orange Canvas.exe")],
                common_roots=[common_root],
            )

            self.assertEqual(
                [(install.source, install.root) for install in installs],
                [
                    ("registry", registry_root.resolve()),
                    ("shortcut", shortcut_root.resolve()),
                    ("common", common_root.resolve()),
                ],
            )

    def test_finds_python_under_official_orange_folder_layouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            embedded = root / "lib" / "python.exe"
            embedded.parent.mkdir(parents=True)
            embedded.write_text("", encoding="utf-8")

            self.assertEqual(find_orange_python(root), embedded)

    def test_rejects_folder_without_usable_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = validate_orange_folder(Path(tmp))

            self.assertFalse(result.ok)
            self.assertIn("python.exe", result.message)


if __name__ == "__main__":
    unittest.main()
