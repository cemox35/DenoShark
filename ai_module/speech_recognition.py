"""
Speech Recognition - Whisper ile otomatik altyazı
"""
import whisper
from pathlib import Path
from utils.logger import setup_logger
from utils.config import WHISPER_MODEL, WHISPER_LANGUAGE

logger = setup_logger(__name__)

class SpeechRecognizer:
    """Whisper ile ses tanıma ve transkripsiyon"""
    
    def __init__(self, model_name: str = WHISPER_MODEL):
        """
        Whisper modelini yükle
        
        Args:
            model_name: Whisper model (tiny, base, small, medium, large)
        """
        logger.info(f"Whisper model yükleniyor: {model_name}")
        self.model = whisper.load_model(model_name)
        self.model_name = model_name
        logger.info(f"Model yüklendi: {model_name}")
    
    def transcribe(
        self,
        audio_path: str,
        language: str = WHISPER_LANGUAGE
    ) -> dict:
        """
        Sesi metne çevir
        
        Args:
            audio_path: Ses dosyası
            language: Dil kodu (tr, en, vb.)
        
        Returns:
            Transkripsiyon sonuçları
        """
        try:
            logger.info(f"Transkripsiyon başlatılıyor: {audio_path}")
            
            result = self.model.transcribe(
                audio=audio_path,
                language=language,
                verbose=False
            )
            
            logger.info(f"Transkripsiyon tamamlandı")
            return result
        
        except Exception as e:
            logger.error(f"Transkripsiyon hatası: {e}")
            return None
    
    def get_subtitles(self, audio_path: str) -> list:
        """
        Altyazıları al (zaman damgalı)
        
        Returns:
            List of {'start': float, 'end': float, 'text': str}
        """
        result = self.transcribe(audio_path)
        if not result:
            return []
        
        subtitles = []
        for segment in result.get('segments', []):
            subtitles.append({
                'start': segment['start'],
                'end': segment['end'],
                'text': segment['text']
            })
        
        return subtitles
    
    def save_srt(self, audio_path: str, output_srt: str) -> bool:
        """
        Altyazıları SRT formatında kaydet
        """
        try:
            subtitles = self.get_subtitles(audio_path)
            
            with open(output_srt, 'w', encoding='utf-8') as f:
                for i, sub in enumerate(subtitles, 1):
                    start = self._seconds_to_srt_time(sub['start'])
                    end = self._seconds_to_srt_time(sub['end'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{sub['text'].strip()}\n\n")
            
            logger.info(f"Altyazılar kaydedildi: {output_srt}")
            return True
        
        except Exception as e:
            logger.error(f"SRT kaydedilirken hata: {e}")
            return False
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Saniyeyi SRT zaman formatına çevir"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
