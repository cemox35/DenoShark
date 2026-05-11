import os
import cv2
from pathlib import Path
from PyQt6.QtGui import QImage, QPixmap
from utils.logger import setup_logger

logger = setup_logger(__name__)

class MediaManager:
    """Projedeki medyaların merkezi yönetimi (Singleton)"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MediaManager, cls).__new__(cls)
            cls._instance.media_items = {} # dict of file_path -> info
        return cls._instance

    def add_media(self, file_path: str):
        if file_path in self.media_items:
            return self.media_items[file_path]
            
        try:
            # Ses dosyası ise mutagen ile süre al
            ext = Path(file_path).suffix.lower()
            if ext in ['.mp3', '.wav', '.aac', '.ogg', '.m4a']:
                try:
                    from mutagen import File
                    audio = File(file_path)
                    duration = audio.info.length if audio else 10.0
                except Exception as e:
                    logger.error(f"Mutagen okuma hatası: {e}")
                    duration = 10.0
                    
                info = {
                    'path': file_path,
                    'name': Path(file_path).name,
                    'duration': duration,
                    'thumbnail': None,
                    'type': 'audio'
                }
                self.media_items[file_path] = info
                return info
                
            # Video zellikleri ve Thumbnail karma
            cap = cv2.VideoCapture(file_path)
            if not cap.isOpened():
                info = {
                    'path': file_path,
                    'name': Path(file_path).name,
                    'duration': 0.0,
                    'thumbnail': None,
                    'type': 'unknown'
                }
                self.media_items[file_path] = info
                return info
                
            fps = cap.get(cv2.CAP_PROP_FPS)
            frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = frames / fps if fps > 0 else 0
            
            # Extract thumbnail (ilk frame)
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            pixmap = None
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
            
            cap.release()
            
            info = {
                'path': file_path,
                'name': Path(file_path).name,
                'duration': duration,
                'thumbnail': pixmap,
                'type': 'video'
            }
            self.media_items[file_path] = info
            return info
        except Exception as e:
            logger.error(f"Media manager hata: {e}")
            return None
            
    def get_all(self):
        return list(self.media_items.values())
