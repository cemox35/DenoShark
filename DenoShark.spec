# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.building.build_main import Tree
from PyInstaller.utils.hooks import collect_data_files

project_root = Path(__file__).parent

datas = [Tree(str(project_root / "img"), prefix="img")]

if (project_root / "models").exists():
    datas.append(Tree(str(project_root / "models"), prefix="models"))

if (project_root / "pretrained_models").exists():
    datas.append(Tree(str(project_root / "pretrained_models"), prefix="pretrained_models"))

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
