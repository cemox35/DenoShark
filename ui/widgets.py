"""
Custom Widgets - Özel PyQt6 bileşenleri
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QSpinBox, QFrame, QFileDialog, QPushButton, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QRect, QPoint, QSize, QUrl
from PyQt6.QtGui import QPixmap, QImage, QDrag, QPainter, QColor, QBrush, QPen, QPalette, QIcon
from utils.media_manager import MediaManager
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
import cv2
from pathlib import Path

class MediaFileDropper(QFrame):
    """Sürükle-bırak ve tıklama destekli gelişmiş medya yükleme widget'ı"""
    
    file_dropped = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.init_ui()
    
    def init_ui(self):
        self.setObjectName("media_dropper")
        self.setStyleSheet("""
            #media_dropper {
                background-color: #1e1e1e;
                border: 2px dashed #3a3a3a;
                border-radius: 12px;
            }
            #media_dropper:hover {
                border: 2px dashed #00a8ff;
                background-color: #252525;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
        
        # Icon
        self.icon_label = QLabel("🎬 📥")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px; color: #a0a0a0; background: transparent; border: none;")
        layout.addWidget(self.icon_label)
        
        self.main_label = QLabel("Video Dosyasını Buraya Sürükle veya Tıkla")
        self.main_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff; background: transparent; border: none;")
        layout.addWidget(self.main_label)
        
        self.sub_label = QLabel("Sadece .mp4, .mov, .avi, .mkv")
        self.sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 13px; color: #888888; background: transparent; border: none;")
        layout.addWidget(self.sub_label)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                #media_dropper {
                    background-color: #252525;
                    border: 2px solid #00a8ff;
                    border-radius: 12px;
                }
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            #media_dropper {
                background-color: #1e1e1e;
                border: 2px dashed #3a3a3a;
                border-radius: 12px;
            }
            #media_dropper:hover {
                border: 2px dashed #00a8ff;
                background-color: #252525;
            }
        """)
    
    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if Path(file_path).suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']:
                self.file_dropped.emit(file_path)
                self.main_label.setText(f"✅ Yüklendi: {Path(file_path).name}")
                self.main_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00a8ff; background: transparent; border: none;")
            else:
                self.main_label.setText("❌ Desteklenmeyen format")
                self.main_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff5555; background: transparent; border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Video Seç",
                "",
                "Video Dosyaları (*.mp4 *.mov *.avi *.mkv);;Tüm Dosyalar (*)"
            )
            if file_path:
                self.file_dropped.emit(file_path)
                self.main_label.setText(f"✅ Yüklendi: {Path(file_path).name}")
                self.main_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00a8ff; background: transparent; border: none;")

