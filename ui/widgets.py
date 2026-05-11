"""
Custom Widgets - Özel PyQt6 bileşenleri
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
    QSpinBox, QFrame, QFileDialog, QPushButton, QDoubleSpinBox,
    QListWidget, QListWidgetItem, QLineEdit, QGraphicsView,
    QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
    QGraphicsPolygonItem, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QRect, QPoint, QPointF, QSize, QUrl, QRectF, QObject, QTimer
from PyQt6.QtGui import QPixmap, QImage, QDrag, QPainter, QColor, QBrush, QPen, QPalette, QIcon, QFont, QLinearGradient, QPolygonF, QUndoStack, QUndoCommand, QAction
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
        self.ab_mode_active = False
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
        
        # Alt Media Player (A/B Testing)
        self.alt_media_player = QMediaPlayer()
        self.alt_audio_output = QAudioOutput()
        self.alt_media_player.setAudioOutput(self.alt_audio_output)
        self.alt_audio_output.setMuted(True)
        
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
        
        ext = Path(path).suffix.lower()
        is_audio = ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a']
        
        # Eski player'ı tamamen yıkıp yeniden oluştur.
        # Bu, pause()+setSource() kombinasyonunun Qt/FFmpeg backend'de
        # oluşturduğu deadlock'ı tamamen önler.
        self.media_player.positionChanged.disconnect()
        self.media_player.durationChanged.disconnect()
        self.media_player.setSource(QUrl())
        self.media_player.deleteLater()
        self.audio_output.deleteLater()

        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)

        self.alt_media_player.setSource(QUrl())
        
        if is_audio:
            self.media_player.setVideoOutput(None)
            self.placeholder_label.setText("🎵\nSes Dosyası")
            self.placeholder_label.show()
            self.video_widget.hide()
        else:
            self.media_player.setVideoOutput(self.video_widget)
            self.placeholder_label.setText("🎬\nVideo Önizleme")
            self.placeholder_label.hide()
            self.video_widget.show()

        self.ab_mode_active = False
        self.audio_output.setMuted(False)
        self.play_btn.setEnabled(True)
        self.range_slider.setEnabled(True)
        self.play_btn.setText("▶")

        self.media_player.setSource(QUrl.fromLocalFile(path))
        
    def toggle_playback(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.alt_media_player.pause()
            self.play_btn.setText("▶")
        else:
            # Restart if at end of trim range
            end_ms = int(self.end_spin.value() * 1000)
            if self.media_player.position() >= end_ms - 100 and end_ms > 0:
                pos = int(self.start_spin.value() * 1000)
                self.media_player.setPosition(pos)
                self.alt_media_player.setPosition(pos)
            self.media_player.play()
            if self.alt_media_player.source().isValid():
                self.alt_media_player.setPosition(self.media_player.position())
                self.alt_media_player.play()
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
        self.alt_audio_output.setVolume(value / 100.0)
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
                self.alt_media_player.pause()
                self.play_btn.setText("▶")
                pos = int(self.start_spin.value() * 1000)
                self.media_player.setPosition(pos)
                self.alt_media_player.setPosition(pos)
        
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
            pos = int(end_sec * 1000)
            self.media_player.setPosition(pos)
            self.alt_media_player.setPosition(pos)
        else:
            pos = int(start_sec * 1000)
            self.media_player.setPosition(pos)
            self.alt_media_player.setPosition(pos)
            
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
        pos = int(start_sec * 1000)
        self.media_player.setPosition(pos)
        self.alt_media_player.setPosition(pos)
        
        self._updating_inputs = False
        self.trim_points_changed.emit(start_sec, end_sec)
        
    def get_start_end_seconds(self):
        return self.start_spin.value(), self.end_spin.value()
        
    def close(self):
        self.media_player.stop()
        self.alt_media_player.stop()
        
    def enable_ab_mode(self, alt_audio_path: str):
        self.alt_media_player.setSource(QUrl.fromLocalFile(alt_audio_path))
        self.alt_media_player.setPosition(self.media_player.position())
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.alt_media_player.play()
            
    def switch_audio(self, use_alt: bool):
        self.ab_mode_active = use_alt
        if use_alt:
            self.audio_output.setMuted(True)
            self.alt_audio_output.setMuted(False)
            self.alt_media_player.setPosition(self.media_player.position())
        else:
            self.audio_output.setMuted(False)
            self.alt_audio_output.setMuted(True)

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

# --- NLE Commands ---
class MoveClipCommand(QUndoCommand):
    def __init__(self, clip, old_start, old_track, new_start, new_track):
        super().__init__("Klibi Taşı")
        self.clip = clip
        self.timeline = clip.scene().views()[0] if clip.scene() and clip.scene().views() else None
        self.old_start = old_start
        self.old_track = old_track
        self.new_start = new_start
        self.new_track = new_track

    def undo(self):
        self.clip.set_position_and_track(self.old_start, self.old_track)
        if self.timeline: self.timeline.get_mix_data()

    def redo(self):
        self.clip.set_position_and_track(self.new_start, self.new_track)
        if self.timeline: self.timeline.get_mix_data()

class TrimClipCommand(QUndoCommand):
    def __init__(self, clip, old_start, old_dur, old_media_start, new_start, new_dur, new_media_start):
        super().__init__("Klibi Kırp")
        self.clip = clip
        self.timeline = clip.scene().views()[0] if clip.scene() and clip.scene().views() else None
        self.old_start = old_start
        self.old_dur = old_dur
        self.old_media_start = old_media_start
        self.new_start = new_start
        self.new_dur = new_dur
        self.new_media_start = new_media_start

    def undo(self):
        self.clip.set_geometry(self.old_start, self.old_dur, self.old_media_start)
        if self.timeline: self.timeline.get_mix_data()

    def redo(self):
        self.clip.set_geometry(self.new_start, self.new_dur, self.new_media_start)
        if self.timeline: self.timeline.get_mix_data()

class AddClipCommand(QUndoCommand):
    def __init__(self, timeline, clip):
        super().__init__("Klip Ekle")
        self.timeline = timeline
        self.clip = clip

    def undo(self):
        if self.clip.scene() == self.timeline.scene:
            self.timeline.scene.removeItem(self.clip)
        if self.clip in self.timeline.clips:
            self.timeline.clips.remove(self.clip)
        self.timeline.get_mix_data()

    def redo(self):
        if self.clip.scene() != self.timeline.scene:
            self.timeline.scene.addItem(self.clip)
        if self.clip not in self.timeline.clips:
            self.timeline.clips.append(self.clip)
        self.timeline.update_bounds_for_clip(self.clip)
        self.timeline.get_mix_data()

class DeleteClipCommand(QUndoCommand):
    def __init__(self, timeline, clips):
        super().__init__("Klip(leri) Sil")
        self.timeline = timeline
        self.clips = clips

    def undo(self):
        for clip in self.clips:
            if clip.scene() != self.timeline.scene:
                self.timeline.scene.addItem(clip)
            if clip not in self.timeline.clips:
                self.timeline.clips.append(clip)
        self.timeline.get_mix_data()

    def redo(self):
        for clip in self.clips:
            if clip.scene() == self.timeline.scene:
                self.timeline.scene.removeItem(clip)
            if clip in self.timeline.clips:
                self.timeline.clips.remove(clip)
        self.timeline.get_mix_data()

class SplitClipCommand(QUndoCommand):
    def __init__(self, timeline, clip, split_time):
        super().__init__("Klibi Böl")
        self.timeline = timeline
        self.clip = clip
        self.split_time = split_time
        
        self.orig_dur = clip.duration
        self.first_dur = split_time - clip.start_time
        self.second_dur = clip.duration - self.first_dur
        
        self.second_clip = AudioClipItem(clip.file_path, split_time, self.second_dur, clip.pps, clip.track_idx, clip.clip_type, clip.is_main)

    def undo(self):
        if self.second_clip.scene() == self.timeline.scene:
            self.timeline.scene.removeItem(self.second_clip)
        if self.second_clip in self.timeline.clips:
            self.timeline.clips.remove(self.second_clip)
        self.clip.set_geometry(self.clip.start_time, self.orig_dur)
        self.timeline.get_mix_data()

    def redo(self):
        self.clip.set_geometry(self.clip.start_time, self.first_dur)
        if self.second_clip.scene() != self.timeline.scene:
            self.timeline.scene.addItem(self.second_clip)
        if self.second_clip not in self.timeline.clips:
            self.timeline.clips.append(self.second_clip)
        self.timeline.get_mix_data()


class AudioClipItem(QGraphicsRectItem):
    """Sürüklenebilir Medya Klibi - DaVinci Resolve Style"""
    def __init__(self, file_path, start_time, duration, pixels_per_second, track_idx, clip_type='audio', is_main=False, media_start=0.0):
        super().__init__()
        self.file_path = file_path
        self.start_time = start_time
        self.duration = duration
        self.media_start = media_start
        self.pps = pixels_per_second
        self.track_idx = track_idx
        self.track_height = 50
        self.clip_type = clip_type
        self.is_main = is_main
        
        self.resize_margin = 10
        self.resize_mode = None
        self.is_resizing = False
        self.is_moving = False
        
        self._temp_start = self.start_time
        self._temp_dur = self.duration
        self._temp_track = self.track_idx
        self._temp_media_start = self.media_start
        
        self.setRect(0, 0, max(1, self.duration * self.pps), self.track_height - 10)
        self.setPos(self.start_time * self.pps, self.track_idx * self.track_height + 5)
        
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.is_hovered = False
        
        self.label = QGraphicsTextItem(Path(file_path).name, self)
        self.label.setDefaultTextColor(QColor("#ffffff"))
        self.label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.label.setPos(5, 5)
        self._update_label_and_tooltip()

    def set_position_and_track(self, start_time, track_idx):
        self.start_time = start_time
        self.track_idx = track_idx
        self.setPos(self.start_time * self.pps, self.track_idx * self.track_height + 5)
        self._update_label_and_tooltip()
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'update_bounds_for_clip'):
                view.update_bounds_for_clip(self)
        
    def set_geometry(self, start_time, duration, media_start=None):
        self.start_time = start_time
        self.duration = duration
        if media_start is not None:
            self.media_start = media_start
        self.setRect(0, 0, max(1, self.duration * self.pps), self.track_height - 10)
        self.setPos(self.start_time * self.pps, self.y())
        self._update_label_and_tooltip()
        if self.scene() and self.scene().views():
            view = self.scene().views()[0]
            if hasattr(view, 'update_bounds_for_clip'):
                view.update_bounds_for_clip(self)

    def _update_label_and_tooltip(self):
        self.setToolTip(f"{Path(self.file_path).name}\nStart: {self.start_time:.2f}s\nDuration: {self.duration:.2f}s\nMedia Offset: {self.media_start:.2f}s")
        # Ensure label fits inside clip
        rect_width = self.rect().width()
        text = Path(self.file_path).name
        if rect_width < 40:
            self.label.setPlainText(text[:3] + "..")
        else:
            self.label.setPlainText(text)

    def hoverMoveEvent(self, event):
        pos = event.pos()
        rect = self.rect()
        if pos.x() < self.resize_margin:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resize_mode = 'left'
        elif pos.x() > rect.width() - self.resize_margin:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resize_mode = 'right'
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.resize_mode = None
        super().hoverMoveEvent(event)

    def hoverEnterEvent(self, event):
        self.is_hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.is_hovered = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.resize_mode = None
        self.update()
        super().hoverLeaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.resize_mode:
                self.is_resizing = True
                self._temp_start = self.start_time
                self._temp_dur = self.duration
                self._temp_media_start = self.media_start
                self._orig_click_x = event.scenePos().x()
                event.accept()
                return
            else:
                self.is_moving = True
                self._temp_start = self.start_time
                self._temp_track = self.track_idx
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.is_resizing:
            dx = (event.scenePos().x() - self._orig_click_x) / self.pps
            if self.resize_mode == 'left':
                new_start = min(self._temp_start + self._temp_dur - 0.1, max(0, self._temp_start + dx))
                new_dur = self._temp_dur - (new_start - self._temp_start)
                new_media_start = max(0.0, self._temp_media_start + (new_start - self._temp_start))
                self.set_geometry(new_start, new_dur, new_media_start)
            elif self.resize_mode == 'right':
                new_dur = max(0.1, self._temp_dur + dx)
                self.set_geometry(self._temp_start, new_dur)
            return
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if self.is_resizing:
            self.is_resizing = False
            view = self.scene().views()[0] if self.scene() and self.scene().views() else None
            if view and (abs(self.start_time - self._temp_start) > 0.01 or abs(self.duration - self._temp_dur) > 0.01):
                cmd = TrimClipCommand(self, self._temp_start, self._temp_dur, self._temp_media_start, self.start_time, self.duration, self.media_start)
                self.set_geometry(self._temp_start, self._temp_dur, self._temp_media_start) # revert to let redo handle it
                view.undo_stack.push(cmd)
            event.accept()
            return
        elif self.is_moving:
            self.is_moving = False
            view = self.scene().views()[0] if self.scene() and self.scene().views() else None
            if view and (abs(self.start_time - self._temp_start) > 0.01 or self.track_idx != self._temp_track):
                cmd = MoveClipCommand(self, self._temp_start, self._temp_track, self.start_time, self.track_idx)
                self.set_position_and_track(self._temp_start, self._temp_track) # revert for undo
                view.undo_stack.push(cmd)
                
        super().mouseReleaseEvent(event)

    def paint(self, painter, option, widget=None):
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if self.clip_type == 'video':
            base_colors = ("#3a86ff", "#00509d")
        else:
            base_colors = ("#38b000", "#007200")

        if self.isSelected():
            color1, color2, border, pen_width = QColor(base_colors[0]), QColor(base_colors[1]), QColor("#ffffff"), 2
        elif self.is_hovered:
            color1, color2, border, pen_width = QColor(base_colors[0]).lighter(120), QColor(base_colors[1]).lighter(120), QColor("#ffffff"), 1.5
        else:
            color1, color2, border, pen_width = QColor(base_colors[0]).darker(110), QColor(base_colors[1]).darker(110), QColor(base_colors[0]), 1
            
        gradient = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        gradient.setColorAt(0.0, color1)
        gradient.setColorAt(1.0, color2)
        
        painter.setBrush(QBrush(gradient))
        pen = QPen(border, pen_width)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 5, 5)
        
        if self.clip_type == 'audio':
            painter.setPen(QPen(QColor(255, 255, 255, 40), 1))
            mid_y = rect.height() / 2
            for i in range(15, int(rect.width() - 15), 8):
                h = 8 + ((i * 13) % 20)
                painter.drawLine(int(rect.x() + i), int(mid_y - h/2), int(rect.x() + i), int(mid_y + h/2))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.GraphicsItemChange.ItemPositionChange and not self.is_resizing:
            new_pos = value
            track = round((new_pos.y() - 5) / self.track_height)
            track = max(0, track) # allow dropping on any track >= 0
            
            self.track_idx = track
            new_pos.setY(self.track_idx * self.track_height + 5)
            
            if new_pos.x() < 0:
                new_pos.setX(0)
            return new_pos
            
        elif change == QGraphicsRectItem.GraphicsItemChange.ItemPositionHasChanged and not self.is_resizing:
            self.start_time = self.scenePos().x() / self.pps
            self._update_label_and_tooltip()
            if self.scene() and self.scene().views():
                view = self.scene().views()[0]
                if hasattr(view, 'update_bounds_for_clip'):
                    view.update_bounds_for_clip(self)
        return super().itemChange(change, value)


class RealTimeAudioEngine(QObject):
    def __init__(self):
        super().__init__()
        self.players = []
        self.master_playing = False
        
    def sync_clips(self, mix_data):
        new_players = []
        
        for c in mix_data:
            # Try to find an existing player for this path
            reused_player = None
            for p in self.players:
                if p.get('path') == c['path']:
                    reused_player = p
                    self.players.remove(p)
                    break
                    
            if reused_player:
                reused_player['offset'] = c['offset_sec']
                reused_player['media_offset'] = c.get('media_offset', 0.0)
                reused_player['duration'] = c.get('duration', 60.0)
                reused_player['track'] = c['track']
                new_players.append(reused_player)
            else:
                player = QMediaPlayer()
                audio_out = QAudioOutput()
                audio_out.setVolume(1.0)
                player.setAudioOutput(audio_out)
                player.setSource(QUrl.fromLocalFile(c['path']))
                
                new_players.append({
                    'path': c['path'],
                    'player': player,
                    'output': audio_out,
                    'offset': c['offset_sec'],
                    'media_offset': c.get('media_offset', 0.0),
                    'duration': c.get('duration', 60.0),
                    'track': c['track'],
                    'is_active': False
                })
                
        # Clean up unused players
        for p in self.players:
            p['player'].stop()
            p['output'].deleteLater()
            p['player'].deleteLater()
            
        self.players = new_players
            
    def set_playing(self, is_playing, master_sec):
        self.master_playing = is_playing
        self.update_position(master_sec)
        if not is_playing:
            for p in self.players:
                p['player'].pause()
                p['is_active'] = False

    def update_position(self, master_sec):
        for p in self.players:
            t_internal = master_sec - p['offset']
            if 0 <= t_internal < p['duration']:
                target_media_pos = t_internal + p['media_offset']
                if self.master_playing:
                    if not p['is_active']:
                        p['player'].setPosition(int(target_media_pos * 1000))
                        p['player'].play()
                        p['is_active'] = True
                    else:
                        if abs(p['player'].position() - int(target_media_pos * 1000)) > 300:
                            p['player'].setPosition(int(target_media_pos * 1000))
                else:
                    p['player'].setPosition(int(target_media_pos * 1000))
                    if p['is_active']:
                        p['player'].pause()
                        p['is_active'] = False
            else:
                if p['is_active']:
                    p['player'].pause()
                    p['is_active'] = False

class AudioTimelineWidget(QGraphicsView):
    """DaVinci Resolve Style Çoklu Kanal Ses Zaman Çizelgesi"""
    
    seek_requested = pyqtSignal(float)
    timeline_changed = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setFixedHeight(220)
        
        self.setStyleSheet("""
            QGraphicsView {
                background-color: #121212;
                border: 1px solid #2a2a2a;
                border-radius: 8px;
            }
        """)
        
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setAcceptDrops(True)
        
        self.pixels_per_second = 50
        self.total_duration = 60
        self.clips = []
        self.main_video_clip = None
        self.main_audio_clip = None
        
        self.track_height = 50
        self.num_tracks = 5
        
        self.undo_stack = QUndoStack(self)
        
        self.media_manager = MediaManager()
        
        self.grid_lines = []
        self.track_backgrounds = []
        
        self._scrubbing = False
        
        self._init_playhead()
        self._update_scene_rect()
        self._draw_background()

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, AudioClipItem) or (isinstance(item, QGraphicsTextItem) and isinstance(item.parentItem(), AudioClipItem)):
            super().mousePressEvent(event)
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self._scrubbing = True
            self._handle_scrub(event)
            event.accept()
            return
            
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._scrubbing:
            self._handle_scrub(event)
            event.accept()
            return
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._scrubbing and event.button() == Qt.MouseButton.LeftButton:
            self._scrubbing = False
            event.accept()
            return
            
        super().mouseReleaseEvent(event)

    def _handle_scrub(self, event):
        scene_pos = self.mapToScene(event.pos())
        time_sec = max(0.0, min(self.total_duration, scene_pos.x() / self.pixels_per_second))
        self.update_playhead(time_sec)
        self.seek_requested.emit(time_sec)
        
    def _init_playhead(self):
        self.playhead_line = QGraphicsLineItem()
        self.playhead_line.setPen(QPen(QColor("#ff3b30"), 2))
        self.playhead_line.setZValue(100)
        self.scene.addItem(self.playhead_line)
        
        self.playhead_head = QGraphicsPolygonItem()
        poly = QPolygonF([QPointF(-8, 0), QPointF(8, 0), QPointF(0, 10)])
        self.playhead_head.setPolygon(poly)
        self.playhead_head.setBrush(QBrush(QColor("#ff3b30")))
        self.playhead_head.setPen(QPen(Qt.PenStyle.NoPen))
        self.playhead_head.setZValue(101)
        self.scene.addItem(self.playhead_head)

    def set_duration(self, duration_sec):
        if duration_sec <= 0: return
        self.total_duration = max(duration_sec, 60)
        self._update_scene_rect()
        self._draw_background()
        
    def _update_scene_rect(self):
        width = max(self.width(), self.total_duration * self.pixels_per_second)
        height = max(self.height() - 5, self.num_tracks * self.track_height)
        self.scene.setSceneRect(0, 0, width, height)
        
    def update_bounds_for_clip(self, clip):
        needs_update = False
        if clip.track_idx >= self.num_tracks:
            self.num_tracks = clip.track_idx + 1
            needs_update = True
            
        end_time = clip.start_time + clip.duration
        if end_time > self.total_duration - 5:
            self.total_duration = end_time + 20
            needs_update = True
            
        if needs_update:
            self._update_scene_rect()
            self._draw_background()

    def _draw_background(self):
        for item in self.track_backgrounds + self.grid_lines:
            if item.scene() == self.scene:
                self.scene.removeItem(item)
        self.track_backgrounds.clear()
        self.grid_lines.clear()
        
        width = self.scene.width()
        
        for i in range(self.num_tracks):
            y = i * self.track_height
            bg_color = QColor("#1e1e1e") if i % 2 == 0 else QColor("#181818")
            bg_rect = self.scene.addRect(0, y, width, self.track_height, QPen(Qt.PenStyle.NoPen), QBrush(bg_color))
            bg_rect.setZValue(-10)
            self.track_backgrounds.append(bg_rect)
            
            border_line = self.scene.addLine(0, y + self.track_height, width, y + self.track_height, QPen(QColor("#2a2a2a")))
            border_line.setZValue(-9)
            self.track_backgrounds.append(border_line)
            
            track_name = f"V1" if i == 0 else f"A{i}"
            text = self.scene.addText(track_name)
            text.setDefaultTextColor(QColor("#a0a0a0") if i == 0 else QColor("#666666"))
            text.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            text.setPos(5, y + (self.track_height/2) - 10)
            text.setZValue(-8)
            self.track_backgrounds.append(text)

        grid_pen = QPen(QColor("#333333"), 1, Qt.PenStyle.DashLine)
        for i in range(0, int(self.total_duration) + 1, 5):
            x = i * self.pixels_per_second
            line = self.scene.addLine(x, 0, x, self.scene.height(), grid_pen)
            line.setZValue(-9)
            self.grid_lines.append(line)
            
            if i % 10 == 0:
                t_text = self.scene.addText(f"{i}s")
                t_text.setDefaultTextColor(QColor("#888888"))
                t_text.setFont(QFont("Segoe UI", 7))
                t_text.setPos(x + 2, 0)
                t_text.setZValue(-8)
                self.grid_lines.append(t_text)

    def update_playhead(self, current_time_sec):
        x = current_time_sec * self.pixels_per_second
        self.playhead_line.setLine(x, 0, x, self.scene.height())
        self.playhead_head.setPos(x, 0)
        self.ensureVisible(x, 0, 1, self.height(), 50, 0)
        
    def set_main_video(self, file_path, duration_sec):
        if self.main_video_clip:
            if self.main_video_clip.scene() == self.scene:
                self.scene.removeItem(self.main_video_clip)
            if self.main_video_clip in self.clips:
                self.clips.remove(self.main_video_clip)
                
        if self.main_audio_clip:
            if self.main_audio_clip.scene() == self.scene:
                self.scene.removeItem(self.main_audio_clip)
            if self.main_audio_clip in self.clips:
                self.clips.remove(self.main_audio_clip)
            
        self.main_video_clip = AudioClipItem(file_path, 0, duration_sec, self.pixels_per_second, 0, clip_type='video', is_main=True)
        self.scene.addItem(self.main_video_clip)
        self.clips.append(self.main_video_clip)
        
        self.main_audio_clip = AudioClipItem(file_path, 0, duration_sec, self.pixels_per_second, 1, clip_type='audio', is_main=True)
        self.scene.addItem(self.main_audio_clip)
        self.clips.append(self.main_audio_clip)
        
        if duration_sec > self.total_duration:
            self.set_duration(duration_sec + 20)
            
        self.get_mix_data()
            
    def add_clip(self, file_path, duration_sec=None):
        if duration_sec is None:
            info = self.media_manager.add_media(file_path)
            duration_sec = info['duration'] if info else 10.0
                
        track_idx = 2 + (len([c for c in self.clips if not c.is_main]) % (self.num_tracks - 2))
        clip = AudioClipItem(file_path, 0, duration_sec, self.pixels_per_second, track_idx, clip_type='audio', is_main=False)
        cmd = AddClipCommand(self, clip)
        self.undo_stack.push(cmd)

    def get_mix_data(self):
        """Returns sorted list of audio items for backend processing"""
        mix_data = []
        for c in self.clips:
            if c.clip_type == 'audio':
                mix_data.append({'path': c.file_path, 'offset_sec': c.start_time, 'media_offset': c.media_start, 'track': c.track_idx, 'duration': c.duration})
        mix_data = sorted(mix_data, key=lambda x: (x['track'], x['offset_sec']))
        self.timeline_changed.emit(mix_data)
        return mix_data

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, QGraphicsTextItem):
            item = item.parentItem()
            
        if isinstance(item, AudioClipItem):
            menu = QMenu(self)
            split_action = menu.addAction("✂️ Playhead'de Böl (Split)")
            duplicate_action = menu.addAction("📋 Çoğalt (Duplicate)")
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ Sil (Delete)")
            
            action = menu.exec(event.globalPos())
            if action == split_action:
                self.split_clip(item)
            elif action == duplicate_action:
                self.duplicate_clip(item)
            elif action == delete_action:
                self.delete_clips([item])
        else:
            super().contextMenuEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete or event.key() == Qt.Key.Key_Backspace:
            selected = [item for item in self.scene.selectedItems() if isinstance(item, AudioClipItem) and not item.is_main]
            if selected:
                self.delete_clips(selected)
        elif event.key() == Qt.Key.Key_Z and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo_stack.undo()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.undo_stack.redo()
        else:
            super().keyPressEvent(event)

    def delete_clips(self, clips):
        cmd = DeleteClipCommand(self, clips)
        self.undo_stack.push(cmd)

    def split_clip(self, clip):
        playhead_time = self.playhead_line.line().x1() / self.pixels_per_second
        if clip.start_time + 0.1 < playhead_time < clip.start_time + clip.duration - 0.1:
            cmd = SplitClipCommand(self, clip, playhead_time)
            self.undo_stack.push(cmd)

    def duplicate_clip(self, clip):
        new_track = clip.track_idx + 1
        new_clip = AudioClipItem(clip.file_path, clip.start_time, clip.duration, self.pixels_per_second, new_track, clip.clip_type, is_main=False)
        cmd = AddClipCommand(self, new_clip)
        self.undo_stack.push(cmd)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("QGraphicsView { background-color: #1a1a1a; border: 2px solid #00a8ff; border-radius: 8px; }")
            
    def dragLeaveEvent(self, event):
        self.setStyleSheet("QGraphicsView { background-color: #121212; border: 1px solid #2a2a2a; border-radius: 8px; }")
        
    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        urls = event.mimeData().urls()
        
        drop_pos = self.mapToScene(event.position().toPoint())
        start_time = max(0.0, drop_pos.x() / self.pixels_per_second)
        track_idx = max(0, min(self.num_tracks - 1, int(drop_pos.y() / self.track_height)))
        
        from pathlib import Path
        for url in urls:
            path = url.toLocalFile()
            if not path: continue
            
            # Detect type
            # Audio dosyası mı video dosyası mı?
            ext = Path(path).suffix.lower()
            clip_type = 'audio' if ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a'] else 'video'
            
            info = self.media_manager.add_media(path)
            duration = info.get('duration', 10.0) if info else 10.0
            
            clip = AudioClipItem(path, start_time, duration, self.pixels_per_second, track_idx, clip_type=clip_type, is_main=False)
            cmd = AddClipCommand(self, clip)
            self.undo_stack.push(cmd)
            start_time += duration + 0.5
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scene_rect()
        self._draw_background()
