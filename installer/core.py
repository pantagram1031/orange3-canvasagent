from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


@dataclass(frozen=True)
class DetectionResult:
    ok: bool
    message: str
    python_executable: Path | None = None


@dataclass(frozen=True)
class OrangeInstall:
    root: Path
    python_executable: Path
    source: str
    label: str


PYTHON_CANDIDATES = (
    "python.exe",
    "lib/python.exe",
    "Scripts/python.exe",
    "venv/Scripts/python.exe",
    "python/python.exe",
    "Orange/python.exe",
)

SMOKE_CHECK_SCRIPT = textwrap.dedent(
    """
    import importlib
    import json
    import pkgutil
    import sys
    import warnings
    from importlib.metadata import entry_points

    from orangecanvas.registry import WidgetRegistry
    from orangecanvas.registry.discovery import WidgetDiscovery

    CATEGORY_NAME = "Canvas Agent"
    WIDGET_NAME = "Canvas Agent"
    CATEGORY_MODULE = "orangecontrib.canvasagent.widgets"
    WIDGET_MODULE = "orangecontrib.canvasagent.widgets.OWCanvasAgent"

    def fail(message, diagnostics):
        payload = {"message": message, **diagnostics}
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
        raise SystemExit(1)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        category_module = importlib.import_module(CATEGORY_MODULE)
        widget_module = importlib.import_module(WIDGET_MODULE)
        registry = WidgetRegistry()
        WidgetDiscovery(registry).run(entry_points(group="orange.widgets"))

    categories = list(registry.categories())
    diagnostics = {
        "categories": [getattr(category, "name", "<unnamed>") for category in categories],
        "entry_points": sorted(ep.name for ep in entry_points(group="orange.widgets")),
    }

    category = next((item for item in categories if getattr(item, "name", None) == CATEGORY_NAME), None)
    if category is None:
        fail("Canvas Agent category missing after WidgetDiscovery.", diagnostics)

    category_icon = getattr(category_module, "ICON", "")
    diagnostics["category_icon"] = category_icon
    if not category_icon or not pkgutil.get_data(CATEGORY_MODULE, category_icon):
        fail("Canvas Agent category icon resource could not be loaded.", diagnostics)

    widgets = list(registry.widgets(category))
    diagnostics["category_widgets"] = [getattr(widget, "name", "<unnamed>") for widget in widgets]

    widget = next((item for item in widgets if getattr(item, "name", None) == WIDGET_NAME), None)
    if widget is None:
        fail("Canvas Agent widget missing from Canvas Agent category.", diagnostics)

    diagnostics["qualified_name"] = getattr(widget, "qualified_name", "")
    widget_icon = getattr(widget_module, "ICON", "")
    diagnostics["widget_icon"] = widget_icon
    if not widget_icon or not pkgutil.get_data(CATEGORY_MODULE, widget_icon):
        fail("Canvas Agent widget icon resource could not be loaded.", diagnostics)

    print(
        json.dumps(
            {
                "message": "Canvas Agent category, widget, and icon discovery passed.",
                **diagnostics,
            },
            sort_keys=True,
        )
    )
    """
).strip()


def subprocess_creationflags() -> int:
    if sys.platform == "win32":
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return 0


def find_orange_python(folder: str | Path) -> Path | None:
    root = Path(folder)
    for candidate in PYTHON_CANDIDATES:
        executable = root / Path(candidate)
        if executable.exists():
            return executable
    return None


def validate_orange_folder(
    folder: str | Path,
    *,
    runner=subprocess.run,
    require_import: bool = False,
) -> DetectionResult:
    root = Path(folder)
    python_executable = find_orange_python(root)
    if python_executable is None:
        return DetectionResult(False, f"No python.exe was found inside {root}.")
    if require_import:
        result = runner(
            [
                str(python_executable),
                "-c",
                "import Orange, AnyQt; print(Orange.__version__)",
            ],
            capture_output=True,
            text=True,
            timeout=60,
            creationflags=subprocess_creationflags(),
        )
        if getattr(result, "returncode", 1) != 0:
            message = (getattr(result, "stderr", "") or getattr(result, "stdout", "")).strip()
            return DetectionResult(False, message or "Orange import check failed.", python_executable)
    return DetectionResult(True, "Orange Python was found.", python_executable)


