# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# __file__ is not defined in some PyInstaller spec execution contexts.
project_root = Path.cwd()

datas = [(str(project_root / "img"), "img")]

if (project_root / "models").exists():
    datas.append((str(project_root / "models"), "models"))

if (project_root / "pretrained_models").exists():
    datas.append((str(project_root / "pretrained_models"), "pretrained_models"))

try:
    imageio_ffmpeg_datas = collect_data_files(
        "imageio_ffmpeg",
        includes=["**/binaries/*", "**/binaries/**/*"]
    )
    datas.extend(imageio_ffmpeg_datas)
except Exception:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DenoShark',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DenoShark',
)
