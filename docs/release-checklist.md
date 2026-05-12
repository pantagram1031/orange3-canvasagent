# Release Checklist

## Local Verification

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -m unittest discover -v
python -m Orange.canvas --help
```

## Build Python Distributions

```powershell
.\scripts\build-wheel.ps1
```

Check that `dist` contains both a wheel and source distribution.

## Build Windows Installer

```powershell
.\scripts\build-installer.ps1
```

Check that `dist\CanvasAgentSetup.exe` exists.

## Test Installer Manually

1. Use a Windows machine with official Orange installed.
2. Run `CanvasAgentSetup.exe`.
3. Confirm the installer detects Orange.
4. Install the add-on.
5. Confirm Orange opens.
6. Confirm **Canvas Agent** appears in the toolbox.
7. Drag it onto the canvas.
8. Send: `Add a File widget and a Data Table widget, then connect them.`
9. Test **Keep Changes** and **Revert AI Commit**.

## TestPyPI

1. Open the GitHub **Publish** workflow.
2. Run it manually with `target=testpypi`.
3. Install from TestPyPI in a clean environment.

```powershell
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ Orange3-CanvasAgent
```

## PyPI

1. Create a GitHub release.
2. The publish workflow uploads to PyPI through trusted publishing.
3. Install in a clean environment:

```powershell
python -m pip install Orange3-CanvasAgent
```

