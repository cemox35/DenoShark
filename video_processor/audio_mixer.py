"""
Audio Mixer - Ses karıştırma ve ekleme
"""
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from utils.logger import setup_logger
from utils.config import SAMPLE_RATE

logger = setup_logger(__name__)

class AudioMixer:
    """Ses dosyalarını karıştırma"""
    
    @staticmethod
    def mix_audios(
        primary_audio: str,
        background_audio: str,
        output_audio: str,
        background_volume: float = 0.3
    ) -> bool:
        """
        Ana ses + arka plan sesi karıştır
        
        Args:
            primary_audio: Ana ses dosyası
            background_audio: Arka plan ses dosyası
            output_audio: Çıkış dosyası
            background_volume: Arka plan sesinin seviyesi (0-1)
        """
        try:
            logger.info(f"Sesler karıştırılıyor...")
            
            # Sesler yükle
            y1, sr1 = librosa.load(primary_audio, sr=SAMPLE_RATE)
            y2, sr2 = librosa.load(background_audio, sr=SAMPLE_RATE)
            
            # Uzunluk eşitle
            min_length = min(len(y1), len(y2))
            y1 = y1[:min_length]
            y2 = y2[:min_length]
            
            # Ses seviyeleri normalize et
            y1 = y1 / np.max(np.abs(y1)) if np.max(np.abs(y1)) > 0 else y1
            y2 = y2 / np.max(np.abs(y2)) if np.max(np.abs(y2)) > 0 else y2
            
            # Karıştır
            mixed = y1 + (background_volume * y2)
            
            # Normalizetle (clipping'i önle)
            max_val = np.max(np.abs(mixed))
            if max_val > 1.0:
                mixed = mixed / max_val * 0.95
            
            # Kaydet
            sf.write(output_audio, mixed, SAMPLE_RATE)
            
            logger.info(f"Sesler başarıyla karıştırıldı: {output_audio}")
            return True
        
        except Exception as e:
            logger.error(f"Sesler karıştırılırken hata: {e}")
            return False
    
    @staticmethod
    def replace_audio(
        video_path: str,
        audio_path: str,
        output_video: str
    ) -> bool:
        """
        Videodaki sesi yeni ses dosyası ile değiştir
        """
        try:
            from moviepy import VideoFileClip, AudioFileClip
            
            logger.info(f"Video sesi değiştiriliyors...")
            
            video = VideoFileClip(video_path)
            audio = AudioFileClip(audio_path)
            
            # Audio'nun videoya tam sığması için süresi ayarla (MoviePy 2.x uyumlu)
            if audio.duration > video.duration:
                audio = audio.with_duration(video.duration)
            
            final_video = video.set_audio(audio)
            final_video.write_videofile(
                output_video,
                logger=None
            )
            
            video.close()
            audio.close()
            final_video.close()
            
            logger.info(f"Video ses değiştirildi: {output_video}")
            return True
        
        except Exception as e:
            logger.error(f"Video sesi değiştirilirken hata: {e}")
            return False
