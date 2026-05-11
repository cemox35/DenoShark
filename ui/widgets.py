"""
Custom Widgets - Özel PyQt6 bileşenleri
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox, QFrame, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QPixmap, QImage, QDrag
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
        """Sürükleme ile giriş"""
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
        """Sürükleme ile çıkış"""
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
        """Dosya bırakıldığında"""
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
        """Tıklama ile dosya seçimi"""
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


class VideoTimelineWidget(QWidget):
    """Video timeline widget - kesme noktalarını göster"""
    
    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_duration = self.total_frames / self.fps if self.fps > 0 else 0
        
        self.start_frame = 0
        self.end_frame = self.total_frames
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Timeline slider
        slider_layout = QHBoxLayout()
        
        slider_layout.addWidget(QLabel("Başlangıç:"))
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(self.total_frames)
        self.start_slider.setValue(0)
        self.start_slider.sliderMoved.connect(self.on_start_changed)
        self.start_slider.valueChanged.connect(self.on_start_changed)  # spinbox ile senkron için
        slider_layout.addWidget(self.start_slider)
        
        self.start_time_label = QLabel("0s")
        self.start_time_label.setMinimumWidth(50)
        slider_layout.addWidget(self.start_time_label)
        
        layout.addLayout(slider_layout)
        
        # End slider
        end_slider_layout = QHBoxLayout()
        
        end_slider_layout.addWidget(QLabel("Bitiş:"))
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(self.total_frames)
        self.end_slider.setValue(self.total_frames)
        self.end_slider.sliderMoved.connect(self.on_end_changed)
        self.end_slider.valueChanged.connect(self.on_end_changed)  # spinbox ile senkron için
        end_slider_layout.addWidget(self.end_slider)
        
        self.end_time_label = QLabel(f"{self.total_duration:.1f}s")
        self.end_time_label.setMinimumWidth(50)
        end_slider_layout.addWidget(self.end_time_label)
        
        layout.addLayout(end_slider_layout)
        
        # Preview frame
        self.preview_label = QLabel("Preview frame burada gösterilecek")
        self.preview_label.setMinimumHeight(150)
        self.preview_label.setStyleSheet("border: 1px solid #ccc; background-color: #000;")
        layout.addWidget(self.preview_label)
        
        self.setLayout(layout)
        
        # İlk frame'i göster
        self.show_frame(0)
    
    def on_start_changed(self, value):
        """Başlangıç değiştiğinde"""
        self.start_frame = value
        start_time = value / self.fps
        self.start_time_label.setText(f"{start_time:.1f}s")
        self.show_frame(value)
    
    def on_end_changed(self, value):
        """Bitiş değiştiğinde"""
        self.end_frame = value
        end_time = value / self.fps
        self.end_time_label.setText(f"{end_time:.1f}s")
        self.show_frame(value)
    
    def show_frame(self, frame_number):
        """Frame'i göster"""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        if ret:
            # Frame'i resize et (arayüze uyacak şekilde)
            h, w = frame.shape[:2]
            aspect_ratio = w / h
            new_h = 150
            new_w = int(new_h * aspect_ratio)
            frame = cv2.resize(frame, (new_w, new_h))
            
            # BGR -> RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # QImage'e dönüştür
            h, w, ch = frame.shape
            bytes_per_line = 3 * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            # Pixmap oluştur ve göster
            pixmap = QPixmap.fromImage(qt_image)
            self.preview_label.setPixmap(pixmap)
    
    def get_start_end_seconds(self):
        """Başlangıç ve bitiş zamanlarını saniye cinsinden döndür"""
        start_seconds = self.start_frame / self.fps
        end_seconds = self.end_frame / self.fps
        return start_seconds, end_seconds
    
    def close(self):
        """Kaynakları kapat"""
        self.cap.release()