class RangeSlider(QWidget):
    """Gelişmiş Çift Yönlü Range Slider"""
    rangeChanged = pyqtSignal(float, float, str) # start, end, active_handle ('min' veya 'max')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(40)
        self._current_min = 0.0
        self._current_max = 1.0
        
        self._handle_width = 16
        self._handle_radius = 8
        self._groove_height = 8
        
        self._active_handle = None
        self.setMouseTracking(True)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background groove
        groove_rect = QRect(self._handle_width//2, height//2 - self._groove_height//2, 
                            width - self._handle_width, self._groove_height)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#2a2a2a"))
        painter.drawRoundedRect(groove_rect, 4, 4)
        
        # Active groove (between handles)
        min_x = self._handle_width//2 + int(self._current_min * (width - self._handle_width))
        max_x = self._handle_width//2 + int(self._current_max * (width - self._handle_width))
        
        active_rect = QRect(min_x, height//2 - self._groove_height//2, max_x - min_x, self._groove_height)
        painter.setBrush(QColor("#00a8ff"))
        painter.drawRoundedRect(active_rect, 4, 4)
        
        # Min handle
        min_handle_rect = QRect(min_x - self._handle_width//2, height//2 - 12, self._handle_width, 24)
        if self._active_handle == 'min':
            painter.setBrush(QColor("#ffffff"))
        else:
            painter.setBrush(QColor("#e0e0e0"))
        painter.drawRoundedRect(min_handle_rect, self._handle_radius, self._handle_radius)
        
        # Max handle
        max_handle_rect = QRect(max_x - self._handle_width//2, height//2 - 12, self._handle_width, 24)
        if self._active_handle == 'max':
            painter.setBrush(QColor("#ffffff"))
        else:
            painter.setBrush(QColor("#e0e0e0"))
        painter.drawRoundedRect(max_handle_rect, self._handle_radius, self._handle_radius)
        
    def mousePressEvent(self, event):
        min_x = self._handle_width//2 + int(self._current_min * (self.width() - self._handle_width))
        max_x = self._handle_width//2 + int(self._current_max * (self.width() - self._handle_width))
        
        click_x = event.pos().x()
        
        if abs(click_x - min_x) < 20:
            self._active_handle = 'min'
        elif abs(click_x - max_x) < 20:
            self._active_handle = 'max'
        else:
            self._active_handle = None
            
        self.update()
            
    def mouseMoveEvent(self, event):
        if self._active_handle:
            val = (event.pos().x() - self._handle_width//2) / (self.width() - self._handle_width)
            val = max(0.0, min(1.0, val))
            
            if self._active_handle == 'min':
                self._current_min = min(val, self._current_max - 0.01)
            else:
                self._current_max = max(val, self._current_min + 0.01)
                
            self.update()
            self.rangeChanged.emit(self._current_min, self._current_max, self._active_handle)
            
    def mouseReleaseEvent(self, event):
        self._active_handle = None
        self.update()
        
    def setValues(self, min_val, max_val):
        self._current_min = max(0.0, min(1.0, min_val))
        self._current_max = max(0.0, min(1.0, max_val))
        self.update()

class AdvancedVideoTrimmer(QWidget):
    """Profesyonel video izleme ve kırpma aracı (QMediaPlayer)"""
    
    trim_points_changed = pyqtSignal(float, float) # start_sec, end_sec
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_path = None
        self.duration = 0.0
        self._updating_inputs = False
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Video Player Area
        self.video_container = QFrame()
        self.video_container.setStyleSheet("background-color: #000000; border-radius: 8px; border: 1px solid #2a2a2a;")
        self.video_container.setMinimumHeight(350)
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(2, 2, 2, 2)
        
        self.video_widget = QVideoWidget()
        self.video_widget.hide()
        
        self.placeholder_label = QLabel("🎬\nVideo Önizleme")
        self.placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #555555; font-size: 24px; font-weight: bold; background: transparent; border: none;")
        
        video_layout.addWidget(self.placeholder_label)
        video_layout.addWidget(self.video_widget)
        layout.addWidget(self.video_container)
        
        # Media Player setup
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        
        # Controls Toolbar
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.setStyleSheet("""
            QPushButton { border-radius: 20px; background-color: #2d2d2d; font-size: 18px; color: white; border: none; }
            QPushButton:hover { background-color: #00a8ff; }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setEnabled(False)
        controls_layout.addWidget(self.play_btn)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("font-family: monospace; font-size: 14px; color: #a0a0a0; padding-left: 10px; border: none;")
        controls_layout.addWidget(self.time_label)
        
        controls_layout.addStretch()
        
        self.vol_btn = QPushButton("🔊")
        self.vol_btn.setFixedSize(30, 30)
        self.vol_btn.setStyleSheet("border-radius: 15px; background-color: transparent; font-size: 16px; border: none;")
        self.vol_btn.clicked.connect(self.toggle_mute)
        controls_layout.addWidget(self.vol_btn)
        
        self.vol_slider = QSlider(Qt.Orientation.Horizontal)
        self.vol_slider.setRange(0, 100)
        self.vol_slider.setValue(100)
        self.vol_slider.setFixedWidth(80)
        self.vol_slider.valueChanged.connect(self.set_volume)
        self.vol_slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 4px; background: #2a2a2a; border-radius: 2px; }
            QSlider::handle:horizontal { background: #00a8ff; width: 12px; margin: -4px 0; border-radius: 6px; }
        """)
        controls_layout.addWidget(self.vol_slider)
        
        layout.addLayout(controls_layout)
        
        # Range Slider
        self.range_slider = RangeSlider()
        self.range_slider.rangeChanged.connect(self.on_range_changed)
        self.range_slider.setEnabled(False)
        layout.addWidget(self.range_slider)
        
        # Manual Inputs
        inputs_layout = QHBoxLayout()
        inputs_layout.setContentsMargins(10, 0, 10, 0)
        
        inputs_layout.addWidget(QLabel("Başlangıç:"))
        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0, 10000)
        self.start_spin.setSuffix(" sn")
        self.start_spin.setDecimals(2)
        self.start_spin.setFixedWidth(100)
        self.start_spin.valueChanged.connect(self.on_spin_changed)
        inputs_layout.addWidget(self.start_spin)
        
        inputs_layout.addStretch()
        
        inputs_layout.addWidget(QLabel("Bitiş:"))
        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0, 10000)
        self.end_spin.setSuffix(" sn")
        self.end_spin.setDecimals(2)
        self.end_spin.setFixedWidth(100)
        self.end_spin.valueChanged.connect(self.on_spin_changed)
        inputs_layout.addWidget(self.end_spin)
        
        layout.addLayout(inputs_layout)
        
    def load_video(self, path: str):
        self.video_path = path
        self.media_player.setSource(QUrl.fromLocalFile(path))
        
        self.placeholder_label.hide()
        self.video_widget.show()
        
        self.play_btn.setEnabled(True)
        self.range_slider.setEnabled(True)
        
        self.media_player.pause()
        self.play_btn.setText("▶")
        
    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_btn.setText("▶")
        else:
            # Restart if at end of trim range
            end_ms = int(self.end_spin.value() * 1000)
            if self.media_player.position() >= end_ms - 100 and end_ms > 0:
                self.media_player.setPosition(int(self.start_spin.value() * 1000))
            self.media_player.play()
            self.play_btn.setText("⏸")
            
    def toggle_mute(self):
        if self.audio_output.isMuted():
            self.audio_output.setMuted(False)
            self.vol_btn.setText("🔊")
        else:
            self.audio_output.setMuted(True)
            self.vol_btn.setText("🔇")
            
    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)
        if value == 0:
            self.vol_btn.setText("🔇")
        else:
            self.vol_btn.setText("🔊")
            
    def format_time(self, ms):
        s = ms // 1000
        m = s // 60
        s = s % 60
        return f"{m:02d}:{s:02d}"
        
    def position_changed(self, position):
        if self.duration > 0:
            self.time_label.setText(f"{self.format_time(position)} / {self.format_time(int(self.duration*1000))}")
            
        # Stop at trim end
        end_ms = int(self.end_spin.value() * 1000)
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            if position >= end_ms and end_ms > 0:
                self.media_player.pause()
                self.play_btn.setText("▶")
                self.media_player.setPosition(int(self.start_spin.value() * 1000))
        
    def duration_changed(self, duration):
        if duration > 0:
            self.duration = duration / 1000.0
            self._updating_inputs = True
            self.start_spin.setMaximum(self.duration)
            self.end_spin.setMaximum(self.duration)
            self.end_spin.setValue(self.duration)
            self._updating_inputs = False
            self.time_label.setText(f"00:00 / {self.format_time(duration)}")
            
            # Initial frame preview
            self.media_player.setPosition(0)
            self.media_player.pause()

    def on_range_changed(self, min_val, max_val, active_handle):
        if self._updating_inputs or self.duration == 0: return
        self._updating_inputs = True
        
        start_sec = min_val * self.duration
        end_sec = max_val * self.duration
        
        self.start_spin.setValue(start_sec)
        self.end_spin.setValue(end_sec)
        
        # Seek to the handle being dragged to show live preview
        if active_handle == 'max':
            self.media_player.setPosition(int(end_sec * 1000))
        else:
            self.media_player.setPosition(int(start_sec * 1000))
            
        self._updating_inputs = False
        self.trim_points_changed.emit(start_sec, end_sec)
        
    def on_spin_changed(self):
        if self._updating_inputs or self.duration == 0: return
        self._updating_inputs = True
        
        start_sec = self.start_spin.value()
        end_sec = self.end_spin.value()
        
        if start_sec >= end_sec:
            start_sec = end_sec - 0.1
            self.start_spin.setValue(start_sec)
            
        min_val = start_sec / self.duration
        max_val = end_sec / self.duration
        
        self.range_slider.setValues(min_val, max_val)
        
        # Seek to start
        self.media_player.setPosition(int(start_sec * 1000))
        
        self._updating_inputs = False
        self.trim_points_changed.emit(start_sec, end_sec)
        
    def get_start_end_seconds(self):
        return self.start_spin.value(), self.end_spin.value()
        
    def close(self):
        self.media_player.stop()

class MediaPoolWidget(QFrame):
    """Proje Medya Kütüphanesi (Media Pool)"""
    media_selected = pyqtSignal(str) # file_path
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = MediaManager()
        self.setAcceptDrops(True)
        self.init_ui()
        
    def init_ui(self):
        self.setObjectName("media_pool")
        self.setStyleSheet("""
            #media_pool {
                background-color: #121212;
                border-top: 1px solid #2a2a2a;
            }
            QListWidget {
                background-color: #1a1a1a;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                outline: 0;
            }
            QListWidget::item {
                color: #e0e0e0;
                padding: 10px;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #00a8ff;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #252525;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("📁 Proje Medyası")
        title.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 16px; background: transparent;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = QPushButton("+ Medya Ekle")
        add_btn.setStyleSheet("background-color: #2d2d2d; color: white; border-radius: 4px; padding: 5px 15px; font-weight: bold;")
        add_btn.clicked.connect(self.browse_files)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Search Bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Medya ara...")
        self.search_bar.setStyleSheet("""
            QLineEdit {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 4px;
                padding: 8px 12px;
                color: #e0e0e0;
                margin-bottom: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #00a8ff;
            }
        """)
        self.search_bar.textChanged.connect(self.filter_media)
        layout.addWidget(self.search_bar)
        
        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(120, 90))
        self.list_widget.setSpacing(10)
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        layout.addWidget(self.list_widget)
        
    def filter_media(self, text):
        search_text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setHidden(search_text not in item.text().lower())
            
    def browse_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Medya Seç",
            "",
            "Medya Dosyaları (*.mp4 *.mov *.avi *.mkv *.mp3 *.wav *.aac);;Tüm Dosyalar (*)"
        )
        for f in files:
            self.add_file(f)
            
    def add_file(self, file_path: str):
        info = self.manager.add_media(file_path)
        if info:
            # Check if already added
            for i in range(self.list_widget.count()):
                if self.list_widget.item(i).data(Qt.ItemDataRole.UserRole) == file_path:
                    return
            
            item = QListWidgetItem()
            item.setText(info['name'])
            item.setData(Qt.ItemDataRole.UserRole, info['path'])
            item.setToolTip(f"{info['name']}\\nSüre: {info['duration']:.1f} sn")
            
            if info['thumbnail']:
                # Scale thumbnail
                scaled_pixmap = info['thumbnail'].scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                item.setIcon(QIcon(scaled_pixmap))
            else:
                # Placeholder for audio
                pixmap = QPixmap(120, 90)
                pixmap.fill(QColor("#2d2d2d"))
                painter = QPainter(pixmap)
                painter.setPen(QColor("#a0a0a0"))
                font = painter.font()
                font.setPointSize(24)
                painter.setFont(font)
                painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "🎵")
                painter.end()
                item.setIcon(QIcon(pixmap))
                
            self.list_widget.addItem(item)
            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.list_widget.setStyleSheet("background-color: #252525; border: 2px solid #00a8ff;")
            
    def dragLeaveEvent(self, event):
        self.list_widget.setStyleSheet("background-color: #1a1a1a; border: 1px solid #2a2a2a;")
        
    def dropEvent(self, event):
        self.list_widget.setStyleSheet("background-color: #1a1a1a; border: 1px solid #2a2a2a;")
        urls = event.mimeData().urls()
        for url in urls:
            path = url.toLocalFile()
            self.add_file(path)
            
    def on_item_double_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        self.media_selected.emit(path)
