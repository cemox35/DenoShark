"""
DenoShark Kurulum Rehberi

Bu dosya, DenoShark uygulamasını başarıyla kurmak için adım adım talimatlar içerir.
"""

## ⚡ Hızlı Kurulum (Windows)

### Adım 1: FFmpeg Yükle
```powershell
# Chocolatey ile
choco install ffmpeg

# Veya manuel: https://ffmpeg.org/download.html
```

### Adım 2: Python Environment Kur
```powershell
# Virtual environment oluştur
python -m venv venv

# Aktivate et
.\venv\Scripts\activate
```

### Adım 3: Paketleri Yükle
```powershell
pip install -r requirements.txt
```

### Adım 4: Uygulamayı Başlat
```powershell
python main.py
```

---

## 🐧 Linux/Mac Kurulum

### Ubuntu/Debian:
```bash
# FFmpeg yükle
sudo apt-get install ffmpeg

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Paketler
pip install -r requirements.txt

# Başlat
python main.py
```

### macOS:
```bash
# Homebrew ile FFmpeg
brew install ffmpeg

# Virtual environment
python3 -m venv venv
source venv/bin/activate

# Paketler
pip install -r requirements.txt

# Başlat
python main.py
```

---

## 🤖 GPU Desteği (NVIDIA CUDA)

Daha hızlı işlem için GPU kullanabilirsiniz:

```bash
# CUDA 11.8 için
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1 için
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Konfigürasyonda `USE_GPU = True` olduğundan emin olun.

---

## 📦 Gerekli Paketlerin Açıklaması

| Paket | Kullanım |
|-------|----------|
| **PyQt6** | Masaüstü arayüzü |
| **OpenCV** | Video frame işleme |
| **MoviePy** | Video düzenleme |
| **Librosa** | Ses analizi |
| **Soundfile** | Ses dosyası I/O |
| **Whisper** | Otomatik altyazı |
| **Torch/Torchaudio** | AI modelleri |

---

## 🆘 Sorun Giderme

### Problem: "ffmpeg not found"
```bash
# Windows: FFmpeg path'ını ekle
set PATH=%PATH%;C:\\ffmpeg\\bin

# Linux/Mac: yüklediğinizden emin olun
which ffmpeg
```

### Problem: "Module not found"
```bash
# Virtual environment'in aktif olduğundan emin olun
# Paketleri yeniden yükleyin
pip install --upgrade -r requirements.txt
```

### Problem: "CUDA errors"
```bash
# CPU modunda çalışt
# config.py'de USE_GPU = False yapın
```

### Problem: PyQt6 arayüz açılmıyor
```bash
# Display server kontrol et (Linux)
echo $DISPLAY

# Alternatif: Headless mode kur
pip install PyQt6-webengine
```

---

## ✅ Test Etme

Kurulumdan sonra test edin:

```bash
# Python import test
python -c "import PyQt6, librosa, whisper; print('✅ Tüm paketler yüklü')"

# FFmpeg test
ffmpeg -version

# Uygulamayı çalıştır
python main.py
```

---

## 📚 Ek Kaynaklar

- [PyQt6 Dokümantasyonu](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Whisper Github](https://github.com/openai/whisper)
- [XTTS v2 Github](https://github.com/coqui-ai/TTS)
- [FFmpeg Wiki](https://trac.ffmpeg.org/wiki)

---

Made with ❤️ for my future wife
"""
