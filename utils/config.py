"""
DenoShark Configuration Module
Tüm ayarlar burada yönetilir
"""
import os
from pathlib import Path

# Proje kök dizini
PROJECT_ROOT = Path(__file__).parent.parent

# Dizinler
TEMP_DIR = PROJECT_ROOT / "temp"
OUTPUT_DIR = PROJECT_ROOT / "output"
MODELS_DIR = PROJECT_ROOT / "models"

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
USE_GPU = True

# PyQt6 Arayüz Ayarları
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
APP_NAME = "DenoShark"
APP_VERSION = "1.0.0"
THEME = "dark"  # light, dark

# İşlem Ayarları
MAX_WORKERS = 4  # Paralel işlem sayısı
TIMEOUT_SECONDS = 3600  # 1 saat
