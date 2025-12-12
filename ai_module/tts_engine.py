"""
TTS Engine - XTTS v2 ile metin-ses dönüştürme
"""
import torch
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger(__name__)

class TTSEngine:
    """XTTS v2 ile metin-ses dönüştürme"""
    
    def __init__(self):
        """XTTS v2 modelini yükle"""
        logger.info("XTTS v2 modeli yükleniyor...")
        
        try:
            # XTTS'i importla
            from TTS.tts.models.xtts import Xtts
            from TTS.configs.xtts_config import XttsConfig
            
            # Model yapılandırması
            config = XttsConfig()
            config.load_json("pretrained_models/xtts_v2/config.json")
            
            self.model = Xtts.init_from_config(config)
            self.model.load_checkpoint(
                config,
                checkpoint_dir="pretrained_models/xtts_v2",
                use_cuda=torch.cuda.is_available()
            )
            
            self.model.eval()
            logger.info("XTTS v2 modeli yüklendi")
        
        except ImportError:
            logger.warning(
                "TTS kütüphanesi yüklü değil. "
                "pip install TTS komutu ile yükleyin"
            )
            self.model = None
    
    def synthesize(
        self,
        text: str,
        voice_sample: str,
        output_path: str,
        language: str = "tr"
    ) -> bool:
        """
        Metni sese dönüştür
        
        Args:
            text: Sentez edilecek metin
            voice_sample: Ses örneği dosyası
            output_path: Çıkış ses dosyası
            language: Dil kodu
        """
        if not self.model:
            logger.error("XTTS modeli yüklenmemiş")
            return False
        
        try:
            logger.info(f"Metin sentezleniyor: {text[:50]}...")
            
            # Gels kodu al
            gpt_cond_latent, speaker_embedding = self.model.get_conditioning_latents(
                audio_path=voice_sample,
                gpt_cond_len=30,
                gpt_cond_chunk_len=4,
                gpt_use_speaker_encoder=True
            )
            
            # Sesi sentezle
            outputs = self.model.inference(
                text=text,
                language=language,
                gpt_cond_latent=gpt_cond_latent,
                speaker_embedding=speaker_embedding,
                temperature=0.75,
                length_penalty=1.0,
                repetition_penalty=2.5,
                top_k=50,
                top_p=0.85
            )
            
            # Çıkış kaydet
            import torchaudio
            torchaudio.save(output_path, outputs["wav"], 24000)
            
            logger.info(f"Ses sentezlendi: {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Ses sentezi hatası: {e}")
            return False
