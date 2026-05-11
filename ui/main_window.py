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
    QSpacerItem, QSizePolicy, QSplitter
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
from .widgets import MediaPoolWidget, AdvancedVideoTrimmer

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

/* Splitter */
QSplitter::handle {
    background-color: #1e1e1e;
}
QSplitter::handle:horizontal {
    width: 2px;
}
QSplitter::handle:vertical {
    height: 2px;
}
QSplitter::handle:hover {
    background-color: #00a8ff;
}
QSplitter::handle:horizontal:hover {
    cursor: split-h;
}
QSplitter::handle:vertical:hover {
    cursor: split-v;
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

class DenoiseWorker(QThread):
    finished = pyqtSignal(object)
    
    def __init__(self, audio_path, output_path, strength):
        super().__init__()
        self.audio_path = audio_path
        self.output_path = output_path
        self.strength = strength
        
    def run(self):
        from video_processor.noise_reducer import NoiseReducer
        reducer = NoiseReducer()
        result = reducer.reduce_noise(
            self.audio_path,
            self.output_path,
            reduction_strength=self.strength,
            get_metrics=True
        )
        self.finished.emit(result)

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
        
        # Pencere ikonu ayarla
        icon_path = Path("img/logo-small.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            
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
        
        # App Title / Logo in Sidebar
        logo_label = QLabel()
        logo_path = Path("img/logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            scaled_pixmap = pixmap.scaledToHeight(125, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("padding-left: 10px; margin-bottom: 30px;")
        else:
            logo_label.setText("🦈 " + APP_NAME)
            logo_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
            logo_label.setStyleSheet("color: #ffffff; padding-left: 15px; margin-bottom: 30px;")
        
        sidebar_layout.addWidget(logo_label)
        
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
        
        # Main Splitter (3 Columns)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Add Column 1: Sidebar
        self.main_splitter.addWidget(self.sidebar)
        
        # Add Column 2: Media Pool
        self.media_pool = MediaPoolWidget()
        self.media_pool.media_selected.connect(self.on_media_selected)
        self.media_pool.setMinimumWidth(250)
        self.main_splitter.addWidget(self.media_pool)
        
        # Add Column 3: Workspace (Content Area)
        self.content_area = QWidget()
        self.content_area.setObjectName("content_area")
        content_layout = QVBoxLayout(self.content_area)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        self.main_splitter.addWidget(self.content_area)
        
        # Set Proportions
        self.main_splitter.setStretchFactor(0, 0) # Sidebar fixed
        self.main_splitter.setStretchFactor(1, 1) # Media Pool stretches slightly
        self.main_splitter.setStretchFactor(2, 4) # Workspace gets max stretch
        self.main_splitter.setSizes([260, 300, 1000])
        
        main_layout.addWidget(self.main_splitter)
        
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
        
        # Video kırpma (timeline preview ile)
        trim_group = QGroupBox("1. Video Kırpma")
        trim_layout = QVBoxLayout()
        trim_layout.setSpacing(15)
        
        # Advanced Timeline and Preview widget
        self.timeline_widget = AdvancedVideoTrimmer()
        trim_layout.addWidget(self.timeline_widget)
        
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
        
        # Ses İşlemleri Başlangıcı
        
        # Advanced Timeline and Preview widget
        self.audio_timeline_widget = AdvancedVideoTrimmer()
        layout.addWidget(self.audio_timeline_widget)
        
        # Horizontal Layout for Tools
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(20)
        
        # Ses çıkarma
        extract_group = QGroupBox("1. Ses İşlemleri")
        extract_layout = QVBoxLayout()
        extract_layout.setSpacing(15)
        
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
        
        denoise_group = QGroupBox("2. Gürültü Azaltma")
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
        
        # A/B Toggle Switch
        self.ab_toggle_layout = QHBoxLayout()
        self.btn_original = QPushButton("Orijinal")
        self.btn_denoised = QPushButton("Temizlenmiş")
        self.btn_original.setCheckable(True)
        self.btn_denoised.setCheckable(True)
        self.btn_original.setChecked(True)
        self.btn_denoised.setEnabled(False) # Disabled until processed
        
        segmented_style = """
            QPushButton {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                padding: 5px 10px;
                color: #888;
                border-radius: 4px;
                font-weight: normal;
            }
            QPushButton:checked {
                background-color: #00a8ff;
                color: white;
                border: 1px solid #00a8ff;
                font-weight: bold;
            }
        """
        self.btn_original.setStyleSheet(segmented_style)
        self.btn_denoised.setStyleSheet(segmented_style)
        
        self.btn_original.clicked.connect(lambda: self.toggle_ab_mode(False))
        self.btn_denoised.clicked.connect(lambda: self.toggle_ab_mode(True))
        
        self.ab_toggle_layout.addWidget(self.btn_original)
        self.ab_toggle_layout.addWidget(self.btn_denoised)
        denoise_layout.addLayout(self.ab_toggle_layout)
        
        self.btn_denoise = QPushButton("🔇 Gürültüyü Temizle")
        self.btn_denoise.setObjectName("primary_action")
        self.btn_denoise.clicked.connect(self.reduce_noise)
        denoise_layout.addWidget(self.btn_denoise)
        
        denoise_group.setLayout(denoise_layout)
        right_tools_layout.addWidget(denoise_group)
        
        # Ses karıştırma
        mix_group = QGroupBox("3. Ses Ekleme")
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
    
    def on_media_selected(self, file_path: str):
        """Media Pool'dan dosya seçildiğinde aktif sekmeye yükle"""
        current_tab = self.stacked_widget.currentIndex()
        if current_tab == 0: # Video İşleme
            self.load_video_internal(file_path)
        elif current_tab == 1: # Ses İşleme
            self.load_video_audio_internal(file_path)
        else:
            self.statusBar().showMessage("Medya eklemek için Video veya Ses İşleme sekmesine gidin.")
    
    def load_video_internal(self, file_path: str):
        """Video'yu iç olarak yükle"""
        try:
            self.current_video_path = file_path
            handler = VideoHandler(file_path)
            info = handler.get_info()
            
            duration = info['duration_seconds']
            
            # Load video into advanced trimmer
            self.timeline_widget.load_video(file_path)
            
            # Status mesajı
            self.statusBar().showMessage(f"✅ Video yüklendi: {Path(file_path).name} ({duration:.1f}s)")
            logger.info(f"Video yüklendi: {file_path}")
        
        except Exception as e:
            logger.error(f"Video yükleme hatası: {e}")
            self.statusBar().showMessage(f"❌ Hata: {str(e)[:50]}")
    
    # load_video_audio removed as handled by Media Pool
    
    def load_video_audio_internal(self, file_path: str):
        """Ses işleme sekmesi için video'yu iç olarak yükle"""
        try:
            self.audio_video_path = file_path
            handler = VideoHandler(file_path)
            info = handler.get_info()
            
            duration = info['duration_seconds']
            
            # Load video into advanced trimmer
            self.audio_timeline_widget.load_video(file_path)
            
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
        
        # Timeline'dan değerleri al
        start_time, end_time = self.timeline_widget.get_start_end_seconds()
        
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
        """Gürültü azalt (Arka planda)"""
        if not self._ensure_current_audio_path():
            self.statusBar().showMessage("Lütfen önce bir video seçin")
            return
        
        default_path = str(TEMP_DIR / f"preview_denoised.wav")
        
        self.statusBar().showMessage("Gürültü azaltılıyor... (biraz zaman alabilir)")
        self.btn_denoise.setText("⏳ İşleniyor...")
        self.btn_denoise.setEnabled(False)
        self.btn_original.setEnabled(False)
        self.btn_denoised.setEnabled(False)
        
        self.denoise_worker = DenoiseWorker(
            self.current_audio_path,
            default_path,
            self.denoise_strength.value()
        )
        self.denoise_worker.finished.connect(lambda res: self.on_denoise_finished(res, default_path))
        self.denoise_worker.start()

    def on_denoise_finished(self, result, output_path):
        self.btn_denoise.setText("🔇 Gürültüyü Temizle")
        self.btn_denoise.setEnabled(True)
        
        if isinstance(result, dict) and result.get("success"):
            metrics = result.get("metrics") or {}
            if metrics:
                snr_db = metrics.get("snr_db")
                quality = metrics.get("quality_score")
                self.denoise_metrics_label.setText(f"SNR: {snr_db:.1f} dB | Kalite: {quality:.2f}/5")
            self.statusBar().showMessage(f"✅ Gürültü azaltıldı! A/B modunu kullanarak karşılaştırabilirsiniz.")
            
            # Enable A/B testing
            self.btn_original.setEnabled(True)
            self.btn_denoised.setEnabled(True)
            self.btn_denoised.setChecked(True)
            self.toggle_ab_mode(True, output_path)
        else:
            error_msg = result.get("error") if isinstance(result, dict) else None
            self.statusBar().showMessage("❌ Gürültü azaltılamadı" + (f": {error_msg}" if error_msg else ""))
            self.btn_original.setChecked(True)
            self.toggle_ab_mode(False)

    def toggle_ab_mode(self, use_denoised, alt_path=None):
        if not hasattr(self, 'audio_timeline_widget'): return
        
        if use_denoised:
            self.btn_denoised.setChecked(True)
            self.btn_original.setChecked(False)
            if alt_path:
                self.audio_timeline_widget.enable_ab_mode(alt_path)
            self.audio_timeline_widget.switch_audio(True)
        else:
            self.btn_original.setChecked(True)
            self.btn_denoised.setChecked(False)
            self.audio_timeline_widget.switch_audio(False)

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
