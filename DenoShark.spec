# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

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

# Modules not used at runtime — excluding them prevents PyInstaller from
# bundling large optional dependencies (numba/llvmlite alone = ~100 MB).
EXCLUDES = [
    # numba JIT acceleration for librosa — optional, falls back to numpy
    "numba",
    "llvmlite",
    # torch / torchaudio — not needed at runtime:
    #   faster-whisper uses ctranslate2 directly (no torch dependency)
    #   TTS/XTTS (tts_engine.py) is optional and handles ImportError gracefully
    "torch",
    "torchaudio",
    "torchvision",
    # ML libs not used in this project
    "sklearn",
    "skimage",
    "onnxruntime",
    # tkinter not used — app uses PyQt6
    "tkinter",
    "_tkinter",
    "tcl",
    "tk",
    # matplotlib not used at runtime
    "matplotlib",
    # Development / testing tools — never needed in a packaged app
    "IPython",
    "ipykernel",
    "jupyter",
    "notebook",
    "pytest",
    "unittest",
    "doctest",
    "pydoc",
    "pdb",
    # Unused standard-library heavyweights (only truly safe ones)
    "turtle",
    "curses",
    "ftplib",
    "telnetlib",
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=1,  # Remove assert statements and docstrings from .pyc files
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
    # These DLLs can silently break when UPX-compressed on Windows
    upx_exclude=[
        "vcruntime140.dll",
        "msvcp140.dll",
        "python3*.dll",
        "api-ms-win-*.dll",
    ],
    name='DenoShark',
)
