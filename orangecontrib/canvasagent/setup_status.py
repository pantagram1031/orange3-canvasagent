from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Callable


@dataclass(frozen=True)
class SetupStatus:
    name: str
    state: str
    ready: bool
    message: str
    details: str = ""


def check_codex_status(
    *,
    which: Callable[[str], str | None] = shutil.which,
    run_process: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> SetupStatus:
    codex = which("codex")
    if not codex:
        return SetupStatus(
            name="Codex CLI",
            state="missing",
            ready=False,
            message="Codex CLI was not found on PATH.",
        )
    try:
        result = run_process(
            [codex, "login", "status"],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except Exception as exc:  # pragma: no cover - external CLI defensive path
        return SetupStatus(
            name="Codex CLI",
            state="error",
            ready=False,
            message=f"Could not check Codex login status: {exc}",
        )

    output = f"{getattr(result, 'stdout', '')}\n{getattr(result, 'stderr', '')}".strip()
    if getattr(result, "returncode", 1) == 0:
        return SetupStatus(
            name="Codex CLI",
            state="ready",
            ready=True,
            message=output or "Codex CLI is signed in.",
        )
    return SetupStatus(
        name="Codex CLI",
        state="signed_out",
        ready=False,
        message=output or "Codex CLI is not signed in.",
    )


def check_orange_widget_discovery() -> SetupStatus:
    matches = [
        ep.value
        for ep in entry_points(group="orange.widgets")
        if ep.name == "Canvas Agent"
    ]
    if matches:
        return SetupStatus(
            name="Orange Widget Discovery",
            state="ready",
            ready=True,
            message="Canvas Agent entry point is registered.",
            details=matches[0],
        )
    return SetupStatus(
        name="Orange Widget Discovery",
        state="missing",
        ready=False,
        message="Canvas Agent entry point is not registered.",
    )


def diagnostic_report() -> str:
    codex = check_codex_status()
    discovery = check_orange_widget_discovery()
    return "\n".join(
        [
            "Orange Canvas Agent diagnostics",
            f"{codex.name}: {codex.state} - {codex.message}",
            f"{discovery.name}: {discovery.state} - {discovery.message}",
            f"Entry point: {discovery.details or 'not available'}",
        ]
    )

