from __future__ import annotations

import importlib
import pkgutil
import tomllib
import unittest
import importlib.util
import warnings
from pathlib import Path


class PackagingTests(unittest.TestCase):
    def test_project_version_matches_package_version(self):
        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        package = importlib.import_module("orangecontrib.canvasagent")

        self.assertEqual(pyproject["project"]["version"], "0.1.3")
        self.assertEqual(package.__version__, "0.1.3")

    def test_orange_widget_entry_point_is_declared(self):
        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        entry_points = pyproject["project"]["entry-points"]["orange.widgets"]

        self.assertEqual(entry_points["Canvas Agent"], "orangecontrib.canvasagent.widgets")

    def test_category_icon_points_to_packaged_parent_icon(self):
        category = importlib.import_module("orangecontrib.canvasagent.widgets")

        self.assertEqual(category.ICON, "../icons/agent.svg")
        self.assertTrue(pkgutil.get_data("orangecontrib.canvasagent.widgets", category.ICON))

    def test_litellm_optional_dependency_excludes_compromised_versions(self):
        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        llm_dependencies = pyproject["project"]["optional-dependencies"]["llm"]

        self.assertIn("litellm!=1.82.7,!=1.82.8,>=1.83.14,<1.84", llm_dependencies)

    @unittest.skipUnless(
        importlib.util.find_spec("orangecanvas") is not None,
        "Orange Canvas is not installed",
    )
    def test_orange_discovery_registers_canvas_agent_widget(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from importlib.metadata import entry_points
            from orangecanvas.registry import WidgetRegistry
            from orangecanvas.registry.discovery import WidgetDiscovery

            registry = WidgetRegistry()
            WidgetDiscovery(registry).run(entry_points(group="orange.widgets"))

        matches = []
        for category in registry.categories():
            for widget in registry.widgets(category):
                if widget.name == "Canvas Agent":
                    matches.append((category.name, widget.qualified_name))

        self.assertEqual(
            matches,
            [
                (
                    "Canvas Agent",
                    "orangecontrib.canvasagent.widgets.OWCanvasAgent.OWCanvasAgent",
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