def discover_orange_installs(
    *,
    registry_entries: Sequence[dict] | None = None,
    shortcut_targets: Sequence[str | Path] | None = None,
    common_roots: Sequence[str | Path] | None = None,
) -> list[OrangeInstall]:
    installs: list[OrangeInstall] = []
    seen: set[Path] = set()

    for entry in registry_entries if registry_entries is not None else iter_registry_entries():
        name = str(entry.get("display_name", ""))
        location = entry.get("install_location") or entry.get("display_icon")
        if "orange" not in name.lower() or not location:
            continue
        root = _normalize_install_root(Path(str(location)))
        _append_install(installs, seen, root, "registry", name or "Orange")

    for target in shortcut_targets if shortcut_targets is not None else iter_start_menu_shortcuts():
        root = _normalize_install_root(Path(target).parent)
        _append_install(installs, seen, root, "shortcut", "Orange shortcut")

    roots = list(common_roots) if common_roots is not None else default_common_roots()
    for root in roots:
        path = Path(root)
        candidates = [path]
        if path.exists() and path.is_dir():
            candidates.extend(child for child in path.iterdir() if child.is_dir() and "orange" in child.name.lower())
        for candidate in candidates:
            _append_install(installs, seen, candidate, "common", "Orange")

    return installs


def iter_registry_entries() -> Iterable[dict]:
    if sys.platform != "win32":
        return []
    try:
        import winreg
    except ImportError:  # pragma: no cover - Windows-only fallback
        return []

    hives = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    entries: list[dict] = []
    for hive, path in hives:
        try:
            with winreg.OpenKey(hive, path) as key:
                for index in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            entries.append(
                                {
                                    "display_name": _registry_value(winreg, subkey, "DisplayName"),
                                    "install_location": _registry_value(winreg, subkey, "InstallLocation"),
                                    "display_icon": _registry_value(winreg, subkey, "DisplayIcon"),
                                }
                            )
                    except OSError:
                        continue
        except OSError:
            continue
    return entries


def iter_start_menu_shortcuts() -> list[Path]:
    start_menu_roots = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("ProgramData", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]
    shortcuts: list[Path] = []
    for root in start_menu_roots:
        if root.exists():
            for shortcut in root.rglob("*Orange*.lnk"):
                shortcuts.append(resolve_windows_shortcut(shortcut) or shortcut)
    return shortcuts


def resolve_windows_shortcut(shortcut: str | Path) -> Path | None:
    if sys.platform != "win32":
        return None
    script = (
        "$shell = New-Object -ComObject WScript.Shell; "
        "$shortcut = $shell.CreateShortcut($args[0]); "
        "Write-Output $shortcut.TargetPath"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script, str(shortcut)],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess_creationflags(),
        )
    except Exception:
        return None
    if getattr(result, "returncode", 1) != 0:
        return None
    target = getattr(result, "stdout", "").strip()
    return Path(target) if target else None


def default_common_roots() -> list[Path]:
    roots = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LocalAppData"):
        value = os.environ.get(env_name)
        if value:
            roots.append(Path(value) / "Orange")
            roots.append(Path(value) / "Orange3")
    return roots


def install_wheel(
    python_executable: str | Path,
    wheel_path: str | Path,
    *,
    runner=subprocess.run,
) -> DetectionResult:
    result = runner(
        [
            str(python_executable),
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--force-reinstall",
            "--no-deps",
            str(wheel_path),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        creationflags=subprocess_creationflags(),
    )
    if getattr(result, "returncode", 1) != 0:
        return DetectionResult(False, (getattr(result, "stderr", "") or "Wheel install failed.").strip())
    return DetectionResult(True, "Canvas Agent was installed.", Path(python_executable))


def smoke_check(python_executable: str | Path, *, runner=subprocess.run) -> DetectionResult:
    result = runner(
        [
            str(python_executable),
            "-c",
            SMOKE_CHECK_SCRIPT,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        creationflags=subprocess_creationflags(),
    )
    if getattr(result, "returncode", 1) != 0:
        message = (getattr(result, "stderr", "") or getattr(result, "stdout", "") or "Smoke check failed.").strip()
        return DetectionResult(False, message, Path(python_executable))
    details = getattr(result, "stdout", "").strip()
    message = "Canvas Agent category, widget, and icon discovery passed."
    if details:
        message = f"{message} {details}"
    return DetectionResult(True, message, Path(python_executable))


def _append_install(
    installs: list[OrangeInstall],
    seen: set[Path],
    root: Path,
    source: str,
    label: str,
) -> None:
    result = validate_orange_folder(root)
    if not result.ok or result.python_executable is None:
        return
    resolved = root.resolve()
    if resolved in seen:
        return
    seen.add(resolved)
    installs.append(
        OrangeInstall(
            root=resolved,
            python_executable=result.python_executable.resolve(),
            source=source,
            label=label,
        )
    )


def _normalize_install_root(path: Path) -> Path:
    if path.suffix.lower() == ".exe":
        return path.parent
    return path


def _registry_value(winreg, key, name: str) -> str:
    try:
        return str(winreg.QueryValueEx(key, name)[0])
    except OSError:
        return ""
