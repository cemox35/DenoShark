"""
Main Window - Ana arayüz
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QSpinBox, QDoubleSpinBox,
    QFileDialog, QProgressBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QComboBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtGui import QPixmap

from utils.logger import setup_logger
from utils.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION
)
from video_processor import (
    VideoHandler, VideoTrimmer, AudioExtractor,
    NoiseReducer, AudioMixer, VideoExporter
)
from .widgets import VideoDragDropWidget, VideoTimelineWidget

logger = setup_logger(__name__)

class ProcessingThread(QThread):
    """Arka planda işlem yapan thread"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)
    
    def __init__(self, task_func, *args):
        super().__init__()
        self.task_func = task_func
        self.args = args
    
    def run(self):
        try:
            self.task_func(*self.args)
            self.finished.emit(True)
        except Exception as e:
            logger.error(f"İşlem hatası: {e}")
            self.finished.emit(False)

class MainWindow(QMainWindow):
    """Ana pencere"""
    
    def __init__(self):
        super().__init__()
        self.current_video_path = None
        self.current_audio_path = None
        self.init_ui()
    
    def init_ui(self):
        """Arayüzü oluştur"""
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Ana widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Sekmeler
        self.tabs.addTab(self._create_video_tab(), "📹 Video İşleme")
        self.tabs.addTab(self._create_audio_tab(), "🔊 Ses İşleme")
        self.tabs.addTab(self._create_ai_tab(), "🤖 AI Araçları")
        self.tabs.addTab(self._create_settings_tab(), "⚙️ Ayarlar")
        
        # Status bar
        self.statusBar().showMessage("Hazır")
    
    def _create_video_tab(self):
        """Video işleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Sürükle-bırak video yükleme
        load_group = QGroupBox("Video Yükle")
        load_layout = QVBoxLayout()
        
        self.drag_drop_widget = VideoDragDropWidget()
        self.drag_drop_widget.video_dropped.connect(self.on_video_dropped)
        load_layout.addWidget(self.drag_drop_widget)
        
        # Alternatif: Dosya seçme butonu
        load_btn = QPushButton("📂 Veya buradan video seç...")
        load_btn.clicked.connect(self.load_video)
        load_layout.addWidget(load_btn)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Video kırpma (timeline preview ile)
        trim_group = QGroupBox("Video Kırpma")
        trim_layout = QVBoxLayout()
        
        # Timeline widget (video yüklendikten sonra gösterilecek)
        self.timeline_widget = None
        self.timeline_container = QWidget()
        self.timeline_container_layout = QVBoxLayout()
        self.timeline_container.setLayout(self.timeline_container_layout)
        trim_layout.addWidget(self.timeline_container)
        
        # Manuel giriş (timeline yüklü değilse)
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Başlangıç (s):"))
        self.trim_start = QDoubleSpinBox()
        self.trim_start.setMaximum(10000)
        manual_layout.addWidget(self.trim_start)
        
        manual_layout.addWidget(QLabel("Bitiş (s):"))
        self.trim_end = QDoubleSpinBox()
        self.trim_end.setMaximum(10000)
        self.trim_end.setValue(10)
        manual_layout.addWidget(self.trim_end)
        trim_layout.addLayout(manual_layout)
        
        trim_btn = QPushButton("✂️ Video Kırp")
        trim_btn.clicked.connect(self.trim_video)
        trim_layout.addWidget(trim_btn)
        
        trim_group.setLayout(trim_layout)
        layout.addWidget(trim_group)
        
        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_audio_tab(self):
        """Ses işleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Video yükleme (Ses İşleme sekmesi için)
        load_group_audio = QGroupBox("Video Yükle")
        load_layout_audio = QVBoxLayout()
        
        # Sürükle-bırak widget
        self.drag_drop_audio = VideoDragDropWidget()
        self.drag_drop_audio.video_dropped.connect(
            lambda path: self.load_video_audio(path)
        )
        load_layout_audio.addWidget(self.drag_drop_audio)
        
        # Dosya seçme butonu
        load_btn_audio = QPushButton("📂 Veya buradan video seç...")
        load_btn_audio.clicked.connect(self.load_video_audio)
        load_layout_audio.addWidget(load_btn_audio)
        
        load_group_audio.setLayout(load_layout_audio)
        layout.addWidget(load_group_audio)
        
        # Video timeline (ses işleme için)
        self.audio_timeline_widget = None
        self.audio_timeline_container = QWidget()
        self.audio_timeline_container_layout = QVBoxLayout()
        self.audio_timeline_container.setLayout(self.audio_timeline_container_layout)
        layout.addWidget(self.audio_timeline_container)
        
        # Ses çıkarma
        extract_group = QGroupBox("Sesi Çıkar")
        extract_layout = QVBoxLayout()
        
        extract_layout.addWidget(QLabel("Çıkartılacak ses aralığı:"))
        extract_manual_layout = QHBoxLayout()
        extract_manual_layout.addWidget(QLabel("Başlangıç (s):"))
        self.audio_extract_start = QDoubleSpinBox()
        self.audio_extract_start.setMaximum(10000)
        extract_manual_layout.addWidget(self.audio_extract_start)
        
        extract_manual_layout.addWidget(QLabel("Bitiş (s):"))
        self.audio_extract_end = QDoubleSpinBox()
        self.audio_extract_end.setMaximum(10000)
        self.audio_extract_end.setValue(10)
        extract_manual_layout.addWidget(self.audio_extract_end)
        extract_layout.addLayout(extract_manual_layout)
        
        # Checkbox'lar
        checkbox_layout = QHBoxLayout()
        self.extract_audio_checkbox = QCheckBox("📢 Sesi İndir")
        self.extract_audio_checkbox.setChecked(True)
        self.extract_video_checkbox = QCheckBox("🎬 Videoyu İndir")
        checkbox_layout.addWidget(self.extract_audio_checkbox)
        checkbox_layout.addWidget(self.extract_video_checkbox)
        extract_layout.addLayout(checkbox_layout)
        
        extract_btn = QPushButton("📥 İndir")
        extract_btn.clicked.connect(self.extract_audio_video)
        extract_layout.addWidget(extract_btn)
        
        extract_group.setLayout(extract_layout)
        layout.addWidget(extract_group)
        
        # Gürültü azaltma
        denoise_group = QGroupBox("Gürültü Azaltma")
        denoise_layout = QVBoxLayout()
        
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("Güç:"))
        self.denoise_strength = QDoubleSpinBox()
        self.denoise_strength.setMinimum(0)
        self.denoise_strength.setMaximum(1)
        self.denoise_strength.setValue(0.8)
        self.denoise_strength.setSingleStep(0.1)
        strength_layout.addWidget(self.denoise_strength)
        denoise_layout.addLayout(strength_layout)
        
        denoise_btn = QPushButton("🔇 Gürültüyü Azalt")
        denoise_btn.clicked.connect(self.reduce_noise)
        denoise_layout.addWidget(denoise_btn)
        
        denoise_group.setLayout(denoise_layout)
        layout.addWidget(denoise_group)
        
        # Ses karıştırma
        mix_group = QGroupBox("Ses Karıştır")
        mix_layout = QVBoxLayout()
        
        mix_btn = QPushButton("🎵 Arka Plan Sesi Ekle")
        mix_btn.clicked.connect(self.mix_audio)
        mix_layout.addWidget(mix_btn)
        
        mix_group.setLayout(mix_layout)
        layout.addWidget(mix_group)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_ai_tab(self):
        """AI araçları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Otomatik altyazı
        subtitle_group = QGroupBox("Otomatik Altyazı (Whisper)")
        subtitle_layout = QVBoxLayout()
        
        subtitle_btn = QPushButton("📝 Altyazı Oluştur")
        subtitle_btn.clicked.connect(self.generate_subtitles)
        subtitle_layout.addWidget(subtitle_btn)
        
        subtitle_group.setLayout(subtitle_layout)
        layout.addWidget(subtitle_group)
        
        # XTTS
        tts_group = QGroupBox("Metin-Ses (XTTS v2) - Yakında")
        tts_layout = QVBoxLayout()
        
        tts_btn = QPushButton("🎤 Metni Sese Dönüştür (Hazırlanıyor)")
        tts_btn.setEnabled(False)
        tts_layout.addWidget(tts_btn)
        
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        # Voicecraft
        vc_group = QGroupBox("Ses Klonlama (Voicecraft) - Yakında")
        vc_layout = QVBoxLayout()
        
        vc_btn = QPushButton("🎧 Ses Klonla (Hazırlanıyor)")
        vc_btn.setEnabled(False)
        vc_layout.addWidget(vc_btn)
        
        vc_group.setLayout(vc_layout)
        layout.addWidget(vc_group)
        
        self.progress = QProgressBar()
        layout.addWidget(self.progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_settings_tab(self):
        """Ayarlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        info_label = QLabel(
            f"<b>{APP_NAME} v{APP_VERSION}</b><br><br>"
            "Nişanlın için yapılmış profesyonel video düzenleme aracı<br><br>"
            "Özellikler:<br>"
            "• Video kırpma<br>"
            "• Ses çıkarma<br>"
            "• Gürültü azaltma<br>"
            "• Ses ekleme<br>"
            "• Otomatik altyazı (Whisper)<br>"
            "• Metin-ses sentezi (XTTS v2)<br><br>"
            "Geliştirilmekte: Voicecraft entegrasyonu"
        )
        layout.addWidget(info_label)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def on_video_dropped(self, file_path: str):
        """Sürükle-bırak ile video yüklendi"""
        self.load_video_internal(file_path)
    
    def load_video(self):
        """Video dosyası yükle (dialog ile)"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Video Seç",
            "",
            "Video Dosyaları (*.mp4 *.mov *.avi);;Tüm Dosyalar (*)"
        )
        
        if file_path:
            self.load_video_internal(file_path)
    
    def load_video_internal(self, file_path: str):
        """Video'yu iç olarak yükle"""
        try:
            self.current_video_path = file_path
            handler = VideoHandler(file_path)
            info = handler.get_info()
            
            duration = info['duration_seconds']
            self.trim_end.setValue(duration)
            
            # Timeline widget'ı oluştur
            if self.timeline_widget:
                self.timeline_widget.close()
            
            self.timeline_widget = VideoTimelineWidget(file_path)
            
            # Eski layout'u temizle
            while self.timeline_container_layout.count():
                self.timeline_container_layout.takeAt(0).widget().deleteLater()
            
            self.timeline_container_layout.addWidget(self.timeline_widget)
            
            # Timeline slider'larını spinbox'lara bağla (senkronizasyon)
            # Slider değeri frame numarası, FPS ile bölüp saniyeye çevir
            fps = self.timeline_widget.fps
            self.timeline_widget.start_slider.valueChanged.connect(
                lambda v: self.trim_start.blockSignals(True) or self.trim_start.setValue(v / fps) or self.trim_start.blockSignals(False)
            )
            self.timeline_widget.end_slider.valueChanged.connect(
                lambda v: self.trim_end.blockSignals(True) or self.trim_end.setValue(v / fps) or self.trim_end.blockSignals(False)
            )
            
            # Spinbox'ları timeline slider'larına bağla
            # Spinbox değeri saniye, FPS ile çarpıp frame numarasına çevir
            self.trim_start.valueChanged.connect(
                lambda v: self.timeline_widget.start_slider.blockSignals(True) or self.timeline_widget.start_slider.setValue(int(v * fps)) or self.timeline_widget.start_slider.blockSignals(False)
            )
            self.trim_end.valueChanged.connect(
                lambda v: self.timeline_widget.end_slider.blockSignals(True) or self.timeline_widget.end_slider.setValue(int(v * fps)) or self.timeline_widget.end_slider.blockSignals(False)
            )
            
            # Status mesajı
            self.statusBar().showMessage(f"✅ Video yüklendi: {Path(file_path).name} ({duration:.1f}s)")
            logger.info(f"Video yüklendi: {file_path}")
        
        except Exception as e:
            logger.error(f"Video yükleme hatası: {e}")
            self.statusBar().showMessage(f"❌ Hata: {str(e)[:50]}")
    
    def load_video_audio(self, file_path: str = None):
        """Ses işleme sekmesi için video yükle"""
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Video Seç",
                "",
                "Video Dosyaları (*.mp4 *.mov *.avi *.mkv);;Tüm Dosyalar (*)"
            )
        
        if file_path:
            self.load_video_audio_internal(file_path)
    
    def load_video_audio_internal(self, file_path: str):
        """Ses işleme sekmesi için video'yu iç olarak yükle"""
        try:
            self.audio_video_path = file_path
            handler = VideoHandler(file_path)
            info = handler.get_info()
            
            duration = info['duration_seconds']
            self.audio_extract_end.setValue(duration)
            
            # Timeline widget'ı oluştur
            if self.audio_timeline_widget:
                self.audio_timeline_widget.close()
            
            self.audio_timeline_widget = VideoTimelineWidget(file_path)
            
            # Eski layout'u temizle
            while self.audio_timeline_container_layout.count():
                self.audio_timeline_container_layout.takeAt(0).widget().deleteLater()
            
            self.audio_timeline_container_layout.addWidget(self.audio_timeline_widget)
            
            # Timeline slider'larını spinbox'lara bağla (senkronizasyon)
            fps = self.audio_timeline_widget.fps
            self.audio_timeline_widget.start_slider.valueChanged.connect(
                lambda v: self.audio_extract_start.blockSignals(True) or self.audio_extract_start.setValue(v / fps) or self.audio_extract_start.blockSignals(False)
            )
            self.audio_timeline_widget.end_slider.valueChanged.connect(
                lambda v: self.audio_extract_end.blockSignals(True) or self.audio_extract_end.setValue(v / fps) or self.audio_extract_end.blockSignals(False)
            )
            
            # Spinbox'ları timeline slider'larına bağla
            self.audio_extract_start.valueChanged.connect(
                lambda v: self.audio_timeline_widget.start_slider.blockSignals(True) or self.audio_timeline_widget.start_slider.setValue(int(v * fps)) or self.audio_timeline_widget.start_slider.blockSignals(False)
            )
            self.audio_extract_end.valueChanged.connect(
                lambda v: self.audio_timeline_widget.end_slider.blockSignals(True) or self.audio_timeline_widget.end_slider.setValue(int(v * fps)) or self.audio_timeline_widget.end_slider.blockSignals(False)
            )
            
            # Status mesajı
            self.statusBar().showMessage(f"✅ Video yüklendi (Ses): {Path(file_path).name} ({duration:.1f}s)")
            logger.info(f"Ses sekmesi için video yüklendi: {file_path}")
        
        except Exception as e:
            logger.error(f"Video yükleme hatası (Ses): {e}")
            self.statusBar().showMessage(f"❌ Hata: {str(e)[:50]}")
    
    def trim_video(self):
        """Video kırp"""
        if not self.current_video_path:
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return
        
        # Timeline'dan değerleri al (varsa), yoksa manual girdileri kullan
        if self.timeline_widget:
            start_time, end_time = self.timeline_widget.get_start_end_seconds()
        else:
            start_time = self.trim_start.value()
            end_time = self.trim_end.value()
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Kırpılmış Videoyu Kaydet",
            "",
            "MP4 Dosyası (*.mp4);;MOV Dosyası (*.mov)"
        )
        
        if output_path:
            logger.info(f"Video kırpma başlatılıyor: {start_time}s - {end_time}s")
            self.statusBar().showMessage("Video kırpılıyor... (biraz zaman alabilir)")
            
            trimmer = VideoTrimmer()
            success = trimmer.trim(
                self.current_video_path,
                output_path,
                start_time,
                end_time
            )
            
            if success:
                self.statusBar().showMessage(f"✅ Video başarıyla kırpıldı: {Path(output_path).name}")
            else:
                self.statusBar().showMessage("❌ Video kırpılamadı")
    
    def extract_audio_video(self):
        """Ses ve/veya video'yu indir (checkbox'a göre)"""
        # Hangi sekmede olduğunu kontrol et
        current_tab = self.tabs.currentIndex()
        
        # Ses sekmesi (index 1) ise audio timeline'ını kullan
        if current_tab == 1 and self.audio_timeline_widget:
            video_path = self.audio_video_path if hasattr(self, 'audio_video_path') else None
            start_time, end_time = self.audio_timeline_widget.get_start_end_seconds()
        elif self.timeline_widget:
            video_path = self.current_video_path
            start_time, end_time = self.timeline_widget.get_start_end_seconds()
        else:
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return
        
        download_audio = self.extract_audio_checkbox.isChecked()
        download_video = self.extract_video_checkbox.isChecked()
        
        if not download_audio and not download_video:
            self.statusBar().showMessage("Lütfen indirmek istediğiniz dosya türünü seçin")
            return
        
        # Ses indir
        if download_audio:
            video_name = Path(video_path).stem
            default_path = str(Path.home() / "Desktop" / f"{video_name}_audio.wav")
            
            output_audio_path, _ = QFileDialog.getSaveFileName(
                self,
                "Ses Dosyasını Kaydet",
                default_path,
                "WAV Dosyası (*.wav);;MP3 Dosyası (*.mp3)"
            )
            
            if output_audio_path:
                logger.info(f"Ses çıkarma başlatılıyor: {video_path} ({start_time:.1f}s - {end_time:.1f}s)")
                self.statusBar().showMessage("Ses çıkarılıyor... (biraz zaman alabilir)")
                
                extractor = AudioExtractor()
                success = extractor.extract(video_path, output_audio_path, start_time, end_time)
                
                if success:
                    self.current_audio_path = output_audio_path
                    self.statusBar().showMessage(f"✅ Ses başarıyla çıkarıldı: {Path(output_audio_path).name}")
                else:
                    self.statusBar().showMessage("❌ Ses çıkarılamadı")
        
        # Video indir
        if download_video:
            video_name = Path(video_path).stem
            default_path = str(Path.home() / "Desktop" / f"{video_name}_trimmed.mp4")
            
            output_video_path, _ = QFileDialog.getSaveFileName(
                self,
                "Video Dosyasını Kaydet",
                default_path,
                "MP4 Dosyası (*.mp4);;MOV Dosyası (*.mov)"
            )
            
            if output_video_path:
                logger.info(f"Sessiz video kırpması başlatılıyor: {video_path} ({start_time:.1f}s - {end_time:.1f}s)")
                self.statusBar().showMessage("Sessiz video kırpılıyor... (biraz zaman alabilir)")
                
                trimmer = VideoTrimmer()
                success = trimmer.trim_silent(video_path, output_video_path, start_time, end_time)
                
                if success:
                    self.statusBar().showMessage(f"✅ Sessiz video başarıyla kırpıldı: {Path(output_video_path).name}")
                else:
                    self.statusBar().showMessage("❌ Video kırpılamadı")
    
    def reduce_noise(self):
        """Gürültü azalt"""
        if not self.current_audio_path:
            self.statusBar().showMessage("Lütfen önce bir video seçip ses çıkarın")
            return
        
        audio_name = Path(self.current_audio_path).stem
        default_path = str(Path.home() / "Desktop" / f"{audio_name}_denoised.wav")
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Temiz Sesi Kaydet",
            default_path,
            "WAV Dosyası (*.wav)"
        )
        
        if output_path:
            self.statusBar().showMessage("Gürültü azaltılıyor... (biraz zaman alabilir)")
            logger.info(f"Gürültü azaltma başlatılıyor...")
            
            reducer = NoiseReducer()
            success = reducer.reduce_noise(
                self.current_audio_path,
                output_path,
                reduction_strength=self.denoise_strength.value()
            )
            
            if success:
                self.current_audio_path = output_path
                self.statusBar().showMessage(f"✅ Gürültü azaltıldı: {Path(output_path).name}")
            else:
                self.statusBar().showMessage("❌ Gürültü azaltılamadı")
    
    def mix_audio(self):
        """Ses karıştır"""
        self.statusBar().showMessage("Ses karıştırma özelliği yakında eklenecek")
    
    def generate_subtitles(self):
        """Otomatik altyazı oluştur"""
        if not self.current_audio_path:
            self.statusBar().showMessage("Lütfen önce bir video seçip ses çıkarın")
            return
        
        audio_name = Path(self.current_audio_path).stem
        default_path = str(Path.home() / "Desktop" / f"{audio_name}.srt")
        
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Altyazıları Kaydet",
            default_path,
            "SRT Dosyası (*.srt)"
        )
        
        if output_path:
            self.statusBar().showMessage("Altyazılar oluşturuluyor... (2-3 dakika alabilir)")
            logger.info(f"Altyazı oluşturma başlatılıyor: {self.current_audio_path}")
            
            try:
                from ai_module import SpeechRecognizer
                recognizer = SpeechRecognizer()
                success = recognizer.save_srt(self.current_audio_path, output_path)
                
                if success:
                    self.statusBar().showMessage(f"✅ Altyazılar oluşturuldu: {Path(output_path).name}")
                else:
                    self.statusBar().showMessage("❌ Altyazılar oluşturulamadı")
            except Exception as e:
                logger.error(f"Altyazı oluşturulamadı: {e}")
                self.statusBar().showMessage(f"❌ Hata: {str(e)[:50]}")

