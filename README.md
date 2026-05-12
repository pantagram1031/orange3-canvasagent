# Orange3 Canvas Agent

`Orange3-CanvasAgent` adds a new Orange widget named **Canvas Agent**. It lets
you describe a workflow in plain language, previews the agent's structured
canvas changes, and keeps those changes reversible until you choose
**Keep Changes** or **Revert AI Commit**.

Version `0.1.3` focuses on install polish: a simpler Windows installer flow,
clearer first-run guidance, and better repair steps when the widget is installed
but not visible yet.

## Release Links

- GitHub releases: <https://github.com/pantagram1031/orange3-canvasagent/releases>
- PyPI package: <https://pypi.org/project/Orange3-CanvasAgent/>
- Issue tracker: <https://github.com/pantagram1031/orange3-canvasagent/issues>

## Install For Beginners On Windows

This is the recommended path if you already use the normal Orange desktop app
and do not want to open a terminal.

1. Open the GitHub releases page.
2. Download `CanvasAgentSetup.exe` from the latest release.
3. Double-click the installer.
4. If Windows shows a security warning, verify the file came from the GitHub
   release page above, then continue only if you trust it.
5. In the installer window, wait for Orange detection to finish.
6. Select your Orange installation from the list.
7. If nothing is listed, click **Choose Folder...** and point to your Orange
   install folder.
8. Click **Install / Repair**.
9. Continue to **Verify** and run the smoke check.
10. On **Finish**, confirm the success message and click **Open Orange**.
11. When Orange launches, look in the widget toolbox for the
    **Canvas Agent** category.
12. Drag **Canvas Agent** onto the canvas.

If the widget still does not appear, jump to
[Troubleshooting](#troubleshooting).

## Install For Coders

### From PyPI

```powershell
python -m pip install Orange3-CanvasAgent
python -m Orange.canvas --force-discovery
```

### From Source

```powershell
git clone https://github.com/pantagram1031/orange3-canvasagent.git
cd orange3-canvasagent
python -m pip install -e ".[dev]"
python -B -m unittest discover -v
python -m Orange.canvas --force-discovery
```

## First Run

1. Open Orange.
2. In the left widget toolbox, find the **Canvas Agent** category.
3. Drag **Canvas Agent** onto the canvas.
4. Open the **Setup** tab.
5. Click **Check Setup**.
6. If needed, use **Sign in** to authenticate the installed `codex` CLI.
7. Click **Test Agent**.
8. Open the **Chat** tab and send a request such as:

```text
Add a File widget and a Data Table widget, then connect them.
```

9. Review the proposed changes on the **Preview** tab.
10. Click **Keep Changes** to accept them or **Revert AI Commit** to undo them.

## Troubleshooting

- **Installer did not find Orange:** Re-run the installer and use
  **Choose Folder...** to select the Orange installation directory.
- **A black command window flashed:** Install `v0.1.3` or newer from the
  latest release. The wizard now hides subprocess windows during install,
  verification, and launch.
- **Installed, but Canvas Agent is not visible in Orange:** Close Orange,
  reopen it, and check the left widget toolbox for the **Canvas Agent**
  category. If you installed from PyPI or source, run
  `python -m Orange.canvas --force-discovery` once, then reopen Orange.
- **The widget category is still missing:** Re-run the Windows installer if you
  used `CanvasAgentSetup.exe`, or verify that your PyPI/source install went
  into the same Python environment used by Orange.
- **Codex CLI missing:** Install the `codex` CLI first, then return to the
  widget and click **Check Setup** again.
- **Codex CLI signed out:** Use the widget's **Sign in** button or run
  `codex login` in a terminal.
- **Agent request failed:** Open the **Diagnostics** tab and copy the report
  before filing an issue.

## Screenshot Placeholders

- `[Placeholder] Installer welcome and Orange detection screen`
- `[Placeholder] Installer finish screen after successful install`
- `[Placeholder] Orange toolbox showing the Canvas Agent category`
- `[Placeholder] Canvas Agent Setup tab`
- `[Placeholder] Canvas Agent Preview tab with Keep/Revert controls`
- `[Placeholder] Diagnostics tab with discovery report`

## What The Widget Does

- Adds a dedicated **Canvas Agent** widget category to Orange.
- Uses structured canvas actions instead of arbitrary model-generated Python.
- Keeps an in-memory checkpoint so each AI change can be accepted or reverted.
- Includes **Setup**, **Chat**, **Preview**, and **Diagnostics** tabs.
- Checks both Codex CLI readiness and Orange widget discovery state.
