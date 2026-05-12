# Orange3 Canvas Agent Tutorial

This add-on creates a new Orange widget named **Canvas Agent**. It asks an agent backend for structured canvas actions, applies those actions to the live Orange workflow, and keeps an AI commit checkpoint so you can either keep or revert the changes.

## Install For Existing Local Development

From this project directory:

```powershell
python -m pip install -e .
```

Then launch Orange:

```powershell
python -m Orange.canvas --force-discovery
```

## Install For Official Orange Users

1. Download `CanvasAgentSetup.exe`.
2. Double-click it.
3. Select your Orange installation.
4. Click **Install**.
5. Let the installer open Orange.
6. Find **Canvas Agent** in the widget toolbox.

No coding or PowerShell is required for this path.

## Install For Experienced Coders

From PyPI:

```powershell
python -m pip install Orange3-CanvasAgent
python -m Orange.canvas --force-discovery
```

From GitHub:

```powershell
git clone https://github.com/pantagram1031/orange3-canvasagent.git
cd orange3-canvasagent
python -m pip install -e ".[dev]"
python -B -m unittest discover -v
python -m Orange.canvas --force-discovery
```

## Use The Widget

1. Open Orange.
2. Find the **Canvas Agent** category in the widget toolbox.
3. Drag **Canvas Agent** onto the canvas.
4. Open the **Setup** tab.
5. Click **Check Setup**.
6. Click **Sign in** if Codex is not already authenticated.
7. Click **Test Agent**.
8. Open the **Chat** tab.
9. Type a canvas request, for example:

```text
Add a File widget and a Data Table widget, then connect them.
```

10. Click **Send**.
11. Open the **Preview** tab.
12. Click **Keep Changes** to accept the AI commit, or **Revert AI Commit** to restore the previous canvas snapshot.

## The Four Tabs

- **Setup:** Codex readiness, Orange canvas readiness, sign-in flow, and first-run steps.
- **Chat:** Conversation transcript, command composer, and status log.
- **Preview:** Structured action preview, warnings, and keep/revert controls.
- **Diagnostics:** Codex and Orange discovery report for troubleshooting.

## How It Works

The widget never executes arbitrary Python returned by a model. Instead, the backend must return JSON matching the `CanvasPlan` schema:

```json
{
  "summary": "Create a simple data loading workflow",
  "actions": [
    {
      "type": "add_widget",
      "node_id": "file",
      "qualified_name": "Orange.widgets.data.owfile.OWFile",
      "title": "File",
      "position": [10, 20]
    },
    {
      "type": "add_widget",
      "node_id": "table",
      "qualified_name": "Orange.widgets.data.owtable.OWDataTable",
      "title": "Data Table",
      "position": [220, 20]
    },
    {
      "type": "connect",
      "source_node_id": "file",
      "sink_node_id": "table"
    }
  ],
  "warnings": []
}
```

Supported v1 actions are:

- `add_widget`
- `connect`
- `rename_node`
- `move_node`
- `annotate`

Before applying a plan, the add-on serializes the current Orange scheme into an in-memory checkpoint. If an action fails, the checkpoint is restored automatically. If the actions succeed, the UI keeps the checkpoint until you choose **Keep Changes** or **Revert AI Commit**.

## Verify The Add-On

Run:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -m unittest discover -v
```

Expected result:

```text
Ran 21 tests
OK
```

You can also verify Orange discovery:

```powershell
python -B -u -m Orange.canvas --help
```

If Orange starts and the tests pass, the package is installed correctly.

## Current Limits

- The implemented backend is **Codex CLI**.
- The LiteLLM/OpenAI/Anthropic/Ollama adapter is reserved for a later version.
- The widget changes the canvas through whitelisted structured actions only.
- Real model quality depends on whether Codex returns valid widget qualified names that exist in your Orange installation.
