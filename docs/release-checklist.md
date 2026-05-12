# Release Checklist

Use this checklist before publishing `v0.1.3` or any later polish release.

## 1. Local Verification

Run the current test suite and packaging smoke checks:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -m unittest discover -v
python -m Orange.canvas --help
```

Confirm the test run passes and the Orange canvas command resolves without
environment surprises.

## 2. Verify Real Orange Discovery

Do not rely only on unit tests. Verify the add-on is actually discoverable in a
real Orange install.

1. Install Orange on a clean Windows machine or VM.
2. Install the package into that Orange environment.
3. Launch Orange with forced discovery.
4. Confirm the left toolbox shows a **Canvas Agent** category.
5. Drag **Canvas Agent** onto the canvas.
6. Confirm the widget opens with the four tabs:
   **Setup**, **Chat**, **Preview**, and **Diagnostics**.

## 3. Build Python Distributions

```powershell
.\scripts\build-wheel.ps1
```

Check `dist\` for:

- one source distribution (`.tar.gz`)
- at least one wheel (`.whl`)

## 4. Build The Windows Installer

```powershell
.\scripts\build-installer.ps1
```

Check that `dist\CanvasAgentSetup.exe` exists and is the file you intend to
attach to the GitHub release.

## 5. Verify Installer UI Flow

Use a real Windows machine with Orange already installed.

1. Launch `CanvasAgentSetup.exe`.
2. Confirm the title reads **Canvas Agent Setup**.
3. Confirm the initial scan either finds Orange automatically or allows manual
   selection through **Choose Folder...**.
4. Confirm **Rescan**, **Choose Folder...**, and **Install / Repair** are
   present.
5. Select an Orange install and click **Install / Repair**.
6. Confirm the status text changes to an install or repair progress message.
7. Click **Next** after installation completes.
8. Click **Run Verification**.
9. Confirm verification passes and the wizard moves to **Finish**.
10. Confirm the finish page shows **Canvas Agent is ready**, the Orange path,
    the package version, **Open Orange**, and **View Diagnostics**.
11. Click **Open Orange**.
12. Confirm **Canvas Agent** appears in the Orange toolbox after launch.

## 6. Verify Basic Widget Flow

1. Open the widget's **Setup** tab.
2. Click **Check Setup**.
3. Confirm Codex CLI state is reported correctly.
4. Open **Diagnostics** and confirm it reports the Canvas Agent entry point.
5. Send a simple prompt:

```text
Add a File widget and a Data Table widget, then connect them.
```

6. Confirm the preview renders.
7. Confirm **Keep Changes** works.
8. Confirm **Revert AI Commit** restores the previous state.

## 7. Verify GitHub Release Assets

Before pressing publish on the release page:

1. Draft the GitHub release tag and notes.
2. Attach `CanvasAgentSetup.exe`.
3. Attach the built wheel and source distribution if you are publishing them as
   release assets for users or testers.
4. Open the draft release in a browser and verify the filenames are correct.
5. After publishing, reopen the public release page and verify the assets
   download successfully.

## 8. Verify TestPyPI Or Staging Publish

If you stage through TestPyPI, confirm the package can be installed cleanly:

```powershell
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ Orange3-CanvasAgent
```

Confirm the installed package version matches the release candidate.

## 9. Verify PyPI Publish

After the GitHub publish workflow completes:

1. Open the PyPI project page for `Orange3-CanvasAgent`.
2. Confirm the new version number is visible.
3. Install it in a clean environment:

```powershell
python -m pip install Orange3-CanvasAgent
```

4. Confirm `pip show Orange3-CanvasAgent` reports the expected version.
5. Launch Orange with forced discovery and confirm the widget still appears.
