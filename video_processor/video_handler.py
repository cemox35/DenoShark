"""
Video Handler - Video bilgisi ve yönetimi
"""
import cv2
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

class VideoHandler:
    """Video dosyasını yönetir"""
    
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        self.cap = cv2.VideoCapture(str(self.video_path))
        
        if not self.cap.isOpened():
            raise ValueError(f"Video açılamadı: {video_path}")
        
        self._get_properties()
    
    def _get_properties(self):
        """Video özelliklerini al"""
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.duration_seconds = self.frame_count / self.fps if self.fps > 0 else 0
        
        logger.info(
            f"Video yüklendi: {self.video_path.name} "
            f"({self.width}x{self.height}, {self.fps}fps, {self.duration_seconds:.1f}s)"
        )
    
    def get_info(self) -> dict:
        """Video bilgilerini döndür"""
        return {
            'path': str(self.video_path),
            'fps': self.fps,
            'frame_count': self.frame_count,
            'width': self.width,
            'height': self.height,
            'duration_seconds': self.duration_seconds,
            'codec': self._get_codec()
        }
    
    def _get_codec(self) -> str:
        """Video codec'ini al"""
        codec = self.cap.get(cv2.CAP_PROP_FOURCC)
        if codec != -1:
            return "".join([chr((int(codec) >> 8 * i) & 0xFF) for i in range(4)])
        return "Unknown"
    
    def get_frame(self, frame_number: int):
        """Belirli frame'i al"""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        return frame if ret else None
    
    def close(self):
        """Video kaynağını kapat"""
        if self.cap:
            self.cap.release()
    
    def __del__(self):
        self.close()
