# 🛠️ DenoShark Geliştirici Rehberi

Bu belge, DenoShark projesine katkıda bulunmak isteyenler için rehberdir.

## 🏗️ Proje Mimarisi

### Katmanlar (Layers)

```
┌─────────────────────────────────┐
│        UI Layer (PyQt6)         │  ← Kullanıcı arayüzü
├─────────────────────────────────┤
│   Business Logic Layer          │  ← İş mantığı
│  (VideoProcessor, AI Modules)   │
├─────────────────────────────────┤
│   Core Layer                    │  ← Temel kütüphaneler
│  (FFmpeg, Whisper, XTTS)        │
└─────────────────────────────────┘
```

### Modül Sorumluluğu

| Modül | Sorumluluk |
|-------|-----------|
| `ui/` | PyQt6 arayüzü, kullanıcı etkileşimi |
| `video_processor/` | Video/ses işleme |
| `ai_module/` | AI modelleri (Whisper, XTTS) |
| `utils/` | Yardımcı fonksiyonlar, config |

---

## 🚀 Yeni Özellik Ekleme

### 1. Video Filtresi Ekleme (Örnek)

#### Adım 1: video_processor/filters.py oluştur
```python
# video_processor/filters.py
import cv2
import numpy as np
from utils.logger import setup_logger

logger = setup_logger(__name__)

class VideoFilter:
    """Video filtreleri"""
    
    @staticmethod
    def apply_brightness(video_path: str, output_path: str, brightness: float = 1.2):
        """Parlaklık ayarla"""
        # Implementasyon
        pass
```

#### Adım 2: __init__.py güncelle
```python
# video_processor/__init__.py
from .filters import VideoFilter

__all__ = [..., 'VideoFilter']
```

#### Adım 3: UI'ye ekle
```python
# ui/main_window.py - _create_video_tab() içine

filter_group = QGroupBox("Filtreler")
# Filtre kontrolleri
```

---

## 🤖 AI Modeli Entegrasyonu (Voicecraft Örneği)

### Adım 1: Modül oluştur
```python
# ai_module/voicecraft.py
import torch
from utils.logger import setup_logger

logger = setup_logger(__name__)

class Voicecraft:
    """Voice Craft entegrasyonu"""
    
    def __init__(self):
        logger.info("Voicecraft modeli yükleniyor...")
        # Model yükleme
        pass
    
    def clone_voice(self, reference_audio: str, text: str, output_path: str):
        """Ses klonlama"""
        pass
```

### Adım 2: Requirements güncelle
```bash
pip install voicecraft-model-name
```

### Adım 3: Config ayarla
```python
# utils/config.py
VOICECRAFT_MODEL = "v1"
VOICECRAFT_ENABLED = False  # İlk başta devre dışı
```

### Adım 4: UI entegre et
```python
# ui/main_window.py
voicecraft = Voicecraft()
result = voicecraft.clone_voice(ref_audio, text, output)
```

---

## 🧪 Test Yazma

### Birim Testleri
```python
# tests/test_video_processor.py
import unittest
from video_processor import VideoHandler

class TestVideoHandler(unittest.TestCase):
    def test_video_loading(self):
        handler = VideoHandler("test_video.mp4")
        self.assertIsNotNone(handler.fps)
        self.assertGreater(handler.duration_seconds, 0)
```

### İntegrasyon Testleri
```python
# tests/test_integration.py
class TestFullWorkflow(unittest.TestCase):
    def test_trim_and_denoise(self):
        # Video kırp + gürültü azalt
        pass
```

### Test Çalıştırma
```bash
python -m pytest tests/
```

---

## 📊 Code Style Guide

### Naming Conventions

```python
# Sabitler (UPPER_SNAKE_CASE)
MAX_VIDEO_SIZE = 1024

# Fonksiyonlar (snake_case)
def extract_audio():
    pass

# Sınıflar (PascalCase)
class VideoProcessor:
    pass

# Özel üyeler (_leading_underscore)
def _internal_method():
    pass
```

### Docstring Format
```python
def process_video(input_path: str, output_path: str) -> bool:
    """
    Videoyu işle
    
    Args:
        input_path: Giriş video dosyası
        output_path: Çıkış video dosyası
    
    Returns:
        İşlem başarılı ise True
    
    Raises:
        ValueError: Dosya bulunamazsa
    """
```

---

## 🔄 Workflow

### Branch Stratejisi
```
main (stable)
├── develop (test edilmiş kod)
│   ├── feature/video-effects
│   ├── feature/voicecraft
│   └── bugfix/audio-sync
```

### Commit Mesajları
```
feat: Yeni özellik açıklaması
fix: Hata düzeltme açıklaması
docs: Dokümantasyon güncellemesi
refactor: Kod yeniden yapılandırması
test: Test ekleme/düzeltme
```

### Pull Request Süreci
1. Branch oluştur (`feature/yeni-ozellik`)
2. Kod yaz ve test et
3. PR açıklaması yaz
4. İncelemeden geç
5. Merge et

---

## 📈 Performance İpuçları

### Video Processing
```python
# Kötü: Tüm frameyi yükle
frame = cv2.imread("frame.jpg")

# İyi: Frame skip ile
cap = cv2.VideoCapture("video.mp4")
frame_skip = 5
for i in range(0, total_frames, frame_skip):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
```

### Memory Management
```python
# Dosya işleme sonunda kapat
video.close()
audio.close()

# Large arrays için generator kullan
def process_large_file():
    for chunk in read_in_chunks(file_path):
        yield process(chunk)
```

---

## 🐛 Debug Modu

Config'de debug modunu açın:
```python
# utils/config.py
DEBUG_MODE = True
VERBOSE_LOGGING = True
```

Logger kullanın:
```python
from utils.logger import setup_logger
logger = setup_logger(__name__)

logger.debug("Detaylı bilgi")
logger.info("Bilgi")
logger.warning("Uyarı")
logger.error("Hata")
```

---

## 📚 Faydalı Linkler

- [PyQt6 Docs](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [FFmpeg Wiki](https://trac.ffmpeg.org/wiki)
- [Whisper Research](https://github.com/openai/whisper/discussions)
- [XTTS v2 Paper](https://arxiv.org/abs/2301.13541)

---

## 💡 İyi Uygulamalar

1. **Modular Design**: Her modül tek bir sorumluluğa sahip olsun
2. **Error Handling**: Exception'ları yakala ve loglama yap
3. **Documentation**: Her fonksiyon için docstring yaz
4. **Testing**: Yeni kod için test yaz
5. **Performance**: Optimize etmeden önce profile et

---

Made with ❤️ by Developer Community
