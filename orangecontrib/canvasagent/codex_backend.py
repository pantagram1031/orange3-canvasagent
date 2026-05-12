from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from .backend import AuthStatus, ModelRef
from .schema import CanvasPlan, PlanValidationError


ProcessRunner = Callable[..., subprocess.CompletedProcess]


class CodexCliBackend:
    name = "Codex CLI"

    def __init__(
        self,
        *,
        which: Callable[[str], str | None] = shutil.which,
        run_process: ProcessRunner = subprocess.run,
        cwd: str | None = None,
        model: str = "codex/default",
    ):
        self._which = which
        self._run_process = run_process
        self._cwd = cwd
        self._model = model

    def list_models(self) -> list[ModelRef]:
        return [ModelRef(id=self._model, label="Codex default")]

    def _codex_path(self) -> str | None:
        return self._which("codex")

    def is_authenticated(self) -> AuthStatus:
        codex = self._codex_path()
        if not codex:
            return AuthStatus(False, "Codex CLI was not found on PATH.")
        try:
            result = self._run_process(
                [codex, "login", "status"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self._cwd,
            )
        except Exception as exc:  # pragma: no cover - defensive around user CLI installs
            return AuthStatus(False, f"Could not check Codex login status: {exc}")
        output = f"{getattr(result, 'stdout', '')}\n{getattr(result, 'stderr', '')}".strip()
        if getattr(result, "returncode", 1) == 0:
            return AuthStatus(True, output or "Codex CLI is signed in.")
        return AuthStatus(False, output or "Codex CLI is not signed in.")

    def login(self) -> AuthStatus:
        codex = self._codex_path()
        if not codex:
            return AuthStatus(False, "Codex CLI was not found on PATH.")
        try:
            result = self._run_process([codex, "login"], cwd=self._cwd)
        except Exception as exc:  # pragma: no cover - launches external interactive flow
            return AuthStatus(False, f"Could not launch Codex login: {exc}")
        if getattr(result, "returncode", 1) == 0:
            return AuthStatus(True, "Codex login completed.")
        return AuthStatus(False, "Codex login did not complete.")

    def run(self, prompt: str, canvas_state: dict, output_schema: dict) -> CanvasPlan:
        codex = self._codex_path()
        if not codex:
            raise RuntimeError("Codex CLI was not found on PATH.")

        with tempfile.TemporaryDirectory(prefix="orange-canvasagent-") as tmpdir:
            schema_path = Path(tmpdir) / "canvas_plan.schema.json"
            final_path = Path(tmpdir) / "codex-final.json"
            schema_path.write_text(json.dumps(output_schema), encoding="utf-8")
            process_prompt = self._format_prompt(prompt, canvas_state)
            result = self._run_process(
                [
                    codex,
                    "exec",
                    "--skip-git-repo-check",
                    "--output-schema",
                    str(schema_path),
                    "-o",
                    str(final_path),
                    "-",
                ],
                input=process_prompt,
                capture_output=True,
                text=True,
                timeout=180,
                cwd=self._cwd,
            )
            if getattr(result, "returncode", 1) != 0:
                stderr = getattr(result, "stderr", "") or "Codex execution failed."
                raise RuntimeError(stderr.strip())
            raw = final_path.read_text(encoding="utf-8") if final_path.exists() else ""
            if not raw.strip():
                raw = getattr(result, "stdout", "")
            return self._parse_plan(raw)

    def _parse_plan(self, raw: str) -> CanvasPlan:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PlanValidationError("Codex output was not valid JSON") from exc
        return CanvasPlan.from_dict(data)

    def _format_prompt(self, prompt: str, canvas_state: dict) -> str:
        return (
            "You are controlling an Orange Data Mining canvas. Return ONLY JSON "
            "matching the provided output schema. Do not include Markdown or Python. "
            "Use only supported canvas actions.\n\n"
            f"Current canvas state:\n{json.dumps(canvas_state, indent=2)}\n\n"
            f"User request:\n{prompt}\n"
        )

