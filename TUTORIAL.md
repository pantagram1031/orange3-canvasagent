# Orange3 Canvas Agent Tutorial

This tutorial shows where to find the **Canvas Agent** widget in Orange, how to
run it for the first time, and how to repair the most common "installed but not
visible" problem.

## Where To Find The Widget

After a successful install, open Orange and look at the left widget toolbox.
The add-on creates a category named **Canvas Agent**. Expand that category and
drag the **Canvas Agent** widget onto your workflow canvas.

If you do not see the category, go straight to
[Repair: Installed But Not Visible](#repair-installed-but-not-visible).

## Beginner Install Path

1. Download `CanvasAgentSetup.exe` from the GitHub releases page.
2. Double-click it.
3. Let the installer detect Orange, or click **Choose Folder...** if needed.
4. Click **Install / Repair**.
5. Click **Run Verification** on the Verify page.
6. On the Finish page, click **Open Orange**.
7. In Orange, look for the **Canvas Agent** category in the left toolbox.

This path is designed for normal Orange users and does not require PowerShell.

## Coder Install Path

### From PyPI

```powershell
python -m pip install Orange3-CanvasAgent
python -m Orange.canvas --force-discovery
```

### From A Local Checkout

```powershell
git clone https://github.com/pantagram1031/orange3-canvasagent.git
cd orange3-canvasagent
python -m pip install -e ".[dev]"
python -B -m unittest discover -v
python -m Orange.canvas --force-discovery
```

## First Run Inside Orange

1. Drag **Canvas Agent** onto the canvas.
2. Open the **Setup** tab.
3. Click **Check Setup**.
4. If prompted, click **Sign in** to complete the Codex CLI login flow.
5. Click **Test Agent**.
6. Open the **Chat** tab.
7. Enter a request such as:

```text
Add a File widget and a Data Table widget, then connect them.
```

8. Click **Send**.
9. Review the output on the **Preview** tab.
10. Use **Keep Changes** to accept the plan or **Revert AI Commit** to restore
    the previous canvas state.

## Repair: Installed But Not Visible

Use these steps in order if the installer said Canvas Agent was installed but
you still cannot find it in Orange.

1. Close every Orange window.
2. Open Orange again normally.
3. Check the left toolbox carefully for a category named **Canvas Agent**.
4. If you installed with `CanvasAgentSetup.exe`, rerun the installer and finish
   the install again. The installer launches Orange with forced widget
   discovery, which repairs many first-run registration issues.
5. If you installed from PyPI or source, run the discovery command once:

```powershell
python -m Orange.canvas --force-discovery
```

6. Reopen Orange and check again.
7. If the category is still missing, confirm you installed into the same Python
   environment used by your Orange desktop app.
8. If the widget appears but setup checks fail, open the **Diagnostics** tab in
   the widget and copy the report before filing an issue.

## The Four Tabs

- **Setup:** Checks Codex CLI availability, sign-in state, and Orange readiness.
- **Chat:** Sends natural-language workflow requests.
- **Preview:** Shows the structured action plan and the keep/revert controls.
- **Diagnostics:** Shows the discovery and readiness report for support cases.

## What The Agent Changes

The widget does not execute arbitrary Python from a model response. It accepts a
structured plan and applies only supported canvas actions such as:

- `add_widget`
- `connect`
- `rename_node`
- `move_node`
- `annotate`

Before applying a plan, the add-on stores an in-memory checkpoint of the
current scheme. If anything fails, the checkpoint is restored automatically.

## Quick Verification For Coders

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -m unittest discover -v
python -m Orange.canvas --force-discovery
```
