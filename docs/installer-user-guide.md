# Canvas Agent Installer User Guide

This guide is for people who installed Orange from the official Orange download
page and do not want to use a terminal.

## Install

1. Download `CanvasAgentSetup.exe`.
2. Double-click the file.
3. If Windows shows a security prompt, choose **More info** and then **Run anyway** only if you trust the file source.
4. The installer scans for Orange.
5. If Orange is listed, select it and click **Install**.
6. If Orange is not listed, click **Choose Folder...** and select the folder where Orange is installed.
7. Wait for the installer to finish.
8. Orange opens automatically.

## Find The Widget

1. In Orange, look at the widget toolbox.
2. Find the **Canvas Agent** category.
3. Drag **Canvas Agent** onto the canvas.

## First Run

1. Open the **Setup** tab.
2. Click **Check Setup**.
3. If Codex is missing, install Codex CLI and reopen Orange.
4. If Codex is signed out, click **Sign in**.
5. Click **Test Agent**.
6. Open the **Chat** tab.

## Example Prompt

```text
Add a File widget and a Data Table widget, then connect them.
```

The agent will update the canvas and show the proposed AI commit. Use
**Keep Changes** to accept it or **Revert AI Commit** to undo it.

## Troubleshooting

- **No Orange install found:** Click **Choose Folder...** and select the folder containing Orange's `python.exe`.
- **Widget does not appear:** Start Orange once with widget discovery enabled. The installer does this automatically, but coders can run `python -m Orange.canvas --force-discovery`.
- **Codex is missing:** Install Codex CLI and make sure `codex --version` works in a terminal.
- **Codex is signed out:** Run `codex login` or use the widget's **Sign in** button.
- **Agent output failed:** Open the **Diagnostics** tab and copy the report.

