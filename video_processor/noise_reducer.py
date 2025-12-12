"""
Noise Reducer - Gürültü azaltma (Spectral Subtraction)
"""
import numpy as np
import librosa
import soundfile as sf
from utils.logger import setup_logger
from utils.config import SAMPLE_RATE

logger = setup_logger(__name__)

class QualityMetrics:
    """Ses kalitesi metrikleri"""
    
    @staticmethod
    def calculate_snr(original: np.ndarray, processed: np.ndarray) -> float:
        """Signal-to-Noise Ratio hesapla (dB cinsinden)"""
        signal_power = np.mean(original ** 2)
        noise = original - processed
        noise_power = np.mean(noise ** 2)
        if noise_power == 0:
            return 100.0
        snr_db = 10 * np.log10(signal_power / noise_power)
        return float(np.clip(snr_db, -20, 100))
    
    @staticmethod
    def calculate_pesq_approximation(original: np.ndarray, processed: np.ndarray) -> float:
        """Algılanan ses kalitesi yaklaşımı (0-5 ölçeği)"""
        # Basitleştirilmiş PESQ benzeri skor: spektral distorsiyon + enerji farkı
        # Not: Gerçek PESQ değildir; kullanıcıya karşılaştırmalı bir fikir verir.
        min_len = min(len(original), len(processed))
        if min_len < 16:
            return 0.5
        original = original[:min_len]
        processed = processed[:min_len]

        fft_orig = np.abs(np.fft.rfft(original))
        fft_proc = np.abs(np.fft.rfft(processed))
        
        # Spektral distorsiyon
        spec_dist = float(np.mean(np.abs(fft_orig - fft_proc) / (fft_orig + 1e-10)))
        
        # Enerji korunması
        energy_orig = np.sum(original ** 2)
        energy_proc = np.sum(processed ** 2)
        energy_diff = abs(energy_orig - energy_proc) / (energy_orig + 1e-10)
        
        # Kalite puanı (0-5)
        quality = 4.5 - (spec_dist * 2.0) - (energy_diff * 1.5)
        return float(np.clip(quality, 0.5, 5.0))
    
    @staticmethod
    def estimate_noise_level(audio: np.ndarray) -> float:
        """Gürültü seviyesini tahmin et (0-1 ölçeği)"""
        # Spectrogram üzerinde sessiz bölgeleri tespit et
        S = librosa.stft(audio)
        magnitude = np.abs(S)
        
        # Ortalama ve std deviation
        mean_mag = np.mean(magnitude)
        percentile_10 = np.percentile(magnitude, 10)
        
        # Gürültü oranı
        noise_level = percentile_10 / (mean_mag + 1e-10)
        return float(np.clip(noise_level, 0, 1))

class NoiseReducer:
    """Spectral Subtraction yöntemi ile gürültü azaltma"""
    
    @staticmethod
    def auto_detect_strength(audio_path: str) -> float:
        """Ses dosyasından gürültü seviyesini tespit edip optimal güç ayarını hesapla"""
        try:
            y, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
            noise_level = QualityMetrics.estimate_noise_level(y)
            
            # Gürültü seviyesine göre güç ayarı
            if noise_level > 0.6:
                strength = 0.85  # Çok gürültülü
                logger.info(f"Çok gürültülü algılandı (seviye: {noise_level:.2f}) → Güç: 0.85")
            elif noise_level > 0.4:
                strength = 0.70  # Orta düzey gürültü
                logger.info(f"Orta düzey gürültü algılandı (seviye: {noise_level:.2f}) → Güç: 0.70")
            else:
                strength = 0.50  # Hafif gürültü
                logger.info(f"Hafif gürültü algılandı (seviye: {noise_level:.2f}) → Güç: 0.50")
            
            return strength
        except Exception as e:
            logger.error(f"Otomatik güç ayarı başarısız: {e}, varsayılan 0.70 kullanılıyor")
            return 0.70
    
    @staticmethod
    def reduce_noise(
        audio_path: str,
        output_path: str,
        noise_duration: float = 1.0,
        reduction_strength: float = 0.8,
        get_metrics: bool = False
    ) -> dict:
        """
        Gürültüyü azalt (Spectral Subtraction)
        
        Args:
            audio_path: Giriş ses dosyası
            output_path: Çıkış ses dosyası
            noise_duration: Gürültü profili için kullanılacak süre (saniye)
            reduction_strength: Gürültü azaltma gücü (0-1)
            get_metrics: Kalite metrikleri hesapla ve döndür
        
        Returns:
            dict: Başarı durumu ve metrikleri (opsiyonel)
        """
        try:
            logger.info(f"Gürültü azaltılıyor: {audio_path}")
            
            # Ses yükle
            y, sr = librosa.load(audio_path, sr=SAMPLE_RATE)
            y_original = np.array(y, dtype=np.float32)
            
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
            y_reduced = np.array(y_reduced, dtype=np.float32)
            peak = float(np.max(np.abs(y_reduced))) if len(y_reduced) else 0.0
            if peak > 0:
                y_reduced = (y_reduced / peak) * 0.95
            
            # Dosyaya kaydet
            sf.write(output_path, y_reduced, sr)
            
            logger.info(f"Gürültü azaltma başarılı: {output_path}")

            result: dict = {
                "success": True,
                "output_path": output_path,
                "used_strength": float(reduction_strength),
            }

            if get_metrics:
                min_len = min(len(y_original), len(y_reduced))
                if min_len > 0:
                    orig = y_original[:min_len]
                    proc = y_reduced[:min_len]
                    result["metrics"] = {
                        "snr_db": QualityMetrics.calculate_snr(orig, proc),
                        "quality_score": QualityMetrics.calculate_pesq_approximation(orig, proc),
                        "noise_level": QualityMetrics.estimate_noise_level(orig),
                    }
                else:
                    result["metrics"] = {
                        "snr_db": 0.0,
                        "quality_score": 0.5,
                        "noise_level": 0.0,
                    }

            return result
        
        except Exception as e:
            logger.error(f"Gürültü azaltılırken hata: {e}")
            return {"success": False, "error": str(e)}
