"""
Exporter - Video dışa aktarma
"""
from pathlib import Path
from moviepy import VideoFileClip
from utils.logger import setup_logger

logger = setup_logger(__name__)

class VideoExporter:
    """Video'yu farklı formatlara dışa aktar"""
    
    CODEC_MAP = {
        'mp4': 'libx264',
        'mov': 'mpeg4',
        'avi': 'mpeg4',
        'mkv': 'libx264'
    }
    
    @staticmethod
    def export(
        input_video: str,
        output_video: str,
        quality: str = 'hd'
    ) -> bool:
        """
        Videoyu dışa aktar
        
        Args:
            input_video: Giriş video
            output_video: Çıkış video
            quality: 'hd' (720p), 'fhd' (1080p), 'standard' (480p)
        """
        try:
            logger.info(f"Video dışa aktarılıyor ({quality}): {output_video}")
            
            video = VideoFileClip(input_video)
            
            # Kalite ayarla
            if quality == 'hd':
                bitrate = "3000k"
                fps = 30
            elif quality == 'fhd':
                bitrate = "5000k"
                fps = 30
            else:  # standard
                bitrate = "1500k"
                fps = 24
            
            # Uzantıya göre codec seç
            ext = Path(output_video).suffix.lower().lstrip('.')
            codec = VideoExporter.CODEC_MAP.get(ext, 'libx264')
            
            video.write_videofile(
                output_video,
                codec=codec,
                fps=fps,
                logger=None
            )
            
            video.close()
            logger.info(f"Video başarıyla dışa aktarıldı: {output_video}")
            return True
        
        except Exception as e:
            logger.error(f"Video dışa aktarılırken hata: {e}")
            return False
