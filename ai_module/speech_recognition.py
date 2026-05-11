"""
Speech Recognition - faster-whisper (CTranslate2) ile otomatik altyazı
Lighter deployment, daha hızlı işlem.
"""
import os
import json
from pathlib import Path
from datetime import timedelta
from faster_whisper import WhisperModel
from utils.logger import setup_logger
from utils.config import WHISPER_LANGUAGE

logger = setup_logger(__name__)

class SpeechRecognizer:
    """faster-whisper (CTranslate2) ile ses tanıma ve transkripsiyon"""
    
    # Kullanılabilir modeller
    AVAILABLE_MODELS = {
        "tiny": "tiny",
        "base": "base",
        "small": "small",
        "medium": "medium"
    }
    
    def __init__(self, model_name: str = "base", device: str = "cuda"):
        """
        faster-whisper modelini yükle
        
        Args:
            model_name: Model boyutu (tiny, base, small, medium)
            device: "cuda" veya "cpu"
        """
        try:
            logger.info(f"faster-whisper model yükleniyor: {model_name} ({device})")
            self.model = WhisperModel(model_name, device=device, compute_type="float32")
            self.model_name = model_name
            self.device = device
            logger.info(f"Model başarıyla yüklendi: {model_name}")
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            # CPU'ya düş
            if device == "cuda":
                logger.warning("CUDA kullanalamıyor, CPU'ya geçiliyor...")
                self.model = WhisperModel(model_name, device="cpu", compute_type="float32")
                self.device = "cpu"
            else:
                raise
    
    def transcribe(
        self,
        audio_path: str,
        language: str = None
    ) -> dict:
        """
        Sesi metne çevir
        
        Args:
            audio_path: Ses dosyası yolu
            language: Dil kodu (None = otomatik, 'tr', 'en', vb.)
        
        Returns:
            Transkripsiyon sonuçları (segments + language)
        """
        try:
            logger.info(f"Transkripsiyon başlatılıyor: {audio_path}")
            
            segments, info = self.model.transcribe(
                audio_path,
                language=language,
                verbose=False
            )
            
            # Segments'i list'e dönüştür (lazy generator olduğundan)
            segments_list = list(segments)
            
            logger.info(f"Transkripsiyon tamamlandı. Detected language: {info.language}")
            
            return {
                "success": True,
                "segments": segments_list,
                "language": info.language,
                "duration": info.duration
            }
        
        except Exception as e:
            logger.error(f"Transkripsiyon hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def segments_to_srt(self, segments: list) -> str:
        """
        Segments'i SRT formatına çevir
        
        Args:
            segments: faster-whisper'dan gelen segments
        
        Returns:
            SRT formatında metin
        """
        srt_content = ""
        for i, segment in enumerate(segments, 1):
            start_time = self._seconds_to_srt_time(segment.start)
            end_time = self._seconds_to_srt_time(segment.end)
            text = segment.text.strip()
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{text}\n\n"
        
        return srt_content
    
    def save_srt(self, audio_path: str, output_srt: str, language: str = None) -> bool:
        """
        Altyazıları SRT formatında kaydet
        
        Args:
            audio_path: Ses dosyası yolu
            output_srt: Çıktı .srt dosyası yolu
            language: Dil kodu (opsiyonel)
        
        Returns:
            Başarılı olup olmadığı
        """
        try:
            result = self.transcribe(audio_path, language=language)
            
            if not result.get("success"):
                logger.error(f"Transkripsiyon başarısız: {result.get('error')}")
                return False
            
            segments = result.get("segments", [])
            srt_content = self.segments_to_srt(segments)
            
            # Dosyayı yaz
            output_path = Path(output_srt)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            logger.info(f"Altyazılar kaydedildi: {output_srt} ({len(segments)} segment)")
            return True
        
        except Exception as e:
            logger.error(f"SRT kaydedilirken hata: {e}")
            return False
    
    def save_json(self, audio_path: str, output_json: str, language: str = None) -> bool:
        """
        Transkripsiyon sonuçlarını JSON olarak kaydet
        
        Args:
            audio_path: Ses dosyası yolu
            output_json: Çıktı .json dosyası yolu
            language: Dil kodu (opsiyonel)
        
        Returns:
            Başarılı olup olmadığı
        """
        try:
            result = self.transcribe(audio_path, language=language)
            
            if not result.get("success"):
                return False
            
            output_path = Path(output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Sonuçlar kaydedildi: {output_json}")
            return True
        
        except Exception as e:
            logger.error(f"JSON kaydedilirken hata: {e}")
            return False
    
    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """Saniyeyi SRT zaman formatına çevir (HH:MM:SS,mmm)"""
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        secs = td.seconds % 60
        millis = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

