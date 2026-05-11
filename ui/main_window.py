"""
Main Window - Ana arayüz
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QSpinBox, QDoubleSpinBox,
    QFileDialog, QProgressBar, QStackedWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QComboBox, QCheckBox, QFrame,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap

from utils.logger import setup_logger
from utils.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, APP_NAME, APP_VERSION, TEMP_DIR
)
from video_processor import (
    VideoHandler, VideoTrimmer, AudioExtractor,
    NoiseReducer, AudioMixer, VideoExporter
)
from .widgets import MediaFileDropper, VideoTimelineWidget

logger = setup_logger(__name__)

# Premium Dark Theme QSS
PREMIUM_DARK_THEME = """
/* Ana Pencere */
QMainWindow {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}

/* Sidebar */
#sidebar {
    background-color: #181818;
    border-right: 1px solid #262626;
}

#sidebar QPushButton {
    background-color: transparent;
    color: #a0a0a0;
    text-align: left;
    padding: 14px 20px;
    border: none;
    border-radius: 8px;
    font-size: 15px;
    margin: 4px 12px;
}

#sidebar QPushButton:hover {
    background-color: #242424;
    color: #ffffff;
}

#sidebar QPushButton:checked {
    background-color: #292929;
    color: #00a8ff; /* Accent color */
    font-weight: bold;
    border-left: 4px solid #00a8ff;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

/* Content Area */
#content_area {
    background-color: #121212;
}

/* GroupBox */
QGroupBox {
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    margin-top: 25px;
    padding-top: 15px;
    font-weight: bold;
    color: #ffffff;
    background-color: #1a1a1a;
    font-size: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 15px;
    color: #00a8ff;
    background-color: #1a1a1a;
    border-radius: 4px;
}

/* Buttons */
QPushButton {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: 1px solid #3d3d3d;
    border-radius: 6px;
    padding: 10px 18px;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #383838;
    border: 1px solid #4d4d4d;
}

QPushButton:pressed {
    background-color: #252525;
}

/* Primary Action Button */
QPushButton#primary_action {
    background-color: #0078d7;
    color: white;
    border: none;
    font-weight: bold;
    font-size: 14px;
}

QPushButton#primary_action:hover {
    background-color: #1084ea;
}

QPushButton#primary_action:pressed {
    background-color: #0060ad;
}

/* SpinBox */
QDoubleSpinBox, QSpinBox {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 6px;
    font-size: 13px;
}

QDoubleSpinBox:focus, QSpinBox:focus {
    border: 1px solid #00a8ff;
}

/* Labels */
QLabel {
    color: #cccccc;
}

