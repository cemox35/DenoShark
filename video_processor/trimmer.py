"""
Video Trimmer - Video kırpma
"""
from pathlib import Path
import subprocess
from utils.logger import setup_logger

logger = setup_logger(__name__)

class VideoTrimmer:
    """Video kırpma işlemleri"""
    
    @staticmethod
    def trim(
        input_video: str,
        output_video: str,
        start_time: float,
        end_time: float
    ) -> bool:
        """
        Videoyu kırpla
        
        Args:
            input_video: Giriş video dosyası
            output_video: Çıkış video dosyası
            start_time: Başlangıç zamanı (saniye)
            end_time: Bitiş zamanı (saniye)
        """
        try:
            logger.info(f"Video kırpılıyor: {start_time}s - {end_time}s")
            
            # FFmpeg ile video ve ses'i senkronlu kırp
            # Alternatif: trim filter'ı kullan (daha güvenilir)
            duration = end_time - start_time
            
            cmd = [
                'ffmpeg',
                '-i', str(input_video),
                '-vf', f'trim=start={start_time}:end={end_time},setpts=PTS-STARTPTS',  # Video trim
                '-af', f'atrim=start={start_time}:end={end_time},asetpts=PTS-STARTPTS',  # Audio trim
                '-c:v', 'libx264',  # Video re-encode (kara ekran sorunu olmazsa copy kullan)
                '-c:a', 'aac',      # Audio codec
                '-y',               # Varsa overwrite et
                str(output_video)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            logger.info(f"Video başarıyla kırpıldı: {output_video}")
            return True
        
        except Exception as e:
            logger.error(f"Video kırpılırken hata: {e}")
            return False
    
    @staticmethod
    def trim_silent(
        input_video: str,
        output_video: str,
        start_time: float,
        end_time: float
    ) -> bool:
        """
        Videoyu sesi olmadan kırpla (sessiz video)
        
        Args:
            input_video: Giriş video dosyası
            output_video: Çıkış video dosyası
            start_time: Başlangıç zamanı (saniye)
            end_time: Bitiş zamanı (saniye)
        """
        try:
            logger.info(f"Sessiz video kırpılıyor: {start_time}s - {end_time}s")
            
            duration = end_time - start_time
            
            cmd = [
                'ffmpeg',
                '-i', str(input_video),
                '-vf', f'trim=start={start_time}:end={end_time},setpts=PTS-STARTPTS',  # Video trim
                '-an',              # Audio kaldır (sessiz video)
                '-c:v', 'libx264',  # Video codec
                '-y',               # Varsa overwrite et
                str(output_video)
            ]
            
            subprocess.run(cmd, capture_output=True, check=True)
            
            logger.info(f"Sessiz video başarıyla kırpıldı: {output_video}")
            return True
        
        except Exception as e:
            logger.error(f"Sessiz video kırpılırken hata: {e}")
            return False