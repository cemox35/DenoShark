"""
Audio Extractor - Ses çıkarma
"""
from pathlib import Path
import subprocess
import imageio_ffmpeg
from utils.logger import setup_logger

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
            
            ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            
            cmd = [
                ffmpeg_path,
                '-i', str(video_path)
            ]
            
            if start_time > 0:
                cmd.extend(['-ss', str(start_time)])
                
            if end_time:
                duration = end_time - start_time
                if duration > 0:
                    cmd.extend(['-t', str(duration)])
                    
            cmd.extend([
                '-vn',               # Video'yu yoksay
                '-c:a', 'pcm_s16le', # WAV için standart codec
                '-ar', '44100',      # Sample rate (Librosa'nın patlamaması için garanti)
                '-y',                # Üzerine yaz
                str(audio_output)
            ])
            
            # FFmpeg'i çalıştır
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg ses çıkarma hatası: {result.stderr}")
                return False
                
            # Dosyanın gerçekten oluştuğunu doğrula
            if not Path(audio_output).exists():
                logger.error("FFmpeg başarılı döndü ama dosya oluşturulamadı!")
                return False
                
            logger.info(f"Ses başarıyla çıkarıldı: {audio_output}")
            return True
            
        except Exception as e:
            logger.error(f"Ses çıkarılırken hata: {e}")
            return False
