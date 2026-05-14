"""
Speech Recognition - faster-whisper (CTranslate2) ile otomatik altyazı
Lighter deployment, daha hızlı işlem.
"""
import os
import json
from pathlib import Path
from datetime import timedelta
try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None
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
    
    def __init__(self, model_name: str = "base", device: str = "cpu"):
        """
        faster-whisper modelini yükle
        
        Args:
            model_name: Model boyutu (tiny, base, small, medium)
            device: "cuda" veya "cpu"
        """
        if WhisperModel is None:
            msg = (
                "faster-whisper is not installed. Please install it in your virtualenv:\n"
                "pip install faster-whisper ctranslate2 && pip install -U sentencepiece"
            )
            logger.error(msg)
            raise ModuleNotFoundError(msg)

        # Allow automatic device selection: prefer CUDA when available, otherwise CPU.
        # Uses ctranslate2 directly — no torch import needed for this check.
        if device == "auto":
            try:
                import ctranslate2
                device = "cuda" if ctranslate2.get_cuda_device_count() > 0 else "cpu"
            except Exception:
                device = "cpu"

        # Try to initialize on requested device; on failure (DLL/driver issues) fall back to CPU.
        try:
            logger.info(f"faster-whisper model yükleniyor: {model_name} ({device})")
            self.model = WhisperModel(model_name, device=device, compute_type="float32")
            self.model_name = model_name
            self.device = device
            logger.info(f"Model başarıyla yüklendi: {model_name} on {device}")
        except Exception as e:
            logger.error(f"Model yükleme hatası ({device}): {e}")
            # If CUDA init failed, try CPU before giving up.
            if device == "cuda":
                try:
                    logger.warning("CUDA başlatılamadı — CPU moduna düşülüyor.")
                    self.model = WhisperModel(model_name, device="cpu", compute_type="float32")
                    self.model_name = model_name
                    self.device = "cpu"
                    logger.info(f"Model başarıyla yüklendi: {model_name} on cpu")
                except Exception as e2:
                    logger.error(f"CPU'ya geçişte model yükleme hatası: {e2}")
                    # Provide actionable guidance for DLL/driver issues
                    guidance = (
                        "DLL load failed (c10.dll or similar). Common fixes:\n"
                        " - Reinstall matching PyTorch (CPU-only) or correct CUDA-enabled wheel.\n"
                        " - Update GPU drivers and CUDA toolkit to match your PyTorch build.\n"
                        " - Install Microsoft Visual C++ Redistributable (2015-2022).\n"
                        "If you want a quick workaround, initialize SpeechRecognizer with device='cpu'."
                    )
                    logger.error(guidance)
                    raise
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
                word_timestamps=True
            )
            
            # Segments'i list'e dönüştür (lazy generator olduğundan)
            # Uzun cümleleri küçük parçalara (ör. max 3 saniye veya max 5-6 kelime) bölelim
            segments_list = []
            MAX_DURATION = 2.5
            MAX_WORDS = 6
            
            for segment in segments:
                if not getattr(segment, "words", None):
                    # Fallback (word_timestamps desteklenmiyorsa)
                    segments_list.append(segment)
                    continue
                
                current_words = []
                current_start = -1
                
                for word_info in segment.words:
                    if current_start == -1:
                        current_start = word_info.start
                    
                    current_words.append(word_info)
                    duration = word_info.end - current_start
                    
                    if duration >= MAX_DURATION or len(current_words) >= MAX_WORDS:
                        # Pydantic/Tuple benzeri bir yapı yerine basit dict veya özel sınıf dönebiliriz.
                        # Mevcut kod segment.start, segment.end, segment.text kullanıyor.
                        class SplitSegment:
                            pass
                        
                        s = SplitSegment()
                        s.start = current_start
                        s.end = word_info.end
                        s.text = "".join(w.word for w in current_words).strip()
                        
                        segments_list.append(s)
                        
                        current_words = []
                        current_start = -1
                
                # Kalan kelimeleri ekle
                if current_words:
                    class SplitSegment:
                        pass
                    
                    s = SplitSegment()
                    s.start = current_start
                    s.end = current_words[-1].end
                    s.text = "".join(w.word for w in current_words).strip()
                    
                    segments_list.append(s)
            
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

