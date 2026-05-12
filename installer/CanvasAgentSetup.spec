# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

installer_dir = Path(SPECPATH)
project_root = installer_dir.parent
dist_dir = project_root / "dist"
wheels = sorted(dist_dir.glob("*.whl"))
datas = [(str(wheels[-1]), ".")] if wheels else []

a = Analysis(
    [str(installer_dir / "gui.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="CanvasAgentSetup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
