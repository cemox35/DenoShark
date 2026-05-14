#!/usr/bin/env python3
"""
DenoShark - Nişanlı için Video Düzenleme Uygulaması

Ana giriş noktası
"""
import sys
import traceback
import warnings
from pathlib import Path

# Windows DLL initialization for PyTorch MUST happen in the main thread
try:
    import torch
except Exception as e:
    pass

# imageio_ffmpeg ve pkg_resources uyarılarını gizle
warnings.filterwarnings("ignore", category=UserWarning, module="imageio_ffmpeg")
warnings.filterwarnings("ignore", category=DeprecationWarning)

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from ui import MainWindow
from utils.logger import logger
from utils.config import resource_path

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

def register_win_extension():
    """Windows kayıt defterine .deno uzantısını ve ikonunu kaydeder"""
    if sys.platform != "win32":
        return
        
    try:
        import winreg
        import os
        import ctypes
        from PyQt6.QtGui import QImage
        
        icon_path = str(resource_path("img/logo-small.ico"))
        png_path = str(resource_path("img/logo-small.png"))
        
        # Windows ikon formatı için .ico gerekir, eğer yoksa png'den çevir
        if not os.path.exists(icon_path) and os.path.exists(png_path):
            img = QImage(png_path)
            img.save(icon_path, "ICO")
            
        if os.path.exists(icon_path):
            # Uzantıyı kaydet
            key_path = r"Software\Classes\.deno"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "DenoShark.Project")
                
            prog_key_path = r"Software\Classes\DenoShark.Project"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, prog_key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, "DenoShark Projesi")
                
            # İkonu belirle
            icon_key_path = r"Software\Classes\DenoShark.Project\DefaultIcon"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, icon_key_path) as key:
                winreg.SetValue(key, "", winreg.REG_SZ, f'"{icon_path}"')
                
            # Explorer'a ikon önbelleğini güncellemesini söyle (Anında görünmesi için)
            # SHCNE_ASSOCCHANGED = 0x08000000, SHCNF_IDLIST = 0x0000
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
    except Exception as e:
        logger.error(f"Uzantı kaydedilemedi: {e}")

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
    icon_path = resource_path("img/logo-small.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
    # Windows'ta .deno dosyaları için logoyu entegre et
    register_win_extension()
        
    window = MainWindow()
    window.show()
    
    logger.info("Arayüz başlatıldı")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