/* CheckBox */
QCheckBox {
    color: #cccccc;
    spacing: 8px;
    font-size: 13px;
}
QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 1px solid #444;
    background-color: #1e1e1e;
}
QCheckBox::indicator:hover {
    border: 1px solid #00a8ff;
}
QCheckBox::indicator:checked {
    background-color: #00a8ff;
    border: 1px solid #00a8ff;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #2a2a2a;
    border-radius: 4px;
    text-align: center;
    background-color: #1a1a1a;
    color: white;
    height: 18px;
}
QProgressBar::chunk {
    background-color: #00a8ff;
    border-radius: 3px;
}
"""

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
        self.setStyleSheet(PREMIUM_DARK_THEME)
        
        # Ana widget
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 30, 0, 20)
        sidebar_layout.setSpacing(5)
        
        # App Title in Sidebar
        title_label = QLabel("🦈 " + APP_NAME)
        title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; padding-left: 15px; margin-bottom: 30px;")
        sidebar_layout.addWidget(title_label)
        
        # Navigation Buttons
        self.nav_buttons = []
        
        self.btn_video = QPushButton("📹 Video İşleme")
        self.btn_audio = QPushButton("🔊 Ses İşleme")
        self.btn_ai = QPushButton("🤖 AI Araçları")
        self.btn_settings = QPushButton("⚙️ Ayarlar")
        
        for btn in [self.btn_video, self.btn_audio, self.btn_ai, self.btn_settings]:
            btn.setCheckable(True)
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)
            
        sidebar_layout.addStretch()
        
        # Version Label
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: #666666; padding-left: 20px;")
        sidebar_layout.addWidget(version_label)
        
        # Content Area
        self.content_area = QWidget()
        self.content_area.setObjectName("content_area")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        # Add Pages
        self.stacked_widget.addWidget(self._create_video_tab())
        self.stacked_widget.addWidget(self._create_audio_tab())
        self.stacked_widget.addWidget(self._create_ai_tab())
        self.stacked_widget.addWidget(self._create_settings_tab())
        
        # Connections
        self.btn_video.clicked.connect(lambda: self.switch_page(0))
        self.btn_audio.clicked.connect(lambda: self.switch_page(1))
        self.btn_ai.clicked.connect(lambda: self.switch_page(2))
        self.btn_settings.clicked.connect(lambda: self.switch_page(3))
        
        # Init state
        self.switch_page(0)
        
        # Status bar styling
        self.statusBar().setStyleSheet("background-color: #181818; color: #a0a0a0; padding-left: 10px; border-top: 1px solid #262626;")
        self.statusBar().showMessage("Hazır")

    def switch_page(self, index):
        """Sayfa değiştir ve sidebar buton state'ini güncelle"""
        self.stacked_widget.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
    
    def _create_video_tab(self):
        """Video işleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("Video İşleme")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Sürükle-bırak video yükleme
        load_group = QGroupBox("1. Video Yükle")
        load_layout = QVBoxLayout()
        load_layout.setSpacing(15)
        
        self.drag_drop_widget = MediaFileDropper()
        self.drag_drop_widget.file_dropped.connect(self.on_video_dropped)
        load_layout.addWidget(self.drag_drop_widget)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Video kırpma (timeline preview ile)
        trim_group = QGroupBox("2. Video Kırpma")
        trim_layout = QVBoxLayout()
        trim_layout.setSpacing(15)
        
        # Timeline widget (video yüklendikten sonra gösterilecek)
        self.timeline_widget = None
        self.timeline_container = QWidget()
        self.timeline_container_layout = QVBoxLayout()
        self.timeline_container_layout.setContentsMargins(0, 0, 0, 0)
        self.timeline_container.setLayout(self.timeline_container_layout)
        trim_layout.addWidget(self.timeline_container)
        
        # Manuel giriş (timeline yüklü değilse)
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Başlangıç (s):"))
        self.trim_start = QDoubleSpinBox()
        self.trim_start.setMaximum(10000)
        manual_layout.addWidget(self.trim_start)
        
        manual_layout.addSpacing(20)
        
        manual_layout.addWidget(QLabel("Bitiş (s):"))
        self.trim_end = QDoubleSpinBox()
        self.trim_end.setMaximum(10000)
        self.trim_end.setValue(10)
        manual_layout.addWidget(self.trim_end)
        manual_layout.addStretch()
        trim_layout.addLayout(manual_layout)
        
        trim_btn = QPushButton("✂️ Video Kırp")
        trim_btn.setObjectName("primary_action")
        trim_btn.clicked.connect(self.trim_video)
        trim_layout.addWidget(trim_btn)
        
        trim_group.setLayout(trim_layout)
        layout.addWidget(trim_group)
        
        # Progress bar
        self.video_progress = QProgressBar()
        self.video_progress.hide()
        layout.addWidget(self.video_progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_audio_tab(self):
        """Ses işleme sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("Ses İşleme")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Video yükleme (Ses İşleme sekmesi için)
        load_group_audio = QGroupBox("1. Video Yükle")
        load_layout_audio = QVBoxLayout()
        load_layout_audio.setSpacing(15)
        
        # Sürükle-bırak widget
        self.drag_drop_audio = MediaFileDropper()
        self.drag_drop_audio.file_dropped.connect(
            lambda path: self.load_video_audio(path)
        )
        load_layout_audio.addWidget(self.drag_drop_audio)
        
        load_group_audio.setLayout(load_layout_audio)
        layout.addWidget(load_group_audio)
        
        # Video timeline (ses işleme için)
        self.audio_timeline_widget = None
        self.audio_timeline_container = QWidget()
        self.audio_timeline_container_layout = QVBoxLayout()
        self.audio_timeline_container_layout.setContentsMargins(0, 0, 0, 0)
        self.audio_timeline_container.setLayout(self.audio_timeline_container_layout)
        layout.addWidget(self.audio_timeline_container)
        
        # Horizontal Layout for Tools
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(20)
        
        # Ses çıkarma
        extract_group = QGroupBox("2. Ses İşlemleri")
        extract_layout = QVBoxLayout()
        extract_layout.setSpacing(15)
        
        extract_layout.addWidget(QLabel("Çıkartılacak aralık:"))
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
        checkbox_layout = QVBoxLayout()
        self.extract_audio_checkbox = QCheckBox("📢 Sesi İndir (WAV/MP3)")
        self.extract_audio_checkbox.setChecked(True)
        self.extract_video_checkbox = QCheckBox("🎬 Sessiz Videoyu İndir")
        checkbox_layout.addWidget(self.extract_audio_checkbox)
        checkbox_layout.addWidget(self.extract_video_checkbox)
        extract_layout.addLayout(checkbox_layout)
        
        extract_btn = QPushButton("📥 Seçilenleri İndir")
        extract_btn.setObjectName("primary_action")
        extract_btn.clicked.connect(self.extract_audio_video)
        extract_layout.addWidget(extract_btn)
        
        extract_group.setLayout(extract_layout)
        tools_layout.addWidget(extract_group)
        
        # Gürültü azaltma
        right_tools_layout = QVBoxLayout()
        
        denoise_group = QGroupBox("3. Gürültü Azaltma")
        denoise_layout = QVBoxLayout()
        denoise_layout.setSpacing(15)
        
        strength_layout = QHBoxLayout()
        strength_layout.addWidget(QLabel("Filtre Gücü:"))
        self.denoise_strength = QDoubleSpinBox()
        self.denoise_strength.setMinimum(0)
        self.denoise_strength.setMaximum(1)
        self.denoise_strength.setValue(0.8)
        self.denoise_strength.setSingleStep(0.1)
        strength_layout.addWidget(self.denoise_strength)
        denoise_layout.addLayout(strength_layout)

        auto_strength_btn = QPushButton("🤖 Otomatik Güç Algıla")
        auto_strength_btn.clicked.connect(self.auto_set_denoise_strength)
        denoise_layout.addWidget(auto_strength_btn)

        self.denoise_metrics_label = QLabel("SNR: - dB | Kalite: -/5")
        self.denoise_metrics_label.setStyleSheet("color: #888;")
        denoise_layout.addWidget(self.denoise_metrics_label)
        
        denoise_btn = QPushButton("🔇 Gürültüyü Temizle")
        denoise_btn.setObjectName("primary_action")
        denoise_btn.clicked.connect(self.reduce_noise)
        denoise_layout.addWidget(denoise_btn)
        
        denoise_group.setLayout(denoise_layout)
        right_tools_layout.addWidget(denoise_group)
        
        # Ses karıştırma
        mix_group = QGroupBox("4. Ses Ekleme")
        mix_layout = QVBoxLayout()
        mix_btn = QPushButton("🎵 Arka Plan Sesi Ekle (Yakında)")
        mix_btn.clicked.connect(self.mix_audio)
        mix_layout.addWidget(mix_btn)
        mix_group.setLayout(mix_layout)
        right_tools_layout.addWidget(mix_group)
        
        right_tools_layout.addStretch()
        tools_layout.addLayout(right_tools_layout)
        
        layout.addLayout(tools_layout)
        
        self.audio_progress = QProgressBar()
        self.audio_progress.hide()
        layout.addWidget(self.audio_progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_ai_tab(self):
        """AI araçları sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("AI Araçları")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Otomatik altyazı
        subtitle_group = QGroupBox("Otomatik Altyazı (Whisper)")
        subtitle_layout = QVBoxLayout()
        subtitle_layout.setSpacing(15)
        
        subtitle_info = QLabel("Videonuzdaki sesi analiz edip saniyeler içinde SRT altyazı dosyası üretir.")
        subtitle_info.setWordWrap(True)
        subtitle_layout.addWidget(subtitle_info)
        
        subtitle_btn = QPushButton("📝 Altyazı Oluştur")
        subtitle_btn.setObjectName("primary_action")
        subtitle_btn.clicked.connect(self.generate_subtitles)
        subtitle_layout.addWidget(subtitle_btn)
        
        subtitle_group.setLayout(subtitle_layout)
        layout.addWidget(subtitle_group)
        
        # XTTS
        tts_group = QGroupBox("Metin-Ses (XTTS v2)")
        tts_layout = QVBoxLayout()
        tts_layout.setSpacing(15)
        
        tts_info = QLabel("Gelişmiş AI ses klonlama teknolojisi. Metninizi seçilen sesle okutun. (Çok Yakında)")
        tts_info.setWordWrap(True)
        tts_layout.addWidget(tts_info)
        
        tts_btn = QPushButton("🎤 Metni Sese Dönüştür")
        tts_btn.setEnabled(False)
        tts_layout.addWidget(tts_btn)
        
        tts_group.setLayout(tts_layout)
        layout.addWidget(tts_group)
        
        # Voicecraft
        vc_group = QGroupBox("Ses Klonlama (Voicecraft)")
        vc_layout = QVBoxLayout()
        vc_layout.setSpacing(15)
        
        vc_btn = QPushButton("🎧 Ses Klonla (Hazırlanıyor)")
        vc_btn.setEnabled(False)
        vc_layout.addWidget(vc_btn)
        
        vc_group.setLayout(vc_layout)
        layout.addWidget(vc_group)
        
        self.ai_progress = QProgressBar()
        self.ai_progress.hide()
        layout.addWidget(self.ai_progress)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_settings_tab(self):
        """Ayarlar sekmesi"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        title = QLabel("Hakkında & Ayarlar")
        title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        info_group = QGroupBox("Uygulama Bilgileri")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)
        
        info_label = QLabel(
            f"<h2 style='color:#00a8ff; margin:0;'>{APP_NAME}</h2>"
            f"<p style='color:#888; margin:0;'>Versiyon {APP_VERSION}</p><br>"
            "<p>Nişanlın için yapılmış profesyonel video düzenleme aracı. Modern, hızlı ve kullanışlı.</p>"
            "<ul>"
            "<li>Gelişmiş video kırpma</li>"
            "<li>Hızlı ses çıkarma ve karıştırma</li>"
            "<li>AI destekli gürültü azaltma</li>"
            "<li>Whisper ile otomatik altyazı üretimi</li>"
            "</ul>"
            "<br><p><i>Geliştirilmekte: XTTS v2 ve Voicecraft entegrasyonu</i></p>"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 14px; line-height: 1.5;")
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)
        
        layout.addWidget(info_group)
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
            "Video Dosyaları (*.mp4 *.mov *.avi *.mkv);;Tüm Dosyalar (*)"
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
        current_tab = self.stacked_widget.currentIndex()
        
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

    def _ensure_current_audio_path(self) -> bool:
        """Gerekirse seçili videodan geçici ses çıkarıp current_audio_path set eder."""
        if self.current_audio_path:
            return True

        video_path = None
        start_time = 0.0
        end_time = None

        # Öncelik: Ses sekmesinde yüklü video
        if hasattr(self, 'audio_video_path') and self.audio_video_path:
            video_path = self.audio_video_path
            if self.audio_timeline_widget:
                start_time, end_time = self.audio_timeline_widget.get_start_end_seconds()
        elif self.current_video_path:
            video_path = self.current_video_path
            if self.timeline_widget:
                start_time, end_time = self.timeline_widget.get_start_end_seconds()

        if not video_path:
            return False

        try:
            TEMP_DIR.mkdir(exist_ok=True)
            tmp_audio_path = str(TEMP_DIR / f"{Path(video_path).stem}_auto_audio.wav")
            self.statusBar().showMessage("Ses çıkarılıyor... (gürültü azaltma için)")
            extractor = AudioExtractor()
            success = extractor.extract(video_path, tmp_audio_path, float(start_time), end_time)
            if success:
                self.current_audio_path = tmp_audio_path
                return True
            return False
        except Exception as e:
            logger.error(f"Otomatik ses çıkarma hatası: {e}")
            return False
    
    def reduce_noise(self):
        """Gürültü azalt"""
        if not self._ensure_current_audio_path():
            self.statusBar().showMessage("Lütfen önce bir video seçin")
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
            result = reducer.reduce_noise(
                self.current_audio_path,
                output_path,
                reduction_strength=self.denoise_strength.value(),
                get_metrics=True
            )
            
            if isinstance(result, dict) and result.get("success"):
                self.current_audio_path = output_path
                metrics = result.get("metrics") or {}
                if metrics:
                    snr_db = metrics.get("snr_db")
                    quality = metrics.get("quality_score")
                    self.denoise_metrics_label.setText(f"SNR: {snr_db:.1f} dB | Kalite: {quality:.2f}/5")
                self.statusBar().showMessage(f"✅ Gürültü azaltıldı: {Path(output_path).name}")
            else:
                error_msg = result.get("error") if isinstance(result, dict) else None
                self.statusBar().showMessage("❌ Gürültü azaltılamadı" + (f": {error_msg}" if error_msg else ""))

    def auto_set_denoise_strength(self):
        """Gürültü azaltma gücünü otomatik ayarla"""
        if not self._ensure_current_audio_path():
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return

        try:
            strength = NoiseReducer.auto_detect_strength(self.current_audio_path)
            self.denoise_strength.setValue(float(strength))
            self.statusBar().showMessage(f"🤖 Otomatik güç ayarlandı: {strength:.2f}")
        except Exception as e:
            logger.error(f"Otomatik güç ayarı UI hata: {e}")
            self.statusBar().showMessage("❌ Otomatik güç ayarlanamadı")
    
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
