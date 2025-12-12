"""
Noise Reducer - Gürültü azaltma (Spectral Subtraction)
"""
import numpy as np
import librosa
import soundfile as sf
from utils.logger import setup_logger
from utils.config import SAMPLE_RATE

logger = setup_logger(__name__)

class NoiseReducer:
    """Spectral Subtraction yöntemi ile gürültü azaltma"""
    
    @staticmethod
    def reduce_noise(
        audio_path: str,
        output_path: str,
        noise_duration: float = 1.0,
        reduction_strength: float = 0.8
    ) -> bool:
        """
        Gürültüyü azalt (Spectral Subtraction)
        
        Args:
            audio_path: Giriş ses dosyası
            output_path: Çıkış ses dosyası
            noise_duration: Gürültü profili için kullanılacak süre (saniye)
            reduction_strength: Gürültü azaltma gücü (0-1)
        """
        try:
            logger.info(f"Gürültü azaltılıyor: {audio_path}")
            
            # Ses yükle
            y, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
            
            # Gürültü profili çıkar (ilk noise_duration saniye)
            noise_sample_count = int(noise_duration * sr)
            noise_profile = y[:noise_sample_count]
            
            # STFT hesapla
            D = librosa.stft(y)
            magnitude = np.abs(D)
            phase = np.angle(D)
            
            # Gürültü spektrumu hesapla
            noise_D = librosa.stft(noise_profile)
            noise_magnitude = np.abs(noise_D)
            noise_spectrum = np.median(noise_magnitude, axis=1, keepdims=True)
            
            # Spectral Subtraction uygula
            reduced_magnitude = magnitude - (reduction_strength * noise_spectrum)
            reduced_magnitude = np.maximum(reduced_magnitude, 0.01)  # Minimum seviye
            
            # İfadeyi yeniden oluştur
            D_reduced = reduced_magnitude * np.exp(1j * phase)
            y_reduced = librosa.istft(D_reduced)
            
            # Seslendir (normalize)
            y_reduced = np.array(y_reduced) / np.max(np.abs(y_reduced)) * 0.95
            
            # Dosyaya kaydet
            sf.write(output_path, y_reduced, sr)
            
            logger.info(f"Gürültü azaltma başarılı: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Gürültü azaltılırken hata: {e}")
            return False
