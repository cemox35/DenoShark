# 🎬 DenoShark - Professional Video Editor

Nişanlı için yapılmış, Python tabanlı profesyonel video düzenleme aracı.

## ✨ Özellikler

### Video İşleme
- ✅ Video kırpma (trim)
- ✅ Video dışa aktarma (MP4, MOV, AVI)
- 🎯 Video birleştirme (geliştirilmekte)
- 🎯 Efekt ekleme (geliştirilmekte)

### Ses İşleme
- ✅ Sesi çıkarma
- ✅ Gürültü azaltma (Spectral Subtraction)
- ✅ Ses karıştırma
- ✅ Ses düzeyi ayarlama
- 🎯 Gelişmiş gürültü azaltma - AI ile (geliştirilmekte)

### AI Araçları
- ✅ Otomatik Altyazı (Whisper - OpenAI)
- 🎯 Metin-Ses Sentezi (XTTS v2)
- 🎯 Ses Klonlama (Voicecraft - Meta AI)
- 🎯 Yüz Tespiti/Bulanıklaştırma (YOLO v8)

## 📋 Gereksinimler

- Python 3.9+
- FFmpeg
- NVIDIA CUDA (GPU işlemleri için opsiyonel)

## 🚀 Kurulum

### 1. Repository Klonla
```bash
git clone https://github.com/yourusername/DenoShark.git
cd DenoShark
```

### 2. Virtual Environment Oluştur
```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

### 3. Bağımlılıkları Yükle
```bash
pip install -r requirements.txt
```

### 4. FFmpeg Yükle

**Windows (Chocolatey):**
```bash
choco install ffmpeg
```

**Mac (Homebrew):**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

## 🎯 Kullanım

Uygulamayı başlat:
```bash
python main.py
```

### Video Kırpma
1. 📹 Video İşleme sekmesine git
2. 📂 Video Seç butonuna tıkla
3. Başlangıç ve bitiş zamanlarını ayarla
4. ✂️ Video Kırp butonuna tıkla

### Gürültü Azaltma
1. 🔊 Ses İşleme sekmesine git
2. 🔊 Videodan Ses Çıkar (opsiyonel)
3. 🔇 Gürültüyü Azalt butonuna tıkla
4. Gücü (0-1) ayarla

### Otomatik Altyazı Oluşturma
1. 🤖 AI Araçları sekmesine git
2. 📝 Altyazı Oluştur butonuna tıkla
3. SRT dosyası olarak kaydet

## 📁 Proje Yapısı

```
DenoShark/
├── main.py                      # Ana giriş noktası
├── requirements.txt             # Python paketleri
├── README.md                    # Dokümantasyon
│
├── video_processor/             # Video işleme modülü
│   ├── __init__.py
│   ├── video_handler.py         # Video bilgisi
│   ├── trimmer.py               # Video kırpma
│   ├── audio_extractor.py       # Ses çıkarma
│   ├── noise_reducer.py         # Gürültü azaltma
│   ├── audio_mixer.py           # Ses karıştırma
│   └── exporter.py              # Video dışa aktarma
│
├── ai_module/                   # AI araçları
│   ├── __init__.py
│   ├── speech_recognition.py    # Whisper entegrasyonu
│   ├── tts_engine.py            # XTTS v2 (yakında)
│   └── voicecraft.py            # Voicecraft (yakında)
│
├── ui/                          # Arayüz
│   ├── __init__.py
│   ├── main_window.py           # Ana pencere
│   ├── dialogs.py               # Diyaloglar (yakında)
│   └── widgets.py               # Özel widgetler (yakında)
│
├── utils/                       # Yardımcı fonksiyonlar
│   ├── __init__.py
│   ├── config.py                # Ayarlar
│   ├── logger.py                # Loglama
│   └── helpers.py               # Yardımcı fonksiyonlar (yakında)
│
├── temp/                        # Geçici dosyalar
├── output/                      # Çıkış dosyaları
├── models/                      # AI modelleri
└── logs/                        # Log dosyaları
```

## 🔧 Konfigürasyon

`utils/config.py` dosyasında ayarları değiştirebilirsiniz:

```python
# Video Ayarları
MAX_VIDEO_DURATION_MINUTES = 120

# Audio Ayarları
SAMPLE_RATE = 16000

# AI Model Ayarları
WHISPER_MODEL = "base"  # tiny, base, small, medium, large
USE_GPU = True
```

## 📊 İşlem Akışı

### Basit Video Düzenleme
```
Video Yükle → Kırp → Ses Çıkar → Gürültü Azalt → Dışa Aktar
```

### Gelişmiş İşlem (AI ile)
```
Video Yükle → Ses Çıkar → Gürültü Azalt → Altyazı Oluştur 
→ Metin İle Oyna → Ses Sentezi → Video Birleştir → Dışa Aktar
```

## 🎓 Teknoloji Stack

### Backend
- **FFmpeg**: Video/Ses işleme
- **OpenCV**: Frame işleme
- **Librosa**: Ses analizi
- **MoviePy**: Video düzenleme
- **NumPy/SciPy**: Sayısal işlem

### AI/ML
- **Whisper**: Otomatik transkripsiyon
- **XTTS v2**: Metin-Ses sentezi
- **Voicecraft**: Ses klonlama (yakında)
- **YOLO v8**: Yüz tespiti (yakında)

### Frontend
- **PyQt6**: Masaüstü arayüzü

## 🚧 Gelecek Özellikler

- [ ] Voicecraft entegrasyonu (Ses klonlama)
- [ ] XTTS v2 entegrasyonu (Metin-Ses)
- [ ] YOLO v8 entegrasyonu (Yüz tespiti)
- [ ] Video birleştirme (Concat)
- [ ] Efekt ekleme (Transitions, Filters)
- [ ] Batch işleme
- [ ] Özel profiller kaydetme
- [ ] Eklenti sistemi

## 📝 Lisans

MIT License - Detaylar için LICENSE dosyasına bakın

## 👤 Katkıda Bulunma

Katkılarınız memnuniyetle karşılanır!

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişiklikleri commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'e push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📞 Destek

Sorun veya önerileriniz için GitHub Issues'de yazın.

## 💝 Nişanlıma Armağan

Bu proje, nişanlım için yapılmış bir aşk gösterisidir. 💕

---

Made with ❤️ for my future wife
