# Orange3 Canvas Agent

`Orange3-CanvasAgent` adds an experimental Orange widget that can ask an agent
backend for structured canvas actions, apply them to the live scheme, and keep a
reversible checkpoint until the user accepts or reverts the AI commit.

The first backend targets the installed `codex` CLI and its ChatGPT/Codex login
flow. Direct API-key routing through LiteLLM is reserved for a later adapter.

## Install For Official Orange Users

Download `CanvasAgentSetup.exe` from the project release page, run it, choose
your Orange installation if it is not detected automatically, and click
**Install**. The installer places the add-on into Orange's Python environment
and opens Orange with widget discovery enabled.

After Orange opens, look for the **Canvas Agent** category and drag the widget
onto your workflow.

## Install For Coders

From PyPI:

```powershell
python -m pip install Orange3-CanvasAgent
python -m Orange.canvas --force-discovery
```

From a local checkout:

```powershell
git clone https://github.com/pantagram1031/orange3-canvasagent.git
cd orange3-canvasagent
python -m pip install -e ".[dev]"
python -B -m unittest discover -v
python -m Orange.canvas --force-discovery
```

## Build The Installer

```powershell
.\scripts\build-installer.ps1
```

The generated installer is written to `dist\CanvasAgentSetup.exe`.

## What The Widget Does

- Shows a setup tab for Codex login and Orange readiness.
- Provides a chat tab for canvas requests.
- Shows a preview tab with the structured AI commit.
- Shows diagnostics for troubleshooting.
- Applies only whitelisted canvas actions, never arbitrary model-generated Python.
- Lets you keep or revert each AI commit.
