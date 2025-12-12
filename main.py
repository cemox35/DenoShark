#!/usr/bin/env python3
"""
DenoShark - Nişanlı için Video Düzenleme Uygulaması

Ana giriş noktası
"""
import sys
from PyQt6.QtWidgets import QApplication
from ui import MainWindow
from utils.logger import logger

def main():
    """Uygulamayı başlat"""
    logger.info("="*50)
    logger.info("DenoShark v1.0.0 başlatılıyor...")
    logger.info("="*50)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    logger.info("Arayüz başlatıldı")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
