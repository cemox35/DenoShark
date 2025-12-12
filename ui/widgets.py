"""
Custom Widgets - Özel PyQt6 bileşenleri
"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData
from PyQt6.QtGui import QPixmap, QImage, QDrag
import cv2
from pathlib import Path

class VideoDragDropWidget(QWidget):
    """Sürükle-bırak destekli video yükleme widget'ı"""
    
    video_dropped = pyqtSignal(str)  # Video yolu sinyal
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.label = QLabel("📂 Videoyu buraya sürükle veya tıkla")
        self.label.setStyleSheet(
            "border: 2px dashed #888; border-radius: 5px; "
            "padding: 20px; text-align: center; font-size: 14px; "
            "background-color: #f5f5f5;"
        )
        self.label.setMinimumHeight(100)
        layout.addWidget(self.label)
        
        self.setLayout(layout)
    
    def dragEnterEvent(self, event):
        """Sürükleme ile giriş"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet(
                "border: 2px solid #4CAF50; border-radius: 5px; "
                "padding: 20px; text-align: center; font-size: 14px; "
                "background-color: #e8f5e9;"
            )
    
    def dragLeaveEvent(self, event):
        """Sürükleme ile çıkış"""
        self.label.setStyleSheet(
            "border: 2px dashed #888; border-radius: 5px; "
            "padding: 20px; text-align: center; font-size: 14px; "
            "background-color: #f5f5f5;"
        )
    
    def dropEvent(self, event):
        """Dosya bırakıldığında"""
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if Path(file_path).suffix.lower() in ['.mp4', '.mov', '.avi', '.mkv']:
                self.video_dropped.emit(file_path)
                self.label.setText(f"✅ Video yüklendi: {Path(file_path).name}")
            else:
                self.label.setText("❌ Desteklenmeyen format")


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
