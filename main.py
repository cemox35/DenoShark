#!/usr/bin/env python3
"""
DenoShark - Nişanlı için Video Düzenleme Uygulaması

Ana giriş noktası
"""
import sys
import traceback
import warnings
from pathlib import Path

# imageio_ffmpeg ve pkg_resources uyarılarını gizle
warnings.filterwarnings("ignore", category=UserWarning, module="imageio_ffmpeg")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui import MainWindow
from utils.logger import logger

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Tüm yakalanmayan hataları yakalayan global hata yöneticisi (Global Exception Handler)"""
    # Hatayı logla
    logger.error("Yakalanmayan bir hata oluştu:", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Hata metnini oluştur
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    # Kullanıcıya gösterilecek hata mesajı kutusu
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Icon.Critical)
    msg_box.setWindowTitle("Beklenmeyen Bir Hata Oluştu")
    msg_box.setText(f"Program çalışırken uygulamanın çökmesini engelleyen bir güvenlik çemberine takınıldı.\n\nHata:\n{str(exc_value)}")
    msg_box.setInformativeText("Hatayı incelemek için 'Show Details...' (Detayları Göster) butonuna tıklayabilirsiniz. Uygulama çalışmaya devam edecektir.")
    msg_box.setDetailedText(error_msg)
    
    # Tamam butonu
    msg_box.addButton("Tamam", QMessageBox.ButtonRole.AcceptRole)
    msg_box.exec()

def main():
    """Uygulamayı başlat"""
    # Global exception handler'ı sys.excepthook'a bağla
    sys.excepthook = global_exception_handler
    
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
