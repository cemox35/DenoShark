#!/usr/bin/env python3
"""
DenoShark - Nişanlı için Video Düzenleme Uygulaması

Ana giriş noktası
"""
import sys
import warnings
from pathlib import Path

# imageio_ffmpeg ve pkg_resources uyarılarını gizle
warnings.filterwarnings("ignore", category=UserWarning, module="imageio_ffmpeg")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from ui import MainWindow
from utils.logger import logger

def main():
    """Uygulamayı başlat"""
    logger.info("="*50)
    logger.info("DenoShark v1.0.0 başlatılıyor...")
    logger.info("="*50)
    
    # Windows Taskbar Icon Fix
    import ctypes
    myappid = 'cemox35.denoshark.videoeditor.1'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    
    app = QApplication(sys.argv)
    
    # Uygulama ikonunu ayarla
    icon_path = Path("img/logo-small.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
    window = MainWindow()
    window.show()
    
    logger.info("Arayüz başlatıldı")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
