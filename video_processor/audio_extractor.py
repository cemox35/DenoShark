"""
Audio Extractor - Ses çıkarma
"""
from pathlib import Path
from moviepy import VideoFileClip
import soundfile as sf
from utils.logger import setup_logger
from utils.config import SAMPLE_RATE

logger = setup_logger(__name__)

class AudioExtractor:
    """Video'dan ses çıkarma"""
    
    @staticmethod
    def extract(
        video_path: str,
        audio_output: str,
        start_time: float = 0,
        end_time: float = None
    ) -> bool:
        """
        Video'dan ses çıkar
        
        Args:
            video_path: Video dosyası
            audio_output: Çıkış ses dosyası (.wav)
            start_time: Başlangıç zamanı
            end_time: Bitiş zamanı
        """
        try:
            logger.info(f"Ses çıkarılıyor: {video_path}")
            
            video = VideoFileClip(video_path)
            
            if video.audio is None:
                logger.warning("Video ses içermiyor!")
                return False
            
            # Ses zaman aralığını ayarla (MoviePy 2.x uyumlu)
            audio = video.audio
            if start_time or end_time:
                end_time = end_time or video.duration
                duration = end_time - start_time
                # Audio'yu doğru zaman aralığında kés
                audio = audio.time_transform(lambda t: t + start_time).with_duration(duration)
            
            # Ses dosyasını kaydet
            audio.write_audiofile(
                audio_output,
                logger=None
            )
            
            video.close()
            audio.close()
            
            logger.info(f"Ses başarıyla çıkarıldı: {audio_output}")
            return True
        
        except Exception as e:
            logger.error(f"Ses çıkarılırken hata: {e}")
            return False
