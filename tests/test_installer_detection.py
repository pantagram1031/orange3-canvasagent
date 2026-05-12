from __future__ import annotations

import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from installer.core import (
    discover_orange_installs,
    find_orange_python,
    install_wheel,
    smoke_check,
    subprocess_creationflags,
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

    def test_validate_orange_folder_uses_hidden_subprocess_on_windows(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout="3.40.0", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            python_executable = root / "python.exe"
            python_executable.write_text("", encoding="utf-8")

            with patch("installer.core.sys.platform", "win32"):
                result = validate_orange_folder(root, runner=runner, require_import=True)

        self.assertTrue(result.ok)
        self.assertEqual(calls[0][1]["creationflags"], subprocess_creationflags())

    def test_install_wheel_forces_reinstall_upgrade_and_hidden_subprocess_on_windows(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        with patch("installer.core.sys.platform", "win32"):
            result = install_wheel("python.exe", "dist/pkg.whl", runner=runner)

        self.assertTrue(result.ok)
        self.assertEqual(
            calls[0][0][0],
            [
                "python.exe",
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--force-reinstall",
                "--no-deps",
                "dist/pkg.whl",
            ],
        )
        self.assertEqual(calls[0][1]["creationflags"], subprocess_creationflags())

    def test_smoke_check_runs_full_discovery_and_reports_missing_category(self):
        calls = []

        def runner(*args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=1, stdout="", stderr="missing category")

        with patch("installer.core.sys.platform", "win32"):
            result = smoke_check("python.exe", runner=runner)

        self.assertFalse(result.ok)
        self.assertIn("missing category", result.message)
        self.assertIn("WidgetDiscovery", calls[0][0][0][2])
        self.assertIn("Canvas Agent category", calls[0][0][0][2])
        self.assertIn("pkgutil.get_data", calls[0][0][0][2])
        self.assertEqual(calls[0][1]["creationflags"], subprocess_creationflags())

    def test_smoke_check_returns_success_message_when_discovery_passes(self):
        def runner(*args, **kwargs):
            return SimpleNamespace(returncode=0, stdout="smoke ok", stderr="")

        result = smoke_check("python.exe", runner=runner)

        self.assertTrue(result.ok)
        self.assertIn("Canvas Agent category", result.message)

    def test_resolve_windows_shortcut_uses_hidden_subprocess_on_windows(self):
        with patch("installer.core.sys.platform", "win32"), patch(
            "installer.core.subprocess.run",
            return_value=SimpleNamespace(returncode=0, stdout="C:\\Orange\\Orange.exe\n", stderr=""),
        ) as run_mock:
            from installer.core import resolve_windows_shortcut

            target = resolve_windows_shortcut("C:\\Users\\User\\Desktop\\Orange.lnk")

        self.assertEqual(target, Path("C:\\Orange\\Orange.exe"))
        self.assertEqual(run_mock.call_args.kwargs["creationflags"], subprocess_creationflags())


if __name__ == "__main__":
    unittest.main()
