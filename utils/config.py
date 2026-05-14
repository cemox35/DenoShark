"""
DenoShark Configuration Module
Tüm ayarlar burada yönetilir
"""
import sys
import os
from pathlib import Path

# PyInstaller dist'ten mi çalışıyoruz?
_IS_FROZEN = hasattr(sys, '_MEIPASS')

# Bundled resource'lar (img, models) _MEIPASS içinde; user data exe'nin yanında
_MEIPASS_ROOT = Path(sys._MEIPASS) if _IS_FROZEN else None
_EXE_DIR = Path(sys.executable).parent if _IS_FROZEN else None

# Proje kök dizini (dev modda kaynak ağacı, dist modda _MEIPASS)
PROJECT_ROOT = _MEIPASS_ROOT if _IS_FROZEN else Path(__file__).parent.parent


def resource_path(relative: str) -> Path:
    """Bundled kaynaklara (img, models) giden yol — dev ve dist'te çalışır."""
    if _IS_FROZEN:
        return _MEIPASS_ROOT / relative
    return PROJECT_ROOT / relative


def user_data_path(relative: str) -> Path:
    """Kullanıcı tarafından yazılabilir dizinler (temp, output) — exe'nin yanı."""
    if _IS_FROZEN:
        return _EXE_DIR / relative
    return PROJECT_ROOT / relative


# Dizinler
TEMP_DIR = user_data_path("temp")
OUTPUT_DIR = user_data_path("output")
MODELS_DIR = user_data_path("models")

# Klasörleri oluştur
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)

# Video Ayarları
VIDEO_FORMATS = ('.mp4', '.mov', '.avi', '.mkv', '.flv')
MAX_VIDEO_DURATION_MINUTES = 120  # 2 saat
SUPPORTED_AUDIO_FORMATS = ('.wav', '.mp3', '.aac', '.m4a')

# Audio Ayarları
SAMPLE_RATE = 16000  # Whisper için optimize
NOISE_REDUCTION_THRESHOLD = 0.02
AUDIO_NORMALIZATION_LEVEL = -20.0  # dB

# AI Model Ayarları
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
XTTS_MODEL = "v2"
WHISPER_LANGUAGE = "tr"  # Türkçe
USE_GPU = False  # CUDA DLL hatası olduğundan CPU modunda çalıştırılıyor

# PyQt6 Arayüz Ayarları
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
APP_NAME = "DenoShark"
APP_VERSION = "1.0.0"
THEME = "dark"  # light, dark

# İşlem Ayarları
MAX_WORKERS = 4  # Paralel işlem sayısı
TIMEOUT_SECONDS = 3600  # 1 saat
