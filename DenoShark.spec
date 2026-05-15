# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

project_root = Path.cwd()

# Qt6 Multimedia backend DLL'lerini bul ve binaries listesine ekle.
# QMediaPlayer Windows'ta windowsmediafoundation plugin'ine ihtiyaç duyar;
# PyInstaller bunu otomatik toplamaz, diğer PC'lerde ses çalışmaz.
def _collect_qt6_multimedia():
    result = []
    site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    qt6_root = site_packages / "PyQt6" / "Qt6"

    # Backend plugin: PyQt6/Qt6/plugins/multimedia/
    mm_plugins = qt6_root / "plugins" / "multimedia"
    if mm_plugins.exists():
        for dll in mm_plugins.glob("*.dll"):
            result.append((str(dll), "PyQt6/Qt6/plugins/multimedia"))

    # Çekirdek Multimedia DLL'leri (Qt6/bin/)
    qt6_bin = qt6_root / "bin"
    for name in ["Qt6Multimedia.dll", "Qt6MultimediaWidgets.dll", "Qt6Network.dll"]:
        dll = qt6_bin / name
        if dll.exists():
            result.append((str(dll), "PyQt6/Qt6/bin"))

    return result

# ── Data files ─────────────────────────────────────────────────────────────
datas = [(str(project_root / "img"), "img")]

if (project_root / "models").exists():
    datas.append((str(project_root / "models"), "models"))

if (project_root / "pretrained_models").exists():
    datas.append((str(project_root / "pretrained_models"), "pretrained_models"))

try:
    datas.extend(collect_data_files(
        "imageio_ffmpeg",
        includes=["**/binaries/*", "**/binaries/**/*"]
    ))
except Exception:
    pass

try:
    datas.extend(collect_data_files("faster_whisper"))
except Exception:
    pass

try:
    datas.extend(collect_data_files("ctranslate2"))
except Exception:
    pass

# ── Binaries (native DLLs) ─────────────────────────────────────────────────
# ctranslate2/__init__.py DLL'leri kendi paket dizininden yükler (glob + ctypes).
# DLL'leri zorla _internal/ köküne taşımak, aynı DLL'lerin hem _internal/'da
# hem _internal/ctranslate2/'de bulunmasına yol açar (auto-detection ile).
# libiomp5md.dll gibi OpenMP singleton DLL'leri iki farklı path'ten yüklenince
# süreç 0xC0000005 Access Violation ile crash yapar.
#
# Doğru yaklaşım: DLL'leri auto-detection'a bırakmak (_internal/ctranslate2/),
# pyi_rth_ctranslate2 runtime hook ile doğru sırada yüklemek.
# cudnn64_9.dll CPU-only modda gerekli değil; COLLECT adımında filtreleniyor.
binaries = _collect_qt6_multimedia()

# UPX, native DLL'leri ve .pyd extension'larını bozabilir
UPX_EXCLUDE = [
    "vcruntime140.dll",
    "msvcp140.dll",
    "python3*.dll",
    "api-ms-win-*.dll",
    "ctranslate2.dll",
    "libiomp5md.dll",
    "cudnn64_9.dll",
    "_ext*.pyd",        # ctranslate2 C extension — UPX bunu bozuyor
    "*.pyd",            # tüm Python extension DLL'leri
]

# ── Excluded modules ───────────────────────────────────────────────────────
EXCLUDES = [
    "numba", "llvmlite",
    "torch", "torchaudio", "torchvision",
    "sklearn", "skimage", "onnxruntime",
    "tkinter", "_tkinter", "tcl", "tk",
    "matplotlib",
    "IPython", "ipykernel", "jupyter", "notebook",
    "pytest", "unittest", "doctest", "pydoc", "pdb",
    "turtle", "curses", "ftplib", "telnetlib",
]

# ── Analysis ───────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # ctranslate2 / faster-whisper
        'ctranslate2',
        'ctranslate2._ext',
        'faster_whisper',
        'faster_whisper.transcribe',
        'faster_whisper.audio',
        'faster_whisper.tokenizer',
        'faster_whisper.utils',
        'sentencepiece',
        'huggingface_hub',
        'huggingface_hub.utils',
        'tokenizers',
        # subprocess worker modu
        'utils.whisper_runner',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hooks/pyi_rth_ctranslate2.py'],
    excludes=EXCLUDES,
    noarchive=False,
    optimize=1,
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
    icon=str(project_root / "img" / "logo-small.ico"),
)

def _filter_binaries(binaries):
    """CPU-only modda gereksiz CUDA DLL'lerini çıkar.
    cudnn64_9.dll frozen subprocess'te DllMain 0xC0000005 crash'ine neden oluyor.
    ctranslate2/__init__.py bu DLL'i glob ile yükler; bundle'da yoksa atlar.
    PyInstaller binaries formatı: (dest_path, src_path, typecode)
    """
    import os
    skip = {'cudnn64_9.dll'}
    result = []
    for b in binaries:
        fname = os.path.basename(b[0]).lower()
        if fname not in skip:
            result.append(b)
    return result

coll = COLLECT(
    exe,
    _filter_binaries(a.binaries),
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=UPX_EXCLUDE,
    name='DenoShark',
)
