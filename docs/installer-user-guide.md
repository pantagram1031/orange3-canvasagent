# Canvas Agent Installer User Guide

This guide is for Orange users who want a normal Windows installer experience.
You do not need PowerShell or developer tools for this path.

## Before You Start

- Install Orange first from the official Orange Data Mining download page.
- Download `CanvasAgentSetup.exe` from the matching GitHub release.
- Close Orange before starting the installer.

## Installer Walkthrough

Think of the installer as a short wizard with five simple pages:
**Welcome**, **Detect Orange**, **Install / Repair**, **Verify**, and
**Finish**.

### Page 1: Welcome

1. Double-click `CanvasAgentSetup.exe`.
2. Read the short setup summary.
3. Click **Next**.

### Page 2: Detect Orange

1. Wait for the scan to finish.
2. Review the list of detected Orange installations.
3. If your copy of Orange is listed, click it once to select it.
4. If nothing is listed, click **Choose Folder...** and select your Orange
   installation folder.
5. If needed, use **Rescan** to search again.
6. Click **Next**.

Status text under the buttons will tell you whether Orange was found or whether
you need to choose a folder manually.

### Page 3: Install / Repair

1. Click **Install / Repair**.
2. Wait while the installer copies the Canvas Agent wheel into Orange's Python
   environment.
3. When the page says the install or repair is complete, click **Next**.

If installation fails, the installer shows an error dialog such as:

- **Choose Orange** if no install was selected.
- **Wheel not found** if the packaged add-on asset is missing.
- **Install failed** if pip installation into Orange's Python failed.

### Page 4: Verify

1. Click **Run Verification**.
2. The installer checks that Orange can discover the category, widget, and icon.
3. If verification passes, the wizard moves to **Finish**.
4. If verification fails, click **View Diagnostics** or **Show diagnostics**.

### Page 5: Finish Screen

On success, the finish page says:

`Canvas Agent is ready`

It also shows the selected Orange path, installed Canvas Agent version,
**Open Orange**, **View Diagnostics**, and **Close** buttons. Click
**Open Orange** when you are ready to launch Orange with forced widget
discovery.

## After The Installer Closes

1. Wait for Orange to open.
2. Look at the left widget toolbox.
3. Find the **Canvas Agent** category.
4. Drag **Canvas Agent** onto the canvas.
5. Open the **Setup** tab and click **Check Setup**.

## Diagnostics And Repair

If something looks wrong after install, use these checks in order.

### Orange Was Not Detected

- Run the installer again.
- Click **Choose Folder...**.
- Select the Orange install directory that contains the Orange application and
  bundled Python runtime.

### The Installer Finished, But The Widget Is Missing

- Close Orange completely.
- Run `CanvasAgentSetup.exe` again and complete the install one more time.
- On the finish screen, click **Open Orange**.
- Check the left toolbox for the **Canvas Agent** category.

### The Widget Opens, But Setup Is Not Ready

Inside the widget:

1. Open **Setup**.
2. Click **Check Setup**.
3. Use **Sign in** if Codex CLI needs authentication.
4. Open **Diagnostics** to view the current report.

The diagnostics report summarizes:

- Codex CLI state
- Orange widget discovery state
- The registered entry point, when available

### When To File A Bug

File an issue if:

- the installer never finds a valid Orange installation,
- the finish screen appears but the widget category never shows up, or
- the diagnostics report keeps showing missing discovery after reinstalling.

Include the installer message you saw and the widget diagnostics report if you
can reproduce the issue.
